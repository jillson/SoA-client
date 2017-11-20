#!/usr/bin/env python3
from __future__ import division

import tdl
import tcod
from random import randint
import colors
import math
import textwrap
import shelve

from gameconsts import *

from objects import *

from generators.basegen import Rect, Building, Map

class BaseGenerator:
    def __init__(self,stuff=None):
        pass
    
    def create_h_tunnel(self, x1, x2, y,tile="road"):
        """ creates horizontal tunnel from x1 to x2 """
        for x in range(min(x1, x2), max(x1, x2) + 1):
            self.my_map.setTile(x,y,tile)
 
    def create_v_tunnel(self, y1, y2, x, tile="road"):
        """ creates vertical tunnel from y1 to y2 """
        for y in range(min(y1, y2), max(y1, y2) + 1):
            self.my_map.setTile(x,y,"road")

    

class TownGenerator(BaseGenerator):
    def __init__(self):
        super(TownGenerator,self).__init__()

    def generate_map(self):
        """ For now, we generate a town where the school is at the top
            underneath there's a row of buildings
            underneath that there's a more compact row of houses
            to the left there's a column of farms (with houses)
            to the right along the building row there's the sea port
        """
        #TODO: name the roads using another generator (or q&d hack that glues way/street/drive/etc. to other names?)
        
        self.my_map = Map(width=100, height = 80, default_tile="grass")
        self.my_map.name = tcod.namegen_generate("mingos towns")
        self.rects = []

        school = Building("school",30,20)

        self.placeSchool(school)
        
        shop_list = [Building("store",10,10),
                     Building("tavern",8,8),
                     Building("library",6,6),
                     Building("blacksmith",5,10),
                     Building("market",6,3)]

        self.placeShops(shop_list)
        homes = [Building("house{}".format(i+1),5,5) for i in range(10)]

        self.placeHomes(homes)

        return self.my_map

    def placeShops(self,shops):
        x = 20
        y = 44

        for shop in shops:
            self.rects.append(Rect(x,y,shop.width,shop.height))
            self.drawRoom(x,y,shop)
            doorX = x+(shop.width//2) 
            self.my_map.setTile(doorX,y,"door")
            x += shop.width + 2
            
    def placeHomes(self,homes):
        x = 20
        y = 24

        for home in homes:
            self.rects.append(Rect(x,y,home.width,home.height))
            self.drawRoom(x,y,home)
            doorX = x+(home.width//2) 
            self.my_map.setTile(doorX,y+home.height-1,"door")
            x += home.width + 2
            
    def placeSchool(self,school):
        x = (self.my_map.getWidth() - school.width)//2
        y = 2
        self.rects.append(Rect(x,y,school.width,school.height))

        self.drawRoom(x,y,school)
        doorX = x+randint(0,school.width//2) 
        self.my_map.setTile(doorX,y+school.height-1,"door",target="school_map")
        
    def drawRoom(self,x,y,building):
        for offset in range(building.width-2):
            self.my_map.setTile(x+offset+1,y,"hwall")
            self.my_map.setTile(x+offset+1,y+building.height-1,"hwall")

        for offset in range(building.height-2):
            self.my_map.setTile(x,y+offset+1,"vwall")
            self.my_map.setTile(x+building.width-1,y+offset+1,"vwall")

        for x in range(building.width-2):
            for y in range(building.height-2):
                self.my_map.setTile(x+1,y+1,"floor")

        self.my_map.setTile(x,y,"swall")
        self.my_map.setTile(x+building.width-1,y,"bswall")
        self.my_map.setTile(x+building.width-1,y+building.height-1,"swall")
        self.my_map.setTile(x,y+building.height-1,"bswall")
 

 
