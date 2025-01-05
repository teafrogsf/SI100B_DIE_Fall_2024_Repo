import typing as _typing
from enum import IntEnum as _IntEnum

import pygame as _pygame

from base.constants import *

if _typing.TYPE_CHECKING:
    from game_collections import SceneLike

DEBUG = False
RGBAOutput = _typing.Tuple[int, int, int, int]
ColorValue = _typing.Union[
    _pygame.Color,
    int,
    str,
    _typing.Tuple[int, int, int],
    RGBAOutput,
    _typing.Sequence[int],
]


class CharaterType(_IntEnum):
    PLAYER = get_unused_event_code()
    VILLAGER = get_unused_event_code()
    MONSTER = get_unused_event_code()
    BOSS = get_unused_event_code()


class SceneCode(_IntEnum):
    START_MENU = get_unused_event_code()
    CITY = get_unused_event_code()
    WILD = get_unused_event_code()
    BOSS_SCENE = get_unused_event_code()


# event code | 事件代码
class CollisionEventCode(_IntEnum):
    COLLISION_EVENT = get_unused_event_code()
    MOVE_ATTEMPT = get_unused_event_code()
    MOVE_ALLOW = get_unused_event_code()
    HAVE_VOLUME = (
        get_unused_event_code()
    )  # if a entiry listening this code, means that entity have collision volumn.


class SceneEventCode(_IntEnum):
    CHANGE_SCENE = get_unused_event_code()
    TELEPORT = get_unused_event_code()
    RESTART = get_unused_event_code()


# event body | 事件内容模板
class MoveAttemptBody(_typing.TypedDict):
    sender: str
    target_rect: _pygame.Rect
    charater_type: CharaterType


class MoveAllowBody(_typing.TypedDict):
    receiver: str
    target_rect: _pygame.Rect


class HaveVolumnBody(_typing.TypedDict):
    pass


class ChangeSceneEventBody(_typing.TypedDict):
    new_scene: "SceneLike"


class TeleportEventBody(_typing.TypedDict):
    scene_id: int
    position: _typing.Optional[_typing.Tuple[int, int]]


class CollisionEventBody(_typing.TypedDict):
    sender: str
    charater_type: CharaterType
