# 本程序用于演示事件队列、镜头移动、障碍物等游戏需要的功能的实现原理
# 本程序在单个文件中实现了所有功能，实际实现需要按照模板的要求分文件
# 相较于模板的要求，基础功能的实现较为简易，仅演示原理
# 例如事件队列中的事件可以有优先级属性，并按照优先级排序，优先级较高的事件先处理

import pygame
import random

g_evene_queue = []  # 事件队列


def add_event(event):  # 向事件队列中添加事件
    global g_evene_queue
    g_evene_queue.append(event)


class Event:  # 定义事件类，属性包括用于区分事件种类的编号，以及可选参数body传递一些信息
    def __init__(self, code: int, body={}):
        self.code = code
        self.body = body


class Listener:  # 定义监听者类，该类可以响应事件以及发送新的事件
    def __init__(self): ...

    def post(self, event: Event):
        add_event(event)

    def listen(self, event: Event): ...


# ======================================================
pygame.init()  # 初始化pygame
g_window = pygame.display.set_mode((1000, 800))  # 窗口大小

# 定义不同种类事件的编号
DRAW = 1
STEP = 2
REQUEST_MOVE = 3
CAN_MOVE = 4


class EntityLike(Listener):  # 实体类
    def __init__(self, image: pygame.Surface, rect: pygame.Rect):
        # 两个属性代表显示的图片路径、显示的矩形的位置和大小
        self.image = image
        self.rect = rect

    def listen(self, event: Event): ...

    def draw(
        self, camera: tuple[int, int]
    ):  # 定义显示实体的方法，该方法在场景需要描绘图像的时候调用
        rect = self.rect.move(
            *(-i for i in camera)
        )  # 根据摄像头的位置计算实际要描绘的位置，例如摄像头往上了，实际描绘的位置就要往下
        # 实际上就是将该实体的横纵坐标分别减去摄像头左上角的坐标
        # 这里move方法是产生了一个新的rect，而不是修改了原有的rect。例如，障碍物墙体原本的位置应该是在生成以后就不变的
        # 对于玩家来说，玩家往一个方向移动之后，在这里描绘时又会被向相反方向移动，因此表现出玩家在镜头中间不动的效果
        g_window.blit(self.image, rect)  # 调用pygame的方法描绘图像


class Player(EntityLike):  # 玩家类

    def __init__(self, image: pygame.Surface, rect: pygame.Rect):
        # 继承实体类
        super().__init__(image, rect)
        self.hp = 100

    def listen(self, event: Event):  # 玩家类所响应的事件
        if event.code == pygame.KEYDOWN:  # 键盘按下事件
            self.keydown()
        elif event.code == CAN_MOVE:  # 响应场景发出的允许移动事件
            self.rect.x = event.body["POS"][0]
            self.rect.y = event.body["POS"][1]
        super().listen(event)  # 继承原有的响应事件内容，如对DRAW的响应

    def keydown(self):
        keys = pygame.key.get_pressed()

        # 使用nx和ny计算将要移动到的位置
        nx = self.rect.x
        ny = self.rect.y

        if keys[pygame.K_w]:  # W键被按下
            ny -= 10
        if keys[pygame.K_a]:
            nx -= 10
        if keys[pygame.K_s]:
            ny += 10
        if keys[pygame.K_d]:
            nx += 10
        if keys[pygame.K_ESCAPE]:  # 按下ESC键时退出
            exit()
        self.post(Event(REQUEST_MOVE, {"POS": (nx, ny)}))  # 发出请求移动事件


# 定义一些对tuple的操作，方便坐标运算


def tuple_sub(a, b):
    return (a[0] - b[0], a[1] - b[1])
    # 有一种更好的写法是 return tuple(i - j for i, j in zip(a, b))，不同的运算只要修改中间的符号即可


def tuple_mul(a, b):
    return (a[0] * b, a[1] * b)


def tuple_min(a, b):
    return (min(a[0], b[0]), min(a[1], b[1]))


def tuple_max(a, b):
    return (max(a[0], b[0]), max(a[1], b[1]))


class Wall(EntityLike):  # 障碍物的类
    def __init__(self, rect: pygame.rect.Rect):
        # 图片这里直接指定了，需要传递的参数是该障碍物在游戏中矩形的位置和大小
        super().__init__(
            image=pygame.transform.scale(
                pygame.image.load(r".\assets\tiles\cityWall.png"), (40, 40)
            ),
            rect=rect,
            # 课堂上写的时候rect=rect的位置可能有误，非常抱歉
        )


class Tile(
    EntityLike
):  # 地图背景的类，背景是由一个一个方块组成的，每个方块都是该类的实例
    def __init__(self, type: int, rect: pygame.rect.Rect):
        # 这里接受一个int代表该方块使用哪种图片
        super().__init__(
            image=pygame.transform.scale(
                # 根据type来指定图片路径
                pygame.image.load(rf".\assets\tiles\ground{type}.png"),
                (40, 40),
            ),
            rect=rect,
        )


class SceneLike(Listener):  # 场景的类，管理障碍物、角色、地图背景的描绘、刷新等

    def __init__(self, player):
        super().__init__()
        self.walls = []  # 存储障碍物的列表
        self.tiles = []  # 存储地图背景方块的列表
        self.player = player  # 传递玩家的实例
        self.window_scale = (1000, 800)  # 显示窗口的大小
        self.map_range = (1500, 1000)  # 实际地图的大小
        self.carema = (0, 0)  # 镜头的初始位置
        self.update_camera()  # 更新镜头的位置

        # 根据地图的尺寸每行每列逐个生成地图方块
        for i in range(self.map_range[0] // 40 + 1):
            for j in range(self.map_range[1] // 40 + 1):
                self.tiles.append(
                    # 方块的种类是随机的，即随机选取一张素材作为该方块
                    # 方块的大小是40*40，根据当前的行数和列数来算出位置
                    Tile(random.randint(1, 5), pygame.Rect(i * 40, j * 40, 40, 40))
                )

        # 在地图里随机生成一些障碍物
        for _ in range(20):
            self.walls.append(
                Wall(
                    pygame.Rect(
                        random.randint(0, self.map_range[0]),
                        random.randint(0, self.map_range[1]),
                        40,
                        40,
                    )
                    # 课堂上演示时出现问题是因为第二个random.randint这里写成了random没写randint，非常抱歉！！！ TAT
                )
            )

    # 更新镜头
    def update_camera(self):
        player_center_cord = (
            self.player.rect.center
        )  # 获取玩家当前的位置，使用center是因为玩家有60*60的大小，要获取中间位置
        self.camera = tuple_sub(
            player_center_cord, tuple_mul(self.window_scale, 0.5)
        )  # 镜头的左上角位置应该是玩家的位置减去一半窗口的宽和高
        left_top = (0, 0)  # 镜头的横纵坐标不能低于(0, 0)
        right_down = tuple_sub(
            self.map_range, self.window_scale
        )  # 镜头的横纵坐标不能多于地图大小减去窗口大小
        # 对镜头的位置和上述两点分别取min和max，防止镜头超出地图范围
        self.camera = tuple_min(right_down, self.camera)
        self.camera = tuple_max(left_top, self.camera)

    def listen(self, event: Event):  # 场景所监听的事件
        super().listen(event)
        if event.code == REQUEST_MOVE:  # 监听玩家的移动请求事件
            can_move = 1  # 一开始默认可以移动
            target_rect = pygame.Rect(
                event.body["POS"][0], event.body["POS"][1], 60, 60
            )  # 获得移动后的玩家矩形
            for wall in self.walls:  # 遍历所有障碍物
                if wall.rect.colliderect(target_rect):  # 调用pygame的方法检测碰撞
                    can_move = 0  # 有碰撞则不能移动
                    break  # 有碰撞时不用再判断后面的了
            if can_move:  # 如果可以移动的话就发送允许移动事件
                self.post(Event(CAN_MOVE, event.body))

        if event.code == STEP:  # STEP是每次游戏周期刷新时会被触发的事件
            self.update_camera()  # 更新镜头的位置

        if event.code == DRAW:  # DRAW事件，用于描绘场景中的实体
            for tile in self.tiles:  # 遍历所有地图背景图块并描绘
                tile.draw(self.camera)
            for wall in self.walls:  # 遍历所有障碍物并描绘
                wall.draw(self.camera)
            self.player.draw(self.camera)  # 描绘玩家图像


if __name__ == "__main__":
    mob = Player(
        image=pygame.transform.scale(
            pygame.image.load(r".\assets\npc\monster\1.png"), (60, 60)
        ),
        rect=pygame.Rect(610, 330, 60, 60),
    )  # 生成角色实例
    scene = SceneLike(mob)  # 生成场景实例
    listeners = [mob, scene]  # 将角色和场景加入监听者列表

    while True:
        g_window.fill((0, 0, 0))  # 全屏涂黑
        for event in pygame.event.get():  # 将pygame默认事件如键盘等转换到自己的队列中
            add_event(Event(event.type))
        add_event(Event(STEP))  # 在while循环中，每轮都添加周期事件STEP
        add_event(Event(DRAW))  # 在while循环中，每轮都添加描绘事件DRAW

        while g_evene_queue:  # 依次将事件队列中的事件取出并处理
            event = g_evene_queue.pop(0)  # 取出一个事件
            for l in listeners:  # 遍历所有监听者
                l.listen(event)  # 调用监听者的listen方法来尝试对该事件进行响应

        pygame.display.flip()  # 缓冲绘制到屏幕上
