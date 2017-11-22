#!/usr/bin/env python3
 
import tdl
from tcod import image_load
import random
import colors
import math
import textwrap
import shelve

from gameconsts import *

visible_tiles = []
 
class GameObject:
    #this is a generic object: the player, a monster, an item, the stairs...
    #it's always represented by a character on screen.
    def __init__(self, x, y, char, name, color, my_map, blocks=False, 
                 fighter=None, ai=None, item=None):
        self.x = x
        self.y = y
        self.char = char
        self.color = color
        self.name = name
        self.blocks = blocks
        self.fighter = fighter
        self.my_map = my_map
 
        if self.fighter:  #let the fighter component know who owns it
            self.fighter.owner = self
 
        self.ai = ai
        if self.ai:  #let the AI component know who owns it
            self.ai.owner = self
 
        self.item = item
        if self.item:  #let the Item component know who owns it
            self.item.owner = self
 
    def move(self, dx, dy):
        #move by the given amount, if the destination is not blocked
        if not self.my_map.is_blocked(self.x + dx, self.y + dy):
            self.x += dx
            self.y += dy

    def getName(self):
        if self.item and not self.item.single:
            return "{} {}".format(self.item.amt,self.name)
        return self.name
 
    def move_towards(self, target_x, target_y):
        #vector from this object to the target, and distance
        dx = target_x - self.x
        dy = target_y - self.y
        distance = math.sqrt(dx ** 2 + dy ** 2)
 
        #normalize it to length 1 (preserving direction), then round it and
        #convert to integer so the movement is restricted to the map grid
        dx = int(round(dx / distance))
        dy = int(round(dy / distance))
        self.move(dx, dy)
 
    def distance_to(self, other):
        #return the distance to another object
        dx = other.x - self.x
        dy = other.y - self.y
        return math.sqrt(dx ** 2 + dy ** 2)
 
    def distance(self, x, y):
        #return the distance to some coordinates
        return math.sqrt((x - self.x) ** 2 + (y - self.y) ** 2)
 
    def send_to_back(self):
        #make this object be drawn first, so all others appear above it if 
        #they're in the same tile.
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


class Player(GameObject):
    def __init__(self, x, y, char, name, color, my_map, blocks=False, 
                 fighter=None, ai=None, item=None):
        super(Player, self).__init__(x,y,char,name,color,my_map,blocks,fighter,ai,item)
        self.inventory = []
        self.interactionMap = {"tree":self.chop,"rock":self.mine,"water":self.water,"plant":self.pick}
    def handleInteraction(self,tile):
        self.interactionMap.get(tile.name,self.default)(tile)
    def addItem(self,item):
        if item.item.single:
            self.inventory.append(item)
        else:
            for i in self.inventory:
                if i.name == item.name and i.item.amt < 100:
                    i.item.amt += item.item.amt
                    if i.item.amt > 100:
                        item.item.amt = i.item.amt % 100
                        i.item.amt = 100
                    else:
                        return
            self.inventory.append(item)
    def chop(self,tile):
        print("You summon a magic axe until I implement inventory checking")
        attack = random.randint(1,20)
        if attack < 5:
            print("You swing and ... miss")
            return
        dmg = random.randint(0,500)
        tile.attrs["hp"] = tile.attrs.get("hp",20) - dmg
        if tile.attrs["hp"] <= 0:
            num = random.randint(1,3) + random.randint(1,3)
            tile.convert("dirt")
            self.addItem(GameObject(self.x,self.y,'W','wood',colors.dark_sepia, self, item=Item(amt=num,single=False)))
        pass
    def mine(self,tile):
        pass
    def water(self,tile):
        pass
    def pick(self,tile):
        pass
    def default(self,tile):
        print("Bonk, you tried to walk into a ",tile.name)

        
class Fighter:
    #combat-related properties and methods (monster, player, NPC).
    def __init__(self, hp, defense, power, death_function=None):
        self.max_hp = hp
        self.hp = hp
        self.defense = defense
        self.power = power
        self.death_function = death_function
 
    def take_damage(self, damage):
        #apply damage if possible
        if damage > 0:
            self.hp -= damage
 
            #check for death. if there's a death function, call it
            if self.hp <= 0:
                function = self.death_function
                if function is not None:
                    function(self.owner)
 
    def attack(self, target):
        #a simple formula for attack damage
        damage = self.power - target.fighter.defense
 
        if damage > 0:
            #make the target take some damage
            print(self.owner.name.capitalize() + ' attacks ' + target.name + 
                  ' for ' + str(damage) + ' hit points.')
            target.fighter.take_damage(damage)
        else:
            print(self.owner.name.capitalize() + ' attacks ' + target.name + 
                  ' but it has no effect!')
 
    def heal(self, amount):
        #heal by the given amount, without going over the maximum
        self.hp += amount
        if self.hp > self.max_hp:
            self.hp = self.max_hp
 
class BasicMonster:
    #AI for a basic monster.
    def take_turn(self):
        #a basic monster takes its turn. If you can see it, it can see you
        monster = self.owner
        if (monster.x, monster.y) in visible_tiles:
 
            #move towards player if far away
            if monster.distance_to(player) >= 2:
                monster.move_towards(player.x, player.y)
 
            #close enough, attack! (if the player is still alive.)
            elif player.fighter.hp > 0:
                monster.fighter.attack(player)
 
class ConfusedMonster:
    #AI for a temporarily confused monster (reverts to previous AI after a while).
    def __init__(self, old_ai, num_turns=CONFUSE_NUM_TURNS):
        self.old_ai = old_ai
        self.num_turns = num_turns
 
    def take_turn(self):
        if self.num_turns > 0:  #still confused...
            #move in a random direction, and decrease the number of turns confused
            self.owner.move(random.randint(-1, 1), random.randint(-1, 1))
            self.num_turns -= 1
 
        else:  
            #restore the previous AI (this one will be deleted because it's not 
            #referenced anymore)
            self.owner.ai = self.old_ai
            print('The ' + self.owner.name + ' is no longer confused!', colors.red)
 
class Item:
    #an item that can be picked up and used.
    def __init__(self, use_function=None, single=True, amt=1):
        self.use_function = use_function
        self.amt = amt
        self.single = single
 
    def pick_up(self,inventory,objects):
        #add to the player's inventory and remove from the map
        if len(inventory) >= 26:
            print('Your inventory is full, cannot pick up ' + 
                    self.owner.name + '.', colors.red)
        else:
            inventory.append(self.owner)
            objects.remove(self.owner)
            print('You picked up a ' + self.owner.name + '!', colors.green)
 
    def drop(self, inventory, objects, player):
        #add to the map and remove from the player's inventory. also, place it at the player's coordinates
        objects.append(self.owner)
        inventory.remove(self.owner)
        self.owner.x = player.x
        self.owner.y = player.y
        print('You dropped a ' + self.owner.name + '.', colors.yellow)
 
    def use(self, inventory):
        #just call the "use_function" if it is defined
        if self.use_function is None:
            print('The ' + self.owner.name + ' cannot be used.')
        else:
            if self.use_function() != 'cancelled':
                inventory.remove(self.owner)  #destroy after use, unless it was 
                                              #cancelled for some reason
 
def player_death(player):
    #the game ended!
    global game_state
    print('You died!', colors.red)
    game_state = 'dead'
 
    #for added effect, transform the player into a corpse!
    player.char = '%'
    player.color = colors.dark_red
 
def monster_death(monster):
    #transform it into a nasty corpse! it doesn't block, can't be
    #attacked and doesn't move
    print(monster.name.capitalize() + ' is dead!', colors.orange)
    monster.char = '%'
    monster.color = colors.dark_red
    monster.blocks = False
    monster.fighter = None
    monster.ai = None
    monster.name = 'remains of ' + monster.name
    monster.send_to_back()
 
 
def cast_heal():
    #heal the player
    if player.fighter.hp == player.fighter.max_hp:
        print('You are already at full health.', colors.red)
        return 'cancelled'
 
    print('Your wounds start to feel better!', colors.light_violet)
    player.fighter.heal(HEAL_AMOUNT)
 
def cast_lightning():
    #find closest enemy (inside a maximum range) and damage it
    monster = closest_monster(LIGHTNING_RANGE)
    if monster is None:  #no enemy found within maximum range
        print('No enemy is close enough to strike.', colors.red)
        return 'cancelled'
 
    #zap it!
    print('A lighting bolt strikes the ' + monster.name + ' with a loud ' +
            'thunder! The damage is ' + str(LIGHTNING_DAMAGE) + ' hit points.', 
            colors.light_blue)
 
    monster.fighter.take_damage(LIGHTNING_DAMAGE)
 
def cast_confuse():
    #ask the player for a target to confuse
    print('Left-click an enemy to confuse it, or right-click to cancel.', 
            colors.light_cyan)
    monster = target_monster(CONFUSE_RANGE)
    if monster is None:
        print('Cancelled')
        return 'cancelled'
 
    #replace the monster's AI with a "confused" one; after some turns it will 
    #restore the old AI
    old_ai = monster.ai
    monster.ai = ConfusedMonster(old_ai)
    monster.ai.owner = monster  #tell the new component who owns it
    print('The eyes of the ' + monster.name + ' look vacant, as he starts to ' +
            'stumble around!', colors.light_green)
 
def cast_fireball():
    #ask the player for a target tile to throw a fireball at
    print('Left-click a target tile for the fireball, or right-click to ' +
            'cancel.', colors.light_cyan)
 
    (x, y) = target_tile()
    if x is None: 
        print('Cancelled')
        return 'cancelled'
    print('The fireball explodes, burning everything within ' + 
            str(FIREBALL_RADIUS) + ' tiles!', colors.orange)
 
    for obj in world.my_map.objects:  #damage every fighter in range, including the player
        if obj.distance(x, y) <= FIREBALL_RADIUS and obj.fighter:
            print('The ' + obj.name + ' gets burned for ' + 
                    str(FIREBALL_DAMAGE) + ' hit points.', colors.orange)
 
            obj.fighter.take_damage(FIREBALL_DAMAGE)
 
