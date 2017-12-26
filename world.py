#!/usr/bin/env python3

import json
import os
import tdl
import tcod
from random import randint
import colors

from models.towngen import TownGenerator, SchoolGenerator
from models.dungen import DungeonGenerator
from models.minegen import MineGenerator
from objects import *

from models.items.itemfactory import itemFactory
from models.time import scheduler

def load_name_generators():
    for f in os.listdir("names"):
        if f.find(".cfg") != -1:
            tcod.namegen_parse(os.path.join("names",f))
        
    

class World:
    def __init__(self):
        load_name_generators()
        self.scheduler = scheduler
        self.mapDict = {}
    def new_game(self):
        mapDict = self.mapDict
        mapDict["town"] = TownGenerator(mapDict).generate_map()
        self.my_map = mapDict["town"]
        mapDict["school1"] = SchoolGenerator(mapDict).generate_map()
        mapDict["dungeon1"] = DungeonGenerator(mapDict).generate_map()
        mapDict["mine1"] = MineGenerator(mapDict).generate_map()
        
        self.player = Player(self.my_map.startX, self.my_map.startY, '@', 'player', colors.white, self.my_map)

        self.player.inventory.addByName("hoe")
        self.player.inventory.addByName("wheat seeds",amt=100)
        self.my_map.player = self.player
        self.my_map.objects.append(self.player)
        self.scheduler.reset()

    def load_game(self,name="savegame.json"):
        self.mapDict = {} 
        mapDict = self.mapDict
        try:
            worldJson = json.loads(open(os.path.join("savegames",name)).read())
            bg = BaseGenerator(mapDict)
            for k,v in worldJson["maps"].items():
                mapDict[k] = bg.loadMap(v)
            self.my_map = mapDict[worldJson["mymap"]]
            self.player = Player(0,0, '@', 'player', colors.white, self.my_map)
            self.player.load(worldJson["player"],mapDict)
            #self.scheduler = scheduler
            self.scheduler.load(worldJson["scheduler"])
        except Exception as ex:
            print(ex)
            import sys
            sys.exit(1)
                                   

    def save_game(self,name="savegame.json"):
        worldJson = {}
        worldJson["player"] = self.player.save()
        worldJson["scheduler"] = self.scheduler.save()
        worldJson["maps"] = {}
        worldJson["mymap"] = "ERROR"
        for k,v in self.mapDict.items():
            worldJson["maps"][k] = v.save(self.player)
            #rint(worldJson["maps"][k])
            json.dumps(worldJson["maps"][k])
            if v == self.my_map:
                worldJson["mymap"] = k
        with open(os.path.join("savegames",name),"wt") as f:
            f.write(json.dumps(worldJson))

        
    def getTime(self):
        return self.scheduler.getTime()
    def update(self,visible_tiles):
        print("Check, we have %d objects" % (len(self.my_map.objects)))
        for obj in self.my_map.objects:
            if obj.ai:
                obj.ai.take_turn(visible_tiles, self.player)
        #self.my_map.refresh(self.ticks % self.my_map.getWidth())
        self.scheduler.tick()

