from fastapi import APIRouter, Request, HTTPException, status, Depends
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import select, delete, update
from typing import List, Optional
from src.model.login.auth_service import decode_token
from src.model.base import User, Team, Pokemon, TeamMember, Item, Ability, Nature, Move, TypeTable, Base
from src.model.database import DbSession
from src.controller.login.login import get_current_user

router = APIRouter(tags=["team"])
templates = Jinja2Templates(directory="src/view/templates")

# Junction tables not exposed as classes by automap, use metadata
AbilityPokemon = Base.metadata.tables['Ability_pokemon']
MovePokemon = Base.metadata.tables['Move_pokemon']
TypePokemon = Base.metadata.tables['Type_pokemon']


# ────────────── Pydantic schemas ──────────────

class MemberPayload(BaseModel):
    slot: int = Field(ge=1, le=6)
    pokemonId: int
    itemId: Optional[int] = None
    abilityId: int
    natureId: int
    hpEvs: int = Field(default=0, ge=0, le=252)
    attackEvs: int = Field(default=0, ge=0, le=252)
    defenseEvs: int = Field(default=0, ge=0, le=252)
    spAtkEvs: int = Field(default=0, ge=0, le=252)
    spDefEvs: int = Field(default=0, ge=0, le=252)
    speedEvs: int = Field(default=0, ge=0, le=252)
    move1Id: Optional[int] = None
    move2Id: Optional[int] = None
    move3Id: Optional[int] = None
    move4Id: Optional[int] = None

    @field_validator('hpEvs', 'attackEvs', 'defenseEvs', 'spAtkEvs', 'spDefEvs', 'speedEvs')
    @classmethod
    def ev_max(cls, v):
        if v > 252:
            raise ValueError('EV cannot exceed 252')
        return v

    @field_validator('slot')
    @classmethod
    def slot_range(cls, v):
        if v < 1 or v > 6:
            raise ValueError('Slot must be 1-6')
        return v


class SaveTeamPayload(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    isActive: bool = False
    members: List[MemberPayload] = Field(max_length=6)

    @field_validator('members')
    @classmethod
    def validate_evs_total(cls, members):
        for m in members:
            total_evs = m.hpEvs + m.attackEvs + m.defenseEvs + m.spAtkEvs + m.spDefEvs + m.speedEvs
            if total_evs > 508:
                raise ValueError(f'Total EVs for slot {m.slot} exceed 508 ({total_evs})')
        slots = [m.slot for m in members]
        if len(slots) != len(set(slots)):
            raise ValueError('Duplicate slot numbers')
        return members


class CreateTeamPayload(BaseModel):
    name: str = Field(min_length=1, max_length=50)


# ────────────── Page route ──────────────

@router.get("/team")
async def team_page(request: Request, db: DbSession):
    token = request.cookies.get("access_token")
    if not token:
        return RedirectResponse(url="/")
    token_data = decode_token(token)
    if token_data is None or token_data.username is None:
        return RedirectResponse(url="/")
    result = await db.execute(
        select(User).where(User.Name == token_data.username)
    )
    user = result.scalar_one_or_none()
    if user is None:
        return RedirectResponse(url="/")
    return templates.TemplateResponse(
        request,
        "pages/team.html",
        {"request": request, "username": user.Name, "score": user.Score},
    )


# ────────────── Team CRUD ──────────────

@router.get("/api/teams")
async def list_teams(db: DbSession, current_user: User = Depends(get_current_user)):
    result = await db.execute(
        select(Team).where(Team.UserID == current_user.UserID).order_by(Team.TeamID)
    )
    teams = result.scalars().all()
    output = []
    for team in teams:
        members_result = await db.execute(
            select(TeamMember)
            .where(TeamMember.TeamID == team.TeamID)
            .order_by(TeamMember.Slot)
        )
        member_list = members_result.scalars().all()
        member_sprites = []
        for m in member_list:
            pokemon = await db.get(Pokemon, m.PokemonID)
            if pokemon:
                member_sprites.append({
                    "slot": m.Slot,
                    "pokemonId": m.PokemonID,
                    "pokemonName": pokemon.Name,
                    "frontSprite": pokemon.FrontSpritePNG,
                })
        output.append({
            "teamId": team.TeamID,
            "name": team.Name,
            "isActive": bool(team.IsActive),
            "members": member_sprites,
        })
    return output


@router.post("/api/teams")
async def create_team(payload: CreateTeamPayload, db: DbSession, current_user: User = Depends(get_current_user)):
    team = Team(UserID=current_user.UserID, Name=payload.name, IsActive=False)
    db.add(team)
    await db.commit()
    await db.refresh(team)
    return {"teamId": team.TeamID, "name": team.Name, "isActive": False, "members": []}


@router.get("/api/teams/{team_id}")
async def get_team(team_id: int, db: DbSession, current_user: User = Depends(get_current_user)):
    team = await db.get(Team, team_id)
    if not team or team.UserID != current_user.UserID:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")

    result = await db.execute(
        select(TeamMember)
        .where(TeamMember.TeamID == team_id)
        .order_by(TeamMember.Slot)
    )
    members = result.scalars().all()

    members_out = []
    for m in members:
        pokemon = await db.get(Pokemon, m.PokemonID)
        members_out.append({
            "slot": m.Slot,
            "pokemonId": m.PokemonID,
            "pokemonName": pokemon.Name if pokemon else None,
            "frontSprite": pokemon.FrontSpritePNG if pokemon else None,
            "itemId": m.ItemID,
            "abilityId": m.AbilityID,
            "natureId": m.NatureID,
            "hpEvs": m.HpEVs,
            "attackEvs": m.AttackEVs,
            "defenseEvs": m.DefenseEVs,
            "spAtkEvs": m.SpAtkEVs,
            "spDefEvs": m.SpDefEVs,
            "speedEvs": m.SpeedEVs,
            "move1Id": m.Move1ID,
            "move2Id": m.Move2ID,
            "move3Id": m.Move3ID,
            "move4Id": m.Move4ID,
        })

    return {
        "teamId": team.TeamID,
        "name": team.Name,
        "isActive": bool(team.IsActive),
        "members": members_out,
    }


@router.put("/api/teams/{team_id}")
async def save_team(team_id: int, payload: SaveTeamPayload, db: DbSession, current_user: User = Depends(get_current_user)):
    team = await db.get(Team, team_id)
    if not team or team.UserID != current_user.UserID:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")

    team.Name = payload.name
    if payload.isActive:
        await db.execute(
            update(Team).where(Team.UserID == current_user.UserID).values(IsActive=False)
        )
        team.IsActive = True

    await db.execute(
        delete(TeamMember).where(TeamMember.TeamID == team_id)
    )

    for m in payload.members:
        member = TeamMember(
            TeamID=team_id,
            Slot=m.slot,
            PokemonID=m.pokemonId,
            NatureID=m.natureId,
            ItemID=m.itemId,
            AbilityID=m.abilityId,
            HpEVs=m.hpEvs,
            AttackEVs=m.attackEvs,
            DefenseEVs=m.defenseEvs,
            SpAtkEVs=m.spAtkEvs,
            SpDefEVs=m.spDefEvs,
            SpeedEVs=m.speedEvs,
            Move1ID=m.move1Id,
            Move2ID=m.move2Id,
            Move3ID=m.move3Id,
            Move4ID=m.move4Id,
        )
        db.add(member)

    await db.commit()
    return {"success": True}


@router.delete("/api/teams/{team_id}")
async def delete_team(team_id: int, db: DbSession, current_user: User = Depends(get_current_user)):
    team = await db.get(Team, team_id)
    if not team or team.UserID != current_user.UserID:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")
    await db.delete(team)
    await db.commit()
    return {"success": True}


@router.post("/api/teams/{team_id}/activate")
async def activate_team(team_id: int, db: DbSession, current_user: User = Depends(get_current_user)):
    team = await db.get(Team, team_id)
    if not team or team.UserID != current_user.UserID:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")

    await db.execute(
        update(Team).where(Team.UserID == current_user.UserID).values(IsActive=False)
    )
    team.IsActive = True
    await db.commit()
    return {"success": True}


# ────────────── Catalog endpoints ──────────────

@router.get("/api/pokemon")
async def list_pokemon(db: DbSession):
    result = await db.execute(
        select(Pokemon).order_by(Pokemon.PokemonID)
    )
    pokemon_list = result.scalars().all()
    output = []
    for p in pokemon_list:
        type_result = await db.execute(
            select(TypeTable.Name)
            .join(TypePokemon, TypeTable.TypeID == TypePokemon.c.TypeID)
            .where(TypePokemon.c.PokemonID == p.PokemonID)
        )
        types = [row[0] for row in type_result.fetchall()]
        output.append({
            "pokemonId": p.PokemonID,
            "name": p.Name,
            "hp": p.Hp,
            "attack": p.Attack,
            "defense": p.Defense,
            "spAtk": p.SpAtk,
            "spDef": p.SpDef,
            "speed": p.Speed,
            "frontSprite": p.FrontSpritePNG,
            "backSprite": p.BackSpritePNG,
            "types": types,
        })
    return output


@router.get("/api/pokemon/{pokemon_id}/abilities")
async def pokemon_abilities(pokemon_id: int, db: DbSession):
    result = await db.execute(
        select(Ability)
        .join(AbilityPokemon, Ability.AbilityID == AbilityPokemon.c.AbilityID)
        .where(AbilityPokemon.c.PokemonID == pokemon_id)
    )
    abilities = result.scalars().all()
    return [
        {"abilityId": a.AbilityID, "name": a.Name, "description": a.Description}
        for a in abilities
    ]


@router.get("/api/pokemon/{pokemon_id}/moves")
async def pokemon_moves(pokemon_id: int, db: DbSession):
    result = await db.execute(
        select(Move, TypeTable.Name)
        .join(MovePokemon, Move.MoveID == MovePokemon.c.MoveID)
        .join(TypeTable, Move.TypeID == TypeTable.TypeID)
        .where(MovePokemon.c.PokemonID == pokemon_id)
    )
    rows = result.all()
    return [
        {
            "moveId": row.Move.MoveID,
            "name": row.Move.Name,
            "typeId": row.Move.TypeID,
            "typeName": row[1],
            "category": row.Move.Category,
            "pp": row.Move.PP,
            "power": row.Move.Power,
            "accuracy": row.Move.Accuracy,
            "effect": row.Move.Effect,
        }
        for row in rows
    ]


@router.get("/api/items")
async def list_items(db: DbSession):
    result = await db.execute(select(Item).order_by(Item.Name))
    items = result.scalars().all()
    return [
        {"itemId": i.ItemID, "name": i.Name, "description": i.Description}
        for i in items
    ]


@router.get("/api/abilities")
async def list_abilities(db: DbSession):
    result = await db.execute(select(Ability).order_by(Ability.Name))
    abilities = result.scalars().all()
    return [
        {"abilityId": a.AbilityID, "name": a.Name, "description": a.Description}
        for a in abilities
    ]


@router.get("/api/moves")
async def list_moves(db: DbSession):
    result = await db.execute(
        select(Move, TypeTable.Name)
        .join(TypeTable, Move.TypeID == TypeTable.TypeID)
        .order_by(Move.Name)
    )
    rows = result.all()
    return [
        {
            "moveId": row.Move.MoveID,
            "name": row.Move.Name,
            "typeId": row.Move.TypeID,
            "typeName": row[1],
            "category": row.Move.Category,
            "pp": row.Move.PP,
            "power": row.Move.Power,
            "accuracy": row.Move.Accuracy,
            "effect": row.Move.Effect,
        }
        for row in rows
    ]


@router.get("/api/leaderboard")
async def leaderboard(db: DbSession):
    result = await db.execute(
        select(User).order_by(User.Score.desc()).limit(10)
    )
    users = result.scalars().all()
    return [{"username": u.Name, "score": u.Score} for u in users]


@router.get("/api/natures")
async def list_natures(db: DbSession):
    result = await db.execute(select(Nature).order_by(Nature.Name))
    natures = result.scalars().all()
    return [
        {"natureId": n.NatureID, "name": n.Name, "statChanged": n.StatChanged}
        for n in natures
    ]
