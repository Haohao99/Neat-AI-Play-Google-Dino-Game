import pygame
import os
import random
import math
import sys
import neat
import pickle

pygame.init()

# Global Constants
SCREEN_HEIGHT = 600
SCREEN_WIDTH = 1100
SCREEN = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
DUCKING = [pygame.image.load(os.path.join("Assets/Dino", "DinoDuck1.png")),
           pygame.image.load(os.path.join("Assets/Dino", "DinoDuck2.png"))]
RUNNING = [pygame.image.load(os.path.join("Assets/Dino", "DinoRun1.png")),
           pygame.image.load(os.path.join("Assets/Dino", "DinoRun2.png"))]

JUMPING = pygame.image.load(os.path.join("Assets/Dino", "DinoJump.png"))

SMALL_CACTUS = [pygame.image.load(os.path.join("Assets/Cactus", "SmallCactus1.png")),
                pygame.image.load(os.path.join("Assets/Cactus", "SmallCactus2.png")),
                pygame.image.load(os.path.join("Assets/Cactus", "SmallCactus3.png"))]
LARGE_CACTUS = [pygame.image.load(os.path.join("Assets/Cactus", "LargeCactus1.png")),
                pygame.image.load(os.path.join("Assets/Cactus", "LargeCactus2.png")),
                pygame.image.load(os.path.join("Assets/Cactus", "LargeCactus3.png"))]
BIRD = [pygame.image.load(os.path.join("Assets/Bird", "Bird1.png")),
        pygame.image.load(os.path.join("Assets/Bird", "Bird2.png"))]
BG = pygame.image.load(os.path.join("Assets/Other", "Track.png"))

FONT = pygame.font.Font('freesansbold.ttf', 20)


class Dinosaur:
    X_POS = 80
    Y_POS = 310
    JUMP_VEL = 8.5
    Y_POS_DUCK = 340

    def __init__(self, img=RUNNING[0]):
        self.image = img
        self.dino_run = True
        self.dino_jump = False
        self.dino_duck = False
        self.jump_vel = self.JUMP_VEL
        self.rect = pygame.Rect(self.X_POS, self.Y_POS, img.get_width(), img.get_height())
        self.color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
        self.step_index = 0
        self.dino_recty = 340


    def update(self):
        if self.dino_duck:
            self.duck()
        if self.dino_run:
            self.run()
        if self.dino_jump:
            self.jump()
        if self.step_index >= 10:
            self.step_index = 0

    def duck(self):
        self.image = DUCKING[self.step_index // 5]
        self.rect = self.image.get_rect()
        self.rect.x = self.X_POS
        self.dino_recty = self.Y_POS_DUCK
        self.rect.y = self.Y_POS
        self.step_index += 1

    def jump(self):
        self.image = JUMPING
        if self.dino_jump:
            self.rect.y -= self.jump_vel * 4
            self.jump_vel -= 0.8
        if self.jump_vel <= -self.JUMP_VEL:
            self.dino_jump = False
            self.dino_run = True
            self.dino_duck = False
            self.jump_vel = self.JUMP_VEL

    def run(self):
        self.image = RUNNING[self.step_index // 5]
        self.rect.x = self.X_POS
        self.rect.y = self.Y_POS
        self.step_index += 1

    def draw(self, SCREEN):
        if self.dino_duck != True:
            SCREEN.blit(self.image, (self.rect.x, self.rect.y))
        else:
            SCREEN.blit(self.image, (self.rect.x, self.dino_recty))
        pygame.draw.rect(SCREEN, self.color, (self.rect.x, self.rect.y, self.rect.width, self.rect.height), 2)
        for obstacle in obstacles:
            pygame.draw.line(SCREEN, self.color, (self.rect.x + 54, self.rect.y + 12), obstacle.rect.center, 2)


class Obstacle:
    def __init__(self, image, number_of_cacti):
        self.image = image
        self.type = number_of_cacti
        self.rect = self.image[self.type].get_rect()
        self.rect.x = SCREEN_WIDTH

    def update(self):
        self.rect.x -= game_speed
        if self.rect.x < -self.rect.width:
            obstacles.pop()

    def draw(self, SCREEN):
        SCREEN.blit(self.image[self.type], self.rect)


class SmallCactus(Obstacle):
    def __init__(self, image, number_of_cacti):
        super().__init__(image, number_of_cacti)
        self.rect.y = 325


class LargeCactus(Obstacle):
    def __init__(self, image, number_of_cacti):
        super().__init__(image, number_of_cacti)
        self.rect.y = 300

class Bird(Obstacle):
    def __init__(self, image,number_of_bird):
        super().__init__(image, number_of_bird)
        self.rect.y = 250
        self.index = 0

    def draw(self, SCREEN):
        if self.index >= 9:
            self.index = 0
        SCREEN.blit(self.image[self.index//5], self.rect)
        self.index += 1


def remove(index):
    dinosaurs.pop(index)
    ge.pop(index)
    nets.pop(index)


def distance(pos_a, pos_b):
    dx = pos_a[0]-pos_b[0]
    dy = pos_a[1]-pos_b[1]
    return math.sqrt(dx**2+dy**2)


def eval_genomes(genomes, config):
    global game_speed, x_pos_bg, y_pos_bg, obstacles, dinosaurs, ge, nets, points
    clock = pygame.time.Clock()
    points = 0

    obstacles = []
    dinosaurs = []
    ge = []
    nets = []

    x_pos_bg = 0
    y_pos_bg = 380
    game_speed = 20

    for genome_id, genome in genomes:
        dinosaurs.append(Dinosaur())
        ge.append(genome)
        net = neat.nn.FeedForwardNetwork.create(genome, config)
        nets.append(net)
        genome.fitness = 0

    def score():
        global points, game_speed
        points += 1
        if points % 100 == 0:
            game_speed += 1
        text = FONT.render(f'Points:  {str(points)}', True, (0, 0, 0))
        SCREEN.blit(text, (950, 50))

    def statistics():
        global dinosaurs, game_speed, ge
        text_1 = FONT.render(f'Dinosaurs Alive:  {str(len(dinosaurs))}', True, (0, 0, 0))
        text_2 = FONT.render(f'Generation:  {pop.generation+1}', True, (0, 0, 0))
        text_3 = FONT.render(f'Game Speed:  {str(game_speed)}', True, (0, 0, 0))

        SCREEN.blit(text_1, (50, 450))
        SCREEN.blit(text_2, (50, 480))
        SCREEN.blit(text_3, (50, 510))

    def background():
        global x_pos_bg, y_pos_bg
        image_width = BG.get_width()
        SCREEN.blit(BG, (x_pos_bg, y_pos_bg))
        SCREEN.blit(BG, (image_width + x_pos_bg, y_pos_bg))
        if x_pos_bg <= -image_width:
            x_pos_bg = 0
        x_pos_bg -= game_speed

    run = True
    while run:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        SCREEN.fill((255, 255, 255))

        for dinosaur in dinosaurs:
            dinosaur.update()
            dinosaur.draw(SCREEN)

        if len(dinosaurs) == 0:
            break

        if len(obstacles) == 0:
            rand_int = random.randint(0, 2)
            if rand_int == 0:
                obstacles.append(SmallCactus(SMALL_CACTUS, random.randint(0, 2)))
            elif rand_int == 1:
                obstacles.append(LargeCactus(LARGE_CACTUS, random.randint(0, 2)))
            elif rand_int == 2:
                obstacles.append(Bird(BIRD, random.randint(0, 1)))

        for obstacle in obstacles:
            obstacle.draw(SCREEN)
            obstacle.update()
            for i, dinosaur in enumerate(dinosaurs):
                if dinosaur.rect.colliderect(obstacle.rect):
                    ge[i].fitness -= 1
                    remove(i)

        for i, dinosaur in enumerate(dinosaurs):
            output = nets[i].activate((dinosaur.rect.y,
                                       distance((dinosaur.rect.x, dinosaur.rect.y),
                                        obstacle.rect.midtop)))
            if output[0] > 0.5 and dinosaur.rect.y == dinosaur.Y_POS:
                dinosaur.dino_jump = True
                dinosaur.dino_run = False
                dinosaur.dino_duck = False
            if output[1] > 0.5 and dinosaur.rect.y == dinosaur.Y_POS:
                dinosaur.dino_jump = False
                dinosaur.dino_run = False
                dinosaur.dino_duck = True

        statistics()
        score()
        background()
        clock.tick(30)
        pygame.display.update()


# Setup the NEAT Neural Network
def run(config_path,ifFirst,num,popsize):
    global pop
    config = neat.config.Config(
        neat.DefaultGenome,
        neat.DefaultReproduction,
        neat.DefaultSpeciesSet,
        neat.DefaultStagnation,
        config_path
    )
    if ifFirst:
        pop = neat.Population(config)
        stats = neat.StatisticsReporter()
        pop.add_reporter(stats)
        pop.add_reporter(neat.Checkpointer(popsize))
        pop.run(eval_genomes, popsize)
    else:
        checkpoint_num = num*(popsize-1)
        pop = neat.Checkpointer.restore_checkpoint(f'neat-checkpoint-{checkpoint_num}')
        index = pop.generation+popsize
        stats = neat.StatisticsReporter()
        pop.add_reporter(stats)
        pop.add_reporter(neat.Checkpointer(index))
        pop.run(eval_genomes, popsize)
    stats.save()

def writefile():
    f = open("record.txt", "r+")
    f.truncate(0)
    f.write(str(int(firstline) + 1))
    f.close()
if __name__ == '__main__':
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, 'config.txt')
    for i in range(2):
        with open("record.txt") as f:
            firstline = f.readline().rstrip()
        if firstline == '0':
            print("The begin")
            run(config_path, True, 0, 50)
            writefile()
        else:
            run(config_path, False, int(firstline), 50)
            writefile()




