"""Messages a client may send. Anything that does not match is rejected."""
from typing import Annotated, Literal, Union

from pydantic import BaseModel, Field, TypeAdapter

from .config import MAX_TEAM_SIZE


class Queue(BaseModel):
    type: Literal["queue"]
    size: int = Field(ge=1, le=MAX_TEAM_SIZE)


class CancelQueue(BaseModel):
    type: Literal["cancel_queue"]


class CreateRoom(BaseModel):
    type: Literal["create_room"]
    size: int = Field(ge=1, le=MAX_TEAM_SIZE)


class JoinRoom(BaseModel):
    type: Literal["join_room"]
    code: str = Field(min_length=4, max_length=4)


class ChooseTeam(BaseModel):
    type: Literal["choose_team"]
    team: Literal["A", "B"]


class StartMatch(BaseModel):
    type: Literal["start"]


class Leave(BaseModel):
    type: Literal["leave"]


class SubmitWord(BaseModel):
    type: Literal["word"]
    text: str = Field(max_length=32)


ClientMessage = Annotated[
    Union[Queue, CancelQueue, CreateRoom, JoinRoom, ChooseTeam, StartMatch, Leave, SubmitWord],
    Field(discriminator="type"),
]
parse_message = TypeAdapter(ClientMessage).validate_json
