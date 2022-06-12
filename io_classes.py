import pygame
import rules as r
import math as m
import random

class IoHandler:

    def __init__(self):
        pygame.init()
        self.width = 1366
        self.height = 768
        self.window = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Azul")
        self.objects = []
        self.background = pygame.Surface(self.window.get_size())
        self.font = pygame.font.get_default_font()
        self.playerCount = 0
        self.buffer = 10
        self.tile_size = 40
        self.grid_size = 32
        self.pattern_width_tiles = max(r.rules["patternSizes"])
        self.board_width_tiles = min(r.rules["boardSize"], len(r.rules["colors"]))
        #self.board_width = (self.pattern_width_tiles + self.board_width_tiles) * (self.tile_size + self.buffer) + self.buffer
        self.board_width = (self.pattern_width_tiles + self.board_width_tiles + 1) * self.grid_size
        if r.rules["floorSize"] is None:
            self.floor_size = len(r.rules["floor"]) + 1
        else:
            self.floor_size = r.rules["floorSize"]
        self.floor_width_tiles = min(self.floor_size, self.pattern_width_tiles + self.board_width_tiles)
        if self.floor_size > self.floor_width_tiles:
            self.floor_height_tiles = self.floor_size // self.floor_width_tiles + 1
        else:
            self.floor_height_tiles = 1
        self.text_space_height = 32
        #self.board_height = (self.board_width_tiles + self.floor_height_tiles) * (self.tile_size + self.buffer) + self.buffer + self.text_space_height
        self.board_height = (self.board_width_tiles + self.floor_height_tiles + 2) * self.grid_size
        self.board_x = [self.buffer, self.width - self.buffer - self.board_width, self.width - self.buffer - self.board_width, self.buffer]
        self.board_y = [self.buffer, self.buffer, self.height - self.buffer - self.board_height, self.height - self.buffer - self.board_height]
        self.factory_size = self.tile_size * 2
        self.factory_angle = random.random() * 2 * m.pi
        self.factory_r = (self.width - self.board_width * 2 - self.buffer * 4 - self.factory_size * 2) / 2
        self.center_size = (self.width - self.board_width * 2 - self.buffer * 6 - self.factory_size * 4) / 2
        self.factory_count = r.rules["factories"]
        self.jiggle = 5
        self.tile_colors = {"blue": (0, 0, 255),
                            "yellow": (255, 255, 0),
                            "red": (255, 0, 0),
                            "black": (0, 0, 0),
                            "teal": (0, 255, 255),
                            "green": (0, 255, 0),
                            "1st": (255, 255, 255)}
        self.tiles = pygame.sprite.Group()
        self.tiles_possible = pygame.sprite.Group()
        self.tiles_selected = pygame.sprite.Group()
        self.boards = -1
        self.factories = -1
        self.clock = pygame.time.Clock()
        self.fps = 30
        self.tile_speed = 500 / self.fps
        self.pointer = pygame.sprite.GroupSingle()
        self.board_ios = []
        self.patterns = pygame.sprite.Group()
        self.active_player = pygame.sprite.GroupSingle()
        self.active_patterns = pygame.sprite.Group()
        self.floors = pygame.sprite.Group()
        self.font = pygame.font.Font(None, 30)
        self.floor_font = pygame.font.Font(None, 20)
        self.sprite_sheet = pygame.image.load("sprites.png")

    def Create(self, related_object, i=None):
        if related_object.type == "board":
            self.boards += 1
            return BoardIO(self, related_object, self.boards)
        elif related_object.type == "pattern":
            return PatternIO(self, related_object, i)
        elif related_object.type == "row":
            return RowIO(self, related_object, i)
        elif related_object.type == "floor":
            return FloorIO(self, related_object)
        elif related_object.type == "factory":
            self.factories += 1
            return FactoryIO(self, related_object, self.factories)
        elif related_object.type == "center":
            return CenterIO(self, related_object)
        elif related_object.type == "tile":
            return TileIO(self, related_object)
        elif related_object.type == "bag":
            return TileBagIO(self, related_object)
        elif related_object.type == "discard":
            return TileBagIO(self, related_object)
        elif related_object.type == "player":
            return PlayerIO(self, related_object, i)
        elif related_object.type == "game":
            return GameIO(self, related_object)

    def CheckEvents(self, state):
        event = [None]
        events = pygame.event.get()
        for pygame_event in events:
            if pygame_event.type == pygame.QUIT:
                event[0] = "QUIT"
                break
        if state == "playing":
            for pygame_event in events:
                if pygame_event is not None:
                    if pygame_event.type == pygame.MOUSEBUTTONUP:
                        pos = pygame.mouse.get_pos()
                        pointer = Pointer(self.pointer, pos)
                        tile_collision = pygame.sprite.spritecollide(pointer, self.tiles, False)
                        pattern_collision = pygame.sprite.spritecollide(pointer, self.active_patterns, False)
                        if len(tile_collision) > 0:
                            event[0] = "select"
                            selected_tile = tile_collision[0]
                            event.append(selected_tile.related_object)
                        elif len(pattern_collision) > 0:
                            event[0] = "place"
                            selected_pattern = pattern_collision[0]
                            event.append(selected_pattern.related_object)
                        else:
                            event[0] = "unselect"
        return event

    def get_sprite(self, sprite):
        rect = pygame.Rect(0, 0, 32, 32)
        if sprite == "black":
            rect = pygame.Rect(0,0,32,32)
        elif sprite == "yellow":
            rect = pygame.Rect(32,0,32,32)
        elif sprite == "teal":
            rect = pygame.Rect(64,0,32,32)
        elif sprite == "red":
            rect = pygame.Rect(128 ,0 ,32 ,32)
        elif sprite == "blue":
            rect = pygame.Rect(96, 0, 32, 32)
        elif sprite == "board":
            rect = pygame.Rect(32, 32, 32, 32)
        elif sprite == "blank":
            rect = pygame.Rect(0, 32, 32, 32)
        elif sprite == "1st":
            rect = pygame.Rect(64, 32, 32, 32)
        elif sprite == "arrow":
            rect = pygame.Rect(96, 32, 32, 32)
        elif sprite == "penalty":
            rect = pygame.Rect(128, 32, 32, 32)
        elif sprite == "marker":
            rect = pygame.Rect(0, 64, 32, 32)
        image = pygame.Surface(rect.size).convert()
        image.set_colorkey((0, 255, 0))
        image.blit(self.sprite_sheet, (0, 0), rect)
        return image

    def SetupGame(self):
        self.playerCount = len(r.rules["players"])

    def AddToDisplay(self, thing):
        # io_object =
        self.objects.append(thing)
        return len(self.objects)

    def RemoveFromDisplay(self, i):
        self.objects[i] = None

    def Display(self):
        self.clock.tick(self.fps)
        self.window.blit(self.background, (0, 0))
        self.active_player.draw(self.window)
        for board in self.board_ios:
            board.patterns.draw(self.window)
        # self.patterns.draw(self.window)
        self.tiles.draw(self.window)
        self.tiles_selected.draw(self.window)
        pygame.display.flip()


class GameIO:

    def __init__(self, io_handler, related_object):
        self.io_handler = io_handler
        self.related_object = related_object
        self. x = self.io_handler.width / 2
        self. y = self.io_handler.buffer
        self.display_text = self.related_object.display_text
        self.text = None
        self.display()

    def update(self):
        self.display_text = self.related_object.display_text
        self.display()

    def display(self):
        self.text = self.io_handler.font.render(self.display_text, True, (255, 255, 255), (0, 0, 0))
        self.io_handler.background.blit(self.text, (self.x - self.text.get_rect().width / 2, self.y))


class PlayerIO:

    def __init__(self, io_handler, related_object, i):
        self.io_handler = io_handler
        self.related_object = related_object
        self.number = i
        self.x = self.io_handler.board_x[self.number]
        self.y = self.io_handler.board_y[self.number]
        self.width = self.io_handler.board_width
        self.height = self.io_handler.board_height
        self.rect = (self.x, self.y, self.width, self.height)
        self.active = False

    def update(self):
        if self.related_object.active is True:
            outline = PlayerMarker(self)


class TileContainerIO:

    def __init__(self, io_handler, related_object, i=None):
        self.io_handler = io_handler
        self.related_object = related_object
        self.size = self.related_object.max_size
        self.positions_assigned = []
        self.buffer = self.io_handler.buffer
        self.tile_size = self.io_handler.tile_size
        self.x = 0
        self.y = 0
        if self.size is not None:
            for i in range(self.size):
                self.positions_assigned.append(False)
        else:
            self.positions_assigned.append(False)

    def position(self, n):
        return self.x, self.y


class TileBagIO(TileContainerIO):

    def __init__(self, io_handler, related_object):
        super(TileBagIO, self).__init__(io_handler=io_handler, related_object=related_object)
        self.type = "tile bag"
        self.x = -self.tile_size
        self.y = -self.tile_size


class BoardIO(TileContainerIO):

    def __init__(self, io_handler, related_object, i):
        super(BoardIO, self).__init__(io_handler=io_handler, related_object=related_object)
        self.io_handler.playerCount += 1
        self.number = i
        self.type = "board"
        self.text_height = self.io_handler.text_space_height
        self.x = self.io_handler.board_x[self.number]
        self.y = self.io_handler.board_y[self.number]
        self.width = self.io_handler.board_width
        self.height = self.io_handler.board_height
        self.rect = (self.x, self.y, self.width, self.height)
        self.patterns = pygame.sprite.Group()
        self.io_handler.board_ios.append(self)
        self.player = self.related_object.player.name
        self.score = None
        self.display_text = None
        self.text = None
        for x in range(self.io_handler.board_width_tiles + self.io_handler.pattern_width_tiles + 1):
            for y in range(self.io_handler.board_width_tiles + self.io_handler.floor_height_tiles * 2 + 1):
                image = self.io_handler.get_sprite("blank")
                self.io_handler.background.blit(image,
                    (self.x + self.io_handler.grid_size * x,
                     self.y + self.io_handler.grid_size * y,
                     self.io_handler.grid_size,
                     self.io_handler.grid_size))
        image = self.io_handler.get_sprite("arrow")
        for i in range(self.io_handler.board_width_tiles):
            self. io_handler.background.blit(image,
                (self.x + self.io_handler.grid_size * self.io_handler.pattern_width_tiles,
                 self.y + self.io_handler.grid_size * (i + 1),
                 self.io_handler.grid_size,
                 self.io_handler.grid_size))
        self.display()

    def update(self):
        if self.related_object.player.active:
            self.io_handler.active_patterns = self.patterns.copy()
        self.display()

    def display(self):
        self.score = str(self.related_object.player.score)
        self.display_text = self.player + " | Score: " + self.score
        self.text = self.io_handler.font.render(self.display_text, True, (0, 0, 255), (237, 231, 125))
        self.io_handler.background.blit(self.text, (self.x + (self.width - self.text.get_rect().width) / 2, self.y + (self.io_handler.grid_size - self.text.get_height()) / 2))


class PatternIO(pygame.sprite.Sprite):

    def __init__(self, io_handler, related_object, i):
        pygame.sprite.Sprite.__init__(self, related_object.board.io.patterns, io_handler.patterns)
        self.io_handler = io_handler
        self.related_object = related_object
        self.number = i
        self.buffer = self.io_handler.buffer
        self.tile_size = self.io_handler.tile_size
        self.size = self.related_object.max_size
        self.positions_assigned = []
        for i in range(self.size):
            self.positions_assigned.append(False)
        self.pattern_width_tiles = self.io_handler.pattern_width_tiles
        self.type = "pattern"
        self.board = related_object.board.io
        self.x = self.board.x
        self.y = self.board.y + self.io_handler.grid_size * (self.number + 1)
        self.width = self.pattern_width_tiles * self.io_handler.grid_size
        self.height = self.io_handler.grid_size
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)
        self.color_rgb = (255, 255, 255)
        self.image = pygame.Surface([self.width, self.height])
        #pygame.draw.rect(self.image, self.color_rgb, (0, 0, self.width, self.height), 2)
        # blitting the blank tiles should be eliminated once this sprites background can be made transparent
        for i in range(self.io_handler.pattern_width_tiles):
            image = self.io_handler.get_sprite("blank")
            self.image.blit(image, (i * self.io_handler.grid_size, 0, self.io_handler.grid_size, self.io_handler.grid_size))
        n = self.io_handler.pattern_width_tiles - self.related_object.max_size
        image = self.io_handler.get_sprite("board")
        self.image.set_colorkey((0, 255, 0))
        for i in range(self.related_object.max_size):
            self.image.blit(image, (n * self.io_handler.grid_size, 0, self.io_handler.grid_size, self.io_handler.grid_size))
            n += 1
            #color = (255, 255, 255)
            #tile_space = (self.width - self.buffer / 2 - self.tile_size * (i + 1) - self.buffer * i,
            #              self.buffer / 2,
            #              self.tile_size,
            #              self.tile_size)
            #pygame.draw.rect(self.image, color, tile_space, 2)


    def position(self, n):
        x = self.width - self.io_handler.grid_size / 2 - self.io_handler.grid_size * (self.size - 1 - n)
        y = self.io_handler.grid_size / 2
        return x, y


class RowIO(TileContainerIO):

    def __init__(self, io_handler, related_object, i):
        super(RowIO, self).__init__(io_handler=io_handler, related_object=related_object)
        self.number = i
        self.buffer = self.io_handler.buffer
        self.tile_size = self.io_handler.tile_size
        self.pattern_width_tiles = self.io_handler.pattern_width_tiles
        self.board_width = self.io_handler.board_width_tiles
        self.type = "row"
        self.board = related_object.board.io
        self.x = self.board.x + (self.pattern_width_tiles + 1) * self.io_handler.grid_size
        self.y = self.board.y + self.io_handler.grid_size * (self.number + 1)
        self.width = self.board_width * self.io_handler.grid_size
        self.height = self.io_handler.grid_size
        # self.rect = (self.x, self.y, self.width, self.height)
        self.image = pygame.Surface([self.width, self.height])
        # pygame.draw.rect(self.io_handler.background, (255, 255, 255), self.rect, 2)
        blank = self.io_handler.get_sprite("blank")
        space = self.io_handler.get_sprite("board")
        for i in range(self.related_object.max_size):
            tile = self.io_handler.get_sprite(self.related_object.possible_colors[i])
            tile.set_alpha(64)
            rect = pygame.Rect(i * self.io_handler.grid_size, 0, self.io_handler.grid_size, self.io_handler.grid_size)
            self.image.blit(blank, rect)
            self.image.blit(space, rect)
            self.image.blit(tile, rect)
        self.io_handler.background.blit(self.image, (self.x, self.y, self.width, self.height))
        '''if not self.related_object.possible_colors[i] == "black":
                color = io_handler.tile_colors[self.related_object.possible_colors[i]]
            else:
               color = (255, 255, 255)
            tile_space = (self.x + self.buffer / 2 + i * (self.tile_size + self.buffer),
                          self.y + self.buffer / 2,
                          self.tile_size,
                          self.tile_size)
            pygame.draw.rect(self.io_handler.background, color, tile_space, 2)'''

    def position(self, position):
        x = self.io_handler.grid_size * position + self.io_handler.grid_size / 2
        y = self.io_handler.grid_size / 2
        return x, y


'''class FloorIO(TileContainerIO):

    def __init__(self, io_handler, related_object):
        super(FloorIO, self).__init__(io_handler=io_handler, related_object=related_object)'''


class FloorIO(pygame.sprite.Sprite):

    def __init__(self, io_handler, related_object):
        pygame.sprite.Sprite.__init__(self, related_object.board.io.patterns, io_handler.floors)
        self.io_handler = io_handler
        self.related_object = related_object
        self.buffer = self.io_handler.buffer
        self.tile_size = self.io_handler.tile_size
        self.size = self.io_handler.floor_size
        self.width_tiles = self.io_handler.floor_width_tiles
        self.height_tiles = self.io_handler.floor_height_tiles
        self.board_width_tiles = self.io_handler.board_width_tiles
        self.type = "floor"
        self.board = related_object.board.io
        self.x = self.board.x
        self.y = self.board.y + (self.board_width_tiles + 1) * self.io_handler.grid_size
        self.height = self.io_handler.grid_size * self.height_tiles * 2
        self.width = self.width_tiles * self.io_handler.grid_size
        self.rect = (self.x, self.y, self.width, self.height)
        self.image = pygame.Surface([self.width, self.height])
        #self.color_rgb = (255, 255, 255)
        #pygame.draw.rect(self.image, self.color_rgb, (0, 0, self.width, self.height), 2)
        space = self.io_handler.get_sprite("board")
        header = self.io_handler.get_sprite("penalty")
        for i in range(self.size):
            blank = self.io_handler.get_sprite("blank")
            color = (255, 255, 255)
            x = i % self.width_tiles
            y = i // self.width_tiles
            '''tile_space = (self.buffer / 2 + x * (self.tile_size + self.buffer),
                          self.buffer / 2 + y * (self.tile_size + self.buffer),
                          self.tile_size,
                          self.tile_size)'''
            number = self.io_handler.floor_font.render(str(self.related_object.penalties[i]), True, (0, 0, 255), (237,231, 125))
            rectHeader = pygame.Rect(x * self.io_handler.grid_size,
                y * self.io_handler.grid_size,
                self.io_handler.grid_size,
                self.io_handler.grid_size)
            rectSpace = pygame.Rect(x * self.io_handler.grid_size,
                (y + 1) * self.io_handler.grid_size,
                self.io_handler.grid_size,
                self.io_handler.grid_size)
            self.image.blit(blank, rectHeader)
            self.image.blit(header, rectHeader)
            text_width = number.get_width()
            text_height = number.get_height()
            self.image.blit(number, (x * self.io_handler.grid_size + (self.io_handler.grid_size - text_width) / 2,
                                     y * self.io_handler.grid_size + (self.io_handler.grid_size - text_height) / 2,
                                    text_width,
                                    text_height))
            self.image.blit(blank, rectSpace)
            self.image.blit(space, rectSpace)
            # self.image.blit(image, (x * self.io_handler.grid_size, y * self.io_handler.grid_size, self.io_handler.grid_size, self.io_handler.grid_size))
            # pygame.draw.rect(self.image, color, tile_space, 2)

    def position(self, n):
        x = self.io_handler.grid_size / 2 + self.io_handler.grid_size * (n % self.width_tiles)
        y = self.io_handler.grid_size / 2 + self.io_handler.grid_size * (n // self.width_tiles + 1)
        return x, y


class FactoryIO(TileContainerIO):

    def __init__(self, io_handler, related_object, i):
        super(FactoryIO, self).__init__(io_handler=io_handler, related_object=related_object)
        self.buffer = self.io_handler.buffer
        self.tile_size = self.io_handler.tile_size
        self.r = self.io_handler.factory_r
        self.tile_r = self.tile_size * .9
        self.type = "factory"
        self.factory_count = self.io_handler.factory_count[self.io_handler.playerCount - 2]
        self.number = i
        self.size = self.io_handler.factory_size
        self.angle = self.io_handler.factory_angle
        x, y = polar_to_cart(self.r, self.angle, self.number, self.factory_count)
        self.x = x + self.io_handler.width / 2
        self.y = y + self.io_handler.height / 2
        # self.angle = (2 * m.pi / self.factory_count) * self.number
        # self.x = self.r * m.cos(self.angle) + self.io_handler.width / 2
        # self.y = self.r * m.sin(self.angle) + self.io_handler.height / 2
        # self.x = self.io_handler.factory_x[self.number]
        # self.y = self.io_handler.factory_y[self.n7umber]
        pygame.draw.circle(self.io_handler.background, (255, 255, 255), (self.x, self.y), self.size, 2)
        self.tiles = 0

    def position(self, i):
        n = len(self.related_object.tiles)
        return polar_to_cart(self.tile_r, 2 * m.pi / 8, i, n)


class CenterIO(TileContainerIO):
    def __init__(self, io_handler, related_object):
        super(CenterIO, self).__init__(io_handler=io_handler, related_object=related_object)
        self.buffer = self.io_handler.buffer
        self.tile_size = self.io_handler.tile_size
        self.type = "center"
        self.r = self.io_handler.center_size
        self.x = self.io_handler.width/2
        self.y = self.io_handler.height/2
        # pygame.draw.circle(self.io_handler.background, (255, 255, 255), (self.x, self.y), self.r, 2)

    def position(self, position):
        return polar_to_cart(random.random() * self.r, random.random() * 2 * m.pi)


class TileIO(pygame.sprite.Sprite):

    def __init__(self, io_handler, related_object):
        pygame.sprite.Sprite.__init__(self, io_handler.tiles)
        self.io_handler = io_handler
        self.related_object = related_object
        self.color = self.related_object.color
        self.color_rgb = self.io_handler.tile_colors[self.color]
        self.height = self.io_handler.tile_size
        self.width = self.io_handler.tile_size
        #self.image = pygame.Surface([self.width, self.height])
        #self.image.fill(self.color_rgb)
        self.image = self.io_handler.get_sprite(self.color)
        self.io_container = self.related_object.container.io
        self.position = self.related_object.position
        self.x, self.y = self.io_container.position(self.position)
        self.x_target, self.y_target = self.x, self.y
        self.rect = self.image.get_rect(center=(self.x, self.y))
        self.speed = self.io_handler.tile_speed


    def update(self):
        self.position = self.related_object.position
        if self.io_container != self.related_object.container.io:
            self.io_container = self.related_object.container.io
            self.x_target, self.y_target = self.io_container.position(self.position)
            self.x_target += self.io_container.x
            self.y_target += self.io_container.y
            self.x, self.y = self.x_target, self.y_target
            self.rect = self.image.get_rect(center=(self.x, self.y))

    def toggleSelected(self):
        if self.related_object.selected:
            outline = TileOutline(self)
        else:
            for outline in self.io_handler.tiles_selected:
                if outline.tile == self:
                    outline.kill()

    def move(self):
        if self.x < self.x_target:
            self.x += self.speed
        elif self.x > self.x_target:
            self.x -= self.speed
        if self.y < self.y_target:
            self.y += self.speed
        elif self.y > self.y_target:
            self.y -= self.speed
        self.rect = self.image.get_rect(center=(self.x, self.y))


class TileOutline(pygame.sprite.Sprite):

    def __init__(self, tile):
        pygame.sprite.Sprite.__init__(self, tile.io_handler.tiles_selected)
        self.tile = tile
        self.offset = 0
        self.x, self.y, self.width, self.height = self.tile.x, self.tile.y, self.tile.width, self.tile.height
        self.image = pygame.Surface([self.width, self.height])
        rect = pygame.Rect(self.offset, self.offset, self.width - self.offset * 2, self.height - self.offset * 2)
        self.image.fill((0, 0, 0))
        self.image.set_colorkey((0, 0, 0))
        pygame.draw.rect(self.image, (255, 255, 255), rect, 5)
        self.rect = self.image.get_rect(center=(self.x, self.y))


class PlayerMarker(pygame.sprite.Sprite):

    def __init__(self, player):
        pygame.sprite.Sprite.__init__(self, player.io_handler.active_player)
        self.player = player
        self.x = self.player.x
        self.y = self.player.y
        self.width = self.player.width
        self.height = self.player.height
        self.image = pygame.Surface((self.width, self.height))
        '''self.image.fill((0, 0, 0))
        self.image.set_colorkey((0, 0, 0))
        color = (255, 0, 0)
        pygame.draw.rect(self.image, color, (0, 0, self.width, self.height), 2)'''
        self.image = self.player.io_handler.get_sprite("marker")
        self.rect = pygame.Rect(self.x, self.y, self.player.io_handler.grid_size, self.player.io_handler.grid_size)


class Pointer(pygame.sprite.Sprite):

    def __init__(self, pointer_group, pos):
        pygame.sprite.Sprite.__init__(self, pointer_group)
        self.x = pos[0]
        self.y = pos[1]
        self.width = 1
        self.height = 1
        self.image = pygame.Surface([self.width, self.height])
        self.image.fill((255, 255, 255))
        self.rect = self.image.get_rect(center=(self.x, self.y))


def polar_to_cart(r, angle=0, i=1, n=1):
    angle = 2 * m.pi / n * i + angle
    x = r * m.cos(angle)
    y = r * m.sin(angle)
    return x, y
