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

import typing as _typing
import sys as _sys

import pygame as _pygame

from . import constants as _const
from . import tools as _tools


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

    # Attributes
    code: int
    sender: str
    receivers: _typing.Set[str]
    prior: int
    body: _typing.Dict[str, _typing.Any]

    # pygame键盘事件会带有一个key属性, 代表被按下的按键
    key: _typing.Union[int, _typing.Any]

    @classmethod
    def from_pygame_event(cls, event: _pygame.event.Event) -> "EventLike":
        """
        pygame.event.Event转换为EventLike
        (会使用object.__dict__继承pygame事件的全部属性)

        Parameters
        ---
        event : pygame.event.
            pygame事件
        """
        ins = cls(event.type, sender="pygame", prior=100)  # 创建EventLike实例
        ins.__dict__.update(event.__dict__)  # 继承属性
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
        body: _const.StepEventBody = {"secord": secord}
        return cls(_const.EventCode.STEP, body=body, prior=200)

    @classmethod
    def kill_event(cls, uuid: str) -> "EventLike":
        """
        创建KILL事件

        Parameters
        ---
        uuid : str
            被删除监听者的UUID
        """
        body: _const.KillEventBody = {"suicide": uuid}
        return cls(_const.EventCode.KILL, body=body, sender=uuid, prior=0)

    @classmethod
    def draw_event(
        cls,
        window: _pygame.Surface,
        *,
        receivers: _typing.Set[str] = None,
        camera: _typing.Tuple[int, int] = (0, 0),
    ):
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
        return cls(_const.EventCode.DRAW, body=body, prior=300, receivers=receivers)

    def __init__(
        self,
        code: int,
        *,
        prior: int = 100,
        sender: _typing.Optional[str] = "",
        receivers: _typing.Set[str] = None,
        body: _typing.Optional[_typing.Dict[str, _typing.Any]] = None,
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
        self.code: int = code
        self.prior: int = prior
        self.sender: str = sender
        self.receivers: _typing.Set[str] = (
            receivers if receivers is not None else {_const.EVERYONE_RECEIVER}
        )
        self.body: _typing.Dict[str, _typing.Any] = body if body is not None else {}

    def __lt__(self, other: "EventLike") -> bool:
        """
        运算符重载: `<`, 根据`prior`进行比较。

        Notes
        ---
        - 排序算法只需要定义`<`运算符即可正常工作。
        """
        return self.prior < other.prior


PostEventApiLike: _typing.TypeAlias = _typing.Callable[
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
        监听的接收者 (一般包含监听发送往自己 (UUID) 以及"任何人"`EVERYONE_RECEIVER`的事件)
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

    # Attributes
    __post_api: _typing.Optional[PostEventApiLike]
    __listen_receivers: _typing.Set[str]
    __listen_methods: _typing.Dict[
        int, _typing.Set[_typing.Callable[[EventLike], None]]
    ]

    @property
    def listen_receivers(self) -> _typing.Set[str]:
        """监听的接收者集合"""
        return self.__listen_receivers

    @listen_receivers.setter
    def listen_receivers(self, listen_receivers: _typing.Set[str]) -> None:
        self.__listen_receivers = listen_receivers

    @property
    def listen_codes(self) -> _typing.Set[int]:
        """
        监听的事件代码集合

        Notes
        ---
        本属性集合所有被`basetools.listening`装饰过的函数的事件代码, 修改无效。
        """
        return set(self.__listen_methods)

    @listen_codes.setter
    def listen_codes(self, listen_codes: _typing.Set[int]):
        raise AttributeError("Can't set attribute `listen_codes`")

    @property
    def uuid(self) -> int:
        """监听者的UUID"""
        return str(id(self))

    def __init__(
        self,
        *,
        post_api: _typing.Optional[PostEventApiLike] = None,
        listen_receivers: _typing.Optional[_typing.Set[str]] = None,
    ):
        """
        Parameters
        ---
        post_api : (EventLike) -> None, optional, default = None
            发布事件函数, 一般使用`Core`的`add_event`
        listen_receivers : set[str], optional, default = {EVERYONE_RECEIVER, self.uuid}
            监听的接收者集合, 自动加上EVERYONE_RECEIVER与self.uuid
        """
        self.__post_api: _typing.Optional[PostEventApiLike] = post_api
        self.__listen_receivers = (
            listen_receivers | {_const.EVERYONE_RECEIVER, self.uuid}
            if listen_receivers is not None
            else {_const.EVERYONE_RECEIVER, self.uuid}
        )
        self.__listen_methods: _typing.Dict[
            int, _typing.Set[_typing.Callable[[EventLike], None]]
        ] = _tools.find_listening_methods(self)

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
        if self.__post_api is None:
            raise AttributeError(
                "`The post_api parameter was not passed during the initialization of ListenerLike."
            )
        self.__post_api(event)

    def listen(self, event: EventLike) -> None:
        """
        根据事件的`code`, 分配到对应的被`listening`装饰过的函数进行处理。
        (除非事件的`receivers`中, 不包括此监听者。)

        Parameters
        ---
        event : EventLike
            需要处理的事件
        """
        listen_receivers = self.__listen_receivers
        if not event.receivers & listen_receivers:
            return
        listen_code_methods = self.__listen_methods
        if not event.code in listen_code_methods:
            return
        for method_ in listen_code_methods[event.code]:
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

    Listening Methods
    ---
    kill@KILL
        从群组从删除成员
    """

    # Attributes
    __listeners: _tools.DoubleKeyBarrel[ListenerLike]

    @property
    def listen_codes(self) -> _typing.Set[int]:
        """
        监听事件类型, 是群组监听类型与所有成员监听类型的并集

        Notes
        ---
        不可修改该属性
        """
        return self.__listeners.keys1 | super().listen_codes

    @property
    def listen_receivers(self) -> _typing.Set[str]:
        """
        监听事件接收者, 是群组监听接收者与所有成员监听接收者的并集

        Notes
        ---
        不可修改该属性
        """
        return self.__listeners.keys2 | super().listen_receivers

    @property
    def listeners(self) -> _typing.Set[ListenerLike]:
        """
        返回群组中的所有成员
        """
        return set(self.__listeners)

    def __init__(
        self,
        *,
        post_api: _typing.Optional[PostEventApiLike] = None,
        listen_receivers: _typing.Optional[_typing.Set[str]] = None,
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

        def __get_key1(listener: ListenerLike) -> _typing.Set[int]:
            return listener.listen_codes

        def __get_key2(listener: ListenerLike) -> _typing.Set[str]:
            return listener.listen_receivers

        self.__listeners: _tools.DoubleKeyBarrel[ListenerLike] = _tools.DoubleKeyBarrel(
            __get_key1, __get_key2
        )

    def group_listen(self, event: EventLike) -> None:
        """
        根据事件的`code`, 分配到对应的被`listening`装饰过的函数 (属于GroupLike的函数) 进行处理。
        (除非事件的`receivers`中, 不包括此监听者。)

        Parameters
        ---
        event : EventLike
            需要处理的事件
        """
        super().listen(event)

    def member_listen(self, event: EventLike) -> None:
        """
        将事件传递到群组内所有ListenerLike的listen中。
        (如果事件代码event.code和事件接收者event.receivers合适的话)

        Parameters
        ---
        event : EventLike
            需要处理的事件
        """
        for ls in self.get_listener({event.code}, event.receivers):
            ls.listen(event)

    def get_listener(
        self, codes: _typing.Set[int], receivers: _typing.Set[str]
    ) -> _typing.Set[ListenerLike]:
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
        return self.__listeners.get(codes, receivers)

    def add_listener(self, listener: ListenerLike) -> None:
        """
        向群组中增加ListenerLike

        Parameters
        ---
        listener : ListenerLike
            新增的ListenerLike
        """
        self.__listeners.add(listener)

    def remove_listener(self, listener: ListenerLike) -> None:
        """
        向群组中移除ListenerLike

        Parameters
        ---
        listener : ListenerLike
            移除的ListenerLike
        """
        self.__listeners.remove(listener)

    def clear_listener(self) -> None:
        """
        清除群组中的全部ListenerLike
        """
        self.__listeners.clear()

    def listen(self, event: EventLike) -> None:
        """
        群组处理事件, 群组成员处理事件

        Notes
        ---
        `self.listen(event)`等价于`self.group_listen(event); self.member_listen(event)`
        """
        self.group_listen(event)
        self.member_listen(event)

    @_tools.listening(_const.EventCode.KILL)
    def kill(self, event: EventLike) -> None:
        """
        根据`event.body["suicide"]`提供的UUID, 从群组中删除该成员

        Listening
        ---
        KILL : KillEventBody
            suicide : str
                即将被删除成员的UUID

        Notes
        ---
        先找出所有UUID符合的成员, 然后调用`self.remove_listener`进行删除。
        """
        body: _const.KillEventBody = event.body
        uuid: str = body["suicide"]
        for i in filter(lambda x: x.uuid == uuid, self.listeners):
            self.remove_listener(i)


@_typing.final
@_tools.singleton
class Core:
    """
    核心

    管理事件队列, 窗口, 刻, pygame api

    Notes
    ---
    - 单例类, 每次初始化都返回相同的实例
    """

    def __init__(self):
        def GET_PRIOR(event: EventLike) -> int:
            return event.prior

        self.__winsize: _typing.Tuple[int, int] = (1280, 720)  # width, height
        self.__title: str = "The Bizarre Adventure of the Pufferfish"
        self.__rate: float = 0
        self.__window: _pygame.Surface = _pygame.display.set_mode(
            self.winsize, _pygame.RESIZABLE
        )
        self.__clock: _pygame.time.Clock = _pygame.time.Clock()
        self.__event_queue: _tools.BarrelQueue[EventLike] = _tools.BarrelQueue(
            GET_PRIOR
        )

        self.init()
        _pygame.display.set_caption(self.__title)

    # event
    def yield_events(
        self,
        *,
        add_pygame_event: bool = True,
        add_step: bool = True,
        add_draw: bool = True,
    ) -> _typing.Generator[EventLike, None, None]:
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

        Notes
        ---
        `add_pygame_event=True`时, 会捕获`pygame.VIDEORESIZE`事件, 并更新窗口大小
        """
        if add_pygame_event:
            pygame_events = [
                EventLike.from_pygame_event(i) for i in _pygame.event.get()
            ]
            self.__event_queue.extend(pygame_events)
            for event in filter(lambda x: x.code == _pygame.VIDEORESIZE, pygame_events):
                self.winsize = (event.w, event.h)
        if add_step:
            self.__event_queue.append(self.get_step_event())
        if add_draw:
            self.__event_queue.append(EventLike.draw_event(self.window))
        while self.__event_queue:
            yield self.__event_queue.popleft()

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
        _pygame.event.clear()
        self.__event_queue.clear()

    def get_step_event(self) -> EventLike:
        """
        调用`tick()`, 并生成一个STEP事件
        """
        return EventLike.step_event(self.tick() / 1000)

    # window
    @property
    def winsize(self) -> _typing.Tuple[int, int]:
        """
        窗口大小
        """
        return self.__winsize

    @winsize.setter
    def winsize(self, rect: _typing.Tuple[int, int]):
        self.__winsize = rect
        self.__window = _pygame.display.set_mode(self.__winsize, _pygame.RESIZABLE)

    @property
    def title(self) -> str:
        """
        窗口标题
        """
        return self.__title

    @title.setter
    def title(self, title: str):
        self.__title = title
        _pygame.display.set_caption(title)

    @property
    def window(self) -> _pygame.Surface:
        """
        窗口 (画布)
        """
        return self.__window

    # tick
    @property
    def clock(self) -> _pygame.time.Clock:
        """
        主时钟
        """
        return self.__clock

    @property
    def time_ms(self) -> int:
        """
        程序运行时间 (ms)
        """
        return _pygame.time.get_ticks()

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
    def flip() -> None:
        """
        将`self.window`上画的内容输出的屏幕上
        """
        return _pygame.display.flip()

    @staticmethod
    def init() -> None:
        """
        全局初始化
        """
        _pygame.init()
        _pygame.mixer.init()

    @staticmethod
    def exit() -> None:
        """
        结束程序
        """
        _pygame.quit()
        _sys.exit()

    def blit(
        self,
        source: _pygame.Surface,
        dest,
        area=None,
        special_flags: int = 0,
    ) -> _pygame.Rect:
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
    def play_music(path: str, loop: int = -1, monotone: bool = True) -> None:
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
            _pygame.mixer.music.stop()
        _pygame.mixer.music.load(path)
        _pygame.mixer.music.play(loop)

    @staticmethod
    def stop_music() -> None:
        """
        停止音乐
        """
        _pygame.mixer.music.stop()
