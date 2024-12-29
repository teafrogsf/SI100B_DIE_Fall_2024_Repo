from typing import (
    Callable,
    Tuple,
    Union,
    TypedDict,
)
from collections.abc import Iterable

import math

import pygame

_NumberLike = Union[float, int]
_TupleLike = Union[Tuple[_NumberLike], _NumberLike]
_IntTupleLike = Union[Tuple[int], int]


@staticmethod
def l2norm(a: Union[_NumberLike, Iterable[_NumberLike]]) -> float:
    """计算向量的L2-Norm模长"""
    if isinstance(a, (int, float)):
        return a
    elif isinstance(a, Iterable):
        return sum(i**2 for i in a) ** 0.5
    else:
        raise TypeError(f"Only accecpt tuple[number] or number.")


class IntTupleOper:
    """
    仿Numpy一维整数元组基础运算函数实现 (带有广播机制)

    Examples
    ---
    ```
    op = IntTupleOper

    op.add((1, 2), (20, 30))  # (21, 32)
    op.mul((5, 7), 4.0)  # (20, 28)
    op.div(10.0, (5, 2.0))  # (2, 5)
    ```
    """

    @staticmethod
    def oper(
        a: _TupleLike,
        b: _TupleLike,
        operator: Callable[[_NumberLike, _NumberLike], _NumberLike],
    ) -> _IntTupleLike:
        if isinstance(a, (int, float)) and isinstance(b, (int, float)):
            return int(operator(a, b))

        if isinstance(b, (int, float)):  # 广播机制
            b = tuple(b for _ in a)
        elif isinstance(a, (int, float)):  # 广播机制
            a = tuple(a for _ in b)

        return tuple(int(operator(i, j)) for i, j in zip(a, b))

    @classmethod
    def add(cls, a: _TupleLike, b: _TupleLike) -> _IntTupleLike:
        return cls.oper(a, b, lambda x, y: x + y)

    @classmethod
    def sub(cls, a: _TupleLike, b: _TupleLike) -> _IntTupleLike:
        return cls.oper(a, b, lambda x, y: x - y)

    @classmethod
    def mul(cls, a: _TupleLike, b: _TupleLike) -> _IntTupleLike:
        return cls.oper(a, b, lambda x, y: x * y)

    @classmethod
    def div(cls, a: _TupleLike, b: _TupleLike) -> _IntTupleLike:
        return cls.oper(a, b, lambda x, y: x / y)

    @classmethod
    def min(cls, a: _TupleLike, b: _TupleLike) -> _IntTupleLike:
        return cls.oper(a, b, lambda x, y: min(x, y))

    @classmethod
    def max(cls, a: _TupleLike, b: _TupleLike) -> _IntTupleLike:
        return cls.oper(a, b, lambda x, y: max(x, y))

    @classmethod
    def interp(cls, a: _TupleLike, b: _TupleLike, factor: float) -> _IntTupleLike:
        return cls.oper(a, b, lambda x, y: x * (1 - factor) + y * factor)


class RectOper:
    """
    仿Numpy的`pygame.Rect`基础运算函数实现

    同时对`size`与`topleft`进行运算。
    """

    @staticmethod
    def oper(
        a: pygame.Rect,
        b: pygame.Rect,
        operator: Callable[[_NumberLike, _NumberLike], _NumberLike],
    ) -> pygame.Rect:
        op = IntTupleOper
        size = op.oper(a.size, b.size, operator)
        topleft = op.oper(a.topleft, b.topleft, operator)
        return pygame.Rect(topleft, size)

    @classmethod
    def add(cls, a: pygame.Rect, b: pygame.Rect) -> pygame.Rect:
        return cls.oper(a, b, lambda x, y: x + y)

    @classmethod
    def sub(cls, a: pygame.Rect, b: pygame.Rect) -> pygame.Rect:
        return cls.oper(a, b, lambda x, y: x - y)

    @classmethod
    def mul(cls, a: pygame.Rect, b: pygame.Rect) -> pygame.Rect:
        return cls.oper(a, b, lambda x, y: x * y)

    @classmethod
    def div(cls, a: pygame.Rect, b: pygame.Rect) -> pygame.Rect:
        return cls.oper(a, b, lambda x, y: x / y)

    @classmethod
    def min(cls, a: pygame.Rect, b: pygame.Rect) -> pygame.Rect:
        return cls.oper(a, b, lambda x, y: min(x, y))

    @classmethod
    def max(cls, a: pygame.Rect, b: pygame.Rect) -> pygame.Rect:
        return cls.oper(a, b, lambda x, y: max(x, y))

    @classmethod
    def interp(cls, a: pygame.Rect, b: pygame.Rect, factor: float) -> pygame.Rect:
        return cls.oper(a, b, lambda x, y: x * (1 - factor) + y * factor)


def load_image_and_scale(img_path: str, rect: pygame.Rect) -> pygame.Surface:
    return pygame.transform.scale(pygame.image.load(img_path), rect.size)


class _GridInfo(TypedDict):
    cell_size: Tuple[int, int]
    grid_shape: Tuple[int, int]
    grid_range: Tuple[int, int]


def grid_info(cell_size: Tuple[int, int], grid_range: Tuple[int, int]) -> _GridInfo:
    grid_shape = tuple(math.ceil(i / j) for i, j in zip(grid_range, cell_size))
    grid_range = tuple(i * j for i, j in zip(cell_size, grid_shape))
    res: _GridInfo = {
        "cell_size": cell_size,
        "grid_range": grid_range,
        "grid_shape": grid_shape,
    }
    return res


zote_precepts = [
    "戒律一：永远只打胜仗。 在输掉的战斗中，\n你不能获得任何战利品，更不能学到什么有用\n的东西。 所以，你要打赢所有的战斗，或者\n压根就不参与！",
    "戒律二：永远不要让别人嘲笑你。 傻瓜们会\n嘲笑一切，甚至会嘲笑比他们强大的人。 但\n是，你要注意，嘲笑声本身其实就是有害的！\n 它会像疾病一样蔓延开来，不久之后，所有\n人都会开始嘲笑你。 所以，你需要做的是迅\n速根除它，以阻止其扩散。",
    "戒律三：永远要保证足够的休息。 战斗和冒\n险会消耗你的体力。 而只有当你休息的时候\n，你的体力才会恢复。 所以，你休息的时间\n越长就越强大。",
    "戒律四：学会忘记过去。 过去是痛苦的，回\n忆过去只会徒增伤悲。相反，你可以试着想想\n别的事情，比如未来或者美食等。",
    "戒律五：谨记用力量打败力量。你的对手很强\n大？没关系！只需要用比他们更强大的力量去\n对付他们，你很快就可以战胜他们。",
    "戒律六：学会把握你自己的命运。我们的长辈\n常教导我们说，我们的命运在我们出生之前就\n已注定，说实话，我不同意。",
    "戒律七：永远不要为死者悲伤。死后的世界将\n会是怎样？会变得更好还是更坏？没人知道，\n所以对于“死亡”这件事，我们无需悲伤，更\n无需欢喜。",
    "戒律八：学会独自旅行。你不要去依赖任何人\n，再者，也没人会永远忠诚。所以，请记住：\n没人会永远与你同行。",
    "戒律九：永远让自己的家保持干净整洁。你自\n己就是你最宝贵的财产——你的家是你的安身\n立命之所。所以，你要尽可能地保持它的干净\n与整洁。",
    "戒律十：请让你的武器时刻保持锋利无比。于\n我而言，我会让我的武器——“生命终结者”\n从始至终都锋利无比。这样的话，砍东西就会\n容易得多。",
    "戒律十一：谨防母亲的背叛。这一条不言自明\n。",
    "戒律十二：谨记让你的披风保持干燥。如果你\n的披风湿了，就尽快把它弄干。因为穿着湿漉\n漉的披风不仅会很不舒服，而且还容易生病。",
    "戒律十三：永远不要害怕。恐惧只会让你退缩\n。我知道直面恐惧需要付出巨大的努力。但是\n，直面恐惧的前提就是要先不害怕。",
    "戒律十四：永远尊重强者。尊重力量或者智慧\n，抑或二者都强于你的人。不要轻视或者嘲笑\n他们。",
    "戒律十五：谨记对付一个敌人只用一拳。一拳\n便足以对付一个敌人，再多就是浪费了。这样\n的话，只需记住自己出了几拳，你就知道已经\n打败多少敌人了。",
    "戒律十六：永远不要迟疑。一旦你决定了就去\n做，不要瞻前顾后。这种行事方式会让你终生\n受益，进而取得更多的成就。",
    "戒律十七：永远相信自己的力量。别人可能会\n怀疑你，但有一个人是永远值得你信赖的——\n你自己。相信自己的力量能让你的步伐永远稳\n健。",
    "戒律十八：学会在黑暗中寻求真理。这个戒律\n同样也不言自明。",
    "戒律十九：谨记只有尝试了，你才有可能成功\n。如果你想尝试去做什么，就一定要坚持做到\n。一件事，要么成功，要么失败！所以，你要\n不惜一切代价获得成功。",
    "戒律二十：绝不撒谎。和别人交流时，说真话\n会让人觉得你很谦恭，同时，也会使得整个谈\n话过程变得很高效。不过，你要当心，说真话\n很容易会让你树敌，但这也是你必须要承担的\n代价。",
    "戒律二十一：要时刻警惕周围的环境。别只顾\n着埋头走路！你也要学会抬头看路，免得被偷\n袭。",
    "戒律二十二：好男儿要志在四方。只要有机会\n，我就会离开我的家乡，到处寻名山、访高友\n。梨园虽好，但终究不是久留之所。要知道，\n“温柔乡”即是“英雄冢”。",
    "戒律二十三：要摸清敌人的软肋。你遇到的每\n一个敌人都有其软肋，比如他们的身上有伤或\n者正在酣睡等。你必须时刻保持警惕，并且仔\n细观察你的敌人，从而发现他们的软肋！",
    "戒律二十四：学会痛击敌人的软肋。一旦发现\n敌人的软肋，你就应对其发起猛烈地攻击。这\n样你就能很快地歼灭他们了。",
    "戒律二十五：学会隐藏自己的软肋。要知道你\n的敌人也会试图去摸清你的软肋，所以你必须\n藏好它们。那么最佳的藏法是什么呢？从来就\n没有软肋。",
    "戒律二十六：不要相信你的倒影。当你对着某\n些光亮的表面时，你可能会看到一张自己的脸\n。而且这张脸会模仿你的各个动作，看起来就\n和你一模一样，但请你不要因此而相信它。",
    "戒律二十七：要尽量多吃。吃饭时，能吃多少\n吃多少。这能让你获得足够多的能量，而且还\n间接地减少了吃饭的次数。",
    "戒律二十八：永远不要凝视黑暗。如果当你凝\n视黑暗而久久不见一物时，你的大脑就会开始\n流连于陈旧的记忆，而戒律四已经说过了，要\n学会忘记过去，避免在过去的记忆中无休止地\n纠缠。",
    "戒律二十九：要刻意训练你的方向感。在蜿蜒\n曲折的洞穴中旅行很容易迷路。而有一个好的\n方向感就像有一张神奇的地图在你的脑子里，这非常有用。",
    "戒律三十：永远不要轻信别人的诺言。诺言有\n时候并不是很可靠，因为许诺者经常会食言，\n所以，不要轻信它，尤其是爱情或者婚姻的诺言。",
    "戒律三十一：要注意个人卫生。要知道，在脏\n兮兮的地方呆得太久是会让你生病的。所以，\n如果去别人家里，请要求主人给你提供最高\n规格的卫生条件。",
    "戒律三十二：名字有其内在的力量。所有的名\n字都有其内在的力量，所以，当你在给某个事\n物起名字的时候，你其实就是在赋予它力量。\n比如，我就给我自己的骨钉取名为“生命终结\n者”。",
    "戒律三十三：永远不要向你的敌人献殷勤。向\n你的敌人献殷勤并不是什么美德！因为你的敌\n人不配得到你的尊重、仁慈和怜悯。",
    "戒律三十四：睡前不要吃东西。睡前吃东西首\n先不好消化，其次还影响休息，这已经是常识\n了。",
    "戒律三十五：上就是上，下就是下。如果在黑\n暗中摔倒的话，你很容易就会失去方向感，忘\n记哪条路是向上走的。所以，请记住这条戒律\n！",
    "戒律三十六：谨记蛋壳很容易破碎。这条戒律\n又是不言自明的。",
    "戒律三十七：永远只从别人那里借东西，自己\n的东西绝不外借。如果别人有借有还，那么到\n头来你什么也得不到。但是，如果你只借不还\n，那么你就会赚得钵丰盆满。",
    "戒律三十八：请警惕神秘的力量。在我们头上\n一直有一股神秘的力量将我们往下压。如果你\n在空中停留得太久的话，那么那股神秘的力量\n就会把你压进地里，进而让你丢掉性命。所以\n，你要当心啊！",
    "戒律三十九：学会快吃慢饮。我们的身体是一\n个十分脆弱的东西，所以补充能量的时候，你\n必须小心谨慎。吃饭时你可以尽量快一点，但\n喝水的时候你一定要慢一些。",
    "戒律四十：随心所欲，随心而动。过分地拘泥\n于规则反而会成为你的负担，有时候，你需要\n灵活变通，跟随自己的节奏。",
    "戒律四十一：学会分辨谎言。别人会经常撒谎\n，所以，你要尖锐地指出来，并且当面质疑他\n们，直到他们承认自己撒谎了。",
    "戒律四十二：永远不要做守财奴。有些人宁愿\n将钱带进棺材，也不愿花它们，这就是典型的\n守财奴。所以，你要及时行乐，能花的时候就\n花才是聪明人的做法，不然你就享受不到生命\n中的各种乐趣了。",
    "戒律四十三：永远不要宽恕别人。如果有人恳\n求你的原谅，比如你的兄弟，一定要拒绝。任\n何人都不配得到你的原谅，包括你的那个兄弟\n。",
    "戒律四十四：不要试图在水里呼吸。水是可以\n用来提神的，但如果你想试图在里面呼吸的话\n，你会窒息而死的。",
    "戒律四十五：谨记一个事物永远不可能变成另\n外一个事物。这条戒律应该是显而易见的，但\n总是有人试图指鹿为马，混淆视听。所以，你\n要小心啊！",
    "戒律四十六：谨记世界没你想象的那么大。年\n轻时，你认为天广地阔，这是很自然的。但不\n幸的是，世界实际上要小得多。这是我多年翻\n山越岭、跋山涉水后的感悟。",
    "戒律四十七：要打造属于你自己的武器。只有\n你自己知道你想要什么样的武器。在我在很小\n的时候，我就用壳木制作了一把骨钉——“生\n命终结者”。并且，它从未让我失望过，同样\n地，我也如此。",
    "戒律四十八：请小心火烛。火是一个可以肆意\n妄为的精灵。它能温暖你、照亮你，但如果靠\n得太近的话，它也会烧焦你。",
    "戒律四十九：谨记雕像毫无意义。不要去崇拜\n雕像！况且，从来就没有人为你我立像，那我\n们为什么还要关注这个玩意？",
    "戒律五十：不要痴迷于神秘。生活有时候会让\n我们一头雾水，满脸疑惑。此时，如果你不能\n立刻明白它背后所暗含的意义，那么就不要浪\n费时间去刨根究底了，大胆地继续前进就行。",
    "戒律五十一：谨记没有什么是无害的。如果有\n机会，这世界上的一切都会伤害到你，比如朋\n友、敌人、怪物和不平坦的道路等。所以，你\n要时刻怀有质疑精神。",
    "戒律五十二：谨防父亲的嫉妒。父亲们总是认\n为，正是由于他们创造了我们，所以我们必须\n为他们服务，并且决不能有超越他们的地方。\n如果你想开辟一条属于你自己的道路，就必须\n先战胜你的父亲，或者干脆离开他。",
    "戒律五十三：不要横刀夺爱。不管是谁，都会\n将自己的挚爱之物埋藏在内心深处。如果你不\n小心瞥见了它们，就要学会克制住想占为己有\n的冲动。因为横刀夺爱是不会给你带来任何幸\n福的。",
    "戒律五十四：如果你锁了什么东西，那么请把\n钥匙保管好。没有什么东西可以永远被锁起来\n，所以请保管好你的钥匙。因为，总有一天，\n你会回来取走你锁起来的东西的。",
    "戒律五十五：不要向任何人摧眉折腰。世界上\n总是有人会把自己的意志强加给别人。他们只\n会巧取豪夺，却还总无耻地声称你的食物、土\n地和身体，甚至你的思想都属于他们！所以，\n请记住：永远不要向他们屈服，更不要任他们\n摆布。",
    "戒律五十六：永远不要做梦。梦其实是一个很\n危险的东西，其本质是非你所有的奇怪的想法\n，并且还会潜入你的大脑。可是，如果你想单\n方面排斥它的话，又会惹来一身的病！所以，\n最好就像我一样不要做梦。",
    "戒律五十七：请遵守我说的所有戒律。最重要\n的是要把所有戒律都牢记在心，并且一丝不苟\n地遵守它们。包括这一条！",
]
