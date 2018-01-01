Farming actions:
  add debug actions to skip a day
  look if it's hard to add details on timeouts
  planting seeds should decrement the number of seeds in inventory by one
  seeds should turn into bushes after X days
  bushes should sprout stuff after Y days
  add harvesting
  add watering
  add filling watering can

add ownership (or control) of plots

add hunger

add foodStore

BUGS:
  When selling stuff, selling 2nd item seems to reorder stuff??
  fix town creation so water in farms doesn't block front door
  fix town creation to make stones vs rocks in forest
  chopping tree doesn't change spot to dirt correctly (check also mining stone)

NICE TO HAVES:
  save/loading passes JSON through zip (or bzip or whatever)
  refactor more objects to provide a @classmethod load function
  refactor more objects to have common bases to reduce dupe code if possible
  display should include gold

add prices
add real store inventories
add minor economy sim?
add long-time-actions
refactor objects.py and models/*
add npcs
add talking to npcs
add friendships
add limits to inventory (and/or paginate inventory better :|)
add weather
add quests
refactor store/checkpoint/tbd to use common base class (which also handles reconstituting them?)
add attrs to items (and set/use them)
Dungeons have checkpoints
Dungeons reset on entry
Dungeons rebalanced (note that at deep enough levels, monsters scale too fast)
Redo how links work ... specifically, add links between maps vs remembering on object, because teleport breaks that... also I think name is adding extra 1 somewhere...
enhance mining (more stuff to mine)
make tiles be separate file, possibly as JSON?
add blacksmith items to create
add buying/selling metal and items
add upgrading items
add backpack upgrades / limits
add growing / picking
add day/night cycles
adjust start time to 7am, 1 September (Fall)?
add seasons
add moon cycles?
add debug time-turner
add bed
add sleeping
add hunger / eating
add money
add bank
add reading in library
add magic missile spell
add light spell
add resting
use mp/sp/hp/?? 
adjust light levels indoors/outdoors/dungeons/etc
add pet?
add pc stats
add pc backstory
add pc race?
add pc children?
add holidays
add boat buying/selling
add bulk items on boat
add overworld map
add checkpoint chains (as in: a dungeon set has checkpoints, a town may have checkpoints, there may be checkpoints on overworld to each town, etc.)
add treasure maps
add lat/lng device (levels of accuracy?)
add more towns
add cities??
add other terrains / stuff
add recovery from "death" ako KO
add difficulty levels
add scoring