class Render():
    def __init__(self):
        pass

class ShellRender(Render):
    pass


class TkRender(Render):
    """Game Render using Tkinter module
       Why not?
    """
    CAN_USE_TK = True
    try:
        import tkinter as tk
    except ModuleNotFoundError:
        print("Warning: You can't use TkRender class")
        CAN_USE_TK = False
    import time

    def __init__(self):
        if not self.CAN_USE_TK:
            raise ModuleNotFoundError("Problems with Tk import. This computer may be not configured for Tk")
        super().__init__()
        self._redraw_started = False
        self.root = self.tk.Tk()
        self.root.bind_all('<KeyRelease>', lambda ev: self._key_release_handle(ev))
        self._key_pressed = "q"

    def init_screen(self, h, w):
        self.objects = []
        for l in range(h):
            line = []
            for c in range(w):
                line.append(self.tk.Label(self.root, text=' '))
                line[-1].grid(row=l, column=c)
            self.objects.append(line)

    def _key_release_handle(self, event):
        result = event.keysym
        if result == 'Escape':
            result = 'ESC'
        if result == 'space':
            result = " "
        self._key_pressed = result

    def add_object(self, char, x, y):
        if not self._redraw_started:
            for line in self.objects:
                for el in line:
                    el['text'] = ' '
            self._redraw_started = True
        self.objects[y][x]['text'] = char

    def draw_screen(self):
        self._redraw_started = False
        self.root.update_idletasks()
        self.root.update()

    def get_input(self):
        while self._key_pressed == '':
            self.root.update_idletasks()
            self.root.update()
        res = self._key_pressed
        self._key_pressed = ''
        return res


class GameObject:
    """Main game object Class.
       Methods:
       .render - render :)
       .interact - main object's logic when it
                   if interacting with other objects.
       .process - main object's actions

    """
    def __init__(self, x, y, game):
        self.y = y
        self.x = x
        self.game = game
        self.alive = True
        self.passable = True
        self.interactable = True

    def interact(self, object):
        pass

    def process(self):
        pass

    def render(self):
        raise NotImplementedError


class Coin(GameObject):
    def render(self):
        return "$"


class Wall(GameObject):
    def __init__(self, x, y, game):
        super().__init__(x, y, game)
        self.alive = True
        self.passable = False
        self.interactable = False

    def render(self):
        return "#"


class Player(GameObject):
    def __init__(self, x, y, game):
        super().__init__(x, y, game)
        self.coins = 0

    def interact(self, other):
        if isinstance(other, Coin):
            other.alive = False
            self.coins += 1

    def process(self):
        if self.game.input == 'w':
            self.game.move_to(self, self.x, self.y - 1)
        elif self.game.input == 's':
            self.game.move_to(self, self.x, self.y + 1)
        elif self.game.input == 'a':
            self.game.move_to(self, self.x - 1, self.y)
        elif self.game.input == 'd':
            self.game.move_to(self, self.x + 1, self.y)
        elif self.game.input == ' ':
            self.game.add_object(Bomb(self.x, self.y, self.game))

    def render(self):
        return "@"


class HeatWave(GameObject):
    def __init__(self, x, y, game):
        super().__init__(x, y, game)
        self.alive = True
        self.passable = True
        self.interactable = True

    def interact(self, object):
        if isinstance(object, Player) or isinstance(object, SoftWall):
            object.alive = False
        self.process()


    def process(self):
        self.alive = False

    def render(self):
        return "+"


class Bomb(GameObject):
    def __init__(self, x, y, game):
        super().__init__(x, y, game)
        self.life_time = 3

    def process(self):
        self.life_time -= 1
        if self.life_time < 0:
            self.alive = False
            self.game.add_object(HeatWave(self.x, self.y, self.game))
            self.game.add_object(HeatWave(self.x + 1, self.y, self.game))
            self.game.add_object(HeatWave(self.x - 1, self.y, self.game))
            self.game.add_object(HeatWave(self.x, self.y + 1, self.game))
            self.game.add_object(HeatWave(self.x, self.y - 1, self.game))

    def render(self):
        return "*"


class SoftWall(GameObject):
    def __init__(self, x, y, game):
        super().__init__(x, y, game)
        self.alive = True
        self.passable = False
        self.interactable = True

    def render(self):
        return "%"


class Game:
    # game states
    IN_PROGRESS = 0
    WIN = 1
    LOSE = 2

    def __init__(self, renderer):
        self.renderer = renderer
        self.game_objects = []
        self.new_objects = []
        self.movements = []
        self.interactions = []
        self.player = None
        self.input = ''

    def update(self):   # Game environment update with every step
        self._get_input()
        self._process_all()
        self._create_new()
        self._move_all()
        self._interact_all()
        self._delete_old()


    def game_state(self):   # Game status in current step (WIN / LOSE)
        if self.player is None or not self.player.alive:
            return self.LOSE

        for go in self.game_objects:
            if isinstance(go, Coin):
                return self.IN_PROGRESS
        return self.WIN

    def _get_objects_by_pos(self, x, y):   # Position of the object
        result = []
        for go in self.game_objects:
            if go.x == x and go.y == y:
                result.append(go)
        return result

    def _process_all(self):   # object movement process
        for go in self.game_objects:
            go.process()

    def _create_new(self):   # so-called database of created or destroyed objects
        for new_obj in self.new_objects:
            existing_obj = self._get_objects_by_pos(new_obj.x, new_obj.y)
            if any(not go.interactable for go in existing_obj):
                continue
            for go in existing_obj:
                self.interactions.append((new_obj, go))
            self.game_objects.append(new_obj)
        self.new_objects.clear()

    def _move_all(self):   # object movement to next position
        for obj, new_pos in self.movements:
            existing_obj = self._get_objects_by_pos(new_pos[0], new_pos[1])
            if any(not go.passable for go in existing_obj):
                continue
            for go in existing_obj:
                self.interactions.append((obj, go))
            obj.x = new_pos[0]
            obj.y = new_pos[1]
        self.movements.clear()

    def _interact_all(self):   # Objects interactions logic
        for obj1, obj2 in self.interactions:
            obj1.interact(obj2)
            obj2.interact(obj1)
        self.interactions.clear()

    def _delete_old(self):
        self.game_objects = list(filter(lambda go: go.alive, self.game_objects))

    def load_level(self, level):   # Level load. Version one - only one lvl :(
        obj_char_to_types = {
            "#": Wall,
            "@": Player,
            "%": SoftWall,
            "$": Coin
        }
        w = 0
        h = 0
        for line_number, line in enumerate(level.strip().splitlines()):
            w = max(w, len(line.strip()))
            h += 1
            for char_number, char in enumerate(line.strip()):
                if char == '@':
                    self.player = obj_char_to_types[char](char_number, line_number, self)
                    self.add_object(self.player)
                elif char in obj_char_to_types:
                    self.add_object(obj_char_to_types[char](char_number, line_number, self))

        self._create_new()
        self.renderer.init_screen(h, w)

    def add_object(self, game_object):
        self.new_objects.append(game_object)

    def move_to(self, go, new_x, new_y):
        self.movements.append((go, (new_x, new_y)))

    def render(self):
        for go in self.game_objects:
            self.renderer.add_object(go.render(), go.x, go.y)
        self.renderer.draw_screen()

    def _get_input(self):
        self.input = self.renderer.get_input()


if __name__ == '__main__':
    game = Game(TkRender())
    level = level_example = """
        ##########
        #@  %    #
        #   %    #
        #  %%%   #
        # %%$%%  #
        #  %%%   #
        #   %    #
        #   %    #
        #   %    #
        ##########
    """

    game.load_level(level)
    while game.game_state() == Game.IN_PROGRESS:
        game.render()
        game.update()


    if game.game_state() == Game.WIN:
        print("Win")
    if game.game_state() == Game.LOSE:
        print("lose")