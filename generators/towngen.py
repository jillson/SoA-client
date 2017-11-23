#!/usr/bin/env python3
from __future__ import division

import tcod
import random 

from gameconsts import *

from objects import *

from generators.basegen import Rect, Building, Map, BaseGenerator, MapSwitch, mapDict


class SchoolGenerator(BaseGenerator):
    def __init__(self):
        super(SchoolGenerator,self).__init__()

    def generate_map(self,name="school1"):
        print("Generating {}".format(name))
        if name == "school1":
            if mapDict.get("school1"):
                print("Warning, not sure how/why we generated this multiple times")
                return mapDict.get(name)
            self.my_map = Map(width=MAP_WIDTH, height = MAP_HEIGHT, default_tile="floor")
        
            self.my_map.setTile(5,5,"stairUp",target=MapSwitch(targetName="school3",generator=self))
            self.my_map.startX = 10
            self.my_map.startY = 10
            mapDict[name] = self.my_map
        else:
            m = mapDict.get(name)
            if m:
                return m
            level = int(name[len("school"):])
            self.my_map = Map(width=MAP_WIDTH, height = MAP_HEIGHT, default_tile="floor")
        
            self.my_map.setTile(5,5,"stairDown",target=MapSwitch(targetName="school1",generator=self))
            self.my_map.startX = 10
            self.my_map.startY = 10
            mapDict[name] = self.my_map
                
        return self.my_map

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
        
        self.my_map = Map(width=MAP_WIDTH, height = MAP_HEIGHT, default_tile="grass")
        self.my_map.startX = 27
        self.my_map.startY = 31
        print("Breaking without changing default_tile to use a generator")
        self.my_map.name = tcod.namegen_generate("mingos towns")
        self.rects = []

        school = Building("school",30,20)

        self.placeSchool(school)
        
        shop_list = [Building("store",10,10),
                     Building("tavern",8,8),
                     Building("library",6,6),
                     Building("blacksmith",5,10)]

        random.shuffle(shop_list)

        self.placeShops(shop_list)
        homes = [Building("house{}".format(i+1),6,6) for i in range(10)]
        self.placeHomes(homes)

        self.placeFarms([Building("farm{}".format(i+1),15,15) for i in range(3)])
        self.placeForest()
        
        self.placeBoundary()
        
        return self.my_map

    def placeFarms(self,farms):
        x = 6
        y = 6
        for farm in farms:
            self.placeFarm(farm,x,y)
            y += farm.height+2

    def getFarmTile(self):
        roll = random.randint(1,20)
        if roll <= 8:
            return "grass"
        if roll <= 16:
            return "dirt"
        if roll <= 18:
            return "tree"
        if roll == 19:
            return "water"
        return "rock"

    def getForestTile(self):
        roll = random.randint(1,20)
        if roll <= 7:
            return "grass"
        if roll <= 10:
            return "dirt"
        if roll <= 19:
            return "tree"
        return "rock"

    def getBackgroundTile(self):
        roll = random.randint(1,20)
        if roll == 1:
            return "tree"
        return "grass"

    def placeForest(self):
        for x in range(14):
            for y in range(49):
                self.my_map.setTile(x+61,y+5,self.getForestTile())
    
    def placeFarm(self,farm,sx,sy):
        for x in range(farm.width):
            self.my_map.setTile(x+sx,sy,"fence")
            self.my_map.setTile(x+sx,sy+farm.height-1,"fence")
        for y in range(farm.height):
            self.my_map.setTile(sx,y+sy,"fence")
            self.my_map.setTile(sx+farm.width-1,y+sy,"fence")
        self.my_map.setTile(sx+farm.width-1,sy+farm.height//2,"door")
        self.my_map.setTile(sx+farm.width,sy+farm.height//2,"road")
        for x in range(farm.width-2):
            for y in range(farm.height-2):
                self.my_map.setTile(sx+x+1,sy+y+1,self.getFarmTile())
        
            
    def placeBoundary(self):
        for x in range(self.my_map.getWidth()):
            for offX in range(random.randint(1,3)):
                self.my_map.setTile(x,offX,"water")
            self.my_map.setTile(x,offX+1,"sand")
            
            for offX in range(random.randint(1,3)):
                self.my_map.setTile(x,self.my_map.getHeight()-1-offX,"water")
            self.my_map.setTile(x,self.my_map.getHeight()-2-offX,"sand")

        for y in range(self.my_map.getHeight()):
            for offX in range(random.randint(1,3)):
                self.my_map.setTile(offX,y,"water")
            self.my_map.setTile(offX+1,y,"sand")
            for offX in range(random.randint(1,3)):
                self.my_map.setTile(self.my_map.getWidth()-1-offX,y,"water")
            self.my_map.setTile(self.my_map.getWidth()-2-offX,y,"sand")
            

    def placeHomes(self,homes):
        x = 24
        y = 28

        for index, home in enumerate(homes):
            doorX = x+(home.width//2) 
            if index % 2 == 0:
                self.rects.append(Rect(x,y,home.width,home.height))
                self.drawRoom(x,y,home)
                self.my_map.setTile(doorX,y,"door")
                self.my_map.setTile(doorX,y-1,"road")
            else:
                self.rects.append(Rect(x,y+home.height+3,home.width,home.height))
                self.drawRoom(x,y+home.height+1,home)
                self.my_map.setTile(doorX,y+home.height*2,"door")
                self.my_map.setTile(doorX,y+home.height*2+1,"road")
                x += home.width + 1
            
    def placeShops(self,shops):
        x = 24
        y = 44

        for shop in shops:
            self.rects.append(Rect(x,y,shop.width,shop.height))
            self.drawRoom(x,y,shop)
            doorX = x+(shop.width//2) 
            self.my_map.setTile(doorX,y,"door")
            self.my_map.setTile(doorX,y-1,"road")
            x += shop.width + 2
            
    def placeSchool(self,school):
        x = 1 + (self.my_map.getWidth() - school.width)//2
        startX = x
        y = 5
        self.rects.append(Rect(x,y,school.width,school.height))

        self.drawRoom(x,y,school)
        doorX = x+random.randint(school.width//4,school.width//2) 
        self.my_map.setTile(doorX,y+school.height-1,"door",target="school_map")

        self.my_map.setTile(doorX,y+school.height,"road")
        startX -= 4
        for x in range(school.width+8):
            self.my_map.setTile(startX+x,y+school.height+1,"road")
        for x in range(school.width+8):
            self.my_map.setTile(startX+x,y+school.height+17,"road")
        for yOff in range(50):
            self.my_map.setTile(startX,4+yOff,"road")
            self.my_map.setTile(startX+37,4+yOff,"road")
            
        
    def drawRoom(self,x,y,building):
        for offset in range(building.width-2):
            self.my_map.setTile(x+offset+1,y,"hwall")
            self.my_map.setTile(x+offset+1,y+building.height-1,"hwall")

        for offset in range(building.height-2):
            self.my_map.setTile(x,y+offset+1,"vwall")
            self.my_map.setTile(x+building.width-1,y+offset+1,"vwall")

        for x_off in range(building.width-2):
            for y_off in range(building.height-2):
                self.my_map.setTile(x+1+x_off,y+1+y_off,"floor")

        self.my_map.setTile(x,y,"swall")
        self.my_map.setTile(x+building.width-1,y,"bswall")
        self.my_map.setTile(x+building.width-1,y+building.height-1,"swall")
        self.my_map.setTile(x,y+building.height-1,"bswall")
 

 
