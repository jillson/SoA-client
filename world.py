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
from models.basegen import BaseGenerator, mapGenerators
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
        self.current_map = mapDict["town"]
        mapDict["school1"] = SchoolGenerator(mapDict).generate_map()
        mapDict["dungeon1"] = DungeonGenerator(mapDict).generate_map()
        mapDict["mine1"] = MineGenerator(mapDict).generate_map()
        
        self.player = Player(self.current_map.startX, self.current_map.startY, '@', 'player', colors.white, self.current_map)

        self.player.inventory.addByName("hoe")
        self.player.inventory.addByName("wheat seeds",amt=100)
        self.current_map.player = self.player
        self.current_map.objects.append(self.player)
        self.scheduler.reset()

    def load_game(self,name="quicksave.json"):
        self.mapDict = {} 
        mapDict = self.mapDict

        #remove move later
        import sys, traceback
        
        try:
            worldJson = json.loads(open(os.path.join("savegames",name)).read())
            self.player = Player(0,0, '@', 'player', colors.white, None)
            self.player.load(worldJson["player"])

            bg = BaseGenerator(mapDict)
            for k,v in worldJson["maps"].items():
                mapDict[k] = bg.loadMap(v,self.player)
            self.current_map = mapDict[worldJson["mymap"]]
            self.current_map.player = self.player
            self.player.current_map = self.current_map # UGH...
            #self.scheduler = scheduler
            self.scheduler.load(worldJson["scheduler"])
        except Exception as ex:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            traceback.print_exception(exc_type, exc_value, exc_traceback,
                                      limit=2, file=sys.stdout) 
            print("Error",ex)
                                   

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
            if v == self.current_map:
                worldJson["mymap"] = k
        with open(os.path.join("savegames",name),"wt") as f:
            f.write(json.dumps(worldJson))

        
    def getTime(self):
        return self.scheduler.getTime()
    def update(self,visible_tiles):
        for obj in self.current_map.objects:
            if obj.ai:
                obj.ai.take_turn(visible_tiles, self.player)
        #self.current_map.refresh(self.ticks % self.current_map.getWidth())
        self.scheduler.tick()

