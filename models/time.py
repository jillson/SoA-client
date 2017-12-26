
class ScheduledItem:
    def __init__(self,item,function):
        self.target = item
        self.function = function
        self.time = None

TICKS_PER_MINUTE = 10
TICKS_PER_HOUR = TICKS_PER_MINUTE * 60
TICKS_PER_DAY = TICKS_PER_HOUR * 24
TICKS_PER_MONTH = TICKS_PER_DAY * 30
#TODO: do we want to actually make a WEEK be 7 days (and then maybe month is 28 days or we have fun scheduling)


class Scheduler:
    def __init__(self):
        self.shortterm = []
        self.daily = []
        self.monthly = []
        self.ticks = 0
    def save(self):
        return {}
    def load(self,rez):
        print("Do me load scheduler")
        
    def cancel(self,item):
        self.removeItems(self.shortterm,item)
        self.removeItems(self.daily,item)
        self.removeItems(self.monthly,item)
        
    def removeItems(self,lst,item):
        toRemove = [x for x in lst if x.target == item]
        for i in toRemove:
            lst.remove(i)

    def schedule(self,item,time,function):
        si = ScheduledItem(item,function)
        if time == "nextDay":
            self.daily.append(si)
        elif time == "nextMonth":
            self.monthly.append(si)
        else:
            si.time = time+self.ticks
            self.shortterm.append(si)

    def reset(self):
        self.ticks = 0
        self.items = []
    def getTime(self):
        s = 6 * (self.ticks % 10)
        r = int(self.ticks / 10)
        m = r % 60
        r = int(r/60)
        h = r % 24
        r = int(r/24)
        return r,h,m,s
    
    def tick(self):
        self.ticks += 1
        pendingList = [x for x in self.shortterm if self.ticks >= x.time]
        for p in pendingList:
            self.shortterm.remove(p)
            
        if self.ticks % TICKS_PER_DAY == 0:
            if self.ticks % TICKS_PER_MONTH == 0:
                pendingList += self.monthly
                self.monthly = []
            pendingList += self.daily
            self.daily = []
        
        return pendingList


scheduler = Scheduler()
