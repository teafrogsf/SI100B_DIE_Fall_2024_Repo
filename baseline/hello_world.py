"""
原点在屏幕左上角, 往右为x轴正方向, 往下为y轴正方向。
各种实体的Rect的坐标也是默认为左上角。
"""

import math
import random
from typing import Tuple, Optional

import pygame

import utils
import game_constants as c
from game_collections import (
    EventLike,
    Core,
    listening,
    EntityLike,
    GroupLike,
    ListenerLike,
    TextEntity,
)


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

    @listening(pygame.KEYDOWN)
    @listening(pygame.QUIT)
    def quit(self, event: EventLike):
        if event.code == pygame.QUIT:
            exit()
        if event.code == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            exit()


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
        second = body["second"]
        # ===MOVING
        if self.__speed < self.__max_speed:
            self.__speed += self.__max_speed * 0.1 * second
        self.__walking_radian += second * self.__speed
        shift = utils.IntTupleOper.mul(
            self.__walking_radius,
            (math.cos(self.__walking_radian), math.sin(self.__walking_radian)),
        )
        self.rect = self.__walking_center.move(*shift)


class StateShow(TextEntity):
    def __init__(self, rect=pygame.Rect(640, 550, 1, 1)):
        super().__init__(
            rect,
            font=TextEntity.get_zh_font(36),
            font_color=(255, 255, 255),
            back_ground=(0, 0, 0, 100),
            dynamic_size=True,
        )
        self.__cum_second = 4
        self.__cum_tick = 0
        self.center = self.rect.center

    @listening(c.EventCode.STEP)
    def step(self, event: EventLike):
        body: c.StepEventBody = event.body
        second = body["second"]
        self.__cum_second += second
        self.__cum_tick += 1
        if self.__cum_second > 5:
            self.set_text(
                f"""目前的TPS是: {self.__cum_tick / self.__cum_second:5.0f}\n{random.choice(utils.zote_precepts)}"""
            )
            self.__cum_second = 0
            self.__cum_tick = 0
            self.rect.center = self.center


if __name__ == "__main__":
    co = Core()
    group = GroupLike()
    player = Player()

    tree = EntityLike(
        pygame.Rect(410, 330, 60, 60),
        image=utils.load_image_and_scale(
            r".\assets\tiles\tree.png", pygame.Rect(510, 330, 60, 60)
        ),
    )
    wander_npc = WanderNpc()
    state_show = StateShow()
    group.add_listener(player)
    group.add_listener(wander_npc)
    group.add_listener(tree)
    group.add_listener(state_show)

    while True:
        co.window.fill((255, 255, 255))  # 全屏涂黑
        for event in co.yield_events():
            group.listen(event)  # 听取: 核心事件队列
        co.flip()  # 更新屏幕缓冲区
