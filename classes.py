import random
import rules as r
import math as m


class Tiles:
    def __init__(self):
        self.tiles = []
        self.selected_tiles = []

    def unselect(self):
        for tile in self.tiles:
            if tile.selected:
                tile.Unselect()
        self.selected_tiles.clear()

    def selected(self):
        return self.selected_tiles

    def add(self, tile):
        self.tiles.append(tile)


class Tile:

    def __init__(self, io_handler, tile_group, container, color):
        self.container = container
        self.color = color
        self.type = "tile"
        self.io_handler = io_handler
        self.selected = False
        self.tile_group = tile_group
        self.tile_group.add(self)
        self.position = None
        self.io = self.io_handler.Create(self)

    def __str__(self):
        return self.color[0].upper()

    def Move(self, container, n=None):
        self.container = container
        if n is None:
            self.position = self.container.tiles.index(self)
        else:
            self.position = n
        self.io.update()

    def Select(self):
        self.tile_group.unselect()
        self.selected = True
        self.tile_group.selected_tiles.append(self)
        self.io.toggleSelected()
        if self.container.type == "factory" or self.container.type == "center":
            return self.container.select(self.color)

    def Unselect(self):
        self.selected = False
        self.io.toggleSelected()


class FirstTile(Tile):

    def Move(self, container, n=None):
        super(FirstTile, self).Move(container=container, n=n)
        if self.container.type == "floor" or self.container.type == "pattern":
            for player in self.container.board.player.game.players:
                player.first = False
            self.container.board.player.first = True


class TileContainer:

    def __init__(self, io_handler, name=None, max_size=None, possible_colors=None):
        self.name = name
        self.max_size = max_size
        self.possible_colors = r.rules["colors"].copy()
        if possible_colors is not None:
            self.possible_colors.extend(possible_colors)
        self.possible_colors = list(dict.fromkeys(self.possible_colors))
        self.color = None
        self.tiles = []
        self.selected_tiles = []
        self.selected_color = None
        self.drawn_tiles = []
        self.returned_tiles = []
        self.type = "generic_container"
        self.io_handler = io_handler
        self.tile_status = None

    def __str__(self):
        display = ""
        if self.color is None:
            for color in self.possible_colors:
                display += color[0].upper() + ": " + str(self.count(color)) + "\n"
        else:
            display += self.color[0].upper() + ": " + str(self.count(self.color))
        if self.max_size is not None:
            if self.color is None:
                display += "*" * self.open()
            else:
                display += self.color[0].lower() * self.open()

    def count(self, color=None):
        if color is None:
            return len(self.tiles)
        else:
            return len(keep_tiles(self.tiles, color))

    def full(self):
        if self.max_size is None:
            return False
        else:
            return len(self.tiles) >= self.max_size

    def open(self):
        if self.full():
            return 0
        elif self.max_size is not None:
            return self.max_size - self.count()
        else:
            return -1

    def color_allowed(self, color):
        if color == self.color:
            allowed = True
        elif self.color is not None:
            allowed = False
        else:
            allowed = False
            for possible_color in self.possible_colors:
                if color == possible_color:
                    allowed = True
                    break
        return allowed

    def unselect(self):
        self.selected_tiles.clear()


class Discard(TileContainer):

    def __init__(self, io_handler, tile_group):
        super(Discard, self).__init__(io_handler=io_handler, name="Tile Bag", possible_colors="1st")
        self.type = "discard"
        self.io = io_handler.Create(self)
        self.tile_group = tile_group
        self.tiles.append(FirstTile(self.io_handler, self.tile_group, self, "1st"))
        self.tile_status = "placed"

    def add(self, tiles):
        self.tiles.extend(tiles)
        for tile in tiles:
            tile.Move(self)

    def draw(self):
        self.drawn_tiles.clear()
        if self.count("1st") > 0:
            self.drawn_tiles = keep_tiles(self.tiles, "1st")
            self.tiles = remove_tiles(self.tiles, "1st")
        return self.drawn_tiles


class TileBag(TileContainer):

    def __init__(self, io_handler, tile_group, discard):
        super(TileBag, self).__init__(io_handler=io_handler, name="Tile Bag")
        for i in range(len(r.rules["colors"])):
            self.tiles.extend([r.rules["colors"][i]] * r.rules["amounts"][i])
        self.max_size = self.count()
        self.type = "bag"
        self.io = io_handler.Create(self)
        self.tile_group = tile_group
        for i in range(len(self.tiles)):
            self.tiles[i] = Tile(self.io_handler, self.tile_group, self, self.tiles[i])
        random.shuffle(self.tiles)
        self.discard = discard

    def draw(self, count):
        self.drawn_tiles.clear()
        exhausted = False
        complete = False
        checked = False
        while not (exhausted or complete):
            if self.count() < count:
                count -= self.count()
                self.drawn_tiles = self.tiles.copy()
                self.tiles.clear()
                if self.discard.count() > 0 and not checked:
                    self.refill()
                    checked = True
                else:
                    exhausted = True
            else:
                self.drawn_tiles = self.tiles[0:count]
                self.tiles = self.tiles[count:]
                complete = True
        return self.drawn_tiles, exhausted

    def refill(self):
        for color in list(dict.fromkeys(list(filter(lambda tile: tile.color, self.discard.tiles)))):
            if self.color_allowed(color):
                self.tiles.extend(list(filter(lambda tile: tile.color == color, self.discard.tiles)))
        for tile in self.tiles:
            tile.Move(self)


class Factory(TileContainer):

    def __init__(self, io_handler, number, tile_bag, center, discard):
        super(Factory, self).__init__(io_handler=io_handler, name="Factory " + str(number), max_size=r.rules["factorySize"])
        self.number = number
        self.returned_tiles = []
        self.tile_bag = tile_bag
        self.center = center
        self.discard = discard
        self.type = "factory"
        self.io = self.io_handler.Create(self, self.number)
        self.tile_status = "dealt"

    def __str__(self):
        side = m.ceil(m.sqrt(self.max_size))
        n = 0
        display = ""
        for i in range(side):
            display += "|"
            for j in range(side):
                if n < len(self.tiles):
                    display += str(self.tiles[n])
                else:
                    display += " "
                n += 1
            display += "|\n"
        return display

    def deal(self):
        while True:
            tiles, exhausted = self.tile_bag.draw(self.open())
            self.tiles = tiles.copy()
            for i in range(self.count()-1, -1, -1):
                if not self.color_allowed(self.tiles[i].color):
                    self.returned_tiles.append(self.tiles[i])
                    self.tiles.pop(i)
            if self.full() or exhausted:
                break
        for tile in self.tiles:
            tile.Move(self)
        self.discard.add(self.returned_tiles)

    def select(self, color):
        self.selected_tiles.clear()
        if self.count(color) > 0:
            self.selected_tiles = keep_tiles(self.tiles, color)
            self.selected_color = color
        print(self.selected_tiles)
        return self.selected_tiles

    def draw(self):
        self.drawn_tiles.clear()
        if len(self.selected_tiles) > 0:
            self.drawn_tiles = self.selected_tiles.copy()
            self.selected_tiles.clear()
            self.center.add(remove_tiles(self.tiles, self.selected_color))
            self.selected_color = None
            self.tiles.clear()
        return self.drawn_tiles


class Center(TileContainer):

    def __init__(self, io_handler, discard):
        super(Center, self).__init__(io_handler=io_handler, name="Center", possible_colors=["1st"], max_size=r.rules["centerSize"])
        self.discard = discard
        self.type = "center"
        self.io = self.io_handler.Create(self)
        self.tile_status = "dealt"

    def add(self, tiles):
        self.returned_tiles.clear()
        for tile in tiles:
            if not self.full():
                if self.color_allowed(tile.color):
                    self.tiles.append(tile)
                else:
                    self.returned_tiles.append(tile)
            else:
                self.returned_tiles.append(tile)
        for tile in self.tiles:
            tile.Move(self)
        self.discard.add(self.returned_tiles)

    def select(self, color):
        self.selected_tiles.clear()
        if self.count(color) > 0:
            self.selected_tiles = keep_tiles(self.tiles, color)
            self.selected_color = color
            if len(keep_tiles(self.tiles, "1st")) > 0:
                self.selected_tiles.extend(keep_tiles(self.tiles, "1st").copy())
        return self.selected_tiles

    def draw(self):
        self.drawn_tiles.clear()
        if len(self.selected_tiles) > 0:
            self.drawn_tiles = self.selected_tiles.copy()
            self.tiles = remove_tiles(self.tiles, self.selected_color)
            if len(keep_tiles(self.tiles, "1st")) > 0:
                self.tiles = remove_tiles(self.tiles, "1st")
            self.selected_tiles.clear()
            self.selected_color = None
        return self.drawn_tiles

    def deal(self):
        added_tiles = self.discard.draw()
        if len(added_tiles) > 0:
            self.tiles.extend(added_tiles.copy())
            for tile in added_tiles:
                tile.Move(self)


class Pattern(TileContainer):

    def __init__(self, board, number, colors):
        super(Pattern, self).__init__(io_handler=board.io_handler, name="Pattern " + str(number), max_size=r.rules["patternSizes"][number])
        self.board = board
        self.number = number
        self.possible_colors = colors.copy()
        self.floor = self.board.floor
        self.type = "pattern"
        self.io = self.io_handler.Create(self, self.number)
        self.tile_status = "placed"

    def __str__(self):
        if self.color is None:
            display = "*" * self.max_size
        else:
            display = self.color[0].upper() * self.count() + self.color[0].lower() * self.open()

    def add(self, tiles):
        self.returned_tiles.clear()
        for tile in tiles:
            if not self.full():
                if self.color is None:
                    if self.color_allowed(tile.color):
                        self.color = tile.color
                        self.tiles.append(tile)
                    else:
                        self.returned_tiles.append(tile)
                else:
                    if tile.color == self.color:
                        self.tiles.append(tile)
                    else:
                        self.returned_tiles.append(tile)
            else:
                self.returned_tiles.append(tile)
        for tile in self.tiles:
            tile.Move(self)
        if len(self.returned_tiles) > 0:
            self.floor.add(self.returned_tiles)

    def clear(self):
        self.returned_tiles.clear()
        if len(self.tiles) > 1:
            self.returned_tiles = self.tiles[1:].copy()
        self.board.discard.add(self.returned_tiles)
        tile = self.tiles[0]
        self.possible_colors.pop(self.possible_colors.index(self.color))
        self.color = None
        self.tiles.clear()
        return tile


class Floor(TileContainer):

    def __init__(self, board):
        super(Floor, self).__init__(io_handler=board.io_handler, name="Floor", max_size=r.rules["floorSize"], possible_colors=["1st"])
        self.board = board
        self.penalties = r.rules["floor"].copy()
        self.discard = self.board.discard
        self.type = "floor"
        self.io = self.io_handler.Create(self)
        self.tile_status = "placed"

    def __str__(self):
        display = ""
        for i in range(self.penalties()):
            if not display == "":
                display += "|"
            if i < len(self.penalties):
                display += str(self.penalties[i])
            else:
                display += str(self.penalties[-1])
            display += ":"
            if self.count() > i:
                display += str(self.tiles[i])
            else:
                display += "*"
        if self.count() > len(self.penalties):
            for i in range(self.count()):
                display += "|"
                display += str(self.penalties[-1])
                display += ":"
                display += str(self.tiles[i])
        if self.max_size is None:
            display += "|" + str(self.penalties[-1]) + ":*+"
        elif self.max_size > self.count():
            for i in range(self.count(), self.max_size):
                display += "|" + str(self.penalties[-1]) + ":*"
        return display

    def add(self, tiles):
        self.returned_tiles.clear()
        for tile in tiles:
            if not self.full():
                if self.color_allowed(tile.color):
                    self.tiles.append(tile)
                else:
                    self.returned_tiles.append(tile)
            else:
                self.returned_tiles.append(tile)
        for tile in self.tiles:
            tile.Move(self)
        self.discard.add(self.returned_tiles)

    def Score(self):
        score = 0
        for i in range(self.count()):
            if i < len(self.penalties):
                score += self.penalties[i]
            else:
                score += self.penalties[-1]
        self.returned_tiles = self.tiles.copy()
        self.tiles.clear()
        self.discard.add(self.returned_tiles)
        return score


class Row(TileContainer):

    def __init__(self, board, number, possible_colors):
        super(Row, self).__init__(io_handler=board.io_handler, name="Row " + str(number))
        self.possible_colors = possible_colors
        self.board = board
        self.max_size = self.board.size
        self.number = number
        for i in range(self.max_size):
            self.tiles.append(None)
        self.type = "row"
        self.io = self.io_handler.Create(self, self.number)
        self.tile_status = "scored"

    def __str__(self):
        display = ""
        for i in range(self.max_size):
            if self.tiles[i] is None:
                if r.rules["boardType"] != 0:
                    display += self.possible_colors[i][0].lower()
                else:
                    display += "*"
            else:
                display += str(self.tiles[i])
        return display

    def add(self, tile, x=None):
        self.returned_tiles.clear()
        if r.rules["boardType"] != 0:
            if len(keep_value(self.possible_colors, tile.color)) > 0:
                x = self.possible_colors.index(tile.color)
                self.tiles[x] = tile
                self.possible_colors[x] = None
                self.board.columns[x].add(self.number)
            else:
                raise Exception("Tile color added to row that is not allowed.")
        else:
            pass
        tile.Move(self, x)
        return x

    def count(self, color=None):
        if color is None:
            return len(remove_tiles(self.tiles, None))
        else:
            return len(keep_tiles(self.tiles, color))

    def open(self):
        return len(keep_tiles(self.tiles, None))

    def full(self):
        return len(keep_value(self.tiles, None)) == 0

    def covered(self, x):
        return self.tiles[x] is not None

    def complete(self):
        self.full()


class Column:
    def __init__(self, number, board):
        self.name = "Column " + str(number)
        self.board = board
        self.max_size = self.board.size
        self.psuedo_tiles = []

    def add(self, row):
        self.psuedo_tiles.append(row)

    def complete(self):
        return self.max_size == len(self.psuedo_tiles)


# Board
class Board:

    def __init__(self, io_handler, discard, player):
        self.type = "board"
        self.discard = discard
        self.io_handler = io_handler
        self.player = player
        self.max_size = None  # necessary for IO class
        self.io = io_handler.Create(self)
        self.size = min(r.rules["boardSize"], len(r.rules["colors"]))
        self.rows = []
        self.colors = r.rules["colors"]
        if r.rules["boardType"] > 0 and self.size == len(r.rules["colors"]):
            temp_colors = r.rules["colors"].copy()
            for i in range(self.size):
                if i > 0:
                    for j in range(r.rules["boardType"]):
                        color = temp_colors[-1]
                        temp_colors.insert(0, color)
                        temp_colors.pop()
                self.rows.append(Row(self, i, temp_colors.copy()))
        elif r.rules["boardType"] == 0:  # empty board
            pass
        else:  # randomized board: will need to overwrite self.colors if there are more colors than the board can handle
            pass
        self.columns = []
        for i in range(self.size):
            self.columns.append(Column(i, self))
        self.floor = Floor(self)
        self.patterns = []
        for i in range(self.size):
            self.patterns.append(Pattern(self, i, self.rows[i].possible_colors))
        self.rowScore = r.rules["rowScore"]
        self.columnScore = r.rules["columnScore"]
        self.colorScore = r.rules["colorScore"]

    def __str__(self):
        pattern_width = max(self.patterns[i].max_size for i in range(self.size))
        display = ""
        for i in range(self.size):
            if pattern_width > self.patterns[i].max_size:
                display += " " * pattern_width - self.patterns[i].max_size
            display += str(self.patterns[i])
            display += "|"
            display += str(self.rows[i])
            display += "\n"
        display += str(self.floor)
        return display

    def __ScoreTile__(self, x, y):
        score = 0
        row_score = 0
        column_score = 0
        cont = True
        i = x
        for i in range(x,self.rows[y].max_size,1):
            if self.rows[y].covered(i):
                row_score += 1
            else:
                break
        for i in range(x - 1, -1, -1):
            if self.rows[y].covered(i):
                row_score += 1
            else:
                break
        for i in range(y, self.size, 1):
            if self.rows[i].covered(x):
                column_score += 1
            else:
                break
        for i in range(y -1, -1, -1):
            if self.rows[i].covered(x):
                column_score += 1
            else:
                break
        if row_score > 1 and column_score > 1:
            score = row_score + column_score
        else:
            score = max(row_score, column_score)
        return score

    def PlaceTiles(self, tiles, row):
        if 0 <= row < self.size:
            self.patterns[row].add(tiles)
        else:
            self.floor.add(tiles)

    def RowComplete(self, row_number):
        return self.rows[row_number].complete()

    def ColumnComplete(self, column_number):
        return self.columns[column_number].complete()

    def ColorComplete(self, color):
        complete = True
        for row in self.rows:
            if row.count(color) == 0:
                complete = False
                break
        return complete

    def Complete(self):
        complete = False
        for row in self.rows:
            if row.complete():
                complete = True
                break
        return complete

    def ScoreBonuses(self):
        completed_rows = 0
        completed_columns = 0
        completed_colors = 0
        score = 0
        for i in range(self.size):
            if self.RowComplete(i):
                completed_rows += 1
        for i in range(self.size):
            if self.ColumnComplete(i):
                completed_columns += 1
        for color in self.colors[0]:
            if self.ColorComplete(color):
                completed_colors += 1
        score += completed_rows * r.rules["rowScore"]
        score += completed_columns * r.rules["columnScore"]
        score += completed_colors * r.rules["colorScore"]
        return score

    def PlacementOptions(self, color):
        valid = []
        for i in range(self.size):
            if self.patterns[i].color == color:
                valid.append(True)
            elif len(keep_value(self.patterns[i].possible_colors,color)) > 0 and self.patterns[i].color is None:
                valid.append(True)
            else:
                valid.append(False)
        valid.append(True)
        return valid


# Player
class Player:

    def __init__(self, game, io_handler, name, discard, i, first=False):
        self.io_handler = io_handler
        self.game = game
        self.name = name
        self.score = 0
        self.board = Board(self.io_handler, discard, self)
        self.first = first
        self.selected_container = None
        self.selected_color = None
        self.valid = []
        self.type = "player"
        self.index = i
        self.io = self.io_handler.Create(self, self.index)
        self.active = False

    def __str__(self):
        display = "Player: " + self.name + "|Score: " + str(self.score) + "\n"
        display += str(self.board)
        return display

    def SelectTiles(self, container, color):
        self.selected_container = container
        self.selected_color = color
        self.valid = self.board.PlacementOptions(self.selected_color)

    def PlaceTiles(self):
        self.board.PlaceTiles(self.selected_container.Draw(self.selected_color))
        self.selected_container = None
        self.selected_color = None
        self.valid.clear()
        self.active = False

    def BeginTurn(self):
        self.active = True
        self.io.update()
        self.board.io.update()


class Game:

    def __init__(self, io_handler, players):
        self.io_handler = io_handler
        self.players = []
        self.tile_group = Tiles()
        self.type = "game"
        self.discard = Discard(self.io_handler, self.tile_group)
        self.factory_count = r.rules["factories"][len(players) - 2]
        i = 0
        for player in players:
            if player == players[0]:
                self.players.append(Player(self, io_handler=self.io_handler, name=player, discard=self.discard, i=i, first=True))
            else:
                self.players.append(Player(self, io_handler=self.io_handler, name=player, discard=self.discard, i=i))
            i += 1
        self.tile_bag = TileBag(self.io_handler, self.tile_group, self.discard)
        self.center = Center(self.io_handler, self.discard)
        self.factories = []
        for i in range(self.factory_count):
            self.factories.append(Factory(self.io_handler, i, self.tile_bag, self.center, self.discard))
        self.playing = False
        self.round_over = False
        self.player_index = 0
        self.event = ""
        self.state = "initialized"
        self.player = self.players[0]
        self.player.BeginTurn()
        self.selected_color = None
        self.selected_container = None
        self.selected_tiles = []
        self.winner = None
        self.winning_score = 0
        self.display_text = "Azul"
        self.io = io_handler.Create(self)

    def Play(self, event):
        state = "playing"
        if event[0] == "select":
            self.selected_container = event[1].container
            self.selected_tiles = event[1].Select()
            if self.selected_tiles:
                self.selected_color = event[1].color
            print(self.selected_tiles)
        elif event[0] == "place":
            try:
                length = len(self.selected_tiles)
            except TypeError:
                length = 0
            if length > 0:
                tiles = self.selected_container.draw()
                event[1].add(tiles.copy())
                self.tile_group.unselect()
                self.selected_tiles = []
                self.player_index = (self.player_index + 1) % len(self.players)
                self.player = self.players[self.player_index]
                if not self.RoundComplete():
                    self.player.BeginTurn()
                else:
                    state = "scoring round"
        elif event[0] == "unselect":
            self.tile_group.unselect()
            self.selected_tiles = []
            self.selected_container = None
            self.selected_color = None
        self.io.update()
        return state

    def ScoreRound(self, event):
        # need to add a loop here to place tiles on boards w/o set colors
        state = "dealing"
        for player in self.players:
            score = 0
            for y in range(len(player.board.patterns)):
                if player.board.patterns[y].full():
                    tile = player.board.patterns[y].clear()
                    x = player.board.rows[y].add(tile)
                    score += player.board.__ScoreTile__(x, y)
            score += player.board.floor.Score()
            player.score += score
            if player.board.Complete():
                state = "scoring game"
            player.board.io.update()
        if state != "scoring game":
            self.player_index = self.FirstPlayer()
            self.player = self.players[self.player_index]
            self.player.BeginTurn()
        self.io.update()
        return state

    def ScoreGame(self, event):
        state = "complete"
        max_score = 0
        winner = None
        for player in self.players:
            score = 0
            score = player.board.ScoreBonuses()
            if score > max_score:
                max_score = score
                winner = player.name
            elif score == max_score:
                winner = winner + " & " + player.name
        self.winner = winner
        self.winning_score = max_score
        self.display_text = self.winner + " wins with " + str(self.winning_score) + "!"
        self.io.update()

    def Complete(self, event):
        self.io.update()

    def FirstPlayer(self):
        for i in range(len(self.players)):
            if self.players[i].first:
                break
        return i

    def Deal(self):
        self.center.deal()
        for factory in self.factories:
            factory.deal()

    def SelectTiles(self, tiles):
        self.selected_tiles = tiles.copy()

    def RoundComplete(self):
        complete = True
        if self.center.count() > 0:
            complete = False
        else:
            for factory in self.factories:
                if factory.count() > 0:
                    complete = False
                    break
        return complete


class Controls:

    def __init__(self, io_handler, begun):
        self.io_handler = io_handler
        self.begun = begun
        self.type = "controls"
        self.io = io_handler.Create(self)

    def Check(self):
        self.io.Check()


# Other functions
def remove_value(the_list, val):
    return [value for value in the_list if value != val]


def keep_value(the_list, val):
    return [value for value in the_list if value == val]


def keep_tiles(tiles, color):
    kept_tiles = []
    for tile in tiles:
        if tile.color == color:
            kept_tiles.append(tile)
    return kept_tiles
    # return list(filter(lambda tile: tile.color == color, tiles))


def remove_tiles(tiles, color):
    return list(filter(lambda tile: tile.color != color, tiles))

