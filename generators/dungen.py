#!/usr/bin/env python3
from __future__ import division

import tcod
import random 

from gameconsts import *

from objects import *

from generators.basegen import Rect, Building, Map, BaseGenerator, MapSwitch, mapDict

class DungeonGenerator(BaseGenerator):
    def __init__(self):
        super(DungeonGenerator,self).__init__()

    def generate_map(self,name="dungeon1",oldLoc=None):

        if mapDict.get(name):
            return mapDict[name]
        
        self.my_map = Map(width=MAP_WIDTH, height=MAP_HEIGHT, default_tile="rock")
        rooms = []
        num_rooms = 0

        level = int(name[len("dungeon"):])
        
        for r in range(MAX_ROOMS):
            #random width and height
            w = random.randint(ROOM_MIN_SIZE, ROOM_MAX_SIZE)
            h = random.randint(ROOM_MIN_SIZE, ROOM_MAX_SIZE)
            #random position without going out of the boundaries of the map
            x = random.randint(0, MAP_WIDTH-w-1)
            y = random.randint(0, MAP_HEIGHT-h-1)
 
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
                    self.my_map.startX = new_x
                    self.my_map.startY = new_y
                    if level == 1:
                        self.my_map.setTile(new_x,new_y,"stairUp",target=MapSwitch(targetName="school1",oldLoc=oldLoc))
                    else:
                        self.my_map.setTile(new_x,new_y,"stairUp",target=MapSwitch(targetName="dungeon{}".format(level-1),oldLoc=oldLoc))
                else:
                    if num_rooms == 1:
                        #second room means will go down
                        self.my_map.setTile(new_x+1,new_y,"stairDown",target=MapSwitch(targetName="dungeon{}".format(level+1),oldLoc=(self.my_map.startX+1,self.my_map.startY),generator=self))
                    #all rooms after the first:
                    #connect it to the previous room with a tunnel
                    
                    #center coordinates of previous room
                    (prev_x, prev_y) = rooms[num_rooms-1].center()
 
                    #draw a coin (random number that is either 0 or 1)
                    if random.randint(0, 1):
                        #first move horizontally, then vertically
                        self.create_h_tunnel(prev_x, new_x, prev_y, clear="rock")
                        self.create_v_tunnel(prev_y, new_y, new_x, clear="rock")
                    else:
                        #first move vertically, then horizontally
                        self.create_v_tunnel(prev_y, new_y, prev_x, clear="rock")
                        self.create_h_tunnel(prev_x, new_x, new_y, clear="rock")
 
                    #add some contents to this room, such as monsters
                    self.place_objects(new_room)
 
                #finally, append the new room to the list
                rooms.append(new_room)
                num_rooms += 1
        if True or num_rooms == 1:
            print("Hmm... we only have one room because of unlikely events or debugging")
            self.my_map.setTile(new_x+1,new_y,"stairDown",target=MapSwitch(targetName="dungeon{}".format(level+1),oldLoc=(self.my_map.startX+1,self.my_map.startY),generator=self))
        self.my_map.rooms = rooms
        self.my_map.num_rooms = num_rooms

        mapDict[name] = self.my_map
        return self.my_map
 
    def create_room(self, room):
        """ converts all room tiles to be non blocking """
        for x in range(room.x1 + 1, room.x2):
            for y in range(room.y1 + 1, room.y2):
                self.my_map.setTile(x,y,"floor")
 
    def place_objects(self, room):
        #choose random number of monsters
        num_monsters = random.randint(0, MAX_ROOM_MONSTERS)
        objects = self.my_map.objects
         
        for i in range(num_monsters):
            #choose random spot for this monster
            x = random.randint(room.x1+1, room.x2-1)
            y = random.randint(room.y1+1, room.y2-1)
 
 
            #only place it if the tile is not blocked
            if not self.my_map.is_blocked(x, y):
                if random.randint(0, 100) < 80:  #80% chance of getting an orc
                    #create an orc
                    fighter_component = Fighter(hp=10, defense=0, power=3, 
                                                death_function=monster_death)
                    ai_component = BasicMonster()
 
                    monster = GameObject(x, y, 'o', 'orc', colors.desaturated_green, self.my_map, blocks=True, fighter=fighter_component, ai=ai_component)
                else:
                    #create a troll
                    fighter_component = Fighter(hp=16, defense=1, power=4,
                                            death_function=monster_death)
                    ai_component = BasicMonster()
 
                    monster = GameObject(x, y, 'T', 'troll', colors.darker_green, self.my_map,
                    blocks=True, fighter=fighter_component, ai=ai_component)
 
                    objects.append(monster)
 
        #choose random number of items
        num_items = random.randint(0, MAX_ROOM_ITEMS)
 
        for i in range(num_items):
            #choose random spot for this item
            x = random.randint(room.x1+1, room.x2-1)
            y = random.randint(room.y1+1, room.y2-1)
 
            #only place it if the tile is not blocked
            if not self.my_map.is_blocked(x, y):
                dice = random.randint(0, 100)
                if dice < 70:
                    #create a healing potion (70% chance)
                    item_component = Item(use_function=cast_heal)
 
                    item = GameObject(x, y, '!', 'healing potion', 
                                      colors.violet, self.my_map, item=item_component)
 
                elif dice < 70+10:
                    #create a lightning bolt scroll (15% chance)
                    item_component = Item(use_function=cast_lightning)
 
                    item = GameObject(x, y, '#', 'scroll of lightning bolt', 
                                      colors.light_yellow, self.my_map, item=item_component)
 
                elif dice < 70+10+10:
                    #create a fireball scroll (10% chance)
                    item_component = Item(use_function=cast_fireball)
 
                    item = GameObject(x, y, '#', 'scroll of fireball', 
                                      colors.light_yellow, self.my_map, item=item_component)
 
                else:
                    #create a confuse scroll (15% chance)
                    item_component = Item(use_function=cast_confuse)
                    
                    item = GameObject(x, y, '#', 'scroll of confusion', 
                                      colors.light_yellow, self.my_map, item=item_component)
 
                objects.append(item)
                item.send_to_back()  #items appear below other objects
                
 
