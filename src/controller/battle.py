from fastapi import APIRouter, Request, Depends, HTTPException, status
from sqlalchemy import select, func
from src.model.base import Base, User, Team, Pokemon, TeamMember, Move, TypeTable, Nature
from src.model.database import DbSession
from src.controller.login.login import get_current_user

router = APIRouter(tags=["battle"])

AbilityPokemon = Base.metadata.tables['Ability_pokemon']
MovePokemon = Base.metadata.tables['Move_pokemon']
TypePokemon = Base.metadata.tables['Type_pokemon']


@router.get("/api/battle/data")
async def get_battle_data(db: DbSession, current_user: User = Depends(get_current_user)):
    result = await db.execute(
        select(Team).where(Team.UserID == current_user.UserID, Team.IsActive == True)
    )
    active_team = result.scalar_one_or_none()
    if not active_team:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No active team")

    members_result = await db.execute(
        select(TeamMember)
        .where(TeamMember.TeamID == active_team.TeamID)
        .order_by(TeamMember.Slot)
    )
    members = members_result.scalars().all()

    player_members = []
    for m in members:
        pokemon = await db.get(Pokemon, m.PokemonID)

        type_result = await db.execute(
            select(TypeTable.Name)
            .join(TypePokemon, TypeTable.TypeID == TypePokemon.c.TypeID)
            .where(TypePokemon.c.PokemonID == m.PokemonID)
        )
        types = [row[0] for row in type_result.fetchall()]

        nature = await db.get(Nature, m.NatureID)
        nature_str = nature.StatChanged if nature else None

        moves = []
        for move_id in [m.Move1ID, m.Move2ID, m.Move3ID, m.Move4ID]:
            if move_id is not None:
                move = await db.get(Move, move_id)
                if move:
                    type_name_result = await db.execute(
                        select(TypeTable.Name).where(TypeTable.TypeID == move.TypeID)
                    )
                    type_name = type_name_result.scalar()
                    moves.append({
                        "moveId": move.MoveID,
                        "name": move.Name,
                        "typeName": type_name or "Normal",
                        "pp": move.PP,
                        "power": move.Power,
                        "accuracy": move.Accuracy,
                        "category": move.Category,
                        "effect": move.Effect,
                    })

        player_members.append({
            "slot": m.Slot,
            "pokemonId": pokemon.PokemonID,
            "pokemonName": pokemon.Name,
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
            "natureId": m.NatureID,
            "natureStatChanged": nature_str,
            "frontSpriteGIF": pokemon.FrontSpriteGIF,
            "backSpriteGIF": pokemon.BackSpriteGIF,
            "frontSpritePNG": pokemon.FrontSpritePNG,
            "types": types,
            "moves": moves,
        })

    return {
        "playerTeam": {
            "teamId": active_team.TeamID,
            "name": active_team.Name,
            "members": player_members,
        },
    }
