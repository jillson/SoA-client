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

print("Reminder: set self.explored to False when done debugging")

mapDict = {}


class MapSwitch:
    def __init__(self,targetName=None,generator=None,startX=None,startY=None):
        self.targetName = targetName
        self.generator = generator
        self.startX = startX
        self.startY = startY
    def switch(self):
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
    def __init__(self,basename="base",default_tile="rock",floor_tile="floor"):
        self.basename=basename
        self.default_tile = default_tile
        self.floor_tile = floor_tile
        
    def generate_map(self,name=None):
        if not name:
            name = self.basename + "1"
        if name and mapDict.get(name):
            return mapDict[name]
        
        self.my_map = Map(width=MAP_WIDTH, height=MAP_HEIGHT, default_tile=self.default_tile)
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
                        self.my_map.setTile(new_x,new_y+2,"rune",action=Action(checkpointCheck))
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

        mapDict[name] = self.my_map
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

        self.color = color
        self.alt_color = alt_color
        self.char = char
        self.attrs = {}
        self.target = None
        self.action = None
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
    def __init__(self,width=MAP_WIDTH,height=MAP_HEIGHT,default_tile="grass"):
        #the list of objects on this map
        self.objects = [] #[player]

        self.width = width
        self.height = height
        #fill map with default_tiles
        
        self.my_map = [[ tg[default_tile].generate() for _ in range(self.height)] for _ in range(self.width)]

    def enterSpace(self,obj,oldX,oldY):
        x,y=obj.x,obj.y
        tile = self.my_map[x][y]
        if tile.target:
            if obj in self.objects:
                self.objects.remove(obj)

            obj.previous[self.name] = (oldX,oldY)
            newMap,newX,newY = tile.target.switch()
            obj.x,obj.y = obj.previous.get(newMap.name,(newX,newY))
            obj.my_map = newMap
            e = Event(type="teleport")
            e.map = newMap
            return e
        if tile.action:
            e = Event(type="action")
            e.action = tile.action
            return e
            

    def refresh(self,tick):
        pass
        
    def getWidth(self):
        return self.width

    def getHeight(self):
        return self.height

    def getTile(self,x,y):
        return self.my_map[x][y]

    def setTile(self,x,y,tileName,target=None,action=None):
        if x >= self.width or y >= self.height:
            print("Need to make {} < {} or {} < {}".format(x,self.width,y,self.height))
        t = tg.get(tileName)
        if not t:
            print("Warning, couldn't find {} in tile cache".format(tileName))
            t = tg.get("grass")
        try :
            self.my_map[x][y] = t.generate()
            self.my_map[x][y].target = target
            self.my_map[x][y].action = action
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
        elif self.my_map[x][y].block_sight:
            return False
        else:
            return True
 

