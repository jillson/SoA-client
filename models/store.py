#!/usr/bin/env python3
 

from gameconsts import *
from objects import *

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
        if choice == 0:
            item = GameObject(0,0,'t', 'Acorn', 
                              colors.light_sepia, player.my_map,
                              item=Item(use_function=cast_confuse))
            price = 50
        elif choice == 1:
            item = GameObject(0,0,'t', 'Wheat Seeds', 
                              colors.light_yellow, player.my_map,item=Item())
            price = 10
        elif choice == 2:
            item = GameObject(0,0,'*', 'stone', 
                              colors.grey, player.my_map,item=Item(single=False))
            price = 1
        elif choice == 3:
            item = GameObject(0,0,'*', 'gem', 
                              colors.light_blue, player.my_map,item=Item(single=False))
            price = 1000
        else:
            return
        return player.inventory.buy(item,price)
    def sell(self,player,gui):
        choice = gui.menu("You have {} gold".format(player.inventory.gold),
                          ["{}{}".format(x.name,not x.item.single and "({})".format(x.item.amt) or "") for x in player.inventory.asList()],
                          INVENTORY_WIDTH)
        if choice == 0 or choice:
            try:
                item = player.inventory.asList()[choice]
            except IndexError:
                return
            return player.inventory.sell(item.name,random.randint(1,100),1)
        else:
            return    
                              
        
