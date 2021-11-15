import logging
import time
import webbrowser
from pathlib import Path
from random import choice, randint, sample

from webcolors import hex_to_rgb
from yaml import SafeLoader, load

import pygame


def maxdiff(a, b):
    return(max([a-b for a, b in zip(a, b)]))

# directions
# scroll up or down to change the color
# once the color matches the background click to see how close you are
# if you are close enough you win and move to the next level
# if you are not close enough you lose a life
# if you run out of lives you lose


class TextInfo:
    def __init__(self, font, size):
        self.font = font
        self.size = size

    def render(self, text):
        self.img = self.font.render(self.text, True, (200, 200, 200), (0, 0, 0))


class Block(pygame.sprite.Sprite):
    def __init__(self, color, width, height, x, y, color_axis):
        super().__init__()
        self.image = pygame.Surface([width, height])
        self.foreground = list(color)
        self.update_foreground()
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.color_axis = color_axis

    def update_foreground(self):
        logging.debug(f"Updating foreground to {self.foreground}")
        for i, value in enumerate(self.foreground):
            if value >= 254:
                self.foreground[i] = 254
            elif value <= 0:
                self.foreground[i] = 0
        self.image.fill(self.foreground)

    def draw(self, screen):
        screen.blit(self.image, self.rect)

    def change_color(self, step):
        self.foreground[self.color_axis] += step
        self.update_foreground()

    def move(self, newX, newY):
        self.rect.x = newX
        self.rect.y = newY


class Level():
    def __init__(self, file_name):
        with open(file_name) as f:
            data = load(f, Loader=SafeLoader)
            self.title = data['title']
            self.url = data['url']
            if 'image' in data:
                self.image = pygame.image.load(data['image'])
                self.width = self.image.get_width()
                self.height = self.image.get_height()
            self.colors = [hex_to_rgb(
                color) for color in data['colors']]


class Game():
    def __init__(self):
        self.levels = []
        self.current_level = 0
        self.load_levels()
        self.lives = 3
        self.accuracy = 0
        self.speed = 0
        self.screen_width = 1024
        self.screen_height = 768
        self.running = False
        self.current_color = 0
        heart = pygame.image.load('assets/heart.png')
        external_link = pygame.image.load('assets/external_link.png')
        self.heart = pygame.transform.scale(heart, (25, 25))
        self.external_link = pygame.transform.scale(external_link, (20, 20))
        self.mode = 'playing'  # 'observe' 'intro'

    def load_levels(self):
        levels = list(Path('levels').glob('*.yml'))
        for level in sample(levels, len(levels)):
            self.levels.append(Level(level))
            logging.debug(f"Loaded level {level}")

    def setup_current_level(self):
        logging.debug(f"Setting up level {self.current_level}")
        self.level = self.levels[self.current_level]
        logging.debug(f"with colors {self.level.colors}")
        self.blocks = []
        for background in self.level.colors:
            color_axis = randint(0, 2)
            foreground = list(background).copy()
            foreground[color_axis] = background[color_axis] + 20 * choice([-1, 1])
            self.blocks.append(Block(foreground, 100, 100, (self.screen_width-100)/2, (self.screen_height-100)/2, color_axis))

    def draw_lives(self):
        for i in range(self.lives):
            img_rect = self.heart.get_rect()
            img_rect.x = self.screen_width - 100 + 30*i
            img_rect.y = 10
            self.screen.blit(self.heart, img_rect)

    def draw_level(self):
        self.background = list(self.level.colors[self.current_color])
        self.screen.fill(self.background)
        self.blocks[self.current_color].draw(self.screen)
        self.draw_title()

    def draw_title(self):
        img = self.font.render(f"    {self.level.title} ", True, (200, 200, 200), (0, 0, 0))
        self.screen.blit(img, (3, 3))
        self.screen.blit(self.external_link, (3, 3))

    def end_level(self):
        self.screen.fill("#ECEEEA")
        self.draw_lives()
        self.screen.blit(self.level.image, ((self.screen_width - self.level.width)/2, (self.screen_height - self.level.height)/2))
        for i, block in enumerate(self.blocks):
            block.move(0, self.screen_height - (i+1)*100)
            block.draw(self.screen)
        self.draw_title()
        level_accuracy = self.font.render(f" accuracy: {round(self.accuracy/len(self.blocks),2)} ", True, (200, 200, 200), (0, 0, 0))
        level_speed = self.font.render(f" speed: {round(self.speed/len(self.blocks),2)} ", True, (200, 200, 200), (0, 0, 0))
        self.screen.blit(level_accuracy, (0, 30))
        self.screen.blit(level_speed, (0, 60))
        pygame.display.flip()
        self.mode = 'observe'

    def next_level(self):
        self.current_color = 0
        self.current_level += 1
        if self.current_level == len(self.levels):
            self.end()
        self.setup_current_level()
        self.draw()

    def next_color(self):
        self.current_color += 1
        if self.current_color == len(self.blocks):
            self.end_level()
            return
        self.draw()

    def draw(self):
        self.draw_level()
        self.draw_lives()
        # draw palette bar
        pygame.display.flip()

    def start(self):
        pygame.init()
        self.font = pygame.font.Font(None, 30)
        self.screen = pygame.display.set_mode(
            (self.screen_width, self.screen_height))
        pygame.display.set_caption('Art')
        self.clock = pygame.time.Clock()
        self.running = True
        self.setup_current_level()
        self.draw()
        self.run()

    def run(self):
        while(self.running):
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    self.end()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.running = False
                        self.end()
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if self.external_link.get_rect().collidepoint(event.pos):
                        webbrowser.open(self.level.url, new=0)
                if self.mode == 'observe':
                    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        self.mode = 'playing'
                        self.next_level()
                elif self.mode == 'playing':
                    if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                        score = maxdiff(self.blocks[self.current_color].foreground, self.background)
                        if score < 5:
                            self.accuracy += self.accuracy
                            self.speed += self.clock.get_time()
                            self.clock.tick()
                            self.next_color()
                        else:
                            self.lives -= 1
                            self.draw()
                            if self.lives == 0:
                                self.end()
                    elif event.type == pygame.MOUSEWHEEL:
                        if event.y == -1:
                            self.blocks[self.current_color].change_color(1)
                        if event.y == 1:
                            self.blocks[self.current_color].change_color(-1)
                        self.draw()

    def end(self):
        pygame.quit()
        print('Game Over')
        exit(0)


if __name__ == '__main__':
    logging.basicConfig(filename='debug.log', level=logging.DEBUG, filemode='w')
    game = Game()
    game.start()
    logging.debug('Game ended')
