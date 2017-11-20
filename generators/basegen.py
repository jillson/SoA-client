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


class Tile:
    """ a tile of the map and its properties """
    def __init__(self, blocked, block_sight=None,color=None,char=None):
        self.blocked = blocked
 
        #all tiles start unexplored
        self.explored = False
 
        #by default, if a tile is blocked, it also blocks sight
        if block_sight is None: 
            block_sight = blocked
        self.block_sight = block_sight

        self.color = color
        self.char = char
        

class TileGenerator:
    def __init__(self,name,block_move,block_sight,color,char):
        self.name = name
        self.block_move = block_move
        self.block_sight = block_sight
        self.color = color
        self.char = char
    def generate(self):
        return Tile(self.block_move,self.block_sight,
                    self.color,self.char)



tg = {"road":TileGenerator("road",False,False,colors.sepia,"."),
      "grass":TileGenerator("grass",False,False,colors.green,"."),
      "dirt":TileGenerator("road",False,False,colors.light_sepia,"."),
      "floor":TileGenerator("floor",False,False,colors.light_gray,"."),
      "hwall":TileGenerator("hwall",False,False,colors.white,"-"),
      "vwall":TileGenerator("vwall",False,False,colors.white,"|"),
      "swall":TileGenerator("swall",False,False,colors.white,"/"),
      "bswall":TileGenerator("bswall",False,False,colors.white,"\\"),
      "door":TileGenerator("door",False,False,colors.white,"+"),
      "water":TileGenerator("water",False,False,colors.light_blue,"~")
      }

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
 
class Building:
    def __init__(self,name,meanW,meanH):
        self.name = name
        offsetW = meanW // 4
        if offsetW > 0:
            meanW += randint(0,2*meanW)-meanW
        offsetH = meanH // 4
        if offsetH > 0:
            meanH += randint(0,2*meanH)-meanH
        self.width = meanW
        self.height = meanH


#TODO: pass in objects to start on map?
class Map:
    def __init__(self,width=MAP_WIDTH,height=MAP_HEIGHT,default_tile="grass"):
        #the list of objects on this map
        self.objects = [] #[player]

        self.width = width
        self.height = height
        #fill map with default_tiles
        
        self.my_map = [[ tg[default_tile].generate() for _ in range(self.height)] for _ in range(self.width)]
        
    def getWidth(self):
        return self.width

    def getHeight(self):
        return self.height

    def setTile(self,x,y,tileName,target=None):
        if x >= self.width or y >= self.height:
            print("Need to make {} < {} or {} < {}".format(x,self.width,y,self.height))
        t = tg.get(tileName)
        if not t:
            print("Warning, couldn't find {} in tile cache".format(tileName))
            t = tg.get("grass")
        try :
            self.my_map[x][y] = t.generate()
            self.my_map[x][y].target = target
        except:
            import pdb
            pdb.set_trace()
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
 

