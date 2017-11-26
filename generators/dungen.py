#!/usr/bin/env python3
from __future__ import division

import tcod
import random 

from gameconsts import *

from objects import *

from generators.basegen import Rect, Building, Map, BaseGenerator, MapSwitch, mapDict, Action

class DungeonGenerator(BaseGenerator):
    def __init__(self,name="dungeon1"):
        super(DungeonGenerator,self).__init__(name)
    
    def place_objects(self, room, level):
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
                
 
