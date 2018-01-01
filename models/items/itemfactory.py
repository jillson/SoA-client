
import colors

from models.items.itemactions import *

class Item:
    def __init__(self,name,x,y,char,color,blocks,function,fName,single,amt):
        self.name = name
        self.char = char
        self.color = color
        self.blocks = blocks
        self.function = function
        self.single = single
        self.amt = amt
        self.x = x
        self.y = y
        self.attrs = {}
        self.functionName = fName
    def save(self):
        rez = {}
        rez["name"] = self.name
        rez["char"] = self.char
        rez["color"] = self.color
        rez["blocks"] = self.blocks
        rez["single"] = self.single
        rez["amt"] = self.amt
        rez["x"] = self.x
        rez["y"] = self.y
        rez["function"] = self.functionName
        rez["type"] = "item"
        return rez
        
    def use(self,owner,inv):
        if self.function:
            targetTile = owner.current_map.getTile(owner.x,owner.y)
            return self.function(self,owner,inv,targetTile)
        return
    def getName(self):
        if not self.single:
            return "{} {}".format(self.amt,self.name)
        return self.name
    def send_to_back(self):
        return
        objects = self.my_map.objects
        objects.remove(self)
        objects.insert(0, self)
 
    def draw(self,con, visible_tiles):
        #only show if it's visible to the player
        if (self.x, self.y) in visible_tiles:
            #draw the character that represents this object at its position
            con.draw_char(self.x, self.y, self.char, self.color, bg=None)
 
    def clear(self,con):
        #erase the character that represents this object
        con.draw_char(self.x, self.y, ' ', self.color, bg=None)


class ItemGenerator:
    def __init__(self,name,char="X",color=colors.white,blocks=True,function=None,single=True):
        self.name = name
        self.char = char
        self.color = color
        self.blocks = blocks
        self.functionName = function
        if function:
            self.function = itemActions.get(function)
        else:
            self.function = None
        self.single = single
    def getItem(self,amt=1,x=None,y=None):
        return Item(self.name,x,y,self.char,self.color,self.blocks,self.function,self.functionName,self.single,amt)

class ItemFactory:
    def __init__(self):
        self.factories = {}
        self.factories["default"] = ItemGenerator("default")
                                                  
    def register(self,name,char,color,blocks=False,function=None,single=True):
        self.factories[name] = ItemGenerator(name,char,color,blocks,function,single)
    def getItem(self,name,amt=1,x=None,y=None):
        ig = self.factories.get(name)
        if not ig:
            print("Warning, we had a request for {} that wasn't in our item inventory".format(name))
            ig = self.factories.get("default")
            ig.name = name
        return ig.getItem(amt,x,y)
            
itemFactory = ItemFactory()

itemFactory.register("scroll of lightning bolt", "#", colors.light_yellow)
itemFactory.register("scroll of fireball", "#", colors.light_red)

itemFactory.register("healing potion", "!", colors.light_red)
itemFactory.register("mana potion", "!", colors.light_blue)

itemFactory.register("acorn", "t", colors.light_sepia, single=False, function="plantFunc")
itemFactory.register("wheat seeds", "t", colors.light_yellow, single=False, function="plantFunc")

itemFactory.register("stone", "*", colors.grey, single=False)
itemFactory.register("gem", "*", colors.light_blue, single=False)
itemFactory.register("wood", "w", colors.dark_sepia, single=False)

itemFactory.register("hoe", "/", colors.lighter_grey, function = "hoeFunc")