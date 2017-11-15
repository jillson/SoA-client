#!/usr/bin/env python3
 
import tdl
from tcod import image_load
from random import randint
import colors
import math
import textwrap
import shelve

from gameconsts import *

from objects import *
  
class Rect:
    #a rectangle on the map. used to characterize a room.
    def __init__(self, x, y, w, h):
        self.x1 = x
        self.y1 = y
        self.x2 = x + w
        self.y2 = y + h
 
    def center(self):
        center_x = (self.x1 + self.x2) // 2
        center_y = (self.y1 + self.y2) // 2
        return (center_x, center_y)
 
    def intersect(self, other):
        #returns true if this rectangle intersects with another one
        return (self.x1 <= other.x2 and self.x2 >= other.x1 and
                self.y1 <= other.y2 and self.y2 >= other.y1)
 

#TODO: add options to pass in consts vs getting from gameconsts
#TODO: use my_map.width / my_map.heigh vs consts
#TODO: refactor into base and specific generators
#TODO: make Map object implement __get__ item so it can get/set stuff without needing to do hack.my_map which is ugly...
class DungeonGenerator:
    def __init__(self,hack):
        self.my_map = hack.my_map
        self.hack = hack
        
        rooms = []
        num_rooms = 0
 
        for r in range(MAX_ROOMS):
            #random width and height
            w = randint(ROOM_MIN_SIZE, ROOM_MAX_SIZE)
            h = randint(ROOM_MIN_SIZE, ROOM_MAX_SIZE)
            #random position without going out of the boundaries of the map
            x = randint(0, MAP_WIDTH-w-1)
            y = randint(0, MAP_HEIGHT-h-1)
 
            #"Rect" class makes rectangles easier to work with
            new_room = Rect(x, y, w, h)
 
            #run through the other rooms and see if they intersect with this one
            failed = False
            for other_room in rooms:
                if new_room.intersect(other_room):
                    failed = True
                    break
 
            if not failed:
                #this means there are no intersections, so this room is valid
 
                #"paint" it to the map's tiles
                self.create_room(new_room)
 
                #center coordinates of new room, will be useful later
                (new_x, new_y) = new_room.center()
 
                if num_rooms == 0:
                    #this is the first room, where the player starts at
                    self.startX = new_x
                    self.startY = new_y
                    self.hack.player.x = new_x
                    self.hack.player.y = new_y
 
                else:
                    #all rooms after the first:
                    #connect it to the previous room with a tunnel
 
                    #center coordinates of previous room
                    (prev_x, prev_y) = rooms[num_rooms-1].center()
 
                    #draw a coin (random number that is either 0 or 1)
                    if randint(0, 1):
                        #first move horizontally, then vertically
                        self.create_h_tunnel(prev_x, new_x, prev_y)
                        self.create_v_tunnel(prev_y, new_y, new_x)
                    else:
                        #first move vertically, then horizontally
                        self.create_v_tunnel(prev_y, new_y, prev_x)
                        self.create_h_tunnel(prev_x, new_x, new_y)
 
                #add some contents to this room, such as monsters
                self.place_objects(new_room)
 
                #finally, append the new room to the list
                rooms.append(new_room)
                num_rooms += 1
        self.rooms = rooms
        self.num_rooms = num_rooms
 
    def create_room(self, room):
        """ converts all room tiles to be non blocking """
        for x in range(room.x1 + 1, room.x2):
            for y in range(room.y1 + 1, room.y2):
                self.my_map[x][y].blocked = False
                self.my_map[x][y].block_sight = False
 
    def create_h_tunnel(self, x1, x2, y):
        """ creates horizontal tunnel from x1 to x2 """
        for x in range(min(x1, x2), max(x1, x2) + 1):
            self.my_map[x][y].blocked = False
            self.my_map[x][y].block_sight = False
 
    def create_v_tunnel(self, y1, y2, x):
        """ creates vertical tunnel from y1 to y2 """
        for y in range(min(y1, y2), max(y1, y2) + 1):
            self.my_map[x][y].blocked = False
            self.my_map[x][y].block_sight = False
 
    def place_objects(self, room):
        #choose random number of monsters
        num_monsters = randint(0, MAX_ROOM_MONSTERS)
        objects = self.hack.objects
         
        for i in range(num_monsters):
            #choose random spot for this monster
            x = randint(room.x1+1, room.x2-1)
            y = randint(room.y1+1, room.y2-1)
 
 
            #only place it if the tile is not blocked
            if not self.hack.is_blocked(x, y):
                if randint(0, 100) < 80:  #80% chance of getting an orc
                    #create an orc
                    fighter_component = Fighter(hp=10, defense=0, power=3, 
                                                death_function=monster_death)
                    ai_component = BasicMonster()
 
                    monster = GameObject(x, y, 'o', 'orc', colors.desaturated_green, self.hack, blocks=True, fighter=fighter_component, ai=ai_component)
                else:
                    #create a troll
                    fighter_component = Fighter(hp=16, defense=1, power=4,
                                            death_function=monster_death)
                    ai_component = BasicMonster()
 
                    monster = GameObject(x, y, 'T', 'troll', colors.darker_green, self.hack,
                    blocks=True, fighter=fighter_component, ai=ai_component)
 
                    objects.append(monster)
 
        #choose random number of items
        num_items = randint(0, MAX_ROOM_ITEMS)
 
        for i in range(num_items):
            #choose random spot for this item
            x = randint(room.x1+1, room.x2-1)
            y = randint(room.y1+1, room.y2-1)
 
            #only place it if the tile is not blocked
            if not self.hack.is_blocked(x, y):
                dice = randint(0, 100)
                if dice < 70:
                    #create a healing potion (70% chance)
                    item_component = Item(use_function=cast_heal)
 
                    item = GameObject(x, y, '!', 'healing potion', 
                                      colors.violet, self.hack, item=item_component)
 
                elif dice < 70+10:
                    #create a lightning bolt scroll (15% chance)
                    item_component = Item(use_function=cast_lightning)
 
                    item = GameObject(x, y, '#', 'scroll of lightning bolt', 
                                      colors.light_yellow, self.hack, item=item_component)
 
                elif dice < 70+10+10:
                    #create a fireball scroll (10% chance)
                    item_component = Item(use_function=cast_fireball)
 
                    item = GameObject(x, y, '#', 'scroll of fireball', 
                                      colors.light_yellow, self.hack, item=item_component)
 
                else:
                    #create a confuse scroll (15% chance)
                    item_component = Item(use_function=cast_confuse)
                    
                    item = GameObject(x, y, '#', 'scroll of confusion', 
                                      colors.light_yellow, self.hack, item=item_component)
 
                objects.append(item)
                item.send_to_back()  #items appear below other objects
                
 
