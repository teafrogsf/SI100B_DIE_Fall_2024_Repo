"""
`base/collection.py`的扩展包

实现了游戏中常用的实体类`EntityLike`、文本框`TextEntity`、图层`LayerLike`、场景`SceneLike`

Classes
---
EntityLike
    实体类, 继承了`pygame.sprite.Sprite`类并提供了`mask`、`rect`、`image`属性方便进行碰撞检测。
    会监听`DRAW`事件, 默认使用`self.image`进行绘制。
TextEntity
    文本框 (左上对齐)
LayerLike
    图层（管理绘制顺序）
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
import utils


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

    ---

    listen_receivers : set[int]
        监听的接收者 (一般包含监听发送往自己 (UUID) 以及"任何人"`EVERYONE_RECEIVER`的事件)
    listen_codes : set[int]
        监听的事件代码
    uuid : str
        监听者的通用唯一标识符, 一般是`str(id(self))`
    post_api : Optional[PostEventApiLike]
        发布事件函数, 一般使用`Core`的`add_event`

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
            surface : pygame.Surface
                画布
            offset : tuple[int, int]
                偏移量
        """
        body: c.DrawEventBody = event.body
        surface: pygame.Surface = body["surface"]
        offset: Tuple[int, int] = body["offset"]

        rect = self.rect.move(offset)
        surface.blit(self.image, rect)

        if c.DEBUG:
            # DEBUG框绘制 (红色碰撞箱, 连接到原点的直线, 碰撞箱坐标)
            RED = (255, 0, 0)
            # rect
            pygame.draw.rect(surface, RED, rect, width=1)
            pygame.draw.line(surface, RED, rect.topleft, offset, width=1)
            # font
            text_rect: pygame.Rect = rect.copy()
            text_rect.topleft = rect.bottomleft
            text_surface = utils.debug_text(f"{self.rect.topleft+self.rect.size}")
            surface.blit(text_surface, text_rect)


class LayerLike(GroupLike):
    """
    图层

    Attributes
    ----------
    layers : collections.defaultdict[int, List[ListenerLike]]
        图层。键为整数, 代表绘制顺序 (从小到大)

    ---

    listeners : set[ListenerLike]
        所有成员集合
    listen_codes :set[int]
        监听事件类型, 是群组监听类型与所有成员监听类型的并集
    listen_receivers :set[int]
        监听事件接收者, 是群组监听接收者与所有成员监听接收者的并集
    uuid : str
        监听者的通用唯一标识符, 一般是`str(id(self))`
    post_api : Optional[PostEventApiLike]
        发布事件函数, 一般使用`Core`的`add_event`

    Methods
    -------
    listen(self, event: EventLike) -> None
        场景本体处理事件, 场景内成员 (`self.listeners`) 处理事件 (除了DRAW事件) 。

    ---

    group_listen(self, event: EventLike) -> None
        群组本体处理事件
    member_listen(self, event: EventLike) -> None
        群组成员处理事件
    get_listener(self, codes: set[int], receivers: set[str]) -> set[ListenerLike]
        筛选ListenerLike
    add_listener(self, listener: ListenerLike) -> None
        添加ListenerLike
    remove_listener(self, listener: ListenerLike) -> None
        删除ListenerLike
    clear_listener(self) -> None
        清空群组
    post(self, event: EventLike) -> None
        发布事件 (`通过self.__post_api`)  (一般是发布到Core的事件队列上)

    Listening Methods
    ---
    draw@DRAW
        根据图层顺序, 在画布上绘制实体

    ---

    kill@KILL
        从群组与图层中从删除成员
    """

    # attributes
    layers: collections.defaultdict[int, List[ListenerLike]]

    def __init__(
        self,
        *,
        post_api: Optional[PostEventApiLike] = None,
        listen_receivers: Optional[Set[str]] = None,
    ):
        """
        Parameters
        ---
        post_api : (EventLike) -> None, optional, default = None
            发布事件函数, 一般使用`Core`的`add_event`
        listen_receivers : set[str], optional, default = {EVERYONE_RECEIVER, self.uuid}
            监听的接收者集合
        """
        super().__init__(post_api=post_api, listen_receivers=listen_receivers)
        self.layers: collections.defaultdict[int, List[ListenerLike]] = (
            collections.defaultdict(list)
        )
        self.is_activated = False

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
        根据图层顺序, 在画布上绘制实体。

        Listening
        ---
        DRAW : DrawEventBody
            surface : pygame.Surface
                画布
            offset : tuple[int, int]
                偏移量

        Notes
        ---
        根据图层的键从小到大排序图层, 逐层处理。每个图层中的对象按照列表顺序接收DRAW事件。
        """
        body: c.DrawEventBody = event.body
        surface = body["surface"]
        offset = body["offset"]
        draw_event = EventLike.draw_event(surface, offset=offset)

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


class SceneLike(LayerLike):
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

    ---

    listeners : set[ListenerLike]
        所有成员集合
    listen_codes :set[int]
        监听事件类型, 是群组监听类型与所有成员监听类型的并集
    listen_receivers :set[int]
        监听事件接收者, 是群组监听接收者与所有成员监听接收者的并集
    uuid : str
        监听者的通用唯一标识符, 一般是`str(id(self))`
    post_api : Optional[PostEventApiLike]
        发布事件函数, 一般使用`Core`的`add_event`

    Methods
    -------
    into()
        进入场景
    leave()
        离开场景

    ---

    listen(self, event: EventLike) -> None
        场景本体处理事件, 场景内成员 (`self.listeners`) 处理事件 (除了DRAW事件) 。

    ---

    group_listen(self, event: EventLike) -> None
        群组本体处理事件
    member_listen(self, event: EventLike) -> None
        群组成员处理事件
    get_listener(self, codes: set[int], receivers: set[str]) -> set[ListenerLike]
        筛选ListenerLike
    add_listener(self, listener: ListenerLike) -> None
        添加ListenerLike
    remove_listener(self, listener: ListenerLike) -> None
        删除ListenerLike
    clear_listener(self) -> None
        清空群组
    post(self, event: EventLike) -> None
        发布事件 (`通过self.__post_api`)  (一般是发布到Core的事件队列上)

    Listening Methods
    ---
    draw@DRAW
        根据图层顺序, 在画布上绘制实体

    ---

    kill@KILL
        从群组与图层中从删除成员
    """

    # attributes
    __core: Core
    __camera_cord: Tuple[int, int]
    is_activated: bool
    layers: collections.defaultdict[int, List[ListenerLike]]

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

    @listening(c.EventCode.DRAW)
    def draw(self, event: EventLike):
        """
        根据图层顺序, 在画布上绘制实体。

        Notes
        ---
        无视`event.body`传入的参数, 使用`self.camera_cord`与`self.core.window`绘图。

        Listening
        ---
        DRAW : DrawEventBody
            surface : pygame.Surface
                画布（该参数无效，永远使用`self.core.window`代替该参数。）
            offset : tuple[int, int]
                偏移量（该参数无效，永远使用`-self.camera_cord`代替该参数。）

        Notes
        ---
        根据图层的键从小到大排序图层, 逐层处理。每个图层中的对象按照列表顺序接收DRAW事件。
        """
        window = self.core.window
        offset = utils.IntTupleOper.sub(0, self.camera_cord)
        draw_event = EventLike.draw_event(window, offset=offset)
        super().draw(draw_event)


class TextEntity(EntityLike):
    """
    文本框 (左上对齐)

    Methods
    ---
    set_text(self, text: str = "") -> None
        设置文本框文本
    get_zh_font(font_size: int, *, bold=False, italic=False) -> pygame.font.Font
        获取支持中文的字体, 如果系统中没有找到支持的字体, 则返回pygame默认字体。

    Attributes
    ---
    font : pygame.font.Font
        字体 (含字号)
    font_color : ColorValue
        字体颜色
    back_ground : ColorValue
        背景颜色
    """

    # Attributes
    font: pygame.font.Font
    font_color: c.ColorValue
    back_ground: c.ColorValue

    @staticmethod
    def get_zh_font(font_size: int, *, bold=False, italic=False) -> pygame.font.Font:
        """
        获取支持中文的字体, 如果系统中没有找到支持的字体, 则返回pygame默认字体。

        Parameters
        ---
        font_size : int
            字号
        bold : bool, default = False
            加粗 (仅当在系统中找到支持中文字体时生效)
        italic : bool, default = False
            斜体 (仅当在系统中找到支持中文字体时生效)

        Notes
        ---
        中文字体查找顺序
        SimHei, microsoftyahei, notosanscjk
        """
        available_fonts = pygame.font.get_fonts()
        font_name = None
        for i in ["microsoftyahei", "SimHei", "notosanscjk"]:
            if i not in available_fonts:
                continue
            font_name = i
            break

        if font_name is None:
            return pygame.font.Font(None, font_size)
        return pygame.font.SysFont(font_name, font_size, bold, italic)

    def __init__(
        self,
        rect: pygame.Rect,
        *,
        font: pygame.font.Font = None,
        font_color: c.ColorValue = (255, 255, 255),
        back_ground: c.ColorValue = (0, 0, 0, 0),
        text: str = "",
        dynamic_size: bool = False,
    ):
        """
        Parameters
        ---
        rect : pygame.Rect
            文本框
        font : pygame.font.Font, default = None
            字体
        font_color : ColorValue, default  = (255, 255, 255)
            字体颜色
        back_ground : ColorValue, default  = (0, 0, 0, 0)
            背景颜色
        text : str = ""
            文字
        dynamic_size : bool, default = False
            是否在设置文字时, 自动重新更新文本框大小
        """
        super().__init__(rect)
        self.font: pygame.font.Font = font if font is not None else self.get_zh_font()
        self.font_color: c.ColorValue = font_color
        self.back_ground: c.ColorValue = back_ground
        self.dynamic_size: bool = dynamic_size
        self.set_text(text)

    def set_text(self, text: str = "") -> None:
        """
        设置文本框文本

        Notes
        ---
        当`self.dynamic_size`为True时, 会自动更新文本框大小
        """
        # ===几何计算
        line_width_list: list[int] = []
        line_offset_list: list[int] = []
        current_offset: int = 0
        for line in text.splitlines():
            line_offset_list.append(current_offset)
            line_width, line_height = self.font.size(line)
            current_offset += line_height
            line_width_list.append(line_width)
        max_width = max(line_width_list) if line_width_list else 0
        # ===resize
        if self.dynamic_size:
            self.rect.size = (max_width, current_offset)
        # ===文本框背景
        text_surface = pygame.Surface(self.rect.size, pygame.SRCALPHA)
        text_surface.fill(self.back_ground)
        # ===绘制文本
        for line, offset in zip(text.splitlines(), line_offset_list):
            text_surface.blit(
                self.font.render(line, True, self.font_color), (0, offset)
            )
        self.image = text_surface
