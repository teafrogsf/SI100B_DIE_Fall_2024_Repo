"""
原点在屏幕左上角, 往右为x轴正方向, 往下为y轴正方向。
各种实体的Rect的坐标也是默认为左上角。
"""

import math

import pygame

import utils
import game_constants as c
from game_collections import EventLike, Core, listening, EntityLike, GroupLike


class Player(EntityLike):
    def __init__(
        self,
        rect: pygame.Rect = pygame.Rect(610, 330, 60, 60),  # x, y, width, height
    ):
        image = utils.load_image_and_scale(r".\assets\player\1.png", rect)
        super().__init__(rect, image=image)

    @listening(pygame.KEYDOWN)  # 捕获: 按下按键
    def move(self, event: EventLike):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_w]:  # w被按下
            self.rect.y -= 50  # y坐标减少10
        if keys[pygame.K_a]:
            self.rect.x -= 50
        if keys[pygame.K_s]:
            self.rect.y += 50
        if keys[pygame.K_d]:
            self.rect.x += 50


class WanderNpc(EntityLike):
    def __init__(
        self,
        rect: pygame.Rect = pygame.Rect(400, 330, 60, 60),  # x, y, width, height
    ):
        image = utils.load_image_and_scale(r".\assets\npc\npc.png", rect)
        super().__init__(rect, image=image)

        self.__walking_center: pygame.Rect = self.rect.copy()
        self.__walking_radius: float = 200
        self.__walking_radian: float = 0

        self.__max_speed: float = 5
        self.__speed: float = 0

    @listening(c.EventCode.STEP)
    def step(self, event: EventLike):
        body: c.StepEventBody = event.body
        secord = body["secord"]
        # ===MOVING
        if self.__speed < self.__max_speed:
            self.__speed += self.__max_speed * 0.1 * secord
        self.__walking_radian += secord * self.__speed
        shift = utils.IntTupleOper.mul(
            self.__walking_radius,
            (math.cos(self.__walking_radian), math.sin(self.__walking_radian)),
        )
        self.rect = self.__walking_center.move(*shift)


if __name__ == "__main__":
    co = Core()
    group = GroupLike()
    group.add_listener(Player())
    group.add_listener(
        EntityLike(
            pygame.Rect(410, 330, 60, 60),
            image=utils.load_image_and_scale(
                r".\assets\tiles\tree.png", pygame.Rect(510, 330, 60, 60)
            ),
        )
    )
    group.add_listener(WanderNpc())

    while True:
        co.window.fill((0, 0, 0))  # 全屏涂黑
        for event in co.yield_events():
            group.listen(event)  # 听取: 核心事件队列
        co.flip()  # 更新屏幕缓冲区
