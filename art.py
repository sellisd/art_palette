import logging
import time
import webbrowser
from datetime import datetime
from pathlib import Path
from random import choice, randint, random, sample

import pandas as pd
from webcolors import hex_to_rgb
from yaml import SafeLoader, load

import pygame


def maxdiff(a, b):
    return(max([a-b for a, b in zip(a, b)]))


def rgb_to_greyscale(rgb):
    average = 0.299*rgb[0] + 0.587*rgb[1] + 0.114*rgb[2]
    return([average, average, average])


class Heart(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        heart = pygame.image.load('assets/heart.png')
        broken_heart = pygame.image.load('assets/broken_heart.png')
        self.heart = pygame.transform.scale(heart, (25, 25))
        self.broken_heart = pygame.transform.scale(broken_heart, (25, 25))
        self.bug_assets = {}
        self.image = self.heart
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.last_move = time.time()
        self.speed = [randint(-1, 1), randint(-1, 1)]

    def break_heart(self):
        self.image = self.broken_heart

    def heal_heart(self):
        self.image = self.heart

    def draw(self, screen):
        screen.blit(self.image, self.rect)

    def move(self, width, height):
        if time.time() - self.last_move > 0.01:
            if self.rect.x <= 0 or self.rect.x >= width - self.rect.width:
                self.speed[0] = -self.speed[0]
            if self.rect.y <= 0 or self.rect.y >= height - self.rect.height:
                self.speed[1] = -self.speed[1]
            self.rect.x += self.speed[0]
            self.rect.y += self.speed[1]
            self.last_move = time.time()

    def move_to(self, x, y):
        self.rect.x = x
        self.rect.y = y


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
        self.greyscaleflag = False

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
        if self.greyscaleflag:
            self.foreground = [i + step for i in self.foreground]
        else:
            self.foreground[self.color_axis] += step
        self.update_foreground()

    def move(self, newX, newY):
        self.rect.x = newX
        self.rect.y = newY

    def greyscale(self):
        self.foreground = rgb_to_greyscale(self.foreground)
        self.image.fill(self.foreground)
        self.greyscaleflag = True


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
        self.scrolling_direction = -1
        self.hearts = [Heart(self.screen_width - 100 + 30*i, 10)
                       for i in range(self.lives)]
        self.floating = []
        self.assets = {}
        self.message_buffer = []
        self.elements = {}
        self.stats = pd.DataFrame(
            columns=['level', 'accuracy', 'speed', 'level_order'])

    def load_assets(self):
        blue_screen = pygame.image.load('assets/Windows_NT_3.51_BSOD_ita.png')
        self.assets['blue_screen'] = pygame.transform.scale(
            blue_screen, (self.screen_width, self.screen_height))
        self.assets['noise'] = []
        for i in range(1, 61):
            noise_image = pygame.image.load(
                f"assets/noise/noise000{str(i).zfill(2)}.png")
            self.assets['noise'].append(pygame.transform.scale(
                noise_image, (self.screen_width, self.screen_height)))
        external_link = pygame.image.load('assets/external_link.png')
        self.assets['external_link'] = pygame.transform.scale(
            external_link, (20, 20))

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
            foreground[color_axis] = background[color_axis] + \
                20 * choice([-1, 1])
            self.blocks.append(Block(foreground, 100, 100,
                                     (self.screen_width-100)/2,
                                     (self.screen_height-100)/2, color_axis))

    def draw_lives(self):
        logging.debug('drawing lives')
        for heart in self.hearts:
            heart.draw(self.screen)
        if self.floating:
            for floating_heart in self.floating:
                floating_heart.draw(self.screen)

    def draw_level(self):
        logging.debug('Drawing level')
        self.background = list(self.level.colors[self.current_color])
        self.screen.fill(self.background)
        self.blocks[self.current_color].draw(self.screen)
        self.draw_title()

    def draw_title(self):
        logging.debug('Drawing title')
        self.elements['title'] = self.font.render(
            f"    {self.level.title} ", True, (200, 200, 200), (0, 0, 0))
        self.screen.blit(self.elements['title'], (5, 5))
        self.screen.blit(self.assets['external_link'], (5, 5))

    def end_level(self):
        logging.debug('End of level')
        self.screen.fill("#ECEEEA")
        self.screen.blit(self.level.image,
                         ((self.screen_width - self.level.width)/2,
                          (self.screen_height - self.level.height)/2))
        for i, block in enumerate(self.blocks):
            block.move(0, self.screen_height - (i+1)*100)
            block.draw(self.screen)
        self.draw_lives()
        self.draw_title()
        accuracy = round(self.accuracy/len(self.blocks), 2)
        self.accuracy = 0
        speed = round(self.speed/len(self.blocks), 2)
        self.stats = self.stats.append({'level': self.current_level,
                                        'accuracy': accuracy,
                                        'speed': speed,
                                        'level_order': self.current_level}, ignore_index=True)
        level_accuracy = self.font.render(
            f" accuracy: {accuracy} ", True, (200, 200, 200), (0, 0, 0))
        level_speed = self.font.render(
            f" speed: {speed} ", True, (200, 200, 200), (0, 0, 0))
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
        self.screen.blit(game_over, game_over.get_rect(
            center=(self.screen_width/2, self.screen_height/2)))
        pygame.display.flip()
        self.wait_for_click()
        self.end()

    def next_level(self):
        logging.debug('Next level')
        self.last_bug = time.time()
        self.current_color = 0
        self.current_level += 1
        self.message_buffer = []
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

    def draw_messagebox(self):
        logging.debug('Drawing messagebox')
        for i, message in enumerate(self.message_buffer[-3:]):
            line = self.monofont.render(
                message, True, (200, 200, 200), (0, 0, 0))
            self.screen.blit(line, line.get_rect(
                topleft=(30, self.screen_height - 100 + i*20)))
        pygame.display.flip()

    def draw(self):
        logging.debug('Drawing')
        self.draw_level()
        self.draw_lives()
        self.draw_messagebox()
        pygame.display.flip()

    def setup_game(self):
        logging.debug('Setting up game')
        pygame.init()
        self.font = pygame.font.Font(None, 30)
        self.monofont = pygame.font.SysFont('monospace', 20)
        self.screen = pygame.display.set_mode(
            (self.screen_width, self.screen_height))
        pygame.display.set_caption('Art')
        self.running = True
        usage_list = [
            'COLOR MATCHING ART GAME beta',
            '',
            '',
            'Instructions:',
            '',
            'Scroll to change the color of the central square',
            'Make it match the background color',
            'Click to advance to the next color',
            'After matching all colors in a palette the level ends',
            'and the artwork is revealed.',
            'During the game click on the link in the top left corner to get more information on the art.',
            '',
            'Warning: A number of bugs might make winning the game difficult.'
        ]
        for i, text in enumerate(usage_list):
            line = self.font.render(text, True, (200, 200, 200))
            self.screen.blit(line, line.get_rect(
                center=(self.screen_width/2, 50 + i * 40)))
        pygame.display.flip()
        self.load_assets()
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
                if self.advance(event):
                    waiting = False

    def check_quit(self, event):
        if event.type == pygame.QUIT:
            return True
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return True
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if (self.assets['external_link'].get_rect().collidepoint(event.pos) or
                    ('title' in self.elements and self.elements['title'].get_rect().collidepoint(event.pos))):
                webbrowser.open(self.level.url, new=0)
        return False

    def bug(self):
        logging.debug('Bug')
        # flash noise
        bug_screen = randint(0, 1)
        back = self.screen.copy()
        if bug_screen == 0:
            self.screen.blit(self.assets['blue_screen'], (0, 0))
            pygame.display.flip()
            time.sleep(0.5)
        elif bug_screen == 1:
            r = randint(0, 50)
            for i in range(r, r+10):
                logging.debug(i)
                self.screen.blit(self.assets['noise'][i], (0, 0))
                pygame.display.flip()
                self.clock.tick(20)
        # back to normal
        self.screen.blit(back, (0, 0))
        bug_type = randint(0, 3)
        if bug_type == 0:
            # jump color
            message = "Overflow in srgb random shift of color."
            self.blocks[self.current_color].change_color(choice((-1, 1)) * 100)
        elif bug_type == 1:  # grey scale
            message = "Ink is running low."
            self.blocks[self.current_color].greyscale()
            self.level.colors[self.current_color] = rgb_to_greyscale(
                self.level.colors[self.current_color])
        elif bug_type == 2:
            # - invert direction
            message = "I/O error controls inverted"
            self.scrolling_direction = -self.scrolling_direction
        elif bug_type == 3:  # heart attack
            message = "Kernel panic, heart attack. Hover over heart to heal."
            if self.hearts:
                self.floating.append(self.hearts.pop())
                self.floating[-1].break_heart()
                self.lives -= 1
            else:
                self.game_over(False)
            self.draw_lives()
        time_string = datetime.now().strftime('%b %d %H:%M:%S')
        self.message_buffer.append(f"{time_string} root - 0.0 {message}")
        self.draw()

    def run(self):
        logging.debug('Run game')
        bug_activated = False         # no bugs during in first level
        while(self.running):
            if self.floating:
                for floating_heart in self.floating:
                    floating_heart.move(
                        self.screen_width, self.screen_height)
                self.draw()
            if self.current_level > 0:
                if bug_activated:
                    if time.time() > r:
                        bug_activated = False
                        self.bug()
                else:
                    # pick when to activate bug
                    r = random() * 10 + time.time()
                    bug_activated = True
            for event in pygame.event.get():
                if self.check_quit(event):
                    self.running = False
                    self.end()
                if self.advance(event):
                    score = maxdiff(self.blocks[self.current_color].foreground,
                                    self.background)
                    if score < self.parameters['threshold']:
                        self.accuracy += score
                        self.speed += self.clock.get_time()
                        self.clock.tick()
                        self.next_color()
                    else:
                        self.lives -= 1
                        if self.lives == 0:
                            self.game_over(False)
                        self.hearts.pop()
                        self.draw()
                elif event.type == pygame.MOUSEWHEEL:
                    if event.y == self.scrolling_direction * -1:
                        self.blocks[self.current_color].change_color(1)
                    if event.y == self.scrolling_direction * 1:
                        self.blocks[self.current_color].change_color(-1)
                    self.draw()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_UP:
                        self.blocks[self.current_color].change_color(self.scrolling_direction)
                    if event.key == pygame.K_DOWN:
                        self.blocks[self.current_color].change_color(self.scrolling_direction * -1)
                    self.draw()
                elif event.type == pygame.MOUSEMOTION:
                    for floating_heart in self.floating:
                        if floating_heart.rect.collidepoint(event.pos):
                            self.hearts.append(floating_heart)
                            self.hearts[-1].move_to(self.screen_width -
                                                    100 + 30 * (self.lives-1), 10)
                            self.hearts[-1].heal_heart()
                            self.lives += 1
                            self.floating.remove(floating_heart)
                            self.draw()
                            break

    def advance(self, event):
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            return True
        if event.type == pygame.KEYDOWN:
            if event.key in [pygame.K_SPACE, pygame.K_RETURN]:
                return True
        return False

    def end(self):
        self.stats.to_csv("highscore.csv", index=False)
        pygame.quit()
        print('Game Over')
        exit(0)


if __name__ == '__main__':
    logging.basicConfig(filename='debug.log',
                        level=logging.DEBUG, filemode='w')
    parameters = {'lives': 3, 'threshold': 10}
    game = Game(parameters)
    game.setup_game()
    game.run()
    logging.debug('Game ended')
