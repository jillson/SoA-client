
class ScheduledItem:
    def __init__(self,item,function):
        self.target = item
        self.function = function
        self.time = None
    def save(self):
        fname = str(self.function).split(" ")[1]
        return {"function": fname,"time":self.time}

    @classmethod
    def load(cls, item, rez):
        fName = rez["function"]
        from models.items.itemactions import itemActions

        function = itemActions.get(fName)
        if not function:
            print("Couldn't find",fName)
            import pdb
            pdb.set_trace()
        
        si = cls(item,function)
        si.time = rez["time"]
        if si.time == "day":
            scheduler.daily.append(si)
        elif si.time == "month":
            scheduler.monthly.append(si)
        else:
            scheduler.shortterm.append(si)
        return si
        

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
        return {"ticks":self.ticks}
    def load(self,rez):
        self.ticks = rez["ticks"]
        
    def cancel(self,item):
        print("Going to cancel",item)
        self.removeItems(item.timeItems,item)
        self.removeItems(self.shortterm,item)
        self.removeItems(self.daily,item)
        self.removeItems(self.monthly,item)
        
    def removeItems(self,lst,item):
        print("Trying to remove",item,"from",lst)
        toRemove = [x for x in lst if x.target == item]
        for i in toRemove:
            lst.remove(i)

    def schedule(self,item,time,function):
        si = ScheduledItem(item,function)
        item.timeItems.append(si)
        if time == "nextDay":
            self.daily.append(si)
            si.time="day"
        elif time == "nextMonth":
            self.monthly.append(si)
            si.time="month"
        else:
            print("DEBUG: fix me in time.py")
            si.time = self.ticks+2
            #si.time = time+self.ticks
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
    
    def tick(self,skipDay):
        self.ticks += 1
        pendingList = [x for x in self.shortterm if self.ticks >= x.time]
        for p in pendingList:
            self.shortterm.remove(p)
            
        if self.ticks % TICKS_PER_DAY == 0 or skipDay:
            if self.ticks % TICKS_PER_MONTH == 0:
                pendingList += self.monthly
                self.monthly = []
            pendingList += self.daily
            self.daily = []

        if pendingList:
            for x in pendingList:
                x.target.timeItems.remove(x)
            print([x.function for x in pendingList])
        
        return pendingList


scheduler = Scheduler()
