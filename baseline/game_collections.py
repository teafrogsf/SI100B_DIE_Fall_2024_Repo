"""
`base/collection.py`的扩展包

实现了游戏中常用的实体类`EntityLike`和场景类`SceneLike`。

Classes
---
EntityLike
    实体类, 继承了`pygame.sprite.Sprite`类并提供了`mask`、`rect`、`image`属性方便进行碰撞检测。
    会监听`DRAW`事件, 默认使用`self.image`进行绘制。
SceneLike
    场景类, 主要提供相机坐标, 图层控制, 以及进入与退出
"""

from typing import (
    List,
    Dict,
    Tuple,
    Set,
    Optional,
    Set,
    Any,
)
import collections

import pygame
from loguru import logger

import game_constants as c
from base import (
    EventLike,
    ListenerLike,
    GroupLike,
    Core,
    PostEventApiLike,
    listening,
)


class EntityLike(ListenerLike, pygame.sprite.Sprite):
    """
    表示游戏框架内的实体类, 继承了 `pygame.sprite.Sprite`。
    提供`image`, `mask`, `rect`属性。

    Attributes
    ---
    mask : pygame.Mask:
        返回图像的掩码, 用于碰撞检测
    rect : pygame.Rect
        实体的矩形区域, 用于定位和碰撞检测
    image : pygame.Surface
        实体图像

    Methods
    -------
    draw@DRAW
        在屏幕上绘制实体。
    """

    # attributes
    rect: pygame.Rect
    __image: Optional[pygame.Surface]

    @property
    def mask(self) -> pygame.Mask:
        """
        返回图像的掩码, 用于碰撞检测

        Returns
        -------
        pygame.Mask

        Notes
        ---
        此变量根据`self.image`生成, 不可修改
        """
        return pygame.mask.from_surface(self.image)

    @property
    def image(self) -> pygame.Surface:
        """
        实体图像。

        如果`self.__image`为None, 则返回`self.rect`大小的完全透明图像。

        Returns
        -------
        pygame.Surface
        """
        if self.__image is None:
            return pygame.Surface(self.rect.size, pygame.SRCALPHA)
        return self.__image

    @image.setter
    def image(self, image: Optional[pygame.Surface]):
        self.__image = image

    def __init__(
        self,
        rect: pygame.Rect,
        *,
        image: Optional[pygame.Surface] = None,
        post_api: Optional[PostEventApiLike] = None,
        listen_receivers: Optional[Set[str]] = None,
    ):
        """
        Parameters
        ---
        rect : pygame.Rect
            实体的矩形区域, 用于定位和碰撞检测
        image : Optional[pygame.Surface], optional, default = None
            实体图像, 传入None则会被视作`rect`大小的完全透明图像。
        post_api : (EventLike) -> None, optional, default = None
            发布事件函数, 一般使用`Core`的`add_event`
        listen_receivers : set[str], optional, default = {EVERYONE_RECEIVER, self.uuid}
            监听的接收者集合, 自动加上EVERYONE_RECEIVER与self.uuid
        """
        super().__init__(post_api=post_api, listen_receivers=listen_receivers)
        pygame.sprite.Sprite.__init__(self)

        self.rect: pygame.Rect = rect
        self.__image: Optional[pygame.Surface] = image

    @listening(c.EventCode.DRAW)
    def draw(self, event: EventLike):
        """
        在画布上绘制实体

        Listening
        ---
        DRAW : DrawEventBody
            window : pygame.Surface
                画布
            camera : tuple[int, int]
                镜头坐标（/负偏移量）
        """
        body: c.DrawEventBody = event.body
        window: pygame.Surface = body["window"]
        camera: Tuple[int, int] = body["camera"]

        rect = self.rect.move(*(-i for i in camera))
        if self.image is not None:
            window.blit(self.image, rect)


class SceneLike(GroupLike):
    """
    场景类, 主要提供相机坐标, 图层控制, 以及进入与退出

    Attributes
    ----------
    core : Core
        核心
    camera_cord : Tuple[int, int]
        相机坐标 (绘制位置的负偏移量), 初始值为`(0, 0)`
    is_activated : bool
        场景是否被激活：调用`self.into`时设置为True, 调用`self.leave`时设置为False
    layers : collections.defaultdict[int, List[ListenerLike]]
        图层。键为整数, 代表绘制顺序 (从小到大)

    Methods
    -------
    into()
        进入场景
    leave()
        离开场景
    """

    # attributes
    __core: Core
    __camera_cord: Tuple[int, int]
    is_activated: bool
    layers: collections.defaultdict[int, List[ListenerLike]]
    caches: Dict[str, Any]

    @property
    def core(self):
        """核心"""
        return self.__core

    @property
    def camera_cord(self) -> Tuple[int, int]:
        """
        相机坐标 (绘制位置的负偏移量)

        Notes
        ---
        初始值为`(0, 0)`
        """
        return self.__camera_cord

    @camera_cord.setter
    def camera_cord(self, new_cord: Tuple[int, int]) -> None:
        self.__camera_cord = new_cord

    def __init__(
        self,
        core: Core,
        *,
        listen_receivers: Optional[Set[str]] = None,
        post_api: Optional[PostEventApiLike] = None,
    ):
        """
        Parameters
        ---
        core : Core
            核心
        post_api : (EventLike) -> None, optional, default = None
            发布事件函数, 一般使用`Core`的`add_event`
        listen_receivers : set[str], optional, default = {EVERYONE_RECEIVER, self.uuid}
            监听的接收者集合, 自动加上EVERYONE_RECEIVER与self.uuid
        """
        super().__init__(
            listen_receivers=listen_receivers,
            post_api=post_api if post_api is not None else core.add_event,
        )
        self.__core: Core = core
        self.__camera_cord: Tuple[int, int] = (0, 0)
        self.layers: collections.defaultdict[int, List[ListenerLike]] = (
            collections.defaultdict(list)
        )
        self.caches: Dict[str, Any] = {}
        self.is_activated = False

    def __enter__(self):
        """
        调用`self.into`, 提供给上下文管理器的接口
        """
        self.into()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """
        调用`self.leave`, 提供给上下文管理器的接口
        """
        self.leave()
        return False

    def into(self) -> None:
        """
        进入场景, `self.is_activated`设置为`True`
        """
        self.is_activated = True
        logger.info(f"Into {self.__class__}.")

    def leave(self) -> None:
        """
        离开场景, `self.is_activated`设置为`False`
        """
        self.is_activated = False
        logger.info(f"Leave {self.__class__}.")

    def listen(self, event: EventLike):
        """
        场景本体处理事件, 场景内成员 (`self.listeners`) 处理事件 (除了DRAW事件) 。

        Notes
        ---
        - DRAW事件会被场景捕获, 不会转发给成员。场景本身的`draw`方法根据`self.layers`顺序进行逐层绘制。
        """
        self.group_listen(event)
        if event.code == c.EventCode.DRAW:
            return
        self.member_listen(event)

    @listening(c.EventCode.DRAW)
    def draw(self, event: EventLike):
        """
        根据图层顺序, 在画布上绘制实体

        Listening
        ---
        DRAW : DrawEventBody
            window : pygame.Surface
                画布
            camera : tuple[int, int]
                镜头坐标（/负偏移量）

        Notes
        ---
        根据图层的键从小到大排序图层, 逐层处理。每个图层中的对象按照列表顺序接收DRAW事件。
        """
        window = self.core.window
        camera = self.camera_cord
        draw_event = EventLike.draw_event(window, camera=camera)

        layer_ids = sorted(self.layers.keys())
        for lid in layer_ids:
            layer = self.layers[lid]
            for listener in layer:
                listener.listen(draw_event)

    @listening(c.EventCode.KILL)
    def kill(self, event: EventLike):
        """
        根据`event.body["suicide"]`提供的UUID, 从场景中删除该成员

        Listening
        ---
        KILL : KillEventBody
            suicide : str
                即将被删除成员的UUID

        Notes
        ---
        需要被删除的成员会被`self.remove_listener`删除, 并从`self.layers`中被删除。
        """
        body: c.KillEventBody = event.body
        uuid = body["suicide"]
        for i in self.layers:
            self.layers[i][:] = [j for j in self.layers[i] if j.uuid != uuid]
        super().kill(event)
