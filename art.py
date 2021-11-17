import logging
import webbrowser
from pathlib import Path
from random import choice, randint, sample

from webcolors import hex_to_rgb
from yaml import SafeLoader, load

import pygame


def maxdiff(a, b):
    return(max([a-b for a, b in zip(a, b)]))


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
    def __init__(self, parameters):
        self.parameters = parameters
        self.levels = []
        self.current_level = 0
        self.load_levels()
        self.lives = self.parameters['lives']
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

    def load_levels(self):
        logging.debug('Loading levels')
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
        logging.debug('drawing lives')
        for i in range(self.lives):
            img_rect = self.heart.get_rect()
            img_rect.x = self.screen_width - 100 + 30*i
            img_rect.y = 10
            self.screen.blit(self.heart, img_rect)

    def draw_level(self):
        logging.debug('Drawing level')
        self.background = list(self.level.colors[self.current_color])
        self.screen.fill(self.background)
        self.blocks[self.current_color].draw(self.screen)
        self.draw_title()

    def draw_title(self):
        logging.debug('Drawing title')
        img = self.font.render(f"    {self.level.title} ", True, (200, 200, 200), (0, 0, 0))
        self.screen.blit(img, (3, 3))
        self.screen.blit(self.external_link, (3, 3))

    def end_level(self):
        logging.debug('End of level')
        self.screen.fill("#ECEEEA")
        self.screen.blit(self.level.image, ((self.screen_width - self.level.width)/2, (self.screen_height - self.level.height)/2))
        for i, block in enumerate(self.blocks):
            block.move(0, self.screen_height - (i+1)*100)
            block.draw(self.screen)
        self.draw_lives()
        self.draw_title()
        level_accuracy = self.font.render(f" accuracy: {round(self.accuracy/len(self.blocks),2)} ", True, (200, 200, 200), (0, 0, 0))
        level_speed = self.font.render(f" speed: {round(self.speed/len(self.blocks),2)} ", True, (200, 200, 200), (0, 0, 0))
        self.screen.blit(level_accuracy, (0, 30))
        self.screen.blit(level_speed, (0, 60))
        pygame.display.flip()
        self.wait_for_click()
        self.next_level()

    def game_over(self, win):
        logging.debug('Game over')
        self.screen.fill((0, 0, 0))
        if win:
            game_over = self.font.render("You Win !!!", True, (200, 250, 200))
        else:
            game_over = self.font.render("Game Over", True, (250, 200, 200))
        self.screen.blit(game_over, game_over.get_rect(center=(self.screen_width/2, self.screen_height/2)))
        pygame.display.flip()
        self.wait_for_click()
        self.end()

    def next_level(self):
        logging.debug('Next level')
        self.current_color = 0
        self.current_level += 1
        if self.current_level == len(self.levels):
            self.game_over(True)
            return
        self.setup_current_level()
        self.draw()

    def next_color(self):
        logging.debug('Next color')
        self.current_color += 1
        if self.current_color == len(self.blocks):
            self.end_level()
            return
        self.draw()

    def draw(self):
        logging.debug('Drawing')
        self.draw_level()
        self.draw_lives()
        pygame.display.flip()

    def setup_game(self):
        logging.debug('Setting up game')
        pygame.init()
        self.font = pygame.font.Font(None, 30)
        self.screen = pygame.display.set_mode(
            (self.screen_width, self.screen_height))
        pygame.display.set_caption('Art')
        self.running = True
        usage_list = [
          'COLOR MATCHING ART GAME',
          '',
          '',
          'Instructions:',
          '',
          'Scroll to change the color of the central square',
          'Make it match the background color',
          'Click to advance to the next color',
          'After matching all colors in a palette the level ends', 
          'and the artwork is revealed.',
          'During the game click on the link in the top left corner to get more information on the art.'
        ]
        for i, text in enumerate(usage_list):
            line = self.font.render(text, True, (200, 200, 200))
            self.screen.blit(line, line.get_rect(center=(self.screen_width/2, 50 + i * 40)))
        pygame.display.flip()
        self.clock = pygame.time.Clock()
        self.wait_for_click()
        self.setup_current_level()
        self.draw()

    def wait_for_click(self):
        waiting = True
        while(waiting):
            for event in pygame.event.get():
                if self.check_quit(event):
                    self.end()
                if event.type == pygame.MOUSEBUTTONUP:
                    waiting = False

    def check_quit(self, event):
        if event.type == pygame.QUIT:
            return True
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return True
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.external_link.get_rect().collidepoint(event.pos):
                webbrowser.open(self.level.url, new=0)
        return False

    def run(self):
        logging.debug('Run game')
        while(self.running):
            for event in pygame.event.get():
                if self.check_quit(event):
                    self.running = False
                    self.end()
                if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                    score = maxdiff(self.blocks[self.current_color].foreground, self.background)
                    if score < self.parameters['threshold']:
                        self.accuracy += score
                        self.speed += self.clock.get_time()
                        self.clock.tick()
                        self.next_color()
                    else:
                        self.lives -= 1
                        self.draw()
                        if self.lives == 0:
                            self.game_over(False)
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
    parameters = {'lives': 3, 'threshold': 5}
    game = Game(parameters)
    game.setup_game()
    game.run()
    logging.debug('Game ended')
