"""
`collections.py`依赖常数库

Constants
---
EVERYONE_RECEIVER
    事件的特殊接收者地址: 所有人

Methods
---
get_unused_event_code
    获取尚未被使用的事件代码, 常用于Enum中分配数字

Event Codes
---
EventCode.STEP
    刻代码, 代表主时钟过去了一刻
EventCode.DRAW
    绘制代码
EventCode.KILL
    清除代码

Event Body Templates
---
StepEventBody
    STEP事件body模板
DrawEventBody
    DRAW事件body模板
KILL事件body模板
    KILL事件body模板

"""

import pygame as _pygame
import typing as _typing
from enum import IntEnum as _IntEnum


EVERYONE_RECEIVER: _typing.Final = "constants_everyone"  # 事件接收者: 所有人

# event code
__user_event_start: _typing.Final = _pygame.USEREVENT


def get_unused_event_code() -> int:
    """
    获取一个尚未使用的事件代码

    Returns
    ---
    int
        尚未使用的事件代码
    """
    global __user_event_start
    __user_event_start += 1
    return __user_event_start


class EventCode(_IntEnum):
    STEP = get_unused_event_code()  # 通知监听者已经过去了一个游戏刻
    DRAW = get_unused_event_code()  # 绘制事件
    KILL = get_unused_event_code()  # 删除监听者事件（从群组等中删除监听者）


# event body


class StepEventBody(_typing.TypedDict):
    """
    STEP事件body模板
    """

    second: float  # 距离上一次游戏刻发生经过的时间（秒）


class DrawEventBody(_typing.TypedDict):
    """
    DRAW事件body模板
    """

    surface: _pygame.Surface  # 画布
    offset: tuple[int, int]  # 绘制偏移量


class KillEventBody(_typing.TypedDict):
    """
    KILL事件body模板
    """

    suicide: str  # 被删除监听者的UUID
