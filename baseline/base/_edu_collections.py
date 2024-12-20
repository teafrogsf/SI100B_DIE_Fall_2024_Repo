"""
本文件定义了基础类型, 本项目的场景, 角色等全部继承自本文件的基类。

Classes
---
EventLike
    事件
ListenerLike
    监听器
GroupLike
    监听器群组
Core
    核心。管理事件队列, 窗口, 刻, pygame api

Notes
---
- 字符串形式的类型标注是延迟变量解析（比如`-> "EventLike"`)
"""

from typing import (
    Dict,
    Tuple,
    Set,
    Optional,
    Callable,
    TypeAlias,
    Iterable,
    List,
    Any,
)
import sys

import pygame
from loguru import logger

from . import constants as c
from . import tools as tools

logger.warning(f"Using _edu_base.py as base.py.")


class EventLike:
    """
    事件

    Attributes
    ---
    code: int
        事件代码
    sender: typing.Optional[str]
        发送者 (UUID)
    receivers: typing.Set[str]
        接收者 (UUID集合)
    prior: int
        优先级 (越小优先级越高)
    body: typing.Dict[str, typing.Any]
        事件附加信息

    Attribute `prior`
    ---
    100
        默认优先级, pygame事件优先级
    200
        STEP事件优先级
    300
        DRAW事件优先级
    """

    def __init__(
        self,
        code: int,
        *,
        prior: int = 100,
        sender: Optional[str] = None,
        receivers: Set[str] = None,
        body: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Parameters
        ---
        code : int
            事件代码, 比如baseconst.EventCode
        prior : int, default = 100
            优先级 (越小优先级越高)
        sender : str, defualt = ""
            发送者 (UUID)
        receiver : set[str], default = {EVERYONE_RECEIVER}
            接收者 (UUID集合)。默认参数会提供一个集合, 添加"任何人"作为其中一个接收者。
        body : dict[str, typing.Any], default = {}
            事件附加信息
        """
        self.code = code
        self.prior = prior
        self.sender = sender
        self.receivers = receivers if receivers is not None else {c.EVERYONE_RECEIVER}
        self.body = body if body is not None else {}

    def __lt__(self, other: "EventLike"):
        """
        运算符重载: `<`, 根据`prior`进行比较。

        Notes
        ---
        - 排序算法只需要定义`<`运算符即可正常工作。
        """
        return self.prior < other.prior

    @classmethod
    def kill_event(cls, uuid: str) -> "EventLike":
        body: c.KillEventBody = {"suicide": uuid}
        return cls(c.EventCode.KILL, body=body, sender=uuid, prior=0)

    @classmethod
    def from_pygame_event(cls, event: pygame.event.Event) -> "EventLike":
        """
        pygame.event.Event转换为EventLike
        (会使用object.__dict__继承pygame事件的全部属性)

        Parameters
        ---
        event : pygame.event.
            pygame事件
        """
        ins = cls(event.type, sender="pygame", prior=90)
        ins.__dict__.update(event.__dict__)
        return ins

    @classmethod
    def step_event(cls, secord: float) -> "EventLike":
        """
        创建STEP事件

        Parameters
        ---
        secord : float
            距离上次广播STEP事件经过的时间
        """
        body: c.StepEventBody = {"secord": secord}
        return cls(c.EventCode.STEP, body=body, prior=200)

    @classmethod
    def draw_event(
        cls,
        window: pygame.Surface,
        *,
        receivers: Set[str] = None,
        camera: Tuple[int, int] = (0, 0),
    ) -> "EventLike":
        """
        创建DRAW事件

        Parameters
        ---
        window : pygame.Surface
            一般是pygame.display.set_mode(...)返回的Surface对象, 占满整个窗口的画布
        receivers : set[str], typing.Optional, default = {EVERYONE_RECEIVER}
            事件接收者, 默认是任何Listener
        camera : tuple[int, int], default = (0, 0)
            相机位置, 绘制偏移量
        """
        body = {"window": window, "camera": camera}
        return cls(c.EventCode.DRAW, body=body, prior=300, receivers=receivers)


PostEventApiLike: TypeAlias = Callable[
    [EventLike], None
]  # 事件发布函数类型注释, 一般使用`Core`的`add_event`函数


class ListenerLike:
    """
    监听者

    1. `self.listen(event)`函数可以监听事件

        1. 首先检查事件的类型和接收者集(`EventLike.code`, `EventLike.receivers`) 。(如果是监听者无法处理的事件类型, 或者监听者不是事件的接收者, 那么不会处理该事件)
        2. 根据事件类型`EventLike.code`, 将事件传递到对应的被`listening`(basetools模块提供)装饰过的函数。

    2. `self.post(event)`函数可以发布事件 (发布位置取决初始化时传入的`post_api`, 推荐使用`Core().add_event`作为`post_api`)

    ---

    小例子：
    比如使用`listen(EventLike(114514))`时, 被装饰过的`do_something`被自动调用, 但`other_thing`不会响应`114514`类型的事件。

    ```
    class Example(ListenerLike):
        @listening(114514)
        def do_something(event):
            print("do something")

        @listening(1919810)
        def other_thing(event):
            print("do other thing")

    exp = Example()
    exp.listen(EventLike(114514))
    # OUTPUT:
    # do something
    ```

    Attributes
    ---
    listen_receivers : set[int]
        监听的接收者 (一般会监听发送往自己 (UUID) 以及"任何人"`EVERYONE_RECEIVER`的事件)
    listen_codes : set[int]
        监听的事件代码
    uuid : str
        监听者的通用唯一标识符, 一般是`str(id(self))`

    Methods
    ---
    post(self, event: EventLike) -> None
        发布事件 (`通过self.__post_api`)  (一般是发布到Core的事件队列上)
    listen(self, event: EventLike) -> None:
        处理事件

    Notes
    ---
    basetools模块有两个函数, listening装饰器以及find_listening_methods函数。

    listening(code: int)
        该装饰器会给被装饰的函数增加一个标记, 储存该函数能处理的事件代码 (也就是EventLike.code)

    find_listening_methods(object: object) -> dict[int, set[typing.Callable[[EventLike], None]]]
        找到所有被listening标记的函数, 并根据事件代码分类, 储存到一个字典中

    在ListenerLike中, `self.__listen_methods`会通过`find_listening_methods`初始化。
    调用`listen`函数处理事件时, 会根据`self.__listen_methods`将事件发配到能处理该事件的函数中。
    > 注意: listen发配事件是没有顺序的

    Examples
    ---
    ```
    # EventCode.STEP = 114514

    class Drawable(ListenerLike):
        def __init__(...):
            ...

        @listening(EventCode.STEP)
        def step1(event: EventLike):
            print(event.code, "in step1")
            ...

        @listening(EventCode.STEP)
        def step2(event: EventLike):
            print(event.code, "in step2")
            ...

        @listening(EventCode.DRAW)
        def dealing_draw(event: EventLike):
            print(event.code, "in draw")
            ...

    if __name__ == "__main__":
        a = Drawable()
        a.listen(EventLike(code = EventCode.STEP))
        # 注意: step1, step2的调用顺序不定。有可能先调用step1, 也可能先step2。
        # OUTPUT:
        # 114514 in step2
        # 114514 in step1
    ```
    """

    @property
    def uuid(self) -> int:
        """监听者的UUID"""
        return str(id(self))

    @property
    def listen_receivers(self) -> Set[str]:
        """
        监听的接收者 (一般会监听发送往自己 (UUID) 以及"任何人"`EVERYONE_RECEIVER`的事件)
        """
        return self._listen_receivers

    @property
    def listen_codes(self) -> Set[int]:
        """
        监听的事件代码
        """
        return set(self.listen_methods)

    def __init__(
        self,
        *,
        post_api: Optional[PostEventApiLike] = None,
        listen_receivers: Optional[Set[str]] = None,
    ) -> None:
        """
        Parameters
        ---
        post_api : (EventLike) -> None, optional, default = None
            发布事件函数, 一般使用`Core`的`add_event`
        listen_receivers : set[str], optional, default = {EVERYONE_RECEIVER, self.uuid}
            监听的接收者集合
        """
        self.post_api: Optional[PostEventApiLike] = post_api
        self._listen_receivers = (
            listen_receivers
            if listen_receivers is not None
            else {c.EVERYONE_RECEIVER, self.uuid}
        )
        self.listen_methods: Dict[int, Set[Callable[[EventLike], None]]] = (
            tools.find_listening_methods(self)
        )

    def post(self, event: EventLike) -> None:
        """
        通过`post_api`发布事件。
         (一般是发布到Core的事件队列上)

        Parameters
        ---
        event : EventLike
            需要发布的事件

        Raises
        ---
        AttributeError
            如果初始化时没有传入`post_api`, 则抛出该异常。
        """
        if self.post_api is None:
            raise AttributeError("`post_api` is not available in this instance.")
        self.post_api(event)

    def listen(self, event: EventLike) -> None:
        """
        根据事件的`code`, 分配到对应的被`listening`装饰过的函数进行处理。
        (除非事件的`receivers`中, 不包括此监听者。)

        Parameters
        ---
        event : EventLike
            需要处理的事件
        """
        if event.code not in self.listen_methods:
            return
        if not event.receivers & self.listen_receivers:
            return
        for method_ in self.listen_methods[event.code]:
            method_(event)


class GroupLike(ListenerLike):
    """
    监听者群组

    Attributes
    ---
    listen_codes :set[int]
        监听事件类型, 是群组监听类型与所有成员监听类型的并集
    listen_receivers :set[int]
        监听事件接收者, 是群组监听接收者与所有成员监听接收者的并集
    listeners : set[ListenerLike]
        所有成员集合

    Methods
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
    listen(self, event: EventLike) -> None
        群组处理事件, 群组成员处理事件
    """

    def __init__(self, *, post_api=None, listen_receivers=None):
        """
        Parameters
        ---
        post_api : (EventLike) -> None, optional, default = None
            发布事件函数, 一般使用`Core`的`add_event`
        listen_receivers : set[str], optional, default = {EVERYONE_RECEIVER, self.uuid}
            监听的接收者集合
        """
        super().__init__(post_api=post_api, listen_receivers=listen_receivers)
        self.listeners: List[ListenerLike] = []

    def group_listen(self, event: EventLike):
        """
        根据事件的`code`, 分配到对应的被`listening`装饰过的函数 (属于GroupLike的函数) 进行处理。
        (除非事件的`receivers`中, 不包括此监听者。)

        Parameters
        ---
        event : EventLike
            需要处理的事件
        """
        super().listen(event)

    def member_listen(self, event: EventLike):
        """
        将事件传递到群组内所有ListenerLike的listen中。
        (如果事件代码event.code和事件接收者event.receivers合适的话)

        Parameters
        ---
        event : EventLike
            需要处理的事件
        """
        for ls in self.listeners:
            ls.listen(event)

    def get_listener(self, codes: Set[int], receivers: Set[str]) -> List[ListenerLike]:
        """
        筛选群组内的ListenerLikes。
        即返回所有, 同时满足能接受任意codes, 以及接受任意receivers的ListenerLike。

        Parameters
        ---
        codes : set[int]
            事件代码集合
        receivers : set[str]
            事件接收者集合

        Returns
        ---
        typing.Set[ListenerLike]
            筛选出的ListererLike
        """
        res = []
        for i in self.listeners:
            if i.listen_codes & codes and i.listen_receivers & receivers:
                res.append(i)
        return res

    def add_listener(self, listener: ListenerLike):
        """
        向群组中增加ListenerLike

        Parameters
        ---
        listener : ListenerLike
            新增的ListenerLike
        """
        self.listeners.append(listener)
        self.listen_codes.update(listener.listen_codes)
        self.listen_receivers.update(listener.listen_receivers)

    def remove_listener(self, listener: ListenerLike):
        """
        向群组中移除ListenerLike

        Parameters
        ---
        listener : ListenerLike
            移除的ListenerLike
        """
        self.listeners.remove(listener)

    def clear_listener(self) -> None:
        """
        清除群组中的全部ListenerLike
        """
        self.listeners.clear()

    def listen(self, event: EventLike):
        """
        群组处理事件, 群组成员处理事件

        Notes
        ---
        `self.listen(event)`等价于`self.group_listen(event); self.member_listen(event)`
        """
        self.group_listen(event)
        self.member_listen(event)

    @tools.listening(c.EventCode.KILL)
    def kill(self, event: EventLike) -> None:
        """
        从群组中删除成员
        """
        body: c.KillEventBody = event.body
        uuid: str = body["suicide"]
        for i in filter(lambda x: x.uuid == uuid, self.listeners):
            self.remove_listener(i)


class Core:
    """
    核心

    管理事件队列, 窗口, 刻, pygame api
    """

    def __init__(self):
        self.__winsize: Tuple[int, int] = (1280, 720)  # width, height
        self.__title: str = "The Bizarre Adventure of the Pufferfish"
        self.__rate: float = 0
        self.__window: pygame.Surface = pygame.display.set_mode(self.winsize)
        self.__clock: pygame.time.Clock = pygame.time.Clock()
        self.__event_queue: List[EventLike] = []

        self.init()
        pygame.display.set_caption(self.__title)

    # event
    def yield_events(
        self,
        *,
        add_pygame_event: bool = True,
        add_step: bool = True,
        add_draw: bool = True,
    ) -> Iterable[EventLike]:
        """
        生成事件

        将事件队列的所有事件都yield出来 (根据优先级), 直到事件队列为空

        Parameters
        ---
        add_pygame_event : bool, default = True
            是否自动加入`pygame.event.get()`的事件
        add_step : bool, default = True
            是否自动加入STEP事件
        add_draw : bool, default = True
            是否自动加入DRAW事件

        Yields
        ---
        EventLike
            事件队列中事件

        Examples
        ---
        ```
        core = Core()
        for event in core.yield_events():
            deal(event)
        ```
        """
        if add_pygame_event:
            self.__event_queue.extend(
                (EventLike.from_pygame_event(i) for i in pygame.event.get())
            )
        if add_step:
            self.__event_queue.append(self.get_step_event())
        if add_draw:
            self.__event_queue.append(EventLike.draw_event(self.window))
        while self.__event_queue:
            self.__event_queue.sort()
            yield self.__event_queue.pop(0)
        yield self.get_step_event()

    def add_event(self, event: EventLike) -> None:
        """
        往事件队列增加事件

        Parameters
        ---
        event : EventLike
            事件
        """
        self.__event_queue.append(event)

    def clear_event(self):
        """
        清空所有事件 (包括pygame的队列)
        """
        pygame.event.clear()
        self.__event_queue.clear()

    def get_step_event(self) -> EventLike:
        """
        调用`tick()`, 并生成一个STEP事件
        """
        return EventLike.step_event(self.tick() / 1000)

    # window
    @property
    def winsize(self) -> Tuple[int, int]:
        """
        窗口大小
        """
        return self.__winsize

    @winsize.setter
    def winsize(self, rect: Tuple[int, int]):
        """
        Set the window size and adjust the display accordingly.

        Parameters
        ---
        rect : Tuple[int, int]
            The new dimensions for the window.
        """
        self.__winsize = rect
        self.__window = pygame.display.set_mode(self.__winsize)

    @property
    def title(self) -> str:
        """
        窗口标题
        """
        return self.__title

    @title.setter
    def title(self, title: str):
        self.__title = title
        pygame.display.set_caption(title)

    @property
    def window(self) -> pygame.Surface:
        """
        窗口 (画布)
        """
        return self.__window

    # tick
    @property
    def clock(self) -> pygame.time.Clock:
        """
        主时钟
        """
        return self.__clock

    @property
    def time_ms(self) -> int:
        """
        程序运行时间 (ms)
        """
        return pygame.time.get_ticks()

    @property
    def rate(self) -> float:
        """
        游戏运行速率 (tick rate)
        """
        return self.__rate

    @rate.setter
    def rate(self, tick_rate: float):
        self.__rate = tick_rate
        self.__clock.tick(self.__rate)

    def tick(self, tick_rate: float = None) -> int:
        """
        时钟调用tick

        Parameters
        ---
        tick_rate : float, default = self.rate
            游戏运行速度

        Returns
        ---
        int
            距离上一次调用tick经过的时间 (ms)
        """
        if tick_rate is None:
            tick_rate = self.__rate
        return self.__clock.tick(tick_rate)

    # pygame api
    @staticmethod
    def flip():
        """
        将`self.window`上画的内容输出的屏幕上
        """
        return pygame.display.flip()

    @staticmethod
    def init():
        """
        全局初始化
        """
        pygame.init()
        pygame.mixer.init()

    @staticmethod
    def exit():
        """
        结束程序
        """
        pygame.quit()
        sys.exit()

    def blit(
        self,
        source: pygame.Surface,
        dest,
        area=None,
        special_flags: int = 0,
    ):
        """
        在`self.windows`上绘制
        """
        self.window.blit(
            source,
            dest,
            area,
            special_flags,
        )

    @staticmethod
    def play_music(path: str, loop: int = -1, monotone: bool = True):
        """
        播放音乐

        Parameters
        ---
        path : str
            音乐路径
        loop : int, default = -1
            循环次数, `-1`为无限循环
        monotone : bool, default = True
            是否仅播放该音乐
        """
        if monotone:
            pygame.mixer.music.stop()
        pygame.mixer.music.load(path)
        pygame.mixer.music.play(loop)

    @staticmethod
    def stop_music():
        """
        停止音乐
        """
        pygame.mixer.music.stop()
