import pygame
import sys
import random

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
GRAVITY = 1
FPS = 60

class Button:
    def __init__(self, text, pos, action):
        self.text = text
        self.pos = pos
        self.action = action
        self.font = pygame.font.SysFont('arial', 30)
        self.normal_color = (50, 150, 50)
        self.hover_color = (100, 200, 100)
        self.rect = pygame.Rect(pos[0], pos[1], 200, 50)

    def draw(self, screen):
        mouse_pos = pygame.mouse.get_pos()
        color = self.hover_color if self.rect.collidepoint(mouse_pos) else self.normal_color
        pygame.draw.rect(screen, color, self.rect)
        text_surface = self.font.render(self.text, True, (255, 255, 255))
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)

    def check_click(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and self.rect.collidepoint(event.pos):
            self.action()

class Player:
    def __init__(self):
        self.width, self.height = 40, 60
        self.rect = pygame.Rect(100, 500, self.width, self.height)
        self.color = (0, 0, 255)
        self.move_speed = 5
        self.health = 100
        self.max_health = 100
        self.vel_y = 0
        self.jump_power = -15
        self.on_ground = False
        self.attack_damage = 25
        self.attack_cooldown = 300
        self.last_attack_time = 0
        self.sword_anim_time = 0
        self.sword_anim_duration = 200
        self.sword_swinging = False

    def move(self, keys, platforms, left_limit, right_limit):
        dx = 0
        if keys[pygame.K_a]:
            dx = -self.move_speed
        if keys[pygame.K_d]:
            dx = self.move_speed

        self.vel_y += GRAVITY
        if self.vel_y > 10:
            self.vel_y = 10
        dy = self.vel_y

        if (keys[pygame.K_SPACE] or keys[pygame.K_w]) and self.on_ground:
            self.vel_y = self.jump_power

        self.rect.x += dx
        if self.rect.left < left_limit:
            self.rect.left = left_limit
        if self.rect.right > right_limit:
            self.rect.right = right_limit

        for platform in platforms:
            if self.rect.colliderect(platform):
                if dx > 0:
                    self.rect.right = platform.left
                elif dx < 0:
                    self.rect.left = platform.right

        self.rect.y += dy
        self.on_ground = False
        for platform in platforms:
            if self.rect.colliderect(platform):
                if dy > 0:
                    self.rect.bottom = platform.top
                    self.vel_y = 0
                    self.on_ground = True
                elif dy < 0:
                    self.rect.top = platform.bottom
                    self.vel_y = 0

    def attack(self, enemies):
        now = pygame.time.get_ticks()
        if now - self.last_attack_time < self.attack_cooldown:
            return
        self.last_attack_time = now
        self.sword_anim_time = now
        self.sword_swinging = True

        attack_rect = pygame.Rect(self.rect.centerx, self.rect.top, 50, 40)
        for enemy in enemies:
            if attack_rect.colliderect(enemy.rect) and enemy.health > 0:
                enemy.take_damage(self.attack_damage)

    def update_sword_animation(self):
        if self.sword_swinging:
            now = pygame.time.get_ticks()
            if now - self.sword_anim_time > self.sword_anim_duration:
                self.sword_swinging = False

    def draw(self, screen, offset_x):
        draw_rect = self.rect.move(-offset_x, 0)
        pygame.draw.rect(screen, self.color, draw_rect)
        pygame.draw.circle(screen, (0, 0, 200), (draw_rect.centerx, draw_rect.top + 15), 15)
        sword_color = (192, 192, 192)
        if self.sword_swinging:
            sword_rect = pygame.Rect(draw_rect.right, draw_rect.top + 30, 40, 10)
            pygame.draw.rect(screen, sword_color, sword_rect)
            pygame.draw.line(screen, (150, 150, 150), (sword_rect.left, sword_rect.top), (sword_rect.left, sword_rect.bottom), 3)
        else:
            sword_rect = pygame.Rect(draw_rect.right, draw_rect.top + 30, 10, 40)
            pygame.draw.rect(screen, sword_color, sword_rect)
            pygame.draw.line(screen, (150, 150, 150), (sword_rect.centerx, sword_rect.top), (sword_rect.centerx, sword_rect.bottom), 3)

    def draw_health_bar(self, screen):
        bar_width, bar_height = 200, 20
        x, y = 10, 10
        fill = (self.health / self.max_health) * bar_width
        outline_rect = pygame.Rect(x, y, bar_width, bar_height)
        fill_rect = pygame.Rect(x, y, fill, bar_height)
        pygame.draw.rect(screen, (34, 139, 34), fill_rect)
        pygame.draw.rect(screen, (255, 255, 255), outline_rect, 2)

class Enemy:
    def __init__(self, pos):
        self.image = pygame.Surface((40, 50))
        self.image.fill((255, 0, 0))
        self.rect = self.image.get_rect(topleft=pos)
        self.health = 50
        self.speed = 2

    def update(self, player, platforms, left_limit, right_limit):
        if self.health <= 0:
            return
        if player.rect.centerx < self.rect.centerx:
            self.rect.x -= self.speed
            if self.rect.left < left_limit:
                self.rect.left = left_limit
            for platform in platforms:
                if self.rect.colliderect(platform):
                    self.rect.left = platform.right
        elif player.rect.centerx > self.rect.centerx:
            self.rect.x += self.speed
            if self.rect.right > right_limit:
                self.rect.right = right_limit
            for platform in platforms:
                if self.rect.colliderect(platform):
                    self.rect.right = platform.left

        self.rect.y += GRAVITY
        for platform in platforms:
            if self.rect.colliderect(platform):
                self.rect.bottom = platform.top

    def take_damage(self, amount):
        self.health -= amount
        if self.health <= 0:
            self.die()

    def die(self):
        self.health = 0
        self.rect.topleft = (-100, -100)

    def draw(self, screen, offset_x):
        if self.health > 0:
            draw_rect = self.rect.move(-offset_x, 0)
            screen.blit(self.image, draw_rect)

class Level:
    def __init__(self, screen, player, platforms, enemies, bg_color, name, ground_color, tree_color):
        self.screen = screen
        self.player = player
        self.platforms = platforms
        self.enemies = enemies
        self.bg_color = bg_color
        self.sky_offset = 0
        self.name = name
        self.ground_color = ground_color
        self.tree_color = tree_color
        self.level_width = max(p.right for p in platforms)

    def update(self):
        for enemy in self.enemies:
            enemy.update(self.player, self.platforms, 0, self.level_width)
        self.player.update_sword_animation()
        self.sky_offset = (self.sky_offset + 0.1) % SCREEN_WIDTH

    def draw(self, offset_x):
        self.screen.fill(self.bg_color)
        cloud_color = (255, 255, 255)
        for i in range(-1, 3):
            x = (self.sky_offset * 50 + i * 300) % (SCREEN_WIDTH + 300) - 300
            pygame.draw.ellipse(self.screen, cloud_color, (x, 100, 100, 60))
            pygame.draw.ellipse(self.screen, cloud_color, (x + 40, 80, 100, 60))
            pygame.draw.ellipse(self.screen, cloud_color, (x + 80, 100, 100, 60))

        ground_height = 50
        pygame.draw.rect(self.screen, self.ground_color, (0, SCREEN_HEIGHT - ground_height, SCREEN_WIDTH, ground_height))

        for x in range(100, self.level_width, 250):
            tree_x = x - offset_x
            if -100 < tree_x < SCREEN_WIDTH + 100:
                pygame.draw.rect(self.screen, (139, 69, 19), (tree_x, SCREEN_HEIGHT - ground_height - 120, 18, 120))
                pygame.draw.circle(self.screen, self.tree_color, (tree_x + 9, SCREEN_HEIGHT - ground_height - 120), 45)

        for platform in self.platforms:
            draw_rect = platform.move(-offset_x, 0)
            pygame.draw.rect(self.screen, (120, 72, 0), draw_rect)

        for enemy in self.enemies:
            enemy.draw(self.screen, offset_x)

        self.player.draw(self.screen, offset_x)

class MainMenu:
    def __init__(self, game):
        self.game = game
        self.screen = game.screen
        self.buttons = []
        self.font = pygame.font.SysFont('arial', 40)
        self.create_buttons()

    def create_buttons(self):
        start_button = Button("Start Game", (300, 200), self.start_game)
        quit_button = Button("Quit", (300, 270), self.quit_game)
        self.buttons = [start_button, quit_button]

    def start_game(self):
        self.game.state = "game"

    def quit_game(self):
        pygame.quit()
        sys.exit()

    def run(self):
        running = True
        while running and self.game.state == "main_menu":
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                for button in self.buttons:
                    button.check_click(event)

            self.screen.fill((0, 0, 0))
            title_surface = self.font.render("Epic Fantasy Game", True, (255, 255, 0))
            self.screen.blit(title_surface, (220, 100))

            for button in self.buttons:
                button.draw(self.screen)

            pygame.display.flip()
            self.game.clock.tick(FPS)

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Epic Fantasy 2D Game")
        self.clock = pygame.time.Clock()
        self.state = "main_menu"
        self.player = Player()
        self.levels = {}
        self.create_levels()
        self.current_level_name = "forest"
        self.current_level = self.levels[self.current_level_name]
        self.camera_x = 0
        self.menu = MainMenu(self)
        self.transitioning = False
        self.transition_alpha = 0
        self.transition_speed = 5
        self.next_level_name = None

    def create_levels(self):
        platforms_forest = [pygame.Rect(x, 550, 200, 50) for x in range(0, 2000, 200)]

        enemies_forest = [Enemy((random.randint(200, 1800), 500)) for _ in range(4)]
        self.levels["forest"] = Level(self.screen, self.player, platforms_forest, enemies_forest,
                                     (135, 206, 235), "Ліс", (34, 139, 34), (34, 139, 34))

        platforms_earth = [pygame.Rect(x, 550, 200, 50) for x in range(0, 2000, 200)]

        enemies_earth = [Enemy((random.randint(200, 1800), 500)) for _ in range(3)]
        self.levels["earth"] = Level(self.screen, self.player, platforms_earth, enemies_earth,
                                    (210, 180, 140), "Земля", (160, 82, 45), (85, 107, 47))

        platforms_desert = [pygame.Rect(x, 550, 200, 50) for x in range(0, 2000, 200)]

        enemies_desert = [Enemy((random.randint(200, 1800), 500)) for _ in range(2)]
        self.levels["desert"] = Level(self.screen, self.player, platforms_desert, enemies_desert,
                                     (255, 236, 139), "Пустеля", (238, 214, 175), (205, 133, 63))

    def run(self):
        while True:
            if self.state == "main_menu":
                self.menu.run()
            elif self.state == "game":
                self.game_loop()

    def start_transition(self, next_level_name):
        self.transitioning = True
        self.transition_alpha = 0
        self.next_level_name = next_level_name

    def game_loop(self):
        running = True
        while running and self.state == "game":
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    self.player.attack(self.current_level.enemies)
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.state = "main_menu"
                        running = False

            keys = pygame.key.get_pressed()
            left_limit = 0
            right_limit = self.current_level.level_width
            self.player.move(keys, self.current_level.platforms, left_limit, right_limit)

            self.camera_x = self.player.rect.centerx - SCREEN_WIDTH // 2
            if self.camera_x < 0:
                self.camera_x = 0
            max_camera_x = self.current_level.level_width - SCREEN_WIDTH
            if self.camera_x > max_camera_x:
                self.camera_x = max_camera_x

            # Перевірка переходу між рівнями
            if not self.transitioning:
                if self.current_level_name == "forest" and self.player.rect.right > self.current_level.level_width - 10:
                    self.start_transition("earth")
                elif self.current_level_name == "earth" and self.player.rect.right > self.current_level.level_width - 10:
                    self.start_transition("desert")
                elif self.current_level_name == "desert" and self.player.rect.left < 10:
                    self.start_transition("earth")
                elif self.current_level_name == "earth" and self.player.rect.left < 10:
                    self.start_transition("forest")

            self.current_level.update()
            self.current_level.draw(self.camera_x)
            self.player.draw_health_bar(self.screen)

            # Плавний перехід (fade)
            if self.transitioning:
                self.transition_alpha += self.transition_speed
                if self.transition_alpha >= 255:
                    self.transition_alpha = 255
                    # Змінюємо рівень
                    self.current_level_name = self.next_level_name
                    self.current_level = self.levels[self.current_level_name]
                    # Позиція гравця на новому рівні
                    if self.current_level_name == "forest":
                        self.player.rect.left = 0
                    elif self.current_level_name == "earth":
                        if self.next_level_name == "earth":
                            self.player.rect.left = 0
                        else:
                            self.player.rect.right = self.current_level.level_width
                    elif self.current_level_name == "desert":
                        self.player.rect.left = 0
                    self.transition_speed = -self.transition_speed  # Починаємо fade-in
                elif self.transition_alpha <= 0:
                    self.transition_alpha = 0
                    self.transitioning = False
                    self.transition_speed = abs(self.transition_speed)

                fade_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
                fade_surface.set_alpha(self.transition_alpha)
                fade_surface.fill((0, 0, 0))
                self.screen.blit(fade_surface, (0, 0))

            pygame.display.flip()
            self.clock.tick(FPS)

if __name__ == "__main__":
    game = Game()
    game.run()
