"""
`collections.py`依赖工具包

Methods
---
listening
    装饰函数: 表示这个函数能处理某个事件代码。
find_listening_methods
    寻找实例中, 被listening装饰过的方法
singleton
    单例类装饰器

Classes
---
BarrelQueue
    高度优化的队列, 用于保证事件队列永远有序(排序规则: 1. 优先级 2.插入顺序), 且插入与弹出的复杂度皆为O(1)。
DoubleKeyBarrel
    高度优化的桶。用于快速将事件分发到所有能处理该类型事件(且为接收者)的监听者中。
"""

import functools as _functools
import itertools as _itertools
import typing as _typing
import heapq as heapq
import collections as _collections
import inspect as _inspect

from loguru import logger as _logger

if _typing.TYPE_CHECKING:
    from . import collections as _colls
_LISTENING_METHOD_ATTR_NAME = "_listening_codes"  # listening装饰器修改的函数属性


_WARNING_DO_NOT_DECORATE_PRIVATE = """Do not use the `listening` decorator on private methods!
Private methods can be inherited by subclasses and captured by `find_listening_methods`.  
Additionally, Python's name mangling makes it very difficult to override private methods from the parent class.  

请不要对私有方法使用 `listening` 装饰器！  
私有方法不仅会被子类继承，还会被 `find_listening_methods` 捕捉到。  
此外, Python的名称修饰机制使得重写父类的私有方法变得非常困难。"""


def listening(code: int) -> _typing.Callable[[_typing.Callable], _typing.Callable]:
    """
    修饰函数, 在函数上增加一个属性, 储存函数能处理的事件代码。

    Parameters
    ---
    code : int
        监听的事件代码


    Exameples
    ---
    ```
    class Foo:
        def __init__(self):
            self.methods = find_listening_methods(self)

        @listening(10)
        @listening(20)
        def func120(self, event): ...

        @listening(10)
        def func10(self, event): ...

        @listening(30)
        def func30(self, event): ...


    foo = Foo()
    print(foo.methods)
    # OUTPUT:
    # {
    #   10:{
    #        <bound method Foo.func10,
    #        <bound method Foo.func120
    #      },
    #   20: {<bound method Foo.func120},
    #   30: {<bound method Foo.func30}
    # }
    ```

    Notes
    ---
    函数自身的__name__, __qualname__可能被其他装饰器重写（极端情况）
    检查obj.__class__.__mro__中, 所有父类的__dict__, 只能看到被名称修饰重写后的方法名（无法看到重写前的双下划线开头方法名, 分辨不出是否被重写过）
    而且名称修饰是根据cls.__name__修饰的, mro中不排除出现重名的类（极端情况）
    目前无法阻止父类的私有方法不被捕捉, 或者过滤绝对不出现误判

    另外, listening的作用是给函数加属性。如果有其他装饰器给函数额外包装了一层, 会导致属性被包裹在里面, 使得无法被捕捉。
    """

    def decorator(
        func: _typing.Callable[["_colls.EventLike"], None]
    ) -> _typing.Callable[["_colls.EventLike"], None]:
        if func.__name__.startswith("__"):
            _logger.warning(_WARNING_DO_NOT_DECORATE_PRIVATE)
            func.__qualname__
        if not hasattr(func, _LISTENING_METHOD_ATTR_NAME):
            setattr(func, _LISTENING_METHOD_ATTR_NAME, set())
        getattr(func, _LISTENING_METHOD_ATTR_NAME).add(code)
        return func

    return decorator


def find_listening_methods(
    obj: object,
) -> _typing.Dict[int, _typing.Set[_typing.Callable[["_colls.EventLike"], None]]]:
    """
    找到实例中, 所有被listening装饰过的函数。

    Returns
    ---
    dict[int, set[Callable[[EventLike], None]]]
        键: 事件代码, 值: 事件处理函数

    Exameples
    ---
    ```
    class Foo:
        def __init__(self):
            self.methods = find_listening_methods(self)

        @listening(10)
        @listening(20)
        def func120(self, event): ...

        @listening(10)
        def func10(self, event): ...

        @listening(30)
        def func30(self, event): ...


    foo = Foo()
    print(foo.methods)
    # OUTPUT:
    # {
    #   10:{
    #        <bound method Foo.func10,
    #        <bound method Foo.func120
    #      },
    #   20: {<bound method Foo.func120},
    #   30: {<bound method Foo.func30}
    # }
    ```
    """
    listen_code_methods: _typing.Dict[
        int, _typing.Set[_typing.Callable[["_colls.EventLike"], None]]
    ] = {}
    for _, method in _inspect.getmembers(obj, predicate=_inspect.ismethod):
        if hasattr(method, _LISTENING_METHOD_ATTR_NAME):
            for code in getattr(method, _LISTENING_METHOD_ATTR_NAME):
                if code not in listen_code_methods:
                    listen_code_methods[code] = set()
                listen_code_methods[code].add(method)
    return listen_code_methods


_T = _typing.TypeVar("_T")


def singleton(cls: _T) -> _T:
    """
    单例装饰器

    被装饰的类每次初始化都会
    """
    instances = {}

    @_functools.wraps(cls)
    def wrapper(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        else:
            _logger.debug(
                f"{cls.__name__} is a singleton class. Reinitializing it will only return the instance created during the first initialization. {cls.__name__}是单例类, 重复初始化仅会返回第一次初始化产生的实例。"
            )
        return instances[cls]

    return wrapper


_Key1 = _typing.TypeVar("_Key1")
_Key2 = _typing.TypeVar("_Key2")
_Key = _typing.TypeVar("_Key")
_Element = _typing.TypeVar("_Element")


class BarrelQueue(_typing.Generic[_Element]):
    """
    根据元素的指定特征进行排序的 (排序具有稳定性) 、高效的队列

    Methods
    ---
    append(self, item: Element)
        在队列右边加入物品
    popleft(self)
        弹出队列最左边的元素 (队列中最小的元素)
    extend(self, items: Iterable[Element])
        在队列右边加入多个物品
    clear(self)
        清空队列
    """

    def __init__(self, get_key: _typing.Callable[[_Element], _Key] = lambda x: x):
        self.__get_key: _typing.Callable[[_Element], _Key] = get_key

        self.__barrels: _typing.Dict[_Key, _collections.deque[_Element]] = {}
        self.__barrel_heap: _typing.List[_Key] = []

    def __len__(self) -> int:
        return sum(len(i) for i in self.__barrels.values())

    def __bool__(self) -> bool:
        return bool(self.__barrels)

    def append(self, item: _Element) -> None:
        """
        在队列右边加入元素

        Parameters
        ---
        item : Element
            元素
        """
        k = self.__get_key(item)
        self.__set_default_key(k)
        self.__barrels[k].append(item)

    def popleft(self) -> _Element:
        """
        弹出队列最左边的元素 (队列中最小的元素)

        Returns
        ---
        Element
            队列中最小的元素
        """
        k = self.__barrel_heap[0]
        element = self.__barrels[k].popleft()
        if not self.__barrels[k]:
            self.__pop_key()
        return element

    def extend(self, items: _typing.Iterable[_Element]) -> None:
        """
        在队列右边加入多个元素

        Parameters
        ---
        items : Iterable[Element]
            可迭代出元素的对象
        """
        item_iter = iter(items)
        try:
            item = next(item_iter)
            k_old = self.__get_key(item)
            self.append(item)

            while True:
                item = next(item_iter)
                k = self.__get_key(item)
                if k_old != k:
                    self.__set_default_key(k)
                    k_old = k
                self.__barrels[k].append(item)

        except StopIteration:
            pass

    def clear(self) -> None:
        """清空队列"""
        self.__barrel_heap.clear()
        self.__barrels.clear()

    def __set_default_key(self, k: _Key):
        if k in self.__barrels:
            return
        self.__barrels[k] = _collections.deque()
        heapq.heappush(self.__barrel_heap, k)

    def __pop_key(self):
        k = self.__barrel_heap[0]
        if self.__barrels[k]:
            return
        self.__barrels.pop(k)
        heapq.heappop(self.__barrel_heap)


class DoubleKeyBarrel(_typing.Generic[_Element]):
    """
    双键桶, 用于快速查找元素的数据结构。

    Methods
    ---
    add(self, item: Element) -> None
        添加元素
    remove(self, item: Element) -> None
        删除元素
    get(self, keys1: set[Key1], keys2: set[Key2]) -> set[Element]
        检查`DoubleKeyBarrel`内所有元素, 满足`get_keys1(Element) & keys1 and get_keys2(Element) & keys2`的元素都返回
    clear(self) -> None:
        清空元素

    Notes
    ---
    本质上在维护一个字典`self.__barrels` : `dict[tuple[Key1, Key2], set[Element]]`
    里面储存的每个元素可以提取出两个键集合set[Key1], set[Key2]
    元素会根据其键集合, 储存到相应的桶里面

    比如`item`能提取出两个键集合`{1, 2}`和`{"a", "b"}`, 那么字典中的情况应该是
    ```
    {
        (1, "a") : {..., item, ...},
        (1, "b") : {..., item, ...},
        (2, "a") : {..., item, ...},
        (2, "b") : {..., item, ...},
        {...} : {...},
        {...} : {...},
        ...
    }
    ```
    如果调用`get({2, 3}, {"c", "d"})`
    那么键为`(2, "c")`, `{2, "d"}`, `(3, "c")`, `{3, "d"}`的集合, 其内容都会被返回。
    """

    @property
    def keys1(self) -> _typing.Set[_Key1]:
        """键1集合"""
        return set(map(lambda x: x[0], self.__barrels))

    @property
    def keys2(self) -> _typing.Set[_Key2]:
        """键2集合"""
        return set(map(lambda x: x[1], self.__barrels))

    def __init__(
        self,
        get_keys1: _typing.Callable[[_Element], _typing.Iterable[_Key1]],
        get_keys2: _typing.Callable[[_Element], _typing.Iterable[_Key2]],
    ):
        self.__get_keys1: _typing.Callable[[_Element], _Key1] = get_keys1
        self.__get_keys2: _typing.Callable[[_Element], _Key2] = get_keys2
        self.__barrels: _typing.Dict[
            _typing.Tuple[_Key1, _Key2],
            _typing.Set[_Element],
        ] = {}
        self.__all_elements: _typing.Set[_Element] = set()

    def __iter__(self) -> _typing.Iterable[_Element]:
        return iter(self.__all_elements)

    def __in__(self, item: _Element):
        return item in self.__all_elements

    def __get_comb_keys(
        self, item: _Element
    ) -> _typing.Set[_typing.Tuple[_Key1, _Key2]]:
        keys1: _typing.Iterable[_Key1] = self.__get_keys1(item)
        keys2: _typing.Iterable[_Key2] = self.__get_keys2(item)

        comb_keys: _typing.Set[_typing.Tuple[_Key1, _Key2]] = set(
            _itertools.product(keys1, keys2)
        )
        return comb_keys

    def get(
        self, keys1: _typing.Set[_Key1], keys2: _typing.Set[_Key2]
    ) -> _typing.Set[_Element]:
        """
        返回所有满足`get_keys1(Element) & keys1 and get_keys2(Element) & keys2`的元素

        Parameters
        ---
        keys1, keys2 : set[Key1], set[Key2]
            查询键集
        """
        assert isinstance(keys1, set) and isinstance(keys2, set)

        res = set()
        for ck in _itertools.product(keys1, keys2):
            res.update(self.__barrels.get(ck, set()))
        return res

    def add(self, item: _Element) -> None:
        """
        添加元素

        Parameters
        ---
        item : Element
            元素
        """
        self.__all_elements.add(item)

        comb_keys = self.__get_comb_keys(item)
        for ck in comb_keys:
            if ck not in self.__barrels:
                self.__barrels[ck] = set()
            self.__barrels[ck].add(item)

    def remove(self, item: _Element) -> None:
        """
        删除元素

        Parameters
        ---
        item : Element
            元素

        Raises
        ---
        KeyError
            如果元素不存在
        """
        self.__all_elements.remove(item)

        comb_keys = self.__get_comb_keys(item)
        for ck in comb_keys:
            self.__barrels[ck].remove(item)
            if not self.__barrels[ck]:
                self.__barrels.pop(ck)

    def clear(self) -> None:
        """清空元素"""
        self.__all_elements.clear()
        self.__barrels.clear()
