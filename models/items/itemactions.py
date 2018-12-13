import random
import colors

from models.time import scheduler as timeObj


def revertHoe(tile):
    print("Hoed land reverted to previous")
    tile.attrs["hoed"] = False
    tile.char = " "
    
def revertWater(tile):
    tile.attrs["watered"] = False

def hoeFunc(item,owner,inv,targetTile):
    if targetTile.name != "dirt" and targetTile.name != "grass":
        print("Clang!")
        return
    if targetTile.attrs.get("seed"):
        targetTile.attrs["seed"] = None
    elif targetTile.attrs.get('hoed'):
        print("You can't hoe already hoed ground?")
        return
    targetTile.attrs["hoed"] = True
    targetTile.name = "dirt"
    targetTile.color = colors.light_sepia
    targetTile.char = "="
    timeObj.cancel(targetTile)
    timeObj.schedule(targetTile,random.randint(100,300),revertHoe)
    print("Todo: add hoe event?")
    return [True]

def checkBush(tile):
    if tile.attrs["plant"]["mature"] > 0:
        tile.attrs["plant"]["mature"] -= 1
        timeObj.schedule(tile,"nextDay",checkBush)
    else:
        tile.name = "plant"
        tile.fg_color = colors.red
        tile.attrs["fruit"] = random.randint(2,10)

def checkPlant(tile):
    if True or tile.attrs.get("watered"):
        if tile.attrs["seed"]["mature"] > 5:
            tile.attrs["seed"]["mature"] -= 1
            timeObj.schedule(tile,"nextDay",checkPlant)
        else:
            tile.attrs["plant"] = tile.attrs["seed"]
            tile.attrs["plant"]["mature"] = 2
            tile.attrs["seed"]["mature"] = tile.attrs["seed"]["max_mature"]
            tile.char = "t"
            tile.attrs["fruit"] = None
            tile.blocked = True
            timeObj.schedule(tile,"nextDay",checkBush)
            
def plantFunc(item,owner,inv,targetTile):
    if targetTile.attrs.get("seed"):
        print("Already has seed")
        return
    elif not targetTile.attrs.get('hoed'):
        print("Need to hoe first to plant")
        return
    targetTile.attrs["seed"] = {"name":item.name,"mature":item.attrs.get("matureTime",7),"max_mature":item.attrs.get("matureTime",7)}
    targetTile.char = ","
    timeObj.cancel(targetTile)
    timeObj.schedule(targetTile,"nextDay",checkPlant)
    return [True]

itemActions = {"hoeFunc":hoeFunc,
               "plantFunc":plantFunc,
               "checkBush":checkBush,
               "revertHoe":revertHoe,
               "revertWater":revertWater,
               "checkPlant":checkPlant}
               
    
