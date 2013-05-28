import libtcodpy as libtcod

class Tile:
    def __init__(self, blocked, block_sight = None):
        self.blocked = blocked
        self.explored = False

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
        self.centerxy = self.center()
        
    def center(self):
        center_x = (self.x1+self.x2)/2
        center_y = (self.y1+self.y2)/2
        return (center_x,  center_y)
        
    def intersect(self, other):
        x_intersect = self.x1 <= other.x2 and self.x2 >= other.x1
        y_intersect = self.y1 <= other.y2 and self.y2 >= other.y1
        return (x_intersect and y_intersect)        
        
class Map():
    
    def __init__(self, width, height, tiles=None, labels=False):
        self.width = width
        self.height = height
        if tiles is None:
            self.generate(self.width, self.height)
        else:
            self.tiles = tiles
        self.labels = labels

    def generate(self, w, h):
        # fill map with blocked tiles
        self.tiles = [[Tile(True)
            for y in xrange(h)]
                for x in xrange(w)]

        #place two pillars to test the map
        self.rooms = []
        
        for r in xrange(MAX_ROOMS):
            w = libtcod.random_get_int(0, ROOM_MIN_SIZE, ROOM_MAX_SIZE)
            h = libtcod.random_get_int(0, ROOM_MIN_SIZE, ROOM_MAX_SIZE)
            x = libtcod.random_get_int(0, 0, self.width - w - 1)
            y = libtcod.random_get_int(0, 0, self.height - h - 1)
            
            new_room = Rect(x, y, w, h)
            
            for other_room in self.rooms:
                intersect = new_room.intersect(other_room)
                
                if intersect:
                    break
            else:
                # there were no intersections, so we can go ahead and make it
                self.create_room(new_room)
                (new_x, new_y) = new_room.center()

                if len(self.rooms) > 0:
                    # center of previous room
                    (prev_x, prev_y) = self.rooms[-1].center()
                    
                    if libtcod.random_get_int(0, 0, 1):
                        # first horizontally, than vertically
                        self.create_h_tunnel(prev_x, new_x, prev_y)
                        self.create_v_tunnel(prev_y, new_y, new_x)
                    else:
                        # first vertically, than horizontally
                        self.create_v_tunnel(prev_y, new_y, prev_x)
                        self.create_h_tunnel(prev_x, new_x, new_y) 
                        
                self.rooms.append(new_room)
        
    def create_room(self, room):
        for x in xrange(room.x1, room.x2+1):
            for y in xrange(room.y1, room.y2+1):
                self.tiles[x][y].blocked = False
                self.tiles[x][y].block_sight = False

    def create_h_tunnel(self, x1, x2, y):
        # horizontal tunnel
        for x in xrange(min(x1, x2), max(x1, x2) + 1):
            self.tiles[x][y].blocked = False
            self.tiles[x][y].block_sight = False

    def create_v_tunnel(self, y1, y2, x):
        # vertical tunnel
        for y in range(min(y1, y2), max(y1, y2) + 1):
            self.tiles[x][y].blocked = False
            self.tiles[x][y].block_sight = False



class World:
    def __init__(self, map_width, map_height):
        # generate map
        self.map = Map(map_width, map_height)
        self.npcs = []

        if self.map.labels:
            for i, r in enumerate(self.map.rooms):
                (rx, ry) = r.center()
                room_no = Object(self.map, rx, ry, chr(65+i), libtcod.white)
                self.npcs.insert(0, room_no) #draw early, so monsters are drawn on top
        
        (startx,starty) = self.map.rooms[0].center()
        self.hero = Object(self.map, startx, starty, '@', libtcod.white)
        self.hero.create_fov_map()
        self.hero.refresh_fov_map()
        # characters
        (startx,starty) = self.map.rooms[-1].center()
        self.npcs.append(Object(self.map, startx, starty, 'F', libtcod.yellow))


    def render_all(self, target):
        if target is not None:
            global color_light_wall
            global color_light_ground
            for y in xrange(self.map.height):
                for x in xrange(self.map.width):
                    visible = libtcod.map_is_in_fov(self.hero.fov_map, x, y)
                    wall = self.map.tiles[x][y].block_sight
                    if visible:
                        if wall:
                            libtcod.console_set_char_background(target, x, y, color_light_wall, libtcod.BKGND_SET)
                        else:
                            libtcod.console_set_char_background(target, x, y, color_light_ground, libtcod.BKGND_SET)
                        self.map.tiles[x][y].explored = True
                    else:
                        if self.map.tiles[x][y].explored:
                            if wall:
                                libtcod.console_set_char_background(target, x, y, color_dark_wall, libtcod.BKGND_SET)
                            else:
                                libtcod.console_set_char_background(target, x, y, color_dark_ground, libtcod.BKGND_SET )

            for o in self.npcs:
                if libtcod.map_is_in_fov(self.hero.fov_map, o.x, o.y):
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
        self.fov_map = None
        
        self.torch_radius = 10

    def move(self, dx, dy):
        if not self.map.tiles[self.x + dx][self.y + dy].blocked:
            self.x += dx
            self.y += dy
            self.refresh_fov_map()

    def draw(self, target):
        libtcod.console_set_default_foreground(target, self.color)
        libtcod.console_put_char(target, self.x, self.y, self.char, libtcod.BKGND_NONE)

    def clear(self, target):
        libtcod.console_put_char(target, self.x, self.y, ' ', libtcod.BKGND_NONE)

    def create_fov_map(self):
        self.fov_map = libtcod.map_new(self.map.width,
                                       self.map.height)
                                  
        for x in xrange(self.map.width):
            for y in xrange(self.map.height):
                libtcod.map_set_properties(self.fov_map, x, y,
                                           not self.map.tiles[x][y].block_sight,
                                           not self.map.tiles[x][y].blocked)

    def refresh_fov_map(self):
        if self.fov_map is None:
            return
        libtcod.map_compute_fov(self.fov_map,
                            self.x,
                            self.y,
                            self.torch_radius,
                            True,
                            0)
                            
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
LIMIT_FPS = 20
# size of the screen
SCREEN_WIDE = 80
SCREEN_HIGH = 50
# size of the map
MAP_WIDE = 80
MAP_HIGH = 45

ROOM_MAX_SIZE = 10
ROOM_MIN_SIZE = 6
MAX_ROOMS = 10

#color_dark_wall = libtcod.Color(0, 0, 100)
color_dark_wall = libtcod.Color(30, 30, 30)
color_light_wall = libtcod.Color(130, 110, 50)
#color_dark_ground = libtcod.Color(50, 50, 150)
color_dark_ground = libtcod.Color(20, 18, 5)
color_light_ground = libtcod.Color(200, 180, 50)

libtcod.console_set_custom_font('arial10x10.png', libtcod.FONT_TYPE_GREYSCALE | libtcod.FONT_LAYOUT_TCOD)
libtcod.console_init_root(SCREEN_WIDE, SCREEN_HIGH, 'Bakachooka', False)
con = libtcod.console_new(SCREEN_WIDE, SCREEN_HIGH)
libtcod.sys_set_fps(LIMIT_FPS)

world = World(MAP_WIDE, MAP_HIGH)
world.map.labels = False

while not libtcod.console_is_window_closed():
    world.render_all(con)
    libtcod.console_flush()
    world.clear_all(con)

    exit = handle_keys()
    if exit:
        break
