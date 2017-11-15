#!/usr/bin/env python3
 
import tdl
from tcod import image_load
from random import randint
import colors
import math
import textwrap
import shelve

from gameconsts import *

from world import World
from objects import *

world = None

def render_bar(x, y, total_width, name, value, maximum, bar_color, back_color):
    #render a bar (HP, experience, etc). first calculate the width of the bar
    bar_width = int(float(value) / maximum * total_width)
 
    #render the background first
    panel.draw_rect(x, y, total_width, 1, None, bg=back_color)
 
    #now render the bar on top
    if bar_width > 0:
        panel.draw_rect(x, y, bar_width, 1, None, bg=bar_color)
 
    #finally, some centered text with the values
    text = name + ': ' + str(value) + '/' + str(maximum)
    x_centered = x + (total_width-len(text))//2
    panel.draw_str(x_centered, y, text, fg=colors.white, bg=None)
 
def get_names_under_mouse():
 
    #return a string with the names of all objects under the mouse
    (x, y) = mouse_coord
 
    #create a list with the names of all objects at the mouse's coordinates and in FOV
    names = [obj.name for obj in world.my_map.objects
        if obj.x == x and obj.y == y and (obj.x, obj.y) in visible_tiles]
 
    names = ', '.join(names)  #join the names, separated by commas
    return names.capitalize()
 
def render_all():
    global fov_recompute
    global visible_tiles

    if fov_recompute:
        fov_recompute = False
        visible_tiles = tdl.map.quickFOV(player.x, player.y,
                                         world.my_map.is_visible_tile,
                                         fov=FOV_ALGO,
                                         radius=TORCH_RADIUS,
                                         lightWalls=FOV_LIGHT_WALLS)
        print("Debug",visible_tiles)
 
        #go through all tiles, and set their background color according to the FOV
        for y in range(MAP_HEIGHT):
            for x in range(MAP_WIDTH):
                visible = (x, y) in visible_tiles
                wall = world.my_map.my_map[x][y].block_sight
                if not visible:
                    #if it's not visible right now, the player can only see it 
                    #if it's explored
                    if world.my_map.my_map[x][y].explored:
                        if wall:
                            con.draw_char(x, y, None, fg=None, bg=color_dark_wall)
                        else:
                            con.draw_char(x, y, None, fg=None, bg=color_dark_ground)
                else:
                    if wall:
                        con.draw_char(x, y, None, fg=None, bg=color_light_wall)
                    else:
                        con.draw_char(x, y, None, fg=None, bg=color_light_ground)
                    #since it's visible, explore it
                    world.my_map.my_map[x][y].explored = True
 
 
    #draw all objects in the list
    for obj in world.my_map.objects:
        if obj != player:
            obj.draw(con,visible_tiles)
    player.draw(con, visible_tiles)
    #blit the contents of "con" to the root console and present it
    root.blit(con, 0, 0, MAP_WIDTH, MAP_HEIGHT, 0, 0)
 
    #prepare to render the GUI panel
    panel.clear(fg=colors.white, bg=colors.black)
 
    #print the game messages, one line at a time
    y = 1
    for (line, color) in game_msgs:
        panel.draw_str(MSG_X, y, line, bg=None, fg=color)
        y += 1
 
    #show the player's stats
    render_bar(1, 1, BAR_WIDTH, 'HP', player.fighter.hp, player.fighter.max_hp,
        colors.light_red, colors.darker_red)
 
    #display names of objects under the mouse
    panel.draw_str(1, 0, get_names_under_mouse(), bg=None, fg=colors.light_gray)
 
    #blit the contents of "panel" to the root console
    root.blit(panel, 0, PANEL_Y, SCREEN_WIDTH, PANEL_HEIGHT, 0, 0)
 
def message(new_msg, color = colors.white):
    #split the message if necessary, among multiple lines
    new_msg_lines = textwrap.wrap(new_msg, MSG_WIDTH)
 
    for line in new_msg_lines:
        #if the buffer is full, remove the first line to make room for the new one
        if len(game_msgs) == MSG_HEIGHT:
            del game_msgs[0]
 
        #add the new line as a tuple, with the text and the color
        game_msgs.append((line, color))
 
def player_move_or_attack(dx, dy):
    global fov_recompute
 
    #the coordinates the player is moving to/attacking
    x = player.x + dx
    y = player.y + dy
 
    #try to find an attackable object there
    target = None
    for obj in world.my_map.objects:
        if obj.fighter and obj.x == x and obj.y == y:
            target = obj
            break
 
    #attack if target found, move otherwise
    if target is not None:
        player.fighter.attack(target)
    else:
        player.move(dx, dy)
        fov_recompute = True
 
def menu(header, options, width):
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
    root.blit(window, x, y, width, height, 0, 0, fg_alpha=1.0, bg_alpha=0.7)
 
    #present the root console to the player and wait for a key-press
    tdl.flush()
    key = tdl.event.key_wait()
    key_char = key.char
    if key_char == '':
        key_char = ' ' # placeholder
 
    if key.key == 'ENTER' and key.alt:
        #Alt+Enter: toggle fullscreen
        tdl.set_fullscreen(not tdl.get_fullscreen())
 
    #convert the ASCII code to an index; if it corresponds to an option, return it
    index = ord(key_char) - ord('a')
    if index >= 0 and index < len(options):
        return index
    return None
 
def inventory_menu(header):
    #show a menu with each item of the inventory as an option
    if len(inventory) == 0:
        options = ['Inventory is empty.']
    else:
        options = [item.name for item in inventory]
 
    index = menu(header, options, INVENTORY_WIDTH)
 
    #if an item was chosen, return it
    if index is None or len(inventory) == 0:
        return None
    return inventory[index].item
 
def msgbox(text, width=50):
    menu(text, [], width)  #use menu() as a sort of "message box"
 
def handle_keys():
    global playerx, playery
    global fov_recompute
    global mouse_coord
 
    keypress = False
    for event in tdl.event.get():
        if event.type == 'KEYDOWN':
            user_input = event
            keypress = True
        if event.type == 'MOUSEMOTION':
            mouse_coord = event.cell
 
    if not keypress:
        return 'didnt-take-turn' #TODO: Add to tutorial
 
    if user_input.key == 'ENTER' and user_input.alt:
        #Alt+Enter: toggle fullscreen
        tdl.set_fullscreen(not tdl.get_fullscreen())
 
    elif user_input.key == 'ESCAPE':
        return 'exit'  #exit game
 
    if game_state == 'playing':
        #movement keys
        if user_input.key == 'UP':
            player_move_or_attack(0, -1)
 
        elif user_input.key == 'DOWN':
            player_move_or_attack(0, 1)
 
        elif user_input.key == 'LEFT':
            player_move_or_attack(-1, 0)
 
        elif user_input.key == 'RIGHT':
            player_move_or_attack(1, 0)
        else:
            #test for other keys
            if user_input.text == 'g':
                #pick up an item
                for obj in world.my_map.objects:  #look for an item in the player's tile
                    if obj.x == player.x and obj.y == player.y and obj.item:
                        obj.item.pick_up()
                        break
 
            if user_input.text == 'i':
                #show the inventory; if an item is selected, use it
                chosen_item = inventory_menu('Press the key next to an item to ' +
                                             'use it, or any other to cancel.\n')
                if chosen_item is not None:
                    chosen_item.use()
 
            if user_input.text == 'd':
                #show the inventory; if an item is selected, drop it
                chosen_item = inventory_menu('Press the key next to an item to' + 
                'drop it, or any other to cancel.\n')
                if chosen_item is not None:
                    chosen_item.drop()
 
            return 'didnt-take-turn'
 

def target_tile(max_range=None):
    #return the position of a tile left-clicked in player's FOV (optionally in 
    #a range), or (None,None) if right-clicked.
    global mouse_coord
    while True:
        #render the screen. this erases the inventory and shows the names of
        #objects under the mouse.
        tdl.flush()
 
        clicked = False
        for event in tdl.event.get():
            if event.type == 'MOUSEMOTION':
                mouse_coord = event.cell
            if event.type == 'MOUSEDOWN' and event.button == 'LEFT':
                clicked = True
            elif ((event.type == 'MOUSEDOWN' and event.button == 'RIGHT') or 
                  (event.type == 'KEYDOWN' and event.key == 'ESCAPE')):
                return (None, None)
        render_all()
 
        #accept the target if the player clicked in FOV, and in case a range is 
        #specified, if it's in that range
        x = mouse_coord[0]
        y = mouse_coord[1]
        if (clicked and mouse_coord in visible_tiles and
            (max_range is None or player.distance(x, y) <= max_range)):
            return mouse_coord
 
def target_monster(max_range=None):
    #returns a clicked monster inside FOV up to a range, or None if right-clicked
    while True:
        (x, y) = target_tile(max_range)
        if x is None:  #player cancelled
            return None
 
        #return the first clicked monster, otherwise continue looping
        for obj in world.my_map.objects:
            if obj.x == x and obj.y == y and obj.fighter and obj != player:
                return obj
 
def closest_monster(max_range):
    #find closest enemy, up to a maximum range, and in the player's FOV
    closest_enemy = None
    closest_dist = max_range + 1  #start with (slightly more than) maximum range
 
    for obj in world.my_map.objects:
        if obj.fighter and not obj == player and (obj.x, obj.y) in visible_tiles:
            #calculate distance between this object and the player
            dist = player.distance_to(obj)
            if dist < closest_dist:  #it's closer, so remember it
                closest_enemy = obj
                closest_dist = dist
    return closest_enemy
 

def save_game():
    #open a new empty shelve (possibly overwriting an old one) to write the game data
    with shelve.open('savegame', 'n') as savefile:
        savefile['my_map'] = world.my_map
        savefile['objects'] = world.my_map.objects
        savefile['player_index'] = world.my_map.objects.index(player)  #index of player in objects list
        savefile['inventory'] = inventory
        savefile['game_msgs'] = game_msgs
        savefile['game_state'] = game_state
 
 
def load_game():
    #TODO: implement this correctly
    #open the previously saved shelve and load the game data
    global player, inventory, game_msgs, game_state
 
    with shelve.open('savegame', 'r') as savefile:
        my_map = savefile['my_map']
        objects = savefile['objects']
        player = objects[savefile['player_index']]  #get index of player in objects list and access it
        inventory = savefile['inventory']
        game_msgs = savefile['game_msgs']
        game_state = savefile['game_state']
 
def new_game():
    global player, inventory, game_msgs, game_state, world
 
    

    world = World()
    world.my_map.con = con
    player = world.my_map.player
 
    #generate map (at this point it's not drawn to the screen)
    print("Should probably make map (and rest of world here vs at top)")
    #make_map()
 
    game_state = 'playing'
    inventory = []
 
    #create the list of game messages and their colors, starts empty
    game_msgs = []
 
    #a warm welcoming message!
    message('Welcome stranger! Prepare to perish in the Tombs of the Ancient Kings.', colors.red)
 
def play_game():
    global mouse_coord, fov_recompute
 
    player_action = None
    mouse_coord = (0, 0)
    fov_recompute = True
    con.clear() #unexplored areas start black (which is the default background color)
 
    while not tdl.event.is_window_closed():
 
        #draw all objects in the list
        render_all()
        tdl.flush()
 
        #erase all objects at their old locations, before they move
        for obj in world.my_map.objects:
            obj.clear(con)
 
        #handle keys and exit game if needed
        player_action = handle_keys()
        if player_action == 'exit':
            save_game()
            break
 
        #let monsters take their turn
        if game_state == 'playing' and player_action != 'didnt-take-turn':
            for obj in world.my_map.objects:
                if obj.ai:
                    obj.ai.take_turn()
 
def main_menu():
    img = image_load('menu_background.png')
 
    while not tdl.event.is_window_closed():
        #show the background image, at twice the regular console resolution
        img.blit_2x(root, 0, 0)
 
        #show the game's title, and some credits!
        title = 'TOMBS OF THE ANCIENT KINGS'
        center = (SCREEN_WIDTH - len(title)) // 2
        root.draw_str(center, SCREEN_HEIGHT//2-4, title, bg=None, fg=colors.light_yellow)
 
        title = 'By Jotaf'
        center = (SCREEN_WIDTH - len(title)) // 2
        root.draw_str(center, SCREEN_HEIGHT-2, title, bg=None, fg=colors.light_yellow)
 
        #show options and wait for the player's choice
        choice = menu('', ['Play a new game', 'Continue last game', 'Quit'], 24)
 
        if choice == 0:  #new game
            new_game()
            play_game()
        if choice == 1:  #load last game
            try:
                load_game()
            except:
                msgbox('\n No saved game to load.\n', 24)
                continue
            play_game()
        elif choice == 2:  #quit
            break
 
 
tdl.set_font('arial10x10.png', greyscale=True, altLayout=True)
root = tdl.init(SCREEN_WIDTH, SCREEN_HEIGHT, title="Roguelike", 
                fullscreen=False)
tdl.setFPS(LIMIT_FPS)
con = tdl.Console(MAP_WIDTH, MAP_HEIGHT)
panel = tdl.Console(SCREEN_WIDTH, PANEL_HEIGHT)
 
main_menu()
