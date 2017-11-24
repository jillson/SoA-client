#!/usr/bin/env python3

import os
import tdl
import tcod
from random import randint
import colors

from generators.basegen import mapDict
from generators.towngen import TownGenerator, SchoolGenerator
from generators.dungen import DungeonGenerator
from objects import *

def load_name_generators():
    for f in os.listdir("names"):
        if f.find(".cfg") != -1:
            tcod.namegen_parse(os.path.join("names",f))
        
    

class World:
    def __init__(self):
        load_name_generators()
        mapDict["town"] = TownGenerator()
        self.my_map = mapDict["town"].generate_map()
        mapDict["school1"] = SchoolGenerator().generate_map()
        mapDict["dungeon1"] = DungeonGenerator().generate_map()
        #create object representing the player
        fighter_component = Fighter(hp=30, defense=2, power=5, 
                                death_function=player_death)
        self.player = Player(self.my_map.startX, self.my_map.startY, '@', 'player', colors.white, self.my_map, blocks=True, fighter=fighter_component)
        self.my_map.player = self.player
        self.my_map.objects.append(self.player)
        self.ticks = 0
    def update(self,visible_tiles):
        for obj in self.my_map.objects:
            if obj.ai:
                obj.ai.take_turn(visible_tiles, self.player)
        self.my_map.refresh(self.ticks % self.my_map.getWidth())
        self.ticks += 1

