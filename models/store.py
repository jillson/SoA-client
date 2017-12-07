#!/usr/bin/env python3
 

from gameconsts import *
from objects import *
from models.items.itemfactory import itemFactory

#from generators.basegen import Action

class StoreBaseGenerator:
    def __init__(self):
        self.stores = {}
    def generate_store(self,map,x,y,name,owner=None):
        if not self.stores.get(name):
            self.stores[name] = Store(name,owner)
        map.setTile(x,y,"register",action=Action(self.stores[name].interact))
        return self.stores[name]
    

class Store:
    def __init__(self,name,owner=None):
        self.name = name
        self.owner = owner
        self.ownername = ""
        if self.owner:
            self.ownername = self.owner.name
    def interact(self,player,gui):
        while True:
            choice = gui.menu("Welcome to {}'s Store {}".format(self.ownername or "Noone",self.name), ["Buy","Sell"], INVENTORY_WIDTH)
            cmd = {0:self.buy,1:self.sell}.get(choice)
            if cmd:
                while cmd(player,gui):
                    pass
            else:
                break
    def buy(self,player,gui):
        choice = gui.menu("You have {} gold".format(player.inventory.gold),
                          ["Acorn (50gp)",
                           "Wheat Seeds (10gp)",
                           "Stone (1gp)",
                           "Gem (1000gp)"], INVENTORY_WIDTH)

        v = {0:("acorn",50),
             1:("wheat seeds",10),
             2:("stone",1),
             3:("gem",1000)}.get(choice)
        if not v:
            return
        item,price = v
        return player.inventory.buy(item,price)
    def sell(self,player,gui):
        choice = gui.menu("You have {} gold".format(player.inventory.gold),
                          ["{}{}".format(x.name,not x.single and "({})".format(x.amt) or "") for x in player.inventory.asList()],
                          INVENTORY_WIDTH)
        if choice == 0 or choice:
            try:
                item = player.inventory.asList()[choice]
            except IndexError:
                return
            return player.inventory.sell(item.name,random.randint(1,100),1)
        else:
            return    
                              
        
