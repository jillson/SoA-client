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

class Gui:
    def __init__(self):

        tdl.set_font('arial10x10.png', greyscale=True, altLayout=True)
        self.root = tdl.init(SCREEN_WIDTH, SCREEN_HEIGHT, title="Roguelike", fullscreen=False)
        tdl.setFPS(LIMIT_FPS)
        self.con = tdl.Console(MAP_WIDTH, MAP_HEIGHT)
        self.panel = tdl.Console(SCREEN_WIDTH, PANEL_HEIGHT)
        self.panel2 = tdl.Console(PANEL_2_WIDTH, PANEL_2_HEIGHT)
        self.visible_tiles = []
        self.fov_recompute = True
        self.bg_img = image_load('menu_background.png')
        self.game_msgs = []

    def render_bar(self, x, y, total_width, name, value, maximum, bar_color, back_color):
        #render a bar (HP, experience, etc). first calculate the width of the bar
        bar_width = int(float(value) / maximum * total_width)
        #render the background first
        self.panel.draw_rect(x, y, total_width, 1, None, bg=back_color)
        #now render the bar on top
        if bar_width > 0:
            self.panel.draw_rect(x, y, bar_width, 1, None, bg=bar_color)
        #finally, some centered text with the values
        text = name + ': ' + str(value) + '/' + str(maximum)
        x_centered = x + (total_width-len(text))//2
        self.panel.draw_str(x_centered, y, text, fg=colors.white, bg=None)

    def get_names_under_mouse(self, world_objects, tile):
        #return a string with the names of all objects under the mouse
        (x, y) = self.mouse_coord
 
        #create a list with the names of all objects at the mouse's coordinates and in FOV
        names = [obj.name for obj in world_objects
                 if obj.x == x and obj.y == y and (obj.x, obj.y) in self.visible_tiles]
        if tile:
            names.append(tile.name)
 
        names = ', '.join(names)  #join the names, separated by commas
        return str(self.mouse_coord) + ": " + names.capitalize()

    def clear_all(self,objects):
        tdl.flush()
        #erase all objects at their old locations, before they move
        for obj in objects:
            obj.clear(self.con)
 
    def render_all(self, world):
        player = world.player
        if self.fov_recompute:
            self.fov_recompute = False
            self.visible_tiles = tdl.map.quickFOV(player.x, player.y,
                                         world.my_map.is_visible_tile,
                                         fov=FOV_ALGO,
                                         radius=TORCH_RADIUS,
                                         lightWalls=FOV_LIGHT_WALLS)
 
            #go through all tiles, and set their background color according to the FOV
            for y in range(MAP_HEIGHT):
                for x in range(MAP_WIDTH):
                    visible = (x, y) in self.visible_tiles
                    t = world.my_map.my_map[x][y]
                    wall = world.my_map.my_map[x][y].block_sight
                    if not visible:
                        #if it's not visible right now, the player can only see it 
                        #if it's explored
                        if world.my_map.my_map[x][y].explored:
                            self.con.draw_char(x, y, t.char, fg=None, bg=t.alt_color)
                    else:
                        self.con.draw_char(x, y, t.char, fg=None, bg=t.color)
                        #since it's visible, explore it
                        t.explored = True
 
 
        #draw all objects in the list
        for obj in world.my_map.objects:
            if obj != player:
                obj.draw(self.con,self.visible_tiles)
        player.draw(self.con, self.visible_tiles)
        #blit the contents of "con" to the root console and present it
        self.root.blit(self.con, 0, 0, MAP_WIDTH, MAP_HEIGHT, 0, 0)

        ticks = world.ticks
        s = 6 * (ticks % 10)
        ticks = ticks // 10
        m = ticks % 60
        ticks = ticks // 60
        h = ticks % 12
        timeMsg="%2d:%02d:%02d"%(h,m,s)

        equipMsg = player.inventory.getEquippedStr()
        
        #render right side panel
        self.panel2.clear(fg=colors.white, bg=colors.black)
        self.panel2.draw_str(1,1,timeMsg, bg=None, fg=colors.white)
        self.panel2.draw_str(1,2,equipMsg, bg=None, fg=colors.white)
        #blit the contents of "panel" to the root console
                
        self.root.blit(self.panel2, MAP_WIDTH, 0, PANEL_2_WIDTH, PANEL_2_HEIGHT, 0, 0)

        #prepare to render the GUI panel
        self.panel.clear(fg=colors.white, bg=colors.black)
 
        #print the game messages, one line at a time
        y = 3
        for (line, color) in self.game_msgs:
            self.panel.draw_str(MSG_X, y, line, bg=None, fg=color)
            y += 1
 
        #show the player's stats
        self.render_bar(1, 1, BAR_WIDTH, 'HP', player.fighter.hp, player.fighter.max_hp, colors.light_red, colors.darker_red)

        self.render_bar(BAR_WIDTH+5, 1, BAR_WIDTH, 'MP', 10, 20, colors.light_blue, colors.darker_blue)

        self.render_bar(BAR_WIDTH * 2 +10, 1, BAR_WIDTH, 'SP', 18, 20, colors.light_grey, colors.darker_grey)

        self.panel.draw_str(1, 2, "Hello World", bg=None, fg=colors.light_gray)

        tx,ty = self.mouse_coord
        if world.my_map.is_visible_tile(tx,ty):
            tile = world.my_map.getTile(tx,ty)
        else:
            tile = None
 
        #display names of objects under the mouse
        self.panel.draw_str(1, 0, self.get_names_under_mouse(world.my_map.objects, tile), bg=None, fg=colors.light_gray)
 
        #blit the contents of "panel" to the root console
        self.root.blit(self.panel, 0, PANEL_Y, SCREEN_WIDTH, PANEL_HEIGHT, 0, 0)
 
    def message(self,new_msg, color = colors.white):
        #split the message if necessary, among multiple lines
        new_msg_lines = textwrap.wrap(new_msg, MSG_WIDTH)
 
        for line in new_msg_lines:
            #if the buffer is full, remove the first line to make room for the new one
            if len(self.game_msgs) == MSG_HEIGHT:
                del self.game_msgs[0]
 
            #add the new line as a tuple, with the text and the color
            self.game_msgs.append((line, color))
 
  
    def menu(self,header, options, width):
        if len(options) > 26:
            raise ValueError ('Cannot have a menu with more than 26 options.')
 
        #calculate total height for the header (after textwrap) and one line per option
        header_wrapped = textwrap.wrap(header, width)
        header_height = len(header_wrapped)
        if header == '':
            header_height = 0
        height = len(options) + header_height
 
        #create an off-screen console that represents the menu's window
        window = tdl.Console(width, height)
        bg = tdl.Console(width,height)
 
        #print the header, with wrapped text
        window.draw_rect(0, 0, width, height, None, fg=colors.white, bg=None)
        for i, line in enumerate(header_wrapped):
            window.draw_str(0, 0+i, header_wrapped[i])
 
        #print all the options
        y = header_height
        letter_index = ord('a')
        for option_text in options:
            text = '(' + chr(letter_index) + ') ' + option_text
            window.draw_str(0, y, text, bg=None)
            y += 1
            letter_index += 1
 
        #blit the contents of "window" to the root console
        x = SCREEN_WIDTH//2 - width//2
        y = SCREEN_HEIGHT//2 - height//2

        bg.blit(self.root, 0, 0, width, height, x, y, fg_alpha=1.0, bg_alpha=1.0)
        self.root.blit(window, x, y, width, height, 0, 0, fg_alpha=1.0, bg_alpha=0.7)
 
        #present the root console to the player and wait for a key-press
        tdl.flush()
        while True:
            key = tdl.event.key_wait()
            if key.char != '':
                break
        key_char = key.char
        if key_char == '':
            key_char = ' ' # placeholder
 
        if key.key == 'ENTER' and key.alt:
            #Alt+Enter: toggle fullscreen
            tdl.set_fullscreen(not tdl.get_fullscreen())

        #reset
        self.root.blit(bg, x, y, width, height, 0, 0, fg_alpha=1.0, bg_alpha=1.0)
 
        #convert the ASCII code to an index; if it corresponds to an option, return it
        index = ord(key_char) - ord('a')
        if index >= 0 and index < len(options):
            return index
        return None
 
    def inventory_menu(self,header, inventory):
        #show a menu with each item of the inventory as an option
        if len(inventory) == 0:
            options = ['Inventory is empty.']
        else:
            options = [item.getName() for item in inventory]
 
        index = self.menu(header, options, INVENTORY_WIDTH)
 
        #if an item was chosen, return it
        if index is None or len(inventory) == 0:
            return None
        return inventory[index].item
 
    def msgbox(self, text, width=50):
        self.menu(text, [], width)  #use menu() as a sort of "message box"
 
    def main_menu(self):
        #show the background image, at twice the regular console resolution
        self.bg_img.blit_2x(self.root, 0, 0)
            
        #show the game's title, and some credits!
        title = 'School of Adventure'
        center = (SCREEN_WIDTH - len(title)) // 2
        self.root.draw_str(center, SCREEN_HEIGHT//2-4, title, bg=None, fg=colors.light_yellow)
 
        title = 'By Carletronicon, based on tutorial by Jotaf'
        center = (SCREEN_WIDTH - len(title)) // 2
        self.root.draw_str(center, SCREEN_HEIGHT-2, title, bg=None, fg=colors.light_yellow)
        #show options and wait for the player's choice
        choice = self.menu('', ['Play a new game', 'Continue last game', 'Quit'], 24)
        return choice
 
 
