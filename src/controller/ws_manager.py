import json
import math
import random
import uuid
from dataclasses import dataclass, field
from typing import Dict, Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from sqlalchemy import select
from src.model.login.auth_service import decode_token
from src.model.base import Base, User, Team, Pokemon, TeamMember, Move, TypeTable, Nature
from src.model.database import SessionDep
from src.game_engine import BattlePokemon, StatusCondition, Category, calculate_damage
from src.game_engine.moves import get_move_effects

router = APIRouter(tags=["websocket"])

TypePokemon = Base.metadata.tables['Type_pokemon']


@dataclass
class BattleMon:
    pokemon: BattlePokemon
    slot: int
    hp: int
    max_hp: int
    fainted: bool = False
    move_data: list[dict] = field(default_factory=list)


@dataclass
class BattleRoom:
    p1_mon: list[BattleMon]
    p2_mon: list[BattleMon]
    p1_active: int = 0
    p2_active: int = 0
    p1_ready: bool = False
    p2_ready: bool = False
    p1_action: Optional[dict] = None
    p2_action: Optional[dict] = None
    p1_username: str = ""
    p2_username: str = ""
    turn: int = 0
    ended: bool = False
    phase: str = "choose"
    p1_switch_done: bool = False
    p2_switch_done: bool = False


class ConnectionManager:
    def __init__(self):
        self.online: Dict[int, WebSocket] = {}
        self.username_to_id: Dict[str, int] = {}
        self.id_to_username: Dict[int, str] = {}
        self.queue: list[int] = []
        self.pending_rooms: Dict[str, set[int]] = {}
        self.rooms: Dict[str, Dict[int, WebSocket]] = {}
        self.room_ids: Dict[int, str] = {}
        self.pending_challenges: Dict[int, int] = {}
        self.battles: Dict[str, BattleRoom] = {}

    async def send_json(self, ws: WebSocket, data: dict):
        await ws.send_text(json.dumps(data))

    async def broadcast_to_room(self, room_id: str, data: dict, exclude: int = None):
        for uid, ws in self.rooms.get(room_id, {}).items():
            if uid != exclude:
                await self.send_json(ws, data)

    async def _build_team_member_data(self, db, m) -> Optional[dict]:
        pokemon = await db.get(Pokemon, m.PokemonID)
        if not pokemon:
            return None

        type_result = await db.execute(
            select(TypeTable.Name)
            .join(TypePokemon, TypeTable.TypeID == TypePokemon.c.TypeID)
            .where(TypePokemon.c.PokemonID == m.PokemonID)
        )
        ptypes = [row[0] for row in type_result.fetchall()]

        nature = await db.get(Nature, m.NatureID)
        nature_str = nature.StatChanged if nature else None

        moves = []
        for move_id in [m.Move1ID, m.Move2ID, m.Move3ID, m.Move4ID]:
            if move_id is not None:
                move = await db.get(Move, move_id)
                if move:
                    tname = await db.execute(
                        select(TypeTable.Name).where(TypeTable.TypeID == move.TypeID)
                    )
                    moves.append({
                        "moveId": move.MoveID,
                        "name": move.Name,
                        "typeName": tname.scalar() or "Normal",
                        "pp": move.PP,
                        "power": move.Power,
                        "accuracy": move.Accuracy,
                        "category": move.Category,
                        "effect": move.Effect,
                    })

        bp = self._create_battle_pokemon({
            "pokemonId": pokemon.PokemonID,
            "pokemonName": pokemon.Name,
            "baseStats": {
                "hp": pokemon.Hp, "attack": pokemon.Attack, "defense": pokemon.Defense,
                "spAtk": pokemon.SpAtk, "spDef": pokemon.SpDef, "speed": pokemon.Speed,
            },
            "evs": {
                "hp": m.HpEVs, "attack": m.AttackEVs, "defense": m.DefenseEVs,
                "spAtk": m.SpAtkEVs, "spDef": m.SpDefEVs, "speed": m.SpeedEVs,
            },
            "natureStatChanged": nature_str,
            "types": ptypes,
        })

        return {
            "slot": m.Slot,
            "pokemonId": pokemon.PokemonID,
            "pokemonName": pokemon.Name,
            "hp": bp.max_hp,
            "maxHp": bp.max_hp,
            "baseStats": {
                "hp": pokemon.Hp,
                "attack": pokemon.Attack,
                "defense": pokemon.Defense,
                "spAtk": pokemon.SpAtk,
                "spDef": pokemon.SpDef,
                "speed": pokemon.Speed,
            },
            "evs": {
                "hp": m.HpEVs,
                "attack": m.AttackEVs,
                "defense": m.DefenseEVs,
                "spAtk": m.SpAtkEVs,
                "spDef": m.SpDefEVs,
                "speed": m.SpeedEVs,
            },
            "natureStatChanged": nature_str,
            "frontSpriteGIF": pokemon.FrontSpriteGIF,
            "backSpriteGIF": pokemon.BackSpriteGIF,
            "frontSpritePNG": pokemon.FrontSpritePNG,
            "types": ptypes,
            "moves": moves,
        }

    async def _build_team_data(self, user_id: int) -> Optional[list]:
        async with SessionDep() as db:
            result = await db.execute(
                select(Team).where(Team.UserID == user_id, Team.IsActive == True)
            )
            active_team = result.scalar_one_or_none()
            if not active_team:
                return None

            members_result = await db.execute(
                select(TeamMember)
                .where(TeamMember.TeamID == active_team.TeamID)
                .order_by(TeamMember.Slot)
            )
            members = members_result.scalars().all()

            team = []
            for m in members:
                data = await self._build_team_member_data(db, m)
                if data:
                    team.append(data)
            return team

    async def get_opponent_team_data(self, user_id: int) -> dict | None:
        team = await self._build_team_data(user_id)
        if not team:
            return None
        return {"name": "Opponent Team", "members": team}

    def _create_battle_pokemon(self, member: dict) -> BattlePokemon:
        return BattlePokemon(
            pokemon_id=member["pokemonId"],
            name=member["pokemonName"],
            base_stats={
                "hp": member["baseStats"]["hp"],
                "attack": member["baseStats"]["attack"],
                "defense": member["baseStats"]["defense"],
                "sp_atk": member["baseStats"]["spAtk"],
                "sp_def": member["baseStats"]["spDef"],
                "speed": member["baseStats"]["speed"],
            },
            evs={
                "hp": member["evs"]["hp"],
                "attack": member["evs"]["attack"],
                "defense": member["evs"]["defense"],
                "sp_atk": member["evs"]["spAtk"],
                "sp_def": member["evs"]["spDef"],
                "speed": member["evs"]["speed"],
            },
            nature_str=member.get("natureStatChanged"),
            types=member["types"],
        )

    def _init_battle_room(self, room_id: str, p1_id: int, p2_id: int,
                          p1_team_data: list, p2_team_data: list):
        p1_mon = []
        for m in p1_team_data:
            bp = self._create_battle_pokemon(m)
            p1_mon.append(BattleMon(
                pokemon=bp, slot=m["slot"], hp=bp.max_hp, max_hp=bp.max_hp,
                move_data=m["moves"],
            ))

        p2_mon = []
        for m in p2_team_data:
            bp = self._create_battle_pokemon(m)
            p2_mon.append(BattleMon(
                pokemon=bp, slot=m["slot"], hp=bp.max_hp, max_hp=bp.max_hp,
                move_data=m["moves"],
            ))

        self.battles[room_id] = BattleRoom(
            p1_mon=p1_mon, p2_mon=p2_mon,
            p1_username=self.id_to_username.get(p1_id, "Player 1"),
            p2_username=self.id_to_username.get(p2_id, "Player 2"),
        )

    def _get_active_mon(self, room: BattleRoom, user_id: int) -> Optional[BattleMon]:
        is_p1 = room.p1_username == self.id_to_username.get(user_id)
        team = room.p1_mon if is_p1 else room.p2_mon
        idx = room.p1_active if is_p1 else room.p2_active
        if idx < len(team):
            return team[idx]
        return None

    def _find_move_by_id(self, mon: BattleMon, move_id: int) -> Optional[dict]:
        for m in mon.move_data:
            if m["moveId"] == move_id:
                return m
        return None

    async def _execute_turn(self, room_id: str):
        room = self.battles.get(room_id)
        if not room or room.ended:
            return

        room.turn += 1
        room.p1_ready = False
        room.p2_ready = False
        p1 = room.p1_mon[room.p1_active]
        p2 = room.p2_mon[room.p2_active]

        p1_move = room.p1_action
        p2_move = room.p2_action
        room.p1_action = None
        room.p2_action = None

        p1_name = room.p1_username
        p2_name = room.p2_username
        events = []

        p1_speed = p1.pokemon.speed
        p2_speed = p2.pokemon.speed

        first_is_p1 = p1_speed >= p2_speed

        def _process_action(actor_name, action, attacker_mon, defender_mon, is_p1_attacker):
            nonlocal events
            action_type = action.get("type") if action else None

            if action_type == "move":
                move_data = self._find_move_by_id(attacker_mon, action["moveId"])
                if not move_data:
                    events.append({"type": "log", "text": f"{actor_name}'s move failed!"})
                    return

                move_name = move_data["name"]
                effects = get_move_effects(move_name)
                final_dmg = 0
                eff_value = 1.0
                crit_happened = False

                if effects:
                    for effect in effects:
                        result = effect.apply(
                            attacker_mon.pokemon, defender_mon.pokemon,
                            move_data["typeName"], move_data["category"],
                            move_data["power"],
                        )
                        final_dmg += result.damage_to_target
                        eff_value = result.effectiveness
                        if result.crit:
                            crit_happened = True
                            events.append({"type": "critical", "text": "Critical hit!"})

                    defender_mon.hp = defender_mon.pokemon.current_hp
                    if defender_mon.hp <= 0:
                        defender_mon.hp = 0
                        defender_mon.fainted = True
                else:
                    dmg = 5
                    defender_mon.hp = max(0, defender_mon.hp - dmg)
                    defender_mon.pokemon.current_hp = defender_mon.hp
                    final_dmg = dmg
                    if defender_mon.hp <= 0:
                        defender_mon.fainted = True

                eff_text = ""
                if final_dmg > 0:
                    if eff_value == 0:
                        eff_text = "It doesn't affect..."
                    elif eff_value < 1:
                        eff_text = "It's not very effective..."
                    elif eff_value > 1:
                        eff_text = "It's super effective!"

                events.append({
                    "type": "move",
                    "actor": actor_name,
                    "moveName": move_name,
                    "damage": final_dmg,
                    "effectiveness": eff_text,
                    "targetHp": defender_mon.hp,
                    "targetMaxHp": defender_mon.max_hp,
                    "fainted": defender_mon.fainted,
                    "crit": crit_happened,
                })

            elif action_type == "switch":
                new_slot = action["slot"]
                if is_p1_attacker:
                    for i, m in enumerate(room.p1_mon):
                        if m.slot == new_slot and not m.fainted:
                            room.p1_active = i
                            break
                else:
                    for i, m in enumerate(room.p2_mon):
                        if m.slot == new_slot and not m.fainted:
                            room.p2_active = i
                            break
                events.append({
                    "type": "switch",
                    "actor": actor_name,
                    "slot": new_slot,
                })

        p1_action = p1_move or {"type": "move", "moveId": 0}
        p2_action = p2_move or {"type": "move", "moveId": 0}

        if first_is_p1:
            _process_action(p1_name, p1_action, p1, p2, True)
            if not p2.fainted and not room.ended:
                _process_action(p2_name, p2_action, p2, p1, False)
        else:
            _process_action(p2_name, p2_action, p2, p1, False)
            if not p1.fainted and not room.ended:
                _process_action(p1_name, p1_action, p1, p2, True)

        p1 = room.p1_mon[room.p1_active]
        p2 = room.p2_mon[room.p2_active]

        status_events = []
        for mon_data, owner_name in [(p1, p1_name), (p2, p2_name)]:
            if not mon_data.fainted:
                status_dmg = mon_data.pokemon.apply_end_of_turn_status()
                if status_dmg > 0:
                    mon_data.hp = mon_data.pokemon.current_hp
                    if mon_data.hp <= 0:
                        mon_data.hp = 0
                        mon_data.fainted = True
                    status_events.append({
                        "type": "status_damage",
                        "actor": owner_name,
                        "damage": status_dmg,
                        "status": mon_data.pokemon.status.name if mon_data.pokemon.status else "",
                        "targetHp": mon_data.hp,
                        "targetMaxHp": mon_data.max_hp,
                        "fainted": mon_data.fainted,
                    })
                mon_data.pokemon.advance_turn()

        events.extend(status_events)

        p1_all_fainted = all(m.fainted for m in room.p1_mon)
        p2_all_fainted = all(m.fainted for m in room.p2_mon)

        room_ws = self.rooms.get(room_id, {})
        for uid in list(room_ws.keys()):
            ws = room_ws.get(uid)
            if ws:
                is_p1 = self.id_to_username.get(uid) == room.p1_username
                my_mon = room.p1_mon if is_p1 else room.p2_mon
                opp_mon = room.p2_mon if is_p1 else room.p1_mon
                my_active = room.p1_active if is_p1 else room.p2_active
                opp_active = room.p2_active if is_p1 else room.p1_active

                await self.send_json(ws, {
                    "type": "turn_result",
                    "turn": room.turn,
                    "events": events,
                    "yourActiveSlot": my_mon[my_active].slot,
                    "yourActiveName": my_mon[my_active].pokemon.name,
                    "yourActiveHp": my_mon[my_active].hp if not my_mon[my_active].fainted else 0,
                    "yourActiveMaxHp": my_mon[my_active].max_hp,
                    "yourFainted": my_mon[my_active].fainted,
                    "yourAllFainted": p1_all_fainted if is_p1 else p2_all_fainted,
                    "opponentActiveSlot": opp_mon[opp_active].slot,
                    "opponentActiveName": opp_mon[opp_active].pokemon.name,
                    "opponentActiveHp": opp_mon[opp_active].hp if not opp_mon[opp_active].fainted else 0,
                    "opponentActiveMaxHp": opp_mon[opp_active].max_hp,
                    "opponentFainted": opp_mon[opp_active].fainted,
                    "opponentAllFainted": p2_all_fainted if is_p1 else p1_all_fainted,
                })

        if p1_all_fainted or p2_all_fainted:
            room.ended = True
            winner_name = p2_name if p1_all_fainted else p1_name
            loser_name = p1_name if p1_all_fainted else p2_name
            winner_id = self.username_to_id.get(winner_name)
            loser_id = self.username_to_id.get(loser_name)

            score_change = random.randint(28, 35)
            async with SessionDep() as db:
                winner_user = await db.get(User, winner_id) if winner_id else None
                loser_user = await db.get(User, loser_id) if loser_id else None
                win_new = 0
                lose_new = 0
                if winner_user:
                    winner_user.Score += score_change
                    win_new = winner_user.Score
                if loser_user:
                    new_score = max(0, loser_user.Score - score_change)
                    loser_user.Score = new_score
                    lose_new = loser_user.Score
                await db.commit()

            for uid in list(room_ws.keys()):
                ws = room_ws.get(uid)
                if ws:
                    is_winner = self.id_to_username.get(uid) == winner_name
                    await self.send_json(ws, {
                        "type": "battle_over",
                        "result": "win" if is_winner else "loss",
                        "score_change": score_change,
                        "new_score": win_new if is_winner else lose_new,
                    })

            if room_id in self.rooms:
                del self.rooms[room_id]
            for uid in list(room_ws.keys()):
                self.room_ids.pop(uid, None)
            self.battles.pop(room_id, None)
            return

        needs_switch = []
        for uid in list(room_ws.keys()):
            is_p1 = self.id_to_username.get(uid) == room.p1_username
            my_mon = room.p1_mon if is_p1 else room.p2_mon
            my_active = room.p1_active if is_p1 else room.p2_active
            if my_active < len(my_mon) and my_mon[my_active].fainted:
                if not all(m.fainted for m in my_mon):
                    needs_switch.append(uid)
                    await self.send_json(room_ws[uid], {
                        "type": "request_switch",
                        "message": "Your Pokémon fainted! Choose a replacement.",
                    })

        if needs_switch:
            room.phase = "switch"
            room.p1_switch_done = False
            room.p2_switch_done = False
        else:
            room.phase = "choose"
            await self._notify_next_turn(room_id)

    async def _notify_next_turn(self, room_id: str):
        room_ws = self.rooms.get(room_id, {})
        for uid, ws in room_ws.items():
            await self.send_json(ws, {"type": "new_turn", "turn": self.battles[room_id].turn + 1})

    async def _check_turn_ready(self, room_id: str):
        room = self.battles.get(room_id)
        if not room or room.ended:
            return
        if room.p1_ready and room.p2_ready:
            await self._execute_turn(room_id)

    async def handle_message(self, user_id: int, data: dict):
        ws = self.online.get(user_id)
        if not ws:
            return

        msg_type = data.get("type")

        if msg_type == "find_opponent":
            if user_id in self.queue:
                return
            self.queue.append(user_id)
            await self.send_json(ws, {"type": "in_queue"})

            if len(self.queue) >= 2:
                first = self.queue[0]
                if first not in self.online:
                    self.queue.pop(0)
                    return
                self.queue.pop(0)
                if user_id in self.queue:
                    self.queue.remove(user_id)

                room_id = str(uuid.uuid4())
                opponent_id = first
                opponent_name = self.id_to_username.get(opponent_id, "Unknown")
                my_name = self.id_to_username.get(user_id, "Unknown")

                self.pending_rooms[room_id] = {user_id, opponent_id}

                await self.send_json(ws, {
                    "type": "match_found",
                    "room_id": room_id,
                    "opponent": opponent_name,
                })
                await self.send_json(self.online[opponent_id], {
                    "type": "match_found",
                    "room_id": room_id,
                    "opponent": my_name,
                })

        elif msg_type == "cancel_find":
            if user_id in self.queue:
                self.queue.remove(user_id)

        elif msg_type == "challenge":
            target_username = data.get("target", "")
            target_id = self.username_to_id.get(target_username)

            if target_id is None or target_id not in self.online:
                await self.send_json(ws, {"type": "user_online", "online": False})
                return

            if target_id == user_id:
                await self.send_json(ws, {"type": "error", "message": "You cannot challenge yourself"})
                return

            if target_id in self.room_ids:
                await self.send_json(ws, {"type": "error", "message": "User is currently in a battle"})
                return

            await self.send_json(ws, {"type": "user_online", "online": True})
            self.pending_challenges[target_id] = user_id
            await self.send_json(self.online[target_id], {
                "type": "challenge_request",
                "from": self.id_to_username.get(user_id, "Unknown"),
            })

        elif msg_type == "challenge_response":
            accepted = data.get("accepted", False)
            challenger_id = self.pending_challenges.pop(user_id, None)

            if challenger_id is None or challenger_id not in self.online:
                await self.send_json(ws, {"type": "error", "message": "Challenger is no longer online"})
                return

            challenger_ws = self.online[challenger_id]

            if not accepted:
                await self.send_json(challenger_ws, {
                    "type": "challenge_declined",
                    "from": self.id_to_username.get(user_id, "Unknown"),
                })
                return

            my_team = await self._build_team_data(user_id)
            their_team = await self._build_team_data(challenger_id)

            if not my_team or not their_team:
                await self.send_json(ws, {"type": "error", "message": "Both players need an active team"})
                await self.send_json(challenger_ws, {"type": "error", "message": "Both players need an active team"})
                return

            room_id = str(uuid.uuid4())
            self.pending_rooms[room_id] = {user_id, challenger_id}

            my_name = self.id_to_username.get(user_id, "Unknown")
            ch_name = self.id_to_username.get(challenger_id, "Unknown")

            await self.send_json(ws, {
                "type": "challenge_accepted",
                "room_id": room_id,
                "opponent": ch_name,
            })
            await self.send_json(challenger_ws, {
                "type": "challenge_accepted",
                "room_id": room_id,
                "opponent": my_name,
            })

        elif msg_type == "join_room":
            room_id = data.get("room_id", "")

            if room_id in self.pending_rooms:
                if user_id not in self.pending_rooms[room_id]:
                    await self.send_json(ws, {"type": "error", "message": "Not part of this room"})
                    return
                self.pending_rooms[room_id].discard(user_id)
                if not self.pending_rooms[room_id]:
                    del self.pending_rooms[room_id]

                self.rooms.setdefault(room_id, {})[user_id] = ws
                self.room_ids[user_id] = room_id
            elif room_id in self.rooms:
                if user_id not in self.rooms[room_id]:
                    await self.send_json(ws, {"type": "error", "message": "Not part of this room"})
                    return
                self.rooms[room_id][user_id] = ws
                self.room_ids[user_id] = room_id
            else:
                await self.send_json(ws, {"type": "error", "message": "Room not found"})
                return

            room = self.rooms[room_id]
            if len(room) == 2:
                uids = list(room.keys())
                p1_team = await self._build_team_data(uids[0])
                p2_team = await self._build_team_data(uids[1])
                if not p1_team or not p2_team:
                    for uid in uids:
                        if uid in self.online:
                            await self.send_json(self.online[uid], {
                                "type": "error",
                                "message": "One or both players don't have an active team",
                            })
                    return

                p1_name = self.id_to_username.get(uids[0], "Player 1")
                p2_name = self.id_to_username.get(uids[1], "Player 2")

                self._init_battle_room(room_id, uids[0], uids[1], p1_team, p2_team)

                for uid in uids:
                    oid = uids[0] if uids[1] == uid else uids[1]
                    team = await self._build_team_data(oid)
                    oname = self.id_to_username.get(oid, "Unknown")
                    if uid in self.online:
                        our_team = await self._build_team_data(uid)
                        await self.send_json(self.online[uid], {
                            "type": "battle_start",
                            "opponent": oname,
                            "opponent_team": {"name": "Opponent", "members": team},
                            "your_team": {"name": "Your Team", "members": our_team},
                        })

        elif msg_type == "move_action":
            room_id = self.room_ids.get(user_id)
            if not room_id or room_id not in self.battles:
                return
            room = self.battles[room_id]
            if room.ended or room.phase != "choose":
                return

            is_p1 = self.id_to_username.get(user_id) == room.p1_username
            if is_p1:
                if room.p1_ready:
                    return
                room.p1_action = {"type": "move", "moveId": data.get("moveId")}
                room.p1_ready = True
            else:
                if room.p2_ready:
                    return
                room.p2_action = {"type": "move", "moveId": data.get("moveId")}
                room.p2_ready = True

            await self.send_json(ws, {"type": "action_confirmed", "actionType": "move"})
            opponent_id = None
            for uid in self.rooms.get(room_id, {}):
                if uid != user_id:
                    opponent_id = uid
                    break
            if opponent_id and opponent_id in self.online:
                await self.send_json(self.online[opponent_id], {
                    "type": "opponent_ready",
                })

            await self._check_turn_ready(room_id)

        elif msg_type == "switch_action":
            room_id = self.room_ids.get(user_id)
            if not room_id or room_id not in self.battles:
                return
            room = self.battles[room_id]
            if room.ended:
                return

            slot = data.get("slot")
            is_p1 = self.id_to_username.get(user_id) == room.p1_username
            team = room.p1_mon if is_p1 else room.p2_mon
            target = next((m for m in team if m.slot == slot and not m.fainted), None)
            if not target:
                await self.send_json(ws, {"type": "error", "message": "Invalid switch target"})
                return

            if room.phase == "switch":
                active_idx = room.p1_active if is_p1 else room.p2_active
                if active_idx < len(team):
                    team[active_idx].fainted = True
                new_idx = next(i for i, m in enumerate(team) if m.slot == slot)
                if is_p1:
                    room.p1_active = new_idx
                    room.p1_switch_done = True
                else:
                    room.p2_active = new_idx
                    room.p2_switch_done = True

                await self.send_json(ws, {"type": "switch_done", "slot": slot})
                for uid in list(self.rooms.get(room_id, {}).keys()):
                    if uid != user_id and uid in self.online:
                        await self.send_json(self.online[uid], {
                            "type": "opponent_switch",
                            "slot": slot,
                        })

                needs_p1 = room.p1_mon[room.p1_active].fainted and not all(m.fainted for m in room.p1_mon)
                needs_p2 = room.p2_mon[room.p2_active].fainted and not all(m.fainted for m in room.p2_mon)
                p1_done = not needs_p1 or room.p1_switch_done
                p2_done = not needs_p2 or room.p2_switch_done

                if p1_done and p2_done:
                    room.phase = "choose"
                    room.p1_switch_done = False
                    room.p2_switch_done = False
                    await self._notify_next_turn(room_id)
            else:
                if is_p1:
                    if room.p1_ready:
                        return
                    room.p1_action = {"type": "switch", "slot": slot}
                    room.p1_ready = True
                else:
                    if room.p2_ready:
                        return
                    room.p2_action = {"type": "switch", "slot": slot}
                    room.p2_ready = True

                await self.send_json(ws, {"type": "action_confirmed", "actionType": "switch"})
                opponent_id = None
                for uid in self.rooms.get(room_id, {}):
                    if uid != user_id:
                        opponent_id = uid
                        break
                if opponent_id and opponent_id in self.online:
                    await self.send_json(self.online[opponent_id], {
                        "type": "opponent_ready",
                    })

                await self._check_turn_ready(room_id)

        elif msg_type == "forfeit":
            room_id = self.room_ids.get(user_id)
            if not room_id or room_id not in self.battles:
                return

            battle = self.battles[room_id]
            if battle.ended:
                return
            battle.ended = True

            loser_id = user_id
            winner_id = next((uid for uid in self.rooms.get(room_id, {}) if uid != loser_id), None)
            if winner_id is None:
                return

            loser_name = self.id_to_username.get(loser_id, "Unknown")
            winner_name = self.id_to_username.get(winner_id, "Unknown")
            score_change = random.randint(28, 35)

            async with SessionDep() as db:
                winner_user = await db.get(User, winner_id)
                loser_user = await db.get(User, loser_id)

                win_new = 0
                lose_new = 0
                if winner_user:
                    winner_user.Score += score_change
                    win_new = winner_user.Score
                if loser_user:
                    new_score = max(0, loser_user.Score - score_change)
                    loser_user.Score = new_score
                    lose_new = loser_user.Score

                await db.commit()

            winner_ws = self.online.get(winner_id)
            loser_ws = self.online.get(loser_id)
            if winner_ws:
                await self.send_json(winner_ws, {
                    "type": "battle_result",
                    "result": "win",
                    "score_change": score_change,
                    "new_score": win_new,
                    "opponent": loser_name,
                })
            if loser_ws:
                await self.send_json(loser_ws, {
                    "type": "battle_result",
                    "result": "loss",
                    "score_change": score_change,
                    "new_score": lose_new,
                    "opponent": winner_name,
                })

            if room_id in self.rooms:
                del self.rooms[room_id]
            self.room_ids.pop(winner_id, None)
            self.room_ids.pop(loser_id, None)
            self.battles.pop(room_id, None)

        elif msg_type == "switch_pokemon":
            room_id = self.room_ids.get(user_id)
            if room_id and room_id in self.rooms:
                slot = data.get("slot")
                my_name = self.id_to_username.get(user_id, "Unknown")
                await self.broadcast_to_room(room_id, {
                    "type": "switch_pokemon",
                    "slot": slot,
                    "from": my_name,
                }, exclude=user_id)

        elif msg_type == "chat_message":
            room_id = self.room_ids.get(user_id)
            if room_id and room_id in self.rooms:
                my_name = self.id_to_username.get(user_id, "Unknown")
                await self.broadcast_to_room(room_id, {
                    "type": "chat_message",
                    "from": my_name,
                    "message": data.get("message", ""),
                })

        elif msg_type == "leave_room":
            room_id = self.room_ids.pop(user_id, None)
            if room_id and room_id in self.rooms:
                if user_id in self.rooms[room_id]:
                    del self.rooms[room_id][user_id]
                await self.broadcast_to_room(room_id, {"type": "opponent_disconnected"})
                if not self.rooms[room_id]:
                    del self.rooms[room_id]
                    self.battles.pop(room_id, None)

    def disconnect(self, user_id: int) -> str | None:
        if user_id in self.queue:
            self.queue.remove(user_id)
        self.pending_challenges.pop(user_id, None)
        for k, v in list(self.pending_challenges.items()):
            if v == user_id:
                del self.pending_challenges[k]
        self.online.pop(user_id, None)
        username = self.id_to_username.pop(user_id, None)
        if username:
            self.username_to_id.pop(username, None)
        room_id = self.room_ids.get(user_id)
        return room_id


manager = ConnectionManager()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str = Query(...)):
    token_data = decode_token(token)
    if token_data is None or token_data.username is None:
        await websocket.close(code=4001)
        return

    async with SessionDep() as db:
        result = await db.execute(
            select(User).where(User.Name == token_data.username)
        )
        user = result.scalar_one_or_none()
        if user is None:
            await websocket.close(code=4001)
            return
        user_id = user.UserID
        username = user.Name

    await websocket.accept()

    manager.online[user_id] = websocket
    manager.username_to_id[username] = user_id
    manager.id_to_username[user_id] = username

    try:
        while True:
            raw = await websocket.receive_text()
            try:
                data = json.loads(raw)
                await manager.handle_message(user_id, data)
            except json.JSONDecodeError:
                await manager.send_json(websocket, {"type": "error", "message": "Invalid JSON"})
    except WebSocketDisconnect:
        room_id = manager.disconnect(user_id)
        if room_id and room_id in manager.rooms:
            for uid in list(manager.rooms[room_id].keys()):
                if uid != user_id and uid in manager.online:
                    await manager.send_json(manager.online[uid], {"type": "opponent_disconnected"})
            del manager.rooms[room_id]
            manager.battles.pop(room_id, None)
