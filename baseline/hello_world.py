"""
原点在屏幕左上角, 往右为x轴正方向, 往下为y轴正方向。
各种实体的Rect的坐标也是默认为左上角。
"""

import pygame

import utils
import game_constants as c
from game_collections import EventLike, Core, listening, EntityLike, GroupLike


import pygame


class Mob(EntityLike):
    def __init__(
        self,
        rect: pygame.Rect = pygame.Rect(610, 330, 60, 60),  # x, y, width, height
    ):
        image = utils.load_image_and_scale(r".\assets\npc\monster\1.png", rect)
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


if __name__ == "__main__":
    co = Core()
    group = GroupLike()
    group.add_listener(Mob())
    group.add_listener(
        EntityLike(
            pygame.Rect(410, 330, 60, 60),
            image=utils.load_image_and_scale(
                r".\assets\tiles\tree.png", pygame.Rect(510, 330, 60, 60)
            ),
        )
    )

    while True:
        co.window.fill((0, 0, 0))  # 全屏涂黑
        for event in co.yield_events():
            group.listen(event)  # 听取: 核心事件队列
        co.flip()  # 更新屏幕缓冲区
