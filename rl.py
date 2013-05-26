import libtcodpy as libtcod

class Tile:
    def __init__(self, blocked, block_sight = None):
        self.blocked = blocked

        self.block_sight = block_sight
        if self.block_sight is None:
            self.block_sight = blocked

class Rect:
    # a rectangle on the map, aka a room
    def __init__(self, x, y, w, h):
        self.x1 = x
        self.y1 = y
        self.x2 = x+w
        self.y2 = y+h

class Map():
    def __init__(self, width, height, tiles=None):
        self.width = width
        self.height = height
        if tiles is None:
            self.generate(self.width, self.height)
        else:
            self.tiles = tiles

    def generate(self, w, h):
        # fill map with blocked tiles
        self.tiles = [[Tile(True)
            for y in xrange(h)]
                for x in xrange(w)]

        #place two pillars to test the map
        room1 = Rect(20, 15, 10, 15)
        room2 = Rect(50, 15, 10, 15)
        self.create_room(room1)
        self.create_room(room2)
        self.create_h_tunnel(25, 55, 23)

    def create_room(self, room):
        global dungeon
        for x in xrange(room.x1+1, room.x2):
            for y in xrange(room.y1+1, room.y2):
                self.tiles[x][y].blocked = False
                self.tiles[x][y].block_sight = False

    def create_h_tunnel(self, x1, x2, y):
        global dungeon
        for x in xrange(min(x1, x2), max(x1, x2) + 1):
            self.tiles[x][y].blocked = False
            self.tiles[x][y].block_sight = False

    def create_v_tunnel(self, y1, y2, x):
        global dungeon
        #vertical tunnel
        for y in range(min(y1, y2), max(y1, y2) + 1):
            self.tiles[x][y].blocked = False
            self.tiles[x][y].block_sight = False



class World:
    def __init__(self, map_width, map_heigt):
        # generate map
        self.map = Map(map_width, map_heigt)

        # characters
        self.hero = Object(self.map, 25, 23, '@', libtcod.white)
        self.npcs = [Object(self.map, SCREEN_WIDE/2 -5, SCREEN_HIGH/2, '@', libtcod.yellow)]

    def render_all(self, target):
        if target is not None:
            global color_light_wall
            global color_light_ground
            for y in xrange(self.map.height):
                for x in xrange(self.map.width):
                    if self.map.tiles[x][y].block_sight:
                        libtcod.console_set_char_background(target, x, y, color_dark_wall, libtcod.BKGND_SET )
                    else:
                        libtcod.console_set_char_background(target, x, y, color_dark_ground, libtcod.BKGND_SET )

            for o in self.npcs:
                o.draw(target)
            self.hero.draw(target)
            libtcod.console_blit(target, 0, 0, SCREEN_WIDE, SCREEN_HIGH, 0, 0, 0)

    def clear_all(self, target):
        for o in self.npcs:
            o.clear(target)
        self.hero.clear(target)


class Object:
    def __init__(self, levelmap, x, y, char, color):
        self.x = x
        self.y = y
        self.char = char
        self.color = color
        self.map = levelmap

    def move(self, dx, dy):
        if not self.map.tiles[self.x + dx][self.y + dy].blocked:
            self.x += dx
            self.y += dy

    def draw(self, target):
        libtcod.console_set_default_foreground(target, self.color)
        libtcod.console_put_char(target, self.x, self.y, self.char, libtcod.BKGND_NONE)

    def clear(self, target):
        libtcod.console_put_char(target, self.x, self.y, ' ', libtcod.BKGND_NONE)

#class Player:
#    def __init__(self):

def handle_keys():

    key = libtcod.console_check_for_keypress()  #real-time
    #key = libtcod.console_wait_for_keypress(True)  #turn-based
    if key.vk == libtcod.KEY_ENTER and key.lalt:
        #Alt+Enter: toggle fullscreen
        libtcod.console_set_fullscreen(not libtcod.console_is_fullscreen())
    elif key.vk == libtcod.KEY_ESCAPE:
        return True  #exit game

    if libtcod.console_is_key_pressed(libtcod.KEY_UP):
        world.hero.move(0, -1)
    elif libtcod.console_is_key_pressed(libtcod.KEY_DOWN):
        world.hero.move(0, 1)
    if libtcod.console_is_key_pressed(libtcod.KEY_LEFT):
        world.hero.move(-1, 0)
    elif libtcod.console_is_key_pressed(libtcod.KEY_RIGHT):
        world.hero.move(1, 0)

#############################################
# Initialization & Main Loop
#############################################
LIMIT_FPS = 30
# size of the screen
SCREEN_WIDE = 80
SCREEN_HIGH = 50
# size of the map
MAP_WIDE = 80
MAP_HIGH = 45

color_dark_wall = libtcod.Color(0, 0, 100)
color_dark_ground = libtcod.Color(50, 50, 150)

libtcod.console_set_custom_font('arial10x10.png', libtcod.FONT_TYPE_GREYSCALE | libtcod.FONT_LAYOUT_TCOD)
libtcod.console_init_root(SCREEN_WIDE, SCREEN_HIGH, 'Bakachooka', False)
con = libtcod.console_new(SCREEN_WIDE, SCREEN_HIGH)
libtcod.sys_set_fps(LIMIT_FPS)

world = World(MAP_WIDE, MAP_HIGH)

while not libtcod.console_is_window_closed():
    world.render_all(con)
    libtcod.console_flush()
    world.clear_all(con)

    exit = handle_keys()
    if exit:
        break
