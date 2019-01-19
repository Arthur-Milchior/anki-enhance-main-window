import time
from aqt.qt import *
from aqt.utils import downArrow
from anki.utils import intTime, ids2str
from aqt import mw
import copy
from .config import getUserOption
from .html import *
from .printing import conditionString
from .strings import getHeader, getOverlay

def debug(t):
    #print(t)
    pass


# Dict from deck id to deck node
idToNode = dict()
def idFromOldNode(node):
    #Look at aqt/deckbrowser.py for a description of node
    (_,did,_,_,_,_) = node
    return did

class DeckNode:
    """A node in the new more advanced deck tree.

    name -- the name of the deck
    did -- the id of the deck
    dueRevCards -- number of review to see today
    dueLrnReps -- numbers of cards in learning
    newCards -- number of new cards to see today
    children -- the set of children, as decknode
    deck -- the deck objects

    Information to potentially display
    count -- associate to [absolute/percent][deck/subdeck][value] the number/percont of cards satisfying value in the deck (and its subdeck)
    set -- associate to [deck/subdeck][value] the set of nids satisfying "value" in the deck (and its subdeck)
    markedNotesRec -- the set of marked notes in the deck and its subdkc
    endedMarkedDescendant -- whether the deck has a descendant ended with marked cards
    timeDue[deck/subdeck] -- the number of seconds before the first card in learning will be seen
    isEmpty -- whether deck and subdecks has no unseen cards

    Conf parameters
    isFiltered -- whether this is a filtered deck
    confName -- the name of the configuration of this deck ('Filtered' if filtered)

    content of the deck's name:
    containsEndSymbol -- whether the deck's name contains the end symbol
    containsPauseSymbol
    containsBookSymbol
    containsGivenUpSymbol

    content of the deck's parent:
    endedParent -- whether an ancestor's name contains the end symbol
    givenUpParent
    pauseParent

    content of the deck:
    ended -- whether the deck is ended according to a symbol
    givenUp
    """
    
    def __init__(self, mw, oldNode, endedParent = False, givenUpParent = False, pauseParent = False):
        #Look at aqt/deckbrowser.py for a description of oldNode
        "Build the new deck tree or subtree (with extra info) by traversing the old one."

        # Associate each potentially interesting parameters of this node
        self.param = dict()
        #CSS Style
        self.style = dict()
        self.mw = mw
        self.endedParent = endedParent
        self.pauseParent = pauseParent
        self.givenUpParent = givenUpParent
        self.name, self.did, self.dueRevCards, self.dueLrnReps, self.newCards, oldChildren = oldNode
        self.deck = mw.col.decks.get(self.did)
        self.setConfParameters()
        
        self.setChildren(oldChildren)
        
        self.setSymbolsParameters()
        self.initCountFromDb() # count information of card from database
        self.initCountSum() # basic some from database information
        self.setNid() # set of note from database
        self.setMarked() # set of marked notes
        self.setSubdeckCount() # Sum of subdecks value
        self.setSubdeckSets() #Union of subdecks set
        self.setEndedMarkedDescendant()
        self.setTimeDue()
        self.setEmpty()
        self.setPercentAndBoth()
        self.fromSetToCount()
        self.setText()

    def setConfParameters(self):
        if "conf" in self.deck:#a classical deck
            confId = str(self.deck["conf"])
            conf = mw.col.decks.dconf[confId]
            self.isFiltered = False
            self.confName = conf['name']
        else:
            self.isFiltered = True
            self.confName = "Filtered"
            
    def setChildren(self,oldChildren):
        self.children = list()
        for oldChild in oldChildren:
            childNode = make(oldChild, self.ended, self.givenUp, self.pause) 
            self.children.append(childNode)
        
    def setSymbolsParameters(self):
        self.containsEndSymbol = getUserOption("end symbol", "iefarsietjnasieng")  in self.name
        self.containsPauseSymbol = getUserOption("pause symbol", "iefarsietjnasieng")  in self.name
        self.containsBookSymbol = getUserOption("book symbol", "iefarsietjnasieng")  in self.name
        self.containsGivenUpSymbol = getUserOption("given up symbol", "iefarsietjnasieng")  in self.name
        self.ended = self.endedParent or self.containsEndSymbol
        self.givenUp = self.givenUpParent or self.containsGivenUpSymbol
        self.pause = self.pauseParent or self.containsPauseSymbol

    def initCountFromDb(self):
        cutoff = intTime() + mw.col.conf['collapseTime']
        today = mw.col.sched.today
        queriesCardCount = [
            ("learning now from today", f"sum(case when queue = 1 and due <= {str(cutoff)} then 1 else 0 end)" ),
            ("learning today from past", f"sum(case when queue = 3 and due <= {str(today)} then 1 else 0 end)" ),#"cards in learning to see today and which have waited at least a day"
            ("learning later today", f"sum(case when queue = 1 and due > {str(cutoff)} then 1 else 0 end)" ),
            ("learning future", f"sum(case when queue = 3 and due > {str(today)} then 1 else 0 end)" ),#"cards in learning such that this review will occur at least tomorrow"
            ("learning today repetition from today", f"sum(case when queue = 1 then left/1000 else 0 end)"),
            ("learning today repetition from past", f"sum(case when queue = 3 then left/1000 else 0 end)"),
            ("learning repetition from today", f"sum(case when queue = 1 then mod%1000 else 0 end)"),
            ("learning repetition from past", f"sum(case when queue = 3 then mod%1000 else 0 end)"),
            ("review due", f"sum(case when queue =  2 and due <= {str(today)} then 1 else 0 end)" ),
            ("unseen", f"sum(case when queue = 0 then 1 else 0 end)"),
            ("buried", f"sum(case when queue = -2  or queue = -3 then 1 else 0 end)"),
            ("suspended", f"sum(case when queue = -1 then 1 else 0 end)"),
            ("cards","sum(1)"),
            ("notes","count (distinct nid)"),
            ("undue", f"sum(case when queue = 2 and due >  {str(today)} then 1 else 0 end)"), #Sum of the two next
            ("mature", f"sum(case when queue = 2 and due >  {str(today)} and ivl >= 21 then 1 else 0 end)" ),
            ("young", f"sum(case when queue = 2 and due >  {str(today)} and ivl <21 then 1 else 0 end)" )]
        conjunction = ",".join ([query for (name,query) in queriesCardCount])
        query = f"select {conjunction} from cards where did = ?"
        result = mw.col.db.first(query, str(self.did))
        self.count =  dict()
        self.noteSet =  dict()
        for index, (name, query) in enumerate(queriesCardCount):
            if result[index] is None:
                value = 0
            else:
                value = result[index]
            self.addCount("absolute", "deck", name, value)

    def initCountSum(self):
        self.addCount("absolute","deck","learning now",self.count["absolute"]["deck"]["learning now from today"]+self.count["absolute"]["deck"]["learning today from past"])
        self.addCount("absolute","deck","learning future",self.count["absolute"]["deck"]["learning now from today"]+self.count["absolute"]["deck"]["learning today from past"])
        self.addCount("absolute","deck","learning later",self.count["absolute"]["deck"]["learning later today"]+self.count["absolute"]["deck"]["learning future"])
        self.addCount("absolute","deck","learning card",self.count["absolute"]["deck"]["learning now"]+self.count["absolute"]["deck"]["learning later"])
        self.addCount("absolute","deck","learning today",self.count["absolute"]["deck"]["learning later today"]+self.count["absolute"]["deck"]["learning now"])
        self.addCount("absolute","deck","learning all",self.count["absolute"]["deck"]["learning today"]+self.count["absolute"]["deck"]["learning future"])
        
        # Repetition
        self.addCount("absolute","deck","learning today repetition",self.count["absolute"]["deck"]["learning today repetition from today"]+self.count["absolute"]["deck"]["learning today repetition from past"])
        self.addCount("absolute","deck","learning repetition",self.count["absolute"]["deck"]["learning repetition from today"]+self.count["absolute"]["deck"]["learning repetition from past"])
        self.addCount("absolute","deck","learning future repetition",self.count["absolute"]["deck"]["learning repetition"]-self.count["absolute"]["deck"]["learning today repetition"])

        # Review
        self.addCount("absolute","deck","review today",self.dueRevCards)
        self.addCount("absolute","deck","review later",(self.count["absolute"]["deck"]["review due"]-self.count["absolute"]["deck"]["review today"]))
            
        self.addCount("absolute","deck","new",self.newCards)
        self.addCount("absolute","deck","unseen later" , self.count["absolute"]["deck"]["unseen"]-self.count["absolute"]["deck"]["new"])
        self.addCount("absolute","deck","today" , self.count["absolute"]["deck"]["new"]+self.dueRevCards+self.dueLrnReps)


    def setNid(self):
        self.addSet("deck", "notes",set(mw.col.db.list("""select  nid from cards where did = ?""", self.did)))

    def setMarked(self):
        self.addSet("deck","marked",set(mw.col.db.list("""select  id from notes where tags like '%marked%' and (not (tags like '%notMain%')) and id in """+ ids2str(self.noteSet["deck"]["notes"]))))
        self.someMarked = bool(self.noteSet["deck"]["marked"])
        if self.someMarked and getUserOption("do color marked",False):
            if self.endedMarkedDescendant: 
                self.style["background-color"] = getUserOption("ended marked background color")
            else:
                self.style["background-color"] = getUserOption("marked backgroud color")
            
        
        # if self.containsBookSymbol:
        #     self.endedMarkedDescendant = self.endedMarkedDescendant and self.containsEndSymbol and self.isEmpty 
        # if self.markedNotes and self.containsEndSymbol and self.isEmpty:
        #     self.endedMarkedDescendant = True
        # self.addCount("absolute","deck","marked", len(self.markedNotes))
        # self.addCount("absolute","subdeck","marked", len(self.markedNotesRec))
        # self.param["someMarked"] = self.count["absolute"]["subdeck"]["marked"]>0
            
        # self.endedMarkedDescendant = False
        
        
    def setSubdeckCount(self):
        for name in self.count["absolute"]["deck"]:
            count = self.count["absolute"]["deck"][name]
            for child in self.children:
                count += child.count["absolute"]["subdeck"][name]
            self.addCount("absolute","subdeck",name,count)

    
    def setSubdeckSets(self):
        for name in self.noteSet["deck"]:
            newSet = self.noteSet["deck"][name]
            for child in self.children:
                newSet += child.noteSet["subdeck"][name]
            self.addSet("subdeck",name,newSet)

    def setEndedMarkedDescendant(self):
        self.endedMarkedDescendant = False
        if self.ended and self.someMarked:
            self.endedMarkedDescendant = True
            return
        for child in self.children:
            if child.endedMarkedDescendant:
                self.endedMarkedDescendant = True
                return
            
    def setTimeDue(self):
        learn_soonest = mw.col.db.scalar("select min(case when queue = 1 then due else null end) from cards where did = ?", str(self.did))
        if learn_soonest is None:
            learn_soonest =0
        self.timeDue = {"deck": learn_soonest, "subdeck":learn_soonest} #can be null,
        for child in self.children:
            if self.timeDue["subdeck"]:
                if child.timeDue["subdeck"]:
                    self.timeDue["subdeck"] = min(self.timeDue["subdeck"],child.timeDue["subdeck"])
            else:
                self.timeDue["subdeck"] = child.timeDue["subdeck"]
       
    def setEmpty(self):
        if not getUserOption("do color empty"):
            return
        self.isEmpty = self.count["absolute"]["subdeck"]["unseen"] == 0
        self.hasEmptyDescendant = self.isEmpty
        if self.isEmpty:
            if not self.ended and not self.givenUp and not self.pause:
                self.style["color"] = getUserOption("color empty","black")
                print(f"{self.name} is empty, not ended, not givenUp, not in pause. Its color is set to {self.style['color']}")
            return
        for child in self.children:
            if (child.hasEmptyDescendant and (not child.ended) and (not child.givenUp) and (not child.pause)):
                self.hasEmptyDescendant = True
                self.style['color'] = getUserOption("color empty descendant","black")
                print(f"{self.name} is not empty but has empty descendant. Its color is set to {self.style['color']}")
                return
                
    def _setPercentAndBoth(self, kind, column, base):
        s1 = self.count["absolute"][kind][column]
        if self.count["absolute"][kind][base]:
            s2 = str((100*self.count["absolute"][kind][column])//self.count["absolute"][kind]["cards"]) + "%"
        else:
            s2 = ""
        s = conditionString(s1,s2)
        self.addCount("percent",kind,column,s)
        both = conditionString(self.count["absolute"][kind][column],str(self.count["absolute"][kind][column])+ "|"+self.count["percent"][kind][column])
        self.addCount("both",kind,column,both)
        
    def setPercentAndBoth(self):
        for kind in self.count["absolute"]:
            for column in self.count["absolute"][kind]:
                self._setPercentAndBoth(kind,column,"cards")

    def setText(self):
        self.text = copy.deepcopy(self.count)
        for absoluteOrPercent in self.text:
            for c in ["deck", "subdeck"]:
                self.text[absoluteOrPercent][c]["review"] = conditionString(self.text[absoluteOrPercent][c]["review today"])+ conditionString(self.text[absoluteOrPercent][c]["review later"],parenthesis = True)
                self.text[absoluteOrPercent][c]["unseen new"] = conditionString(self.text[absoluteOrPercent][c]["new"])+conditionString(self.text[absoluteOrPercent][c]["unseen later"], parenthesis = True)
                if ((not  self.text["absolute"][c]["learning now"])) and (self.timeDue[c] is not 0):
                    remainingSeconds = self.timeDue[c] - intTime()
                    if remainingSeconds >= 60:
                        self.text[absoluteOrPercent][c]["learning now"] = "[%dm]" % (remainingSeconds // 60)
                    else :
                        self.text[absoluteOrPercent][c]["learning now"] = "[%ds]" % remainingSeconds
                self.text[absoluteOrPercent][c]["mature/young"] = conditionString(self.text[absoluteOrPercent][c]["mature"] and self.text[absoluteOrPercent][c]["young"],str(self.text[absoluteOrPercent][c]["young"])+"/"+ str(self.text[absoluteOrPercent][c]["mature"]))
                self.text[absoluteOrPercent][c]["notes/cards"] = conditionString(self.text[absoluteOrPercent][c]["notes"] and self.text[absoluteOrPercent][c]["cards"],str(self.text[absoluteOrPercent][c]["cards"])+"/"+ str(self.text[absoluteOrPercent][c]["notes"]))
                self.text[absoluteOrPercent][c]["buried/suspended"] = conditionString(self.text[absoluteOrPercent][c]["buried"] and self.text[absoluteOrPercent][c]["suspended"],str(self.text[absoluteOrPercent][c]["buried"])+"/"+ str(self.text[absoluteOrPercent][c]["suspended"]))
                self.text[absoluteOrPercent][c]["learning today"] = conditionString(self.text[absoluteOrPercent][c]["learning now"])+conditionString(self.text[absoluteOrPercent][c]["learning later today"],parenthesis = True)
                future = self.text[absoluteOrPercent][c]["learning future"]
                if future:
                    later = conditionString(str(self.text[absoluteOrPercent][c]["learning later today"])+conditionString(future,parenthesis = True),parenthesis = True)
                else:
                    later = conditionString(self.text[absoluteOrPercent][c]["learning later today"],parenthesis = True)
                self.text[absoluteOrPercent][c]["learning all"] = (
                    conditionString(self.text[absoluteOrPercent][c]["learning now"])+
                    later
                )
                
    # End of initialization        
    ########### 
    # Initialization tool
    def fromSetToCount(self):
        for c in ["deck","subdeck"]:
            for name in self.noteSet[c]:
                self.addCount("absolute",c,name,len(self.noteSet[c][name]))
            for name in self.noteSet[c]:
                self._setPercentAndBoth(c,name,"notes")
            
    
    def addCount(self,absoluteOrPercent,c,name,value):
        """Ensure that self.count[absoluteOrPercent][c][name] is defined and equals value"""
        if absoluteOrPercent not in self.count:
            self.count[absoluteOrPercent] = dict()
        if c not in self.count[absoluteOrPercent]:
            self.count[absoluteOrPercent][c] = dict()
        if name not in self.count[absoluteOrPercent][c]:
            self.count[absoluteOrPercent][c][name] = dict()
        self.count[absoluteOrPercent][c][name] = value

    def addSet(self,c,name,value):
        """Ensure that self.noteSet[c][name] is defined and equals value"""
        if c not in self.noteSet:
            self.noteSet[c] = dict()
        if name not in self.noteSet[c]:
            self.noteSet[c][name] = dict()
        self.noteSet[c][name] = value

    ########################
    # Printing
    def emptyRow(self, cnt):
        if self.did == 1 and cnt > 1 and not self.children:
            # if the default deck is empty, hide it
            if not mw.col.db.scalar("select 1 from cards where did = 1"):
                return ""
        # parent toggled for collapsing
        for parent in mw.col.decks.parents(self.did):
            if parent['collapsed']:
                buff = ""
                return buff
    
    def getOpenTr(self):
        if self.did == mw.col.conf['curDeck']:
            klass = 'deck current'
        else:
            klass = 'deck'
        return start_line(klass,self.did)
    def getCss(self):
        cssStyle = ""
        for name, value in self.style.items():
            cssStyle += "%s:%s;" %(name,value)
        return cssStyle

    def getCollapse(self):
        prefix = "+" if self.deck['collapsed'] else "-"
        # deck link
        if self.children:
            return collapse_self.children_html(self.did,self.deck["name"],prefix) 
        else:
            return collapse_no_child
        
    def getExtraClass(self):
        if self.deck['dyn']:
            return " filtered"
        else:
            return ""

    def getName(self, depth):
        return deck_name(depth,self.getCollapse(),self.getExtraClass(),self.did,self.getCss(),self.name)

    def getNumberColumns(self):
        buf = ""
        for conf in getUserOption("columns"):
          if conf.get("present",True):
            name = conf["name"]
            if conf.get("percent",False):
                if conf.get("absolute",False):
                    number = "both"
                else:
                    number = "percent"
            else:
                number = "absolute"
            contents = self.text[number]["subdeck" if conf.get("subdeck",False) else "deck"][conf["name"]]
            if contents == 0 or contents == "0":
                colour = "#e0e0e0"
            buf += number_cell(conf.get("color","black"), contents, getOverlay(conf))
        return buf
    
    def getOptionName(self):
        if getUserOption("option"):
            return deck_option_name(self.confName)
        return ""
    
    def makeRow(self, col, depth, cnt):
        "Generate the HTML table cells for this row of the deck tree."
        if self.emptyRow(cnt):
            return ""
        return (
            self.getOpenTr()+
            self.getName(depth)+
            self.getNumberColumns()+
            gear(self.did)+ 
            self.getOptionName()+
            end_line +
            col._renderDeckTree(self.children, depth+1)
        )


def make(oldNode, endedParent = False, givenUpParent = False, pauseParent = False):
    """Essentially similar to DeckNode, but return an element already computed if it exists in the base"""
    did = idFromOldNode(oldNode)
    if did not in idToNode:
       node = DeckNode(mw, oldNode, endedParent, givenUpParent, pauseParent)
       idToNode[did] = node
    return idToNode[did]
        
#based on Anki 2.0.36 aqt/deckbrowser.py DeckBrowser._renderDeckTree
def renderDeckTree(self, nodes, depth = 0):
    mw.progress.timer(getUserOption("refresh rate",30)*1000, onRefreshTimer, True)
    #Look at aqt/deckbrowser.py for a description of oldNode
    if not nodes:
        return ""
    if depth == 0:
                
        buf = f"""<style>{css}</style>{start_header}{deck_header}"""
        for conf in getUserOption("columns"):
          if conf.get("present",True):
                buf += column_header(getHeader(conf))
        buf += option_header #for deck's option
        if getUserOption("option"):
            buf += option_name_header
        buf += end_header
        
        #convert nodes
        nodes = [make(node) for node in nodes]
    
        buf += self._topLevelDragRow()
    else:
        buf = ""
    for node in nodes:
        buf += self._deckRow(node, depth, len(nodes))
    if depth == 0:
        buf += self._topLevelDragRow()
    return buf



#based on Anki 2.0.45 aqt/main.py AnkiQt.onRefreshTimer
def onRefreshTimer():
    if mw.state == "deckBrowser":
        mw.deckBrowser._renderPage()  #was refresh, but we're disabling that








