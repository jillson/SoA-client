#!/usr/bin/env python3
 
import tdl
from tcod import image_load
from random import randint
import colors
import math
import textwrap
import shelve

from gameconsts import *
from mapgen import DungeonGenerator
from objects import *

class Tile:
    """ a tile of the map and its properties """
    def __init__(self, blocked, block_sight=None):
        self.blocked = blocked
 
        #all tiles start unexplored
        self.explored = False
 
        #by default, if a tile is blocked, it also blocks sight
        if block_sight is None: 
            block_sight = blocked
        self.block_sight = block_sight

class World:
    def __init__(self):
        self.my_map = Map()
        #create object representing the player
        fighter_component = Fighter(hp=30, defense=2, power=5, 
                                death_function=player_death)
        self.player = Player(0, 0, '@', 'player', colors.white, self.my_map, blocks=True, fighter=fighter_component)
        self.my_map.player = self.player
        self.my_map.objects.append(self.player)
        dg = DungeonGenerator(self.my_map)

#TODO: pass in objects to start on map?
class Map:
    def __init__(self,width=MAP_WIDTH,height=MAP_HEIGHT):
        #the list of objects on this map
        self.objects = [] #[player]
 
        #fill map with "blocked" tiles
        self.my_map = [[ Tile(True)
                         for y in range(height) ]
                       for x in range(width) ]

        self.width = width
        self.height = height
    
    def is_blocked(self, x, y):
        #first test the map tile
        if self.my_map[x][y].blocked:
            return True
 
        #now check for any blocking objects
        for obj in self.objects:
            if obj.blocks and obj.x == x and obj.y == y:
                return True
 
        return False
    
    def is_visible_tile(self,x, y):
        if x >= self.width or x < 0:
            return False
        elif y >= self.height or y < 0:
            return False
        elif self.my_map[x][y].blocked == True:
            return False
        elif self.my_map[x][y].block_sight == True:
            return False
        else:
            return True
 
