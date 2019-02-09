import time
from aqt.qt import *
from aqt.utils import downArrow
from anki.utils import intTime, ids2str
from aqt import mw
import copy
import sys
from .config import getUserOption, writeConfig
from .html import *
from .printing import *
from .strings import getHeader, getOverlay
from .utils import measureTime, printMeasures
from .debug import debug
from . import tree


# Dict from deck id to deck node
idToNode = dict()
idToOldNode = dict()
@measureTime(False)
def idFromOldNode(node):
    #Look at aqt/deckbrowser.py for a description of node
    (_,did,_,_,_,_) = node
    return did

#The list of column in configuration which does not exists, and such that the user was already warned about it.
warned = set()


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

    #@measureTime(True)
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
        self.name, self.did, self.dueRevCards, self.dueLrnReps, self.newCardsToday, self.oldChildren = oldNode
        self.deck = mw.col.decks.get(self.did)
        #print(f"Init node {self.name}")

        self.initDicts()
        self.setSymbolsParameters()
        self.setChildren()
        self.setDeckLevel()
        self.setSubdeck()

        self.fromSetToCount()
        self.setText()

    #@measureTime(True)
    def setDeckLevel(self):
        """Compute every informations which does not need access to
        children """
        self.setConfParameters()
        self.initCountFromDb() # count information of card from database
        self.initNid() # set of note from database
        self.initMarked() # set of marked notes
        self.initTimeDue()
        self.initFromAlreadyComputed()
        self.initCountSum() # basic some from database information

    #@measureTime(True)
    def setSubdeck(self):
        self.setEndedMarkedDescendant()
        self.setSubdeckCount() # Sum of subdecks value
        self.setSubdeckSets() #Union of subdecks set
        self.setTimeDue()
        self.setEmpty()
        self.setPercentAndBoth()


    @measureTime(True)
    def setConfParameters(self):
        """ Find the configuration and its name """
        if "conf" in self.deck:#a classical deck
            confId = str(self.deck["conf"])
            conf = mw.col.decks.dconf[confId]
            self.isFiltered = False
            self.confName = conf['name']
        else:
            self.isFiltered = True
            self.confName = "Filtered"

    @measureTime(True)
    def testSymbolInName(self, symbolName):
        """ Whether the symbol associate to symbol name in the
        configuration occurs in the deck's name"""
        symbol = getUserOption(symbolName)
        if symbol is None:
            return False
        return symbol in self.name

    @measureTime(True)
    def setSymbolsParameters(self):
        """ Read the deck name and gather information from it"""
        self.containsEndSymbol = self.testSymbolInName("end symbol")
        self.containsPauseSymbol = self.testSymbolInName("pause symbol")
        self.containsBookSymbol = self.testSymbolInName("book symbol")
        self.containsGivenUpSymbol = self.testSymbolInName("given up symbol")
        self.ended = self.endedParent or self.containsEndSymbol
        self.givenUp = self.givenUpParent or self.containsGivenUpSymbol
        self.pause = self.pauseParent or self.containsPauseSymbol

    @measureTime(True)
    def initDicts(self):
        """ Ensure that each dictionarry are created"""
        self.count =  dict()
        for absoluteOrPercent in ["absolute", "percent","both"]:
            self.count[absoluteOrPercent] = dict()
            for kind in ["deck","subdeck"]:
                self.count[absoluteOrPercent][kind]= dict()
        self.noteSet =  dict()
        for kind in ["deck","subdeck"]:
            self.noteSet[kind]= dict()

    @measureTime(True)
    def initCountFromDb(self):
        for name in tree.values:
            self.addCount("absolute", "deck", name, tree.values[name].get(self.did,0))

    @measureTime(True)
    def initFromAlreadyComputed(self):
        """Put in dict values already computed by anki"""
        for subdeckNumber, name in  [(self.dueRevCards, "review today"), (self.newCardsToday,"new today"),(self.dueLrnReps,"repetition of today learning")]:
            deckNumber = subdeckNumber
            for child in self.children:
                deckNumber -= child.count["absolute"]["subdeck"][name]
            self.addCount("absolute", "deck", name, deckNumber)
            self.addCount("absolute", "subdeck", name, subdeckNumber)

    @measureTime(True)
    def absoluteDeckSum(self,newName, sum1, sum2, negate = False):
        sum1 = self.count["absolute"]["deck"][sum1]
        sum2 = self.count["absolute"]["deck"][sum2]
        if negate:
            sum2 = -sum2
        self.addCount("absolute","deck",newName,(sum1+sum2))

    @measureTime(True)
    def initCountSum(self):
        self.absoluteDeckSum("learning now sum","learning now from today","learning today from past")
        self.absoluteDeckSum("learning later","learning later today","learning future")
        self.absoluteDeckSum("learning card","learning now sum","learning later")
        self.absoluteDeckSum("learning today sum","learning later today","learning now sum")

        # Repetition
        self.absoluteDeckSum("learning today repetition","learning today repetition from today","learning today repetition from past")
        self.absoluteDeckSum("learning repetition","learning repetition from today","learning repetition from past")
        self.absoluteDeckSum("learning future repetition","learning repetition","learning today repetition", negate=True)

        # Review
        self.absoluteDeckSum("review later","review due","review today", negate=True)
        self.absoluteDeckSum("unseen later", "unseen","new today", negate=True)
        self.absoluteDeckSum("repetition seen today", "repetition of today learning", "review today")
        self.absoluteDeckSum("repetition today", "repetition seen today", "new today")
        self.absoluteDeckSum("cards seen today", "learning today sum", "review today")
        self.absoluteDeckSum("today", "cards seen today", "new today")


    @measureTime(True)
    def initNid(self):
        """ set the set of nids of this deck"""
        self.addSet("deck", "notes",set(mw.col.db.list("""select  nid from cards where did = ?""", self.did)))

    @measureTime(True)
    def initMarked(self):
        """ set the set of marked cards of this deck, and someMarked"""
        self.addSet("deck","marked",set(mw.col.db.list("""select  id from notes where tags like '%marked%' and (not (tags like '%notMain%')) and id in """+ ids2str(self.noteSet["deck"]["notes"]))))
        self.someMarked = bool(self.noteSet["deck"]["marked"])


        # if self.containsBookSymbol:
        #     self.endedMarkedDescendant = self.endedMarkedDescendant and self.containsEndSymbol and self.isEmpty
        # if self.markedNotes and self.containsEndSymbol and self.isEmpty:
        #     self.endedMarkedDescendant = True
        # self.addCount("absolute","deck","marked", len(self.markedNotes))
        # self.addCount("absolute","subdeck","marked", len(self.markedNotesRec))
        # self.param["someMarked"] = self.count["absolute"]["subdeck"]["marked"]>0

        # self.endedMarkedDescendant = False

    @measureTime(True)
    def initTimeDue(self):
        """find the time before the first element in learning can be seen"""
        self.timeDue = dict()
        self.timeDue["deck"] = tree.times.get(self.did,0) or 0


    #@measureTime(True)
    def setChildren(self):
        """ create node from every child and save them in
        self.children """
        self.children = list()
        for oldChild in self.oldChildren:
            childNode = make(oldChild, self.ended, self.givenUp, self.pause)
            self.children.append(childNode)

    @measureTime(True)
    def setEndedMarkedDescendant(self):
        """ check whether there is a descendant empty with marked note. Set background color appropriately"""
        self.endedMarkedDescendant = False
        if self.ended and self.someMarked:
            self.endedMarkedDescendant = True
            return
        for child in self.children:
            if child.endedMarkedDescendant:
                self.endedMarkedDescendant = True
                return
        if self.someMarked and getUserOption("do color marked",False):
            if self.endedMarkedDescendant:
                self.style["background-color"] = getUserOption("ended marked background color")
            else:
                self.style["background-color"] = getUserOption("marked backgroud color")

    @measureTime(True)
    def setSubdeckCount(self):
        """Compute subdeck value, as the sum of deck, and children's subdeck value"""
        for name in self.count["absolute"]["deck"]:
            count = self.count["absolute"]["deck"][name]
            for child in self.children:
                childNb = child.count["absolute"]["subdeck"][name]
                if not isinstance(childNb,int):
                    print(f"For child {child.name}, the value of {name} is not an int but {childNb}")
                if not isinstance(childNb,int):
                    print (f"childNb for «{name}» is «{childNb}»")
                count += childNb
            self.addCount("absolute","subdeck",name,count)

    @measureTime(True)
    def setSubdeckSets(self):
        """ Compute subdeck's set as union of the deck set and children subdecks set"""
        for name in self.noteSet["deck"]:
            newSet = self.noteSet["deck"][name]
            for child in self.children:
                newSet |= child.noteSet["subdeck"][name]
            self.addSet("subdeck",name,newSet)

    @measureTime(True)
    def setTimeDue(self):
        """Compute first time due for subdeck using the timedue of this deck,
        and the one of subdecks"""
        self.timeDue["subdeck"] = self.timeDue["deck"]
        for child in self.children:
            if self.timeDue["subdeck"]:
                if child.timeDue["subdeck"]:
                    self.timeDue["subdeck"] = min(self.timeDue["subdeck"],child.timeDue["subdeck"])
            else:
                self.timeDue["subdeck"] = child.timeDue["subdeck"]

    @measureTime(True)
    def setEmpty(self):
        """Set value of isEmpty and hasEmptyDescendant. Set the colors appropriately."""
        if not getUserOption("do color empty"):
            return
        self.isEmpty = self.count["absolute"]["subdeck"]["unseen"] == 0
        self.hasEmptyDescendant = self.isEmpty

        if self.isEmpty:
            if not self.ended and not self.givenUp and not self.pause:
                self.style["color"] = getUserOption("color empty","black")
            return
        for child in self.children:
            if (child.hasEmptyDescendant and (not child.ended) and (not child.givenUp) and (not child.pause)):
                self.hasEmptyDescendant = True
                self.style['color'] = getUserOption("color empty descendant","black")
                return

    @measureTime(True)
    def _setPercentAndBoth(self, kind, column, base):
        """Set percent and both count values for this kind and column. In theory, column is a subset of base.

        Returns the numerator if its non null and there are no cards."""
        ret = None
        numerator = self.count["absolute"][kind][column]
        denominator = self.count["absolute"][kind][base]
        if numerator == 0:
            percent = ""
        #base can't be empty since a subset of its is not empty, as ensured by the above test
        else:
            if denominator ==0:
                percent = f"{numerator}/{denominator} ?"
                ret = numerator
            else:
                percent = f"{(100*numerator)//denominator}%"
        self.addCount("percent",kind,column, percent)
        both = conditionString(numerator,f"{numerator}|{percent}")
        self.addCount("both",kind,column,both)
        return ret

    @measureTime(True)
    def setPercentAndBoth(self):
        """Set percent and both count values for each kind and column
        percent. Only considering cards.

        Print in case of division by 0 for the percent computation.
        """
        for kind in self.count["absolute"]:
            for column in self.count["absolute"][kind]:
                ret = self._setPercentAndBoth(kind,column,"cards")
                if ret is not None:
                    print(f"""{self.name}.count["absolute"]["{kind}"]["{column}"] is {ret}, while for cards its 0: """+str(self.count["absolute"][kind]["cards"]))

    @measureTime(True)
    def fromSetToCount(self):
        """Add numbers according to number of notes, for deck, subdeck, absolute, percent, both"""
        for kind in ["deck","subdeck"]:
            for name in self.noteSet[kind]:
                self.addCount("absolute",kind,name,len(self.noteSet[kind][name]))
            for name in self.noteSet[kind]:
                self._setPercentAndBoth(kind,name,"notes")

    @measureTime(True)
    def setLearningAll(self):
        """Set text for learning all"""
        for absoluteOrPercent in self.count:
            for kind in ["deck", "subdeck"]:
                future = self.count[absoluteOrPercent][kind]["learning future"]
                if future:
                    later = nowLater(self.count[absoluteOrPercent][kind]["learning later today"],future)
                else:
                    later = conditionString(self.count[absoluteOrPercent][kind]["learning later today"],parenthesis = True)
                self.addCount(absoluteOrPercent,kind,"learning all", nowLater(self.count[absoluteOrPercent][kind]["learning now sum"],later))

    @measureTime(True)
    def setTextTime(self):
        """set text for the time remaining before next card"""
        for absoluteOrPercent in self.count:
            for kind in ["deck", "subdeck"]:
                self.addCount(absoluteOrPercent,kind,"learning now", self.count[absoluteOrPercent][kind]["learning now sum"])
                if ((not self.count["absolute"][kind]["learning now"])) and (self.timeDue[kind] is not 0):
                    remainingSeconds = self.timeDue[kind] - intTime()
                    if remainingSeconds >= 60:
                        self.addCount(absoluteOrPercent, kind, "learning now", "[%dm]" % (remainingSeconds // 60))
                    else :
                        self.addCount(absoluteOrPercent, kind, "learning now", "[%ds]" % remainingSeconds)

    @measureTime(True)
    def setPairs(self):
        """Set text for columns which are pair"""
        for absoluteOrPercent in self.count:
            for kind in ["deck", "subdeck"]:
                for first,second in [("mature","young"),("notes","cards"), ("buried","suspended")]:
                    name = f"{first}/{second}"
                    firstValue = self.count[absoluteOrPercent][kind][first]
                    secondValue = self.count[absoluteOrPercent][kind][second]
                    values = conditionString(firstValue and secondValue, f"{firstValue}/{secondValue}")
                    self.addCount(absoluteOrPercent, kind, name, values)

    @measureTime(True)
    def setNowLaters(self):
        """ Set text for the pairs with cards to see now, and other to see later/another day"""
        for absoluteOrPercent in self.count:
            for kind in ["deck", "subdeck"]:
                for name, left, right in [
                    ("review",         "review today", "review later"),
                    ("unseen new",     "new today",    "unseen later"),
                    ("learning today", "learning now", "learning later today"),
                ]:
                    value = nowLater(self.count[absoluteOrPercent][kind][left], self.count[absoluteOrPercent][kind][right])
                    self.addCount(absoluteOrPercent,kind, name, value)

    @measureTime(True)
    def setText(self):
        self.setLearningAll()
        self.setTextTime()
        self.setPairs()
        self.setNowLaters()

    # End of initialization
    ###########
    # Initialization tool

    @measureTime(True)
    def addCount(self,absoluteOrPercent,kind,name,value):
        """Ensure that self.count[absoluteOrPercent][kind][name] is defined and equals value"""
        self.count[absoluteOrPercent][kind][name] = value

    @measureTime(True)
    def addSet(self,kind,name,value):
        """Ensure that self.noteSet[kind][name] is defined and equals value"""
        self.noteSet[kind][name] = value

    ########################
    # Printing
    @measureTime(True)
    def emptyRow(self, cnt):
        if self.did == 1 and cnt > 1 and not self.children:
            # if the default deck is empty, hide it
            if not self.count["absolute"]["subdeck"]["cards"]:
                return True
        # parent toggled for collapsing
        for parent in mw.col.decks.parents(self.did):
            if parent['collapsed']:
                return True

    @measureTime(True)
    def getOpenTr(self):
        if self.did == mw.col.conf['curDeck']:
            klass = 'deck current'
        else:
            klass = 'deck'
        return start_line(klass,self.did)
    @measureTime(True)
    def getCss(self):
        cssStyle = ""
        for name, value in self.style.items():
            cssStyle += "%s:%s;" %(name,value)
        return cssStyle

    @measureTime(True)
    def getCollapse(self):
        self.deck = mw.col.decks.get(self.did) # We reload the deck. The collapsed state may have changed.
        prefix = "+" if self.deck['collapsed'] else "-"
        # deck link
        if self.children:
            return collapse_children_html(self.did,self.deck["name"],prefix)
        else:
            return collapse_no_child

    @measureTime(True)
    def getExtraClass(self):
        if self.deck['dyn']:
            return " filtered"
        else:
            return ""

    @measureTime(True)
    def getName(self, depth):
        return deck_name(depth,self.getCollapse(),self.getExtraClass(),self.did,self.getCss(),self.name)

    @measureTime(True)
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
            confName = conf["name"]
            if confName == "new":
                confName = "new today" #It used to be called "new". Introduced back for retrocomputability.
                conf["name"] = "new today"
                writeConfig()
            countNumberKind = self.count[number]["subdeck" if conf.get("subdeck",False) else "deck"]
            if confName not in countNumberKind:
                if confName not in warned :
                    warned.add(confName)
                    print(f"The add-on enhance main window does not now any column whose name is {confName}. It thus won't be displayed. Please correct your add-on's configuration.", file = sys.stderr)
                continue
            contents = countNumberKind[confName]
            if contents == 0 or contents == "0" or contents == "0%":
                contents = ""#colour = "#e0e0e0"
            buf += number_cell(conf.get("color","black"), contents, getOverlay(conf))
        return buf

    @measureTime(True)
    def getOptionName(self):
        if getUserOption("option"):
            return deck_option_name(self.confName)
        return ""

    @measureTime(True)
    def htmlRow(self, col, depth, cnt):
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



@measureTime(False) #number 1 time
def make(oldNode, endedParent = False, givenUpParent = False, pauseParent = False):
    """Essentially similar to DeckNode, but return an element already computed if it exists in the base"""
    did = idFromOldNode(oldNode)
    if oldNode is not idToOldNode.get(did):
       node = DeckNode(mw, oldNode, endedParent, givenUpParent, pauseParent)
       idToNode[did] = node
       idToOldNode[did]=oldNode
    return idToNode[did]

#based on Anki 2.0.36 aqt/deckbrowser.py DeckBrowser._renderDeckTree
@measureTime(False) #number 3
def renderDeckTree(self, nodes, depth = 0):
    #Look at aqt/deckbrowser.py for a description of oldNode
    if not nodes:
        return ""
    if depth == 0:
        tree.computeValues()
        tree.computeTime()
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
    printMeasures()
    return buf



#based on Anki 2.0.45 aqt/main.py AnkiQt.onRefreshTimer
@measureTime(False) #number 2
def onRefreshTimer():
    if mw.state == "deckBrowser":
        mw.deckBrowser._renderPage()  #was refresh, but we're disabling that
