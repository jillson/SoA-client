#!/usr/bin/env python3
 
import tdl
from tcod import image_load
from random import randint
import colors
import math
import textwrap

from gameconsts import *

from objects import *

from models.items.baseobject import GameCharacter
from models.items.itemfactory import Item as NewItem
from models.time import ScheduledItem, scheduler
from models.store import Store

from models.items.itemactions import *

print("Reminder: set self.explored to False when done debugging")


class MapSwitch:
    def __init__(self,targetName=None,generator=None,startX=None,startY=None):
        self.targetName = targetName
        self.generator = generator
        self.startX = startX
        self.startY = startY
    def save(self):
        rez = {}
        rez["targetName"] = self.targetName
        rez["startX"] = self.startX
        rez["startY"] = self.startY
        if self.generator:
            rez["generator"] = {"name": self.generator.Name}
        else:
            rez["generator"] = None
        return rez
    def switch(self,mapDict):
        print("Switching to",self.targetName)
        tMap = None
        if self.targetName and mapDict.get(self.targetName):
            tMap =  mapDict[self.targetName]
        else:
            if self.generator:
                tMap = self.generator.generate_map(self.targetName)
                if self.targetName:
                    mapDict[self.targetName] = tMap
        if not tMap:
            print("Warning, couldn't find {}".format(self.targetName))
            return None,0,0
        if self.startX == None:
            self.startX = tMap.startX
        if self.startY == None:
            self.startY = tMap.startY
        return tMap,self.startX,self.startY

class BaseGenerator:
    Name="BaseGenerator"
    def __init__(self,mapDict,basename="base",default_tile="rock",floor_tile="floor"):
        self.basename=basename
        self.default_tile = default_tile
        self.floor_tile = floor_tile
        self.mapDict = mapDict
    def save(self):
        return {"name": self.Name, "basename":self.basename}

    def load(self,rez):
        print("Do load")

    def createTile(self,rez):
        t = Tile(rez["name"],rez["blocked"],rez["block_sight"],rez["color"],rez["alt_color"],rez["char"])
        t.explored = rez["explored"]
        t.fg_color = rez["fg_color"]
        t.attrs = rez["attrs"]
        
        if rez["action"]:
            aType = rez["action"]["type"]
            if aType == "Store":
                print("TODO: store should be stored in map, not obliquely in a tile")
                t.action = Action(Store(rez["action"]["name"]))
                if rez["action"]["ownername"]:
                    print("Hmm, we need to look up owner by his name")
            elif aType == "Checkpoint":
                t.action = Action(Checkpoint())
            else:
                import pdb
                pdb.set_trace()
        if rez["target"]:
            generator = None
            target = rez["target"]
            if target["generator"]:
                generator = mapGenerators.get(target["generator"]["name"])
                if not generator:
                    print("Hmm, we may have to reconstitute this the hard way?",target["generator"])

            t.target = MapSwitch(startX=target["startX"],startY=target["startY"],targetName=target["targetName"],generator=generator)
        if rez["timeItems"]:
            import pdb
            pdb.set_trace()
            
        t.timeItems = [ScheduledItem.load(t,si) for si in rez["timeItems"]]
        return t

    def loadObject(self,o,myMap):
        if o.get("type","") == "item":
            function = None
            if o["function"]:
                function = itemActions.get(o["function"])
            return NewItem(o["name"],
                       o["x"],
                       o["y"],
                       o["char"],
                       o["color"],
                       o["blocks"],
                       function,
                       o["function"],
                       o["single"],
                       o["amt"])
        elif o.get("type","") in ["GameCharacter","GameObject"]:
            if o["fighter"]:
                if o["fighter"]["type"] == "Fighter":
                    fd = o["fighter"]
                    fighter = Fighter(hp=fd["hp"],defense=fd["defense"],power=fd["power"])
                    fighter.max_hp = fd["max_hp"]
                else:
                    import pdb
                    pdb.set_trace()
            else:
                fighter = None
            if o["ai"]:
                if o["ai"]["type"] == "BasicMonster":
                    ai = BasicMonster()
                else:
                    import pdb
                    pdb.set_trace()

            item = None
            return GameCharacter(o["x"],
                                 o["y"],
                                 o["char"],
                                 o["name"],
                                 o["color"],
                                 myMap,
                                 o["blocks"],
                                 fighter,
                                 ai,
                                 item,
                                 o["attrs"])

        print("Didn't know how to handle this object")
        import pdb
        pdb.set_trace()
        return None

                 
    def loadMap(self,rez,player):
        myMap = Map(width=rez["width"],height=rez["height"],init=False,mapDict=self.mapDict)
        myMap.objects = [self.loadObject(o,myMap) for o in rez["objects"]]
        if rez["pIndex"] > -1:
            myMap.objects.insert(rez["pIndex"],player)
        myMap.tiles = [[self.createTile(tileData) for tileData in row] for row in rez["tiles"]]
        myMap.attrs = rez["attrs"]
        myMap.name = rez["name"]
        myMap.startX = rez["startX"]
        myMap.startY = rez["startY"]
        return myMap
        
    def generate_map(self,name=None):
        if not name:
            name = self.basename + "1"
        if name and self.mapDict.get(name):
            return self.mapDict[name]
        
        self.my_map = Map(width=MAP_WIDTH, height=MAP_HEIGHT, default_tile=self.default_tile, mapDict=self.mapDict)
        self.my_map.name = name
        rooms = []
        num_rooms = 0

        level = int(name[len(self.basename):])
        
        for r in range(MAX_ROOMS):
            #random width and height
            w = random.randint(ROOM_MIN_SIZE, ROOM_MAX_SIZE)
            h = random.randint(ROOM_MIN_SIZE, ROOM_MAX_SIZE)
            #random position without going out of the boundaries of the map
            x = random.randint(0, MAP_WIDTH-w-1)
            y = random.randint(0, MAP_HEIGHT-h-1)
 
            #"Rect" class makes rectangles easier to work with
            new_room = Rect(x, y, w, h)
 
            #run through the other rooms and see if they intersect with this one
            failed = False
            for other_room in rooms:
                if new_room.intersect(other_room):
                    failed = True
                    break
 
            if not failed:
                #this means there are no intersections, so this room is valid
 
                #"paint" it to the map's tiles
                self.create_room(new_room)
 
                #center coordinates of new room, will be useful later
                (new_x, new_y) = new_room.center()
 
                if num_rooms == 0:
                    #this is the first room, where the player starts at
                    self.my_map.startX = new_x
                    self.my_map.startY = new_y
                    if level == 1:
                        self.my_map.setTile(new_x,new_y,"stairUp",target=MapSwitch(targetName="school1"))
                        self.my_map.setTile(new_x,new_y+2,"rune",action=Action(Checkpoint()))
                    else:
                        self.my_map.setTile(new_x,new_y,"stairUp",target=MapSwitch(targetName="{}{}".format(self.basename,level-1)))
                else:
                    if num_rooms == 1:
                        #second room means will go down
                        self.my_map.setTile(new_x+1,new_y,"stairDown",target=MapSwitch(targetName="{}{}".format(self.basename,level+1),generator=self))
                    #all rooms after the first:
                    #connect it to the previous room with a tunnel
                    
                    #center coordinates of previous room
                    (prev_x, prev_y) = rooms[num_rooms-1].center()
 
                    #draw a coin (random number that is either 0 or 1)
                    if random.randint(0, 1):
                        #first move horizontally, then vertically
                        self.create_h_tunnel(prev_x, new_x, prev_y, clear=self.default_tile)
                        self.create_v_tunnel(prev_y, new_y, new_x, clear=self.default_tile)
                    else:
                        #first move vertically, then horizontally
                        self.create_v_tunnel(prev_y, new_y, prev_x, clear=self.default_tile)
                        self.create_h_tunnel(prev_x, new_x, new_y, clear=self.default_tile)
 
                    #add some contents to this room, such as monsters
                    self.place_objects(new_room,level)
 
                #finally, append the new room to the list
                rooms.append(new_room)
                num_rooms += 1
        if True or num_rooms == 1:
            print("Hmm... we only have one room because of unlikely events or debugging")
            self.my_map.setTile(self.my_map.startX+1,self.my_map.startY,"stairDown",target=MapSwitch(targetName="{}{}".format(self.basename,level+1),generator=self))
        self.my_map.rooms = rooms
        self.my_map.num_rooms = num_rooms

        print("Hmm... do we end up setting this twice?")
        self.mapDict[name] = self.my_map
        return self.my_map
 
    def create_room(self, room):
        """ converts all room tiles to be non blocking """
        for x in range(room.x1 + 1, room.x2):
            for y in range(room.y1 + 1, room.y2):
                self.my_map.setTile(x,y,self.floor_tile)
    

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
 
    
    def create_h_tunnel(self, x1, x2, y,tile="road",clear=None):
        """ creates horizontal tunnel from x1 to x2 """
        for x in range(min(x1, x2), max(x1, x2) + 1):
            if not clear or self.my_map.getTile(x,y).name == clear:
                self.my_map.setTile(x,y,tile)
 
    def create_v_tunnel(self, y1, y2, x, tile="road",clear=None):
        """ creates vertical tunnel from y1 to y2 """
        for y in range(min(y1, y2), max(y1, y2) + 1):
            if not clear or self.my_map.getTile(x,y).name == clear:
                self.my_map.setTile(x,y,tile)

    def place_objects(self, room,level):
        print("Warning, basegenerator doesn't place_objects; override")
        return
    


class Tile:
    """ a tile of the map and its properties """
    def __init__(self, name, blocked, block_sight=None,color=None,alt_color=None,char=None):
        self.blocked = blocked
        self.name = name
        #all tiles start unexplored
        #debug
        self.explored = True
 
        #by default, if a tile is blocked, it also blocks sight
        if block_sight is None: 
            block_sight = blocked
        self.block_sight = block_sight

        self.fg_color = None

        self.color = color
        self.alt_color = alt_color
        self.char = char
        self.attrs = {}
        self.target = None
        self.action = None
        self.timeItems = []

    def save(self):
        rez = {}
        rez["alt_color"] = self.alt_color
        if self.action:
            rez["action"] = self.action.save()
        else:
            rez["action"] = None
        rez["attrs"] = self.attrs
        rez["block_sight"] = self.block_sight
        rez["blocked"] = self.blocked
        rez["char"] = self.char
        rez["color"] = self.color
        rez["explored"] = self.explored
        rez["fg_color"] = self.fg_color
        rez["name"] = self.name
        if self.timeItems:
            print("Saving {} timeItems".format(len(self.timeItems)))
        rez["timeItems"] = [si.save() for si in self.timeItems]
        if self.target:
            rez["target"] = self.target.save()
        else:
            rez["target"] = None
        return rez

    def pick(self):
        amt = random.randint(1,self.attrs["fruit"]+1)
        if amt > self.attrs["fruit"]:
            amt = self.attrs["fruit"]
        self.attrs["fruit"] -= amt
        if self.attrs["fruit"] == 0:
            self.fg_color = colors.green
            self.name = "shrub"
            self.attrs["seed"]["mature"] = self.attrs["seed"]["max_mature"]  
            scheduler.schedule(self,"nextDay",checkBush)
        return self.attrs["plant"]["name"],amt
    
    def getDescription(self):
        details = ",".join([str(x.function)+ "@" + str(x.time) for x in self.timeItems])
        if details:
            print("Details for tile",details)
        if self.attrs:
            return "{}({})".format(self.name,",".join([k for k,v in self.attrs.items() if v]))
        return self.name
    def convert(self,target):
        newTileG = tg.get(target)
        if newTileG:
            newTile = newTileG.generate()
            self.blocked = newTile.blocked
            self.block_sight = newTile.block_sight
            self.color = newTile.color
            self.alt_color = newTile.alt_color
            self.char = newTile.char
            self.attrs = newTile.attrs
            self.target = newTile.target
            self.action = newTile.action

class TileGenerator:
    def __init__(self,name,block_move,block_sight,color,alt_color,char):
        self.name = name
        self.block_move = block_move
        self.block_sight = block_sight
        self.color = color
        self.alt_color = alt_color
        self.char = char
    def generate(self):
        return Tile(self.name,self.block_move,self.block_sight,
                    self.color,self.alt_color,self.char)



tg = {"road":TileGenerator("road",False,False,colors.sepia,colors.light_sepia,"."),
      "sand":TileGenerator("sand",False,False,colors.lighter_sepia,colors.lightest_sepia,"."),
      "grass":TileGenerator("grass",False,False,colors.green,colors.light_green,"."),
      "dirt":TileGenerator("dirt",False,False,colors.light_sepia,colors.lighter_sepia,"."),
      "floor":TileGenerator("floor",False,False,colors.light_gray,colors.lighter_gray,"."),
      "stairUp":TileGenerator("stairUp",False,False,colors.light_gray,colors.lighter_gray,">"),
      "stairDown":TileGenerator("stairDown",False,False,colors.light_gray,colors.lighter_gray,"<"),
      "hwall":TileGenerator("hwall",True,False,colors.white,colors.lightest_grey,"-"),
      "vwall":TileGenerator("vwall",True,True,colors.white,colors.lightest_grey,"|"),
      "swall":TileGenerator("swall",True,True,colors.white,colors.lightest_grey,"/"),
      "bswall":TileGenerator("bswall",True,True,colors.white,colors.lightest_grey,"\\"),
      "door":TileGenerator("door",False,True,colors.light_grey,colors.lightest_grey,"+"),
      "water":TileGenerator("water",True,False,colors.light_blue,colors.lighter_blue,"~"),
      "air":TileGenerator("air",True,False,colors.lightest_blue,colors.lighter_blue," "),
      "fence":TileGenerator("fence",True,True,colors.dark_sepia,colors.darker_sepia,"="),
      "rock":TileGenerator("rock",True,True,colors.dark_grey,colors.darker_grey,"."),
      "tree":TileGenerator("tree",True,True,colors.dark_green,colors.darker_sepia,"T"),
      "stone":TileGenerator("stone",True,False,colors.dark_grey,colors.darker_grey,"*"),
      "gem":TileGenerator("gem",True,False,colors.light_blue,colors.lighter_blue,"*"),
      "register":TileGenerator("register",False,False,colors.light_grey,colors.grey,"#"),
      }

mapGenerators = {}

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
        #offsetW = meanW // 4
        #if offsetW > 0:
        #    meanW += randint(0,2*meanW)-meanW
        #offsetH = meanH // 4
        #if offsetH > 0:
        #    meanH += randint(0,2*meanH)-meanH
        self.width = meanW
        self.height = meanH



#TODO: pass in objects to start on map?
class Map:
    def __init__(self,width=MAP_WIDTH,height=MAP_HEIGHT,default_tile="grass",init=True,mapDict=None):
        #the list of objects on this map
        self.objects = [] #[player]
        self.attrs = {}
        self.width = width
        self.height = height
        self.startX = 0
        self.startY = 0
        self.mapDict = mapDict
        #fill map with default_tiles
        if init:
            self.tiles = [[ tg[default_tile].generate() for _ in range(self.height)] for _ in range(self.width)]

    def save(self,player):
        rez = {}
        rez["pIndex"] = -1
        if player in self.objects:
            rez["pIndex"] = self.objects.index(player)
        rez["tiles"] = [[tile.save() for tile in row] for row in self.tiles]
        rez["width"] = self.width
        rez["height"] = self.height
        rez["objects"] = [obj.save() for obj in self.objects if obj != player]
        rez["attrs"] = self.attrs
        rez["name"] = self.name
        rez["startX"] = self.startX
        rez["startY"] = self.startY
        return rez

    def load(self,rez):
        print("Do me load map")

    def enterSpace(self,obj,oldX,oldY):
        x,y=obj.x,obj.y
        tile = self.tiles[x][y]
        if tile.target:
            if obj in self.objects:
                self.objects.remove(obj)

            obj.previous[self.name] = (oldX,oldY)
            newMap,newX,newY = tile.target.switch(self.mapDict)
            obj.x,obj.y = obj.previous.get(newMap.name,(newX,newY))
            obj.current_map = newMap
            e = Event(type="teleport")
            e.map = newMap
            return e
        if tile.action:
            e = Event(type="action")
            e.action = tile.action
            return e
            
    def getWidth(self):
        return self.width

    def getHeight(self):
        return self.height

    def getTile(self,x,y):
        return self.tiles[x][y]

    def setTile(self,x,y,tileName,target=None,action=None):
        if x >= self.width or y >= self.height:
            print("Need to make {} < {} or {} < {}".format(x,self.width,y,self.height))
        t = tg.get(tileName)
        if not t:
            print("Warning, couldn't find {} in tile cache".format(tileName))
            t = tg.get("grass")
        try :
            self.tiles[x][y] = t.generate()
            self.tiles[x][y].target = target
            self.tiles[x][y].action = action
        except Exception as ex:
            print(ex)
            import pdb
            pdb.set_trace()
    def is_blocked(self, x, y):
        #first test the map tile
        if self.tiles[x][y].blocked:
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
        elif self.tiles[x][y].block_sight:
            return False
        else:
            return True
 

