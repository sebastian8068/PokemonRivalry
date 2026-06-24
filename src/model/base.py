from src.model.database import engine_base
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.ext.automap import AutomapBase

Base: type[AutomapBase] = automap_base()

Base.prepare(autoload_with=engine_base)

User = Base.classes.User
Team = Base.classes.Team
Pokemon = Base.classes.Pokemon
TeamMember = Base.classes.Team_member
Item = Base.classes.Item
Ability = Base.classes.Ability
Nature = Base.classes.Nature
Move = Base.classes.Move
TypeTable = Base.classes.Type

MovePokemon = Base.classes.Move_pokemon
TypePokemon = Base.classes.Type_pokemon
AbilityPokemon = Base.classes.Ability_pokemon
