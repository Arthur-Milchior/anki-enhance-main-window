from aqt.deckbrowser import DeckBrowser
import time
doDebug = False

def debug(t):
    #print(t)
    pass

allMeasures = dict()
allNewMeasures = dict()
running = set()
def measureTime(isClass):
    def actualAlfa(fun):
        if not doDebug:
            return fun
        name = fun.__name__
        allNewMeasures[name] = 0
        allMeasures[name] = 0
        def newFun(*args,**kwargs):
            nameInRunning = name in running
            if isClass:
                self = args[0]
            start = time.time()
            ret = fun(*args,**kwargs)
            end = time.time()
            delay = end-start
            if not nameInRunning:
                allNewMeasures[name] += delay
            if delay >.05:
                if isClass:
                    print(f"Spent {delay} in {name}({self.name})")#,{args_},{kwargs})")
                else:
                    print(f"Spent {delay} in {name}()")#{args},{kwargs})")
            return ret
        newname = f"measure_{name}"
        return newFun
    return actualAlfa

def printMeasures():
    for key in sorted(allMeasures, key = lambda name: allNewMeasures[name]):
        print (f"Total time since last time in {key} is {allNewMeasures[key]}")
        allNewMeasures[key]=0
