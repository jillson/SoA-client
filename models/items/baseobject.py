class GameObject:
    #this is a generic object: the player, a monster, an item, the stairs...
    #it's always represented by a character on screen.
    def __init__(self, x, y, char, name, color, my_map, blocks=False, 
                 fighter=None, ai=None, item=None, attrs = None):
        self.x = x
        self.y = y
        self.char = char
        self.color = color
        self.name = name
        self.blocks = blocks
        self.fighter = fighter
        self.my_map = my_map
        self.attrs = attrs or {}
 
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


class GameCharacter(GameObject):
    pass

class GameItem(GameObject):
    pass
