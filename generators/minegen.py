#!/usr/bin/env python3
from __future__ import division

import tcod
import random 

from gameconsts import *

from objects import *

from generators.basegen import Rect, Building, Map, BaseGenerator, MapSwitch, mapDict, Action

class MineGenerator(BaseGenerator):
    def __init__(self,name="mine1"):
        super(MineGenerator,self).__init__(name,floor_tile="dirt")

    def choose_object(self,level):
        emptyRoll = random.randint(1,20)
        if emptyRoll > level:
            return None,None
        choice = random.randint(1,20*level)
        if choice < 20:
            return "stone","tile"
        if choice < 25:
            return "bug","badguy"
        if choice < 40:
            return "rock","tile"
        if choice < 45:
            return "orc","badguy"
        if choice < 60:
            return "gem","tile"
        if choice < 65:
            return "troll","badguy"
        if choice > 100:
            return "gem","tile"
        return self.choose_object(level + 5)
    
    def place_objects(self, room, level):
        for x in range(room.x1+2, room.x2-1):
            for y in range(room.y1+2, room.y2-1):
                if self.my_map.getTile(x,y).name == "dirt":
                    obj,objType = self.choose_object(level)
                    if objType == "tile":
                        self.my_map.setTile(x,y,obj)
                    elif objType == "item":
                        print("Create items next")
                        #create a fireball scroll (10% chance)
                        #item_component = Item(use_function=cast_fireball)
 
                        #item = GameObject(x, y, '#', 'scroll of fireball', 
                        #             colors.light_yellow, self.my_map, item=item_component)
                    elif objType == "badguy":
                        fighter_component = Fighter(hp=random.randint(level*3,level*6), defense=level-1, power=random.randint(level,level*2),death_function=monster_death)
                        ai_component = BasicMonster()
                        monster = GameObject(x, y, 'b', 'bug', colors.desaturated_green, self.my_map, blocks=True, fighter=fighter_component, ai=ai_component)
                        self.my_map.objects.append(monster)
 
                
 
