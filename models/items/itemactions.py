import random

from models.time import scheduler as timeObj

def revertHoe(tile):
    tile.attrs["hoed"] = False
    targetTile.char = " "
    
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
    targetTile.char = "="
    timeObj.cancel(targetTile)
    timeObj.schedule(targetTile,random.randint(100,300),revertHoe)
    print("Todo: add hoe event?")

def checkPlant(tile):
    if True or tile.attrs.get("watered"):
        if tile.attrs["seed"]["mature"] > 0:
            tiles.attrs["seed"]["mature"] -= 1
            scheduler.schedule(tile,"nextDay",checkPlant)
        else:
            tile.attrs["plant"] = tiles.attrs["seed"]
            tile.attrs["seed"] = None
            targetTile.char = "t"
            
def plantFunc(item,owner,inv,targetTile):
    if targetTile.attrs.get("seed"):
        print("Already has seed")
        return
    elif not targetTile.attrs.get('hoed'):
        print("Need to hoe first to plant")
        return
    targetTile.attrs["seed"] = {"name":item.name,"mature":item.attrs.get("matureTime",7)}
    targetTile.char = ","
    timeObj.cancel(targetTile)
    timeObj.schedule(targetTile,"nextDay",checkPlant)
