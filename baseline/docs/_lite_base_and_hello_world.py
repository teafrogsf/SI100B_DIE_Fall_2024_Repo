import pygame

g_evene_queue = []


def add_event(event):
    global g_evene_queue
    g_evene_queue.append(event)


class Event:
    def __init__(self, code: int):
        self.code = code


class Listener:
    def __init__(self): ...

    def post(self, event: Event):
        add_event(event)

    def listen(self, event: Event): ...


# ======================================================
pygame.init()
g_window = pygame.display.set_mode((1000, 800))
DRAW = 1
STEP = 2


class Player(Listener):
    def __init__(self, image, rect):
        self.image = image
        self.rect = rect

    def listen(self, event: Event):
        if event.code == DRAW:
            g_window.blit(self.image, self.rect)
        elif event.code == pygame.KEYDOWN:
            self.keydown()

    def keydown(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_w]:  # w被按下
            self.rect.y -= 50  # y坐标减少10
        if keys[pygame.K_a]:
            self.rect.x -= 50
        if keys[pygame.K_s]:
            self.rect.y += 50
        if keys[pygame.K_d]:
            self.rect.x += 50
        if keys[pygame.K_ESCAPE]:
            exit()


if __name__ == "__main__":
    player = Player(
        image=pygame.transform.scale(
            pygame.image.load(r".\assets\npc\monster\1.png"), (60, 60)
        ),
        rect=pygame.Rect(610, 330, 60, 60),
    )
    listeners = [player]

    while True:
        g_window.fill((0, 0, 0))  # 全屏涂黑
        for event in pygame.event.get():
            add_event(Event(event.type))
        add_event(Event(STEP))
        add_event(Event(DRAW))

        while g_evene_queue:
            event = g_evene_queue.pop(0)
            for l in listeners:
                l.listen(event)

        pygame.display.flip()
