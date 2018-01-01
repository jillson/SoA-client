#!/usr/bin/env python3
 
import tdl
import os
from tcod import image_load
from random import randint
import colors
import math
import textwrap
import shelve

from gameconsts import *

from world import World
from gui import Gui

from objects import *



class Controller:
    def __init__(self):
        self.gui = Gui()
        self.world = World()

        while not tdl.event.is_window_closed():
            choice = self.gui.main_menu()
            if choice == 0:  #new game
                self.new_game()
                self.play_game()
                break
            if choice == 1:  #load last game
                try:
                    self.load_game()
                except:
                    self.gui.msgbox('\n No saved game to load.\n', 24)
                    continue
                self.play_game()
            elif choice == 2:  #quit
                break
 
    def player_move_or_interact(self, dx, dy):
        """ This should probably be part of the player class """
        player = self.world.player
        #the coordinates the player is moving to/attacking
        x = player.x + dx
        y = player.y + dy
 
        #try to find an attackable object there
        target = None
        for obj in self.world.current_map.objects:
            if obj.x == x and obj.y == y:
                target = obj
                break
 
        #attack if target found, move otherwise
        if target is not None:
            if obj.fighter:
                return player.fighter.attack(target)

        newx = player.x + dx
        newy = player.y + dy
        if not self.world.current_map.is_blocked(newx,newy):
            event = player.move(dx, dy)
            if event:
                if event.type == "teleport":
                    self.world.current_map = event.map
                    if player not in event.map.objects:
                        event.map.objects.append(player)
                elif event.type == "action":
                    actionResult = event.action.run(player,self.gui)
                    print(actionResult)
            self.gui.fov_recompute = True
        else:
            blockingTile = self.world.current_map.getTile(newx,newy)
            print("You ran into",blockingTile.name)
            player.handleInteraction(blockingTile)
        

    def handle_keys(self):
        player = self.world.player
        keypress = False
        for event in tdl.event.get():
            if event.type == 'KEYDOWN':
                user_input = event
                keypress = True
            if event.type == 'MOUSEMOTION':
                self.gui.mouse_coord = event.cell
 
        if not keypress:
            return 'didnt-take-turn' #TODO: Add to tutorial
 
        if user_input.key == 'ENTER' and user_input.alt:
            #Alt+Enter: toggle fullscreen
            tdl.set_fullscreen(not tdl.get_fullscreen())
 
        elif user_input.key == 'ESCAPE':
            return 'exit'  #exit game

        elif user_input.text == '~':
            import pdb
            pdb.set_trace()
        elif user_input.text == 'l':
            print ("Debug, waiting a day")
            return 'wait a day'
        else:
            print("Huh,",user_input.text)
 
        if self.game_state == 'playing':
            #movement keys
            if user_input.key == 'UP':
                self.player_move_or_interact(0, -1)
 
            elif user_input.key == 'DOWN':
                self.player_move_or_interact(0, 1)
 
            elif user_input.key == 'LEFT':
                self.player_move_or_interact(-1, 0)
 
            elif user_input.key == 'RIGHT':
                self.player_move_or_interact(1, 0)
            else:
                #test for other keys
                if user_input.text == 'g':
                    #pick up an item
                    for obj in self.world.current_map.objects:  #look for an item in the player's tile
                        if obj.x == player.x and obj.y == player.y and obj.item:
                            obj.item.pick_up(self.world.player.inventory, self.world.current_map.objects)
                            break


                if user_input.text == 'e':
                    #show the inventory; if an item is selected, equip it
                    chosen_item = self.gui.inventory_menu('Press the key next to an item to ' +
                                                          'equip it, or any other to cancel.\n',self.world.player.inventory.asList())
                    if chosen_item is not None:
                        self.world.player.inventory.equip(chosen_item)

                if user_input.text == 'u':
                    self.world.player.inventory.use()

                if user_input.text == 'i':
                    #show the inventory; if an item is selected, use it
                    chosen_item = self.gui.inventory_menu('Press the key next to an item to ' +
                                                          'use it, or any other to cancel.\n',self.world.player.inventory.asList())
                    if chosen_item is not None:
                        self.world.player.inventory.use(chosen_item)
 
                if user_input.text == 'd':
                    #show the inventory; if an item is selected, drop it
                    chosen_item = self.gui.inventory_menu('Press the key next to an item to' + 
                                                          'drop it, or any other to cancel.\n',self.world.player.inventory.asList())
                    if chosen_item is not None:
                        self.world.player.inventory.drop(chosen_item)
 
                return 'didnt-take-turn'
  

    def target_tile(self, max_range=None):
        #return the position of a tile left-clicked in player's FOV (optionally in 
        #a range), or (None,None) if right-clicked.
        while True:
            #render the screen. this erases the inventory and shows the names of
            #objects under the mouse.
            tdl.flush()
 
            clicked = False
            for event in tdl.event.get():
                if event.type == 'MOUSEMOTION':
                    self.gui.mouse_coord = event.cell
                if event.type == 'MOUSEDOWN' and event.button == 'LEFT':
                    clicked = True
                elif ((event.type == 'MOUSEDOWN' and event.button == 'RIGHT') or 
                      (event.type == 'KEYDOWN' and event.key == 'ESCAPE')):
                    return (None, None)
            render_all(self.world)
 
            #accept the target if the player clicked in FOV, and in case a range is 
            #specified, if it's in that range
            x = self.gui.mouse_coord[0]
            y = self.gui.mouse_coord[1]
            if (clicked and mouse_coord in visible_tiles and
                (max_range is None or player.distance(x, y) <= max_range)):
                return self.gui.mouse_coord
 
    def target_monster(self,max_range=None):
        #returns a clicked monster inside FOV up to a range, or None if right-clicked
        while True:
            (x, y) = target_tile(max_range)
            if x is None:  #player cancelled
                return None
            
            #return the first clicked monster, otherwise continue looping
            for obj in self.world.current_map.objects:
                if obj.x == x and obj.y == y and obj.fighter and obj != self.world.player:
                    return obj
 
    def closest_monster(self,max_range):
        #find closest enemy, up to a maximum range, and in the player's FOV
        closest_enemy = None
        closest_dist = max_range + 1  #start with (slightly more than) maximum range
        
        for obj in self.world.current_map.objects:
            if obj.fighter and not obj == self.world.player and (obj.x, obj.y) in self.world.visible_tiles:
                #calculate distance between this object and the player
                dist = player.distance_to(obj)
                if dist < closest_dist:  #it's closer, so remember it
                    closest_enemy = obj
                    closest_dist = dist
        return closest_enemy
  
    def load_game(self):
        self.world.load_game()
        self.world.current_map.con = self.gui.con
        self.game_state = 'playing'
        self.gui.message('Welcome back',colors.green) 
    def new_game(self):
        self.world.new_game()
        self.world.current_map.con = self.gui.con
        #self.world.save_game("testing.json")
        print("Reminder: my_map shouldn't have con... should be called by controller passing in con or some other way")
        self.game_state = 'playing'
         #a warm welcoming message!
        self.gui.message('You celebrate your 9th birthday by enrolling in the [Insert Town Name] School for Adventure.', colors.blue)
 
    def play_game(self):
        player_action = None
        self.gui.mouse_coord = (0, 0)
        self.gui.fov_recompute = True
        self.gui.con.clear() #unexplored areas start black (which is the default background color)
 
        while not tdl.event.is_window_closed():
 
            #draw all objects in the list
            self.gui.render_all(self.world)
            self.gui.clear_all(self.world.current_map.objects)
            
 
            #handle keys and exit game if needed
            player_action = self.handle_keys()
            if player_action == 'exit':
                #save_game()
                break
 
            #let monsters take their turn
            if self.game_state == 'playing' and player_action != 'didnt-take-turn':
                if player_action == 'wait a day':
                    for _ in range(10*60*24):
                        self.world.update(self.gui.visible_tiles)
                else:
                    self.world.update(self.gui.visible_tiles)


if __name__ == "__main__":
    c = Controller()
    c.world.save_game("quicksave.json")
    print("Goodbye")
