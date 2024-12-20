import pygame

g_evene_queue = []

def add_event(event):
    global g_evene_queue
    g_evene_queue.append(event)

class Event:
    def __init__(self, code):
        self.code = code

class Listener:
    def __init__(self): ...

    def post(self, event):
        add_event(event)

    def listen(self, event): ...

DRAW = 1
STEP = 2

class EntityLike(Listener):
    def __init__(self, image, rect):
        self.image = image
        self.rect = rect

    def listen(self, event):
        if event.code == DRAW:
            g_window.blit(self.image, self.rect)

class Player(EntityLike):
    def __init__(self, image, rect):
        super().__init__(image, rect)
        self.hp = 100
    
    def listen(self, event):
        super().listen(event)
        if event.code == pygame.KEYDOWN:
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


pygame.init()
g_window = pygame.display.set_mode((1000, 800))


if __name__ == "__main__":
    mob = Player(
        image=pygame.transform.scale(
            pygame.image.load(r".\assets\npc\monster\1.png"), (60, 60)
        ),
        rect=pygame.Rect(610, 330, 60, 60),
    )
    listeners = [mob]

    while True:
        g_window.fill((0, 0, 0))  # 全屏涂黑
        for event in pygame.event.get(): # 将pygame默认事件如键盘等转换到自己的队列中
            add_event(Event(event.type))
        add_event(Event(STEP))
        add_event(Event(DRAW))

        while g_evene_queue:
            event = g_evene_queue.pop(0)
            for l in listeners:
                l.listen(event)

        pygame.display.flip() # 缓冲绘制到屏幕上
