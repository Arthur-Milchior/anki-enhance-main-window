# -*- coding: utf-8 -*-
# New code copyright Helen Foster and Arthur Milchior <Arthur@Milchior.fr> Some idea from Juda Kaleta <juda.kaleta@gmail.com>
# Github: https://github.com/Arthur-Milchior/anki-enhance-main-window
# Original code from Anki, copyright Damien Elmes <anki@ichi2.net>
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
"""Anki addon to enhance the info displayed in the main deck tree.

Each new options can be configured. 

Makes the "Due" count show only the number of cards due now.
If no cards are due now, but some are due later today,
 shows the time until the next review becomes due.
(Originally, if cards were due now, Anki showed all reps left on those cards.
 Otherwise it showed 0.)

Adds a "Later" column to show the number of cards and reps due later.
Formatted as "cards (reps)" if the numbers are different
 (for cards in the learning stage with more than one learning step).

Adds a "Buried" column to show the number of buried cards.

Adds a "Suspended" column to show the number of Suspended cards.

Adds an "unseen" column to show the number of cards which have not yet
been seen. (In fact, its the number of new cards. But «new cards» in
anki means «new cards you will see today») 

Adds a column with the deck's configuration's name. 

Triggers a refresh every 30 seconds. (Originally every 10 minutes.)
This can be configured.

Allows you to remove the 1000+ (when you have more than 1000 cards in
a deck), or to change this number to any other integer you want.


Allow to give a special color to the name of the deck which have no
unseen cards (by default, red). And to the deck which have a subdeck
have no empty card (by default blue). Allows to turn off this coloring
by adding a special symbol in the name of the deck (by default ";")
"""

####################
#USER CONFIGURATION#
####################
#Write False or True depending on whether you want to see the name of the option group

userOption = {
    ###
    #Counting cards of Decks
    
    #Set to true if you want to show only the number of card in the
    #deck, not taking the subdeck into accounts (This option does not
    #apply to the columns considering the cards due today.) 
    "Do not count subdeck's card"  :False,


    ###
    #List of columns. Reorder the elements to change the order fo the columns.
    #-Long name of the column
    #-Header of the column
    #-Whether this column is shown
    #-Color of the number
    #-Description of the column
    "columns" :[
        ##Learning:
        #This number is the sum of the two numbers below.
        ("learning card", "Learning<br/>(card)", False , "orange", "Cards in learning (either new cards you have seen once, or cards which you have forgotten recently. Assuming those cards didn't graduate)"),
        ("learning later", "Learning<br/>later (review)", False , "orange", "Review which will happen later. Either because a review happened recently, or because the card have many review left."),
        ("learning now", "Learning<br/>now", False , "orange", "Cards in learning which are due now. If there are no such cards, the time in minutes or seconds until another learning card is due"),
        ("learning now later", "Learning<br/>now<br/>(later)", True, "orange", "Cards in learning which are due now (and in parenthesis, the number of reviews which are due later)"),
        ##Review cards:
        ("review due", "Due<br/>all", False , "green", "Review cards which are due today (not counting the one in learning)"),
        ("review today", "Due<br/>today", False , "green", "Review cards you will see today"),
        ("review", "Due<br/>today (all)", True, "green", "Review cards cards you will see today (and total number in parenthesis if this number is bigger)"),
        ##Unseen cards
        ("unseen","Unseen<br/>all", False  , "blue", "Cards that have never been answered"),
        ("new", "New<br/>today", False , "blue", "Unseen cards you will see today (what anki calls new cards)"),
        ("unseen new","New<br/>(Unseen)", True, "blue", "Unseen cards you will see today (and total number of unseen cards in parenthesis if this number is bigger)"),
        ##General count
        ("buried", "Buried", True, "grey","number of buried cards, (cards you decided not to see today)"),        
        ("suspended", "Suspended", True, "brown", "number of suspended cards, (cards you will never see until you unsuspend them in the browser)"),
        ("total", "Total", True, "black", "Number of cards in the deck"),
        ("today", "Today", True, "red", "Number of review you will see today (new, review and learning)"),
    ],

    ######
    #Other options
    #Show the name of the deck's option:
    "option" : True,

    #Change the color of (sub)decks without new cards to color_empty (you can edit it below)
    #change also the color of the (sub)decks with a descendant without new cards to color_empty_descendant (you can edit it below)
    "no_new": True,

    #the number of seconds between two refresh of the screen
    "refresh rate": 30,

    #To which value numbers should be capped.
    #If this value is 0, you only see 0 or +
    #If this value is negative, there is no capping
    "cap value" : -1,

    
    ####Considering deck without unseen cards

    #the color of deck whose every subdeck contains unseen cards
    "default color" :"black",

    #The color of deck who does not contains unseen cards
    "color empty" : "red",

    #The color of deck who have a subdeck which does not contains unseen cards
    "color empty descendant" : "blue",

    #if the symbol, on the right of the equal, is present into the name of the deck, the presence or absence of unseen cards will not be considered.
    "hide symbol" :";",
}
###########################
#code beginning
#################
import time
from aqt.deckbrowser import DeckBrowser
from aqt.qt import *
from aqt.utils import downArrow
from anki.utils import intTime
from aqt import mw

def cap(n):
    if userOption["cap value"]==0:
        if n==0:
            return "0"
        else:
            return "+"
        if n >= userOption["cap value"] and userOption["cap value"] >0:
            return str(c) + "+"
        return str(n)

class DeckNode:
    "A node in the new more advanced deck tree."
    def __init__(self, mw, oldNode, ignoreEmpty=False):
        "Build the new deck tree or subtree (with extra info) by traversing the old one."
        self.mw = mw
        self.name, self.did, self.dueRevCards, self.dueLrnReps, self.newCards, oldChildren = oldNode
        self.deck = mw.col.decks.get(self.did)
        cutoff = intTime() + mw.col.conf['collapseTime']
        if "conf" in self.deck:#a classical deck
            confId = str(self.deck["conf"])
            conf = mw.col.decks.dconf[confId]
            self.confName=conf['name']
        else:
            self.confName="Filtered"

        ignoreEmpty = ignoreEmpty or userOption["hide symbol"]  in self.name
        today = mw.col.sched.today
        #dayCutoff = mw.col.sched.dayCutoff
        result = mw.col.db.first("""select 
            --Number of review total
            sum(case when queue = 1 then left/1000 else 0 end),
            --Number of cards in learning
            sum(case when queue = 1 then 1 else 0 end),
            --Number of cards in learning ready
            sum(case when queue = 1 and due <= ? then 1 else 0 end),
            --Number of cards in learning such that this review was supposed to wait at least a day
            sum(case when queue = 3 and due <= ? then 1 else 0 end),
            --Number of buried Cards
            sum(case when queue = -2  or queue = -3 then 1 else 0 end),
            --suspendedCards
            sum(case when queue = -1 then 1 else 0 end),
            --lrnSoonest
            min(case when queue = 1 then due else null end),
            --unseen
            sum(case when queue = 0 then 1 else 0 end),
            --total
            sum(1),
            --review due today
            sum(case when queue = 2 and due <= ? then 1 else 0 end)
            from cards where did=?""", cutoff, today, today, self.did)
        
        self.count={
            "flat":
            {
                "learning repetition" : result[0] or 0,
                "learning card" : result[1] or 0,
                "learning now" : result[2] or 0,
                "learn > day" : result[3] or 0,
                "buried" : result[4] or 0,
                "suspended" : result[5] or 0,
                "unseen" : result[7] or 0,
                "total" : result[8] or 0,
                "review due" : result[9] or 0,
            }
        }
        self.count["flat"]["learning later"]= self.count["flat"]["learning repetition"]-self.count["flat"]["learning now"]

        self.timeDue= {"flat": result[6], "rec":result[6]} #can be null,
        self.count["rec"] = {name: self.count["flat"][name] for name in self.count["flat"]}
        self.children = [DeckNode(mw, oldChild, ignoreEmpty) for oldChild in oldChildren]
        self.isEmpty = self.count["flat"]["unseen"]==0 and not ignoreEmpty
        self.hasEmptyDescendant = False
        self.today = self.dueRevCards + self.dueLrnReps+self.count["flat"]["learning repetition"]
        for child in self.children:
            for name in self.count["rec"]:
                self.count["rec"][name] += child.count["rec"][name]
            if self.timeDue["rec"]:
                if child.timeDue["rec"]:
                    self.timeDue["rec"]= min(self.timeDue["rec"],child.timeDue["rec"])
            else:
                self.timeDue["rec"] = child.timeDue["rec"]
            self.isEmpty = self.isEmpty and child.isEmpty
            self.hasEmptyDescendant = self.hasEmptyDescendant or child.hasEmptyDescendant or child.isEmpty
        if ignoreEmpty:
            self.hasEmptyDescendant = False
        if self.isEmpty:
            self.color= userOption["color empty"]
        elif self.hasEmptyDescendant:
            self.color = userOption["color empty descendant"]
        else:
            self.color = userOption["default color"]
        for c in ["flat","rec"]:
            self.count[c]["learning later"]= (self.count[c]["learning repetition"]-self.count[c]["learning now"])
            self.count[c]["learning now later"]= str((self.count[c]["learning now"])) + (" (+"+str(self.count[c]["learning later"])+")" if self.count[c]["learning later"] else "")
            self.count[c]["review today"]=(self.dueRevCards)
            reviewLater=(self.count[c]["review due"]-self.count[c]["review today"])
            self.count[c]["review"]=str((self.count[c]["review today"])) + (" (+"+str(reviewLater)+")" if reviewLater else "")
            self.count[c]["new"]=(self.newCards)
            unseenLater = self.count[c]["unseen"]-self.count[c]["new"]
            self.count[c]["unseen new"] = str((self.count[c]["new"])) + (" (+"+str(unseenLater)+")" if unseenLater else "")
            self.count[c]["today"] = self.count[c]["new"]+self.dueRevCards+self.dueLrnReps
            if not  self.count[c]["learning now"] and self.timeDue[c] is not None:
                remainingSeconds = self.timeDue[c] - intTime()
                if remainingSeconds >= 60:
                    self.count[c]["learning now"] = "[" + str(remainingSeconds / 60) + "m]"
                else :
                    self.count[c]["learning now"] = "[" + str(remainingSeconds) + "s]"
            
    def makeRow(self, col, depth, cnt):
        "Generate the HTML table cells for this row of the deck tree."
        node = self

        did = node.did
        children = node.children
        deck = col.mw.col.decks.get(did)
        if did == 1 and cnt > 1 and not children:
            # if the default deck is empty, hide it
            if not col.mw.col.db.scalar("select 1 from cards where did = 1"):
                return ""
        # parent toggled for collapsing
        for parent in col.mw.col.decks.parents(did):
            if parent['collapsed']:
                buff = ""
                return buff
        prefix = "-"
        if col.mw.col.decks.get(did)['collapsed']:
            prefix = "+"
    
        def indent():
            return "&nbsp;"*6*depth
        if did == col.mw.col.conf['curDeck']:
            klass = 'deck current'
        else:
            klass = 'deck'
        buf = "<tr class='%s' id='%d'>" % (klass, did)
        # deck link
        if children:
            collapse = "<a class=collapse href='collapse:%d'>%s</a>" % (did, prefix)
        else:
            collapse = "<span class=collapse></span>"
        if deck['dyn']:
            extraclass = "filtered"
        else:
            extraclass = ""
        buf += """
    
        <td class=decktd colspan=5>%s%s<a class="deck %s" href='open:%d'><font color='%s'>%s</font></a></td>"""% (
            indent(), collapse, extraclass, did, node.color,node.name)

        for (name, _, present, colour, description) in userOption["columns"]:
            if present:
                contents = self.count["flat" if userOption["Do not count subdeck's card"] else "rec"][name]
                if contents == 0 or contents == "0":
                    colour = "#e0e0e0"
                buf +=( "<td align='right' class='tooltip'><font color='%s'>%s</font><span class='tooltiptext'>%s</span></td>"% (colour, contents, description))

        # options
        buf += "<td align=right class=opts>%s</td>" % col.mw.button(
            link="opts:%d"%did, name="<img valign=bottom src='qrc:/icons/gears.png'>"+downArrow())
        if userOption["option"]:
            buf += "<td>%s</td>"% self.confName
        # children
        buf += "</tr>"
        buf += col._renderDeckTree(children, depth+1)
        return buf

#based on Anki 2.0.36 aqt/deckbrowser.py DeckBrowser._renderDeckTree
def renderDeckTree(self, nodes, depth=0):
    if not nodes:
        return ""
    if depth == 0:
                
        buf = """<style>
        /* Tooltip container */
        
        /* Tooltip text */
        .tooltip .tooltiptext {
            visibility: hidden;
            background-color: black;
            color: #fff;
            text-align: center;
            padding: 5px 0;
            border-radius: 6px;
            
            /* Position the tooltip text - see examples below! */
            position: absolute;
            z-index: 1;
        }

        /* Show the tooltip text when you mouse over the tooltip container */
        .tooltip:hover .tooltiptext {
            visibility: visible;
        }
        </style>
        <tr><th colspan=5 align=left>%s</th>""" % (_("Deck"),)
        for (__ ,heading, present, __, __) in userOption["columns"]:
            if present:
                buf += "<th class=count>%s</th>" % (_(heading),)
        buf += "<th class=count></th>" #for deck's option
        if userOption["option"]:
            buf += "<td></td>"
        buf +="</tr>"
        
        #convert nodes
        nodes = [DeckNode(self.mw, node) for node in nodes]
    
        buf += self._topLevelDragRow()
    else:
        buf = ""
    for node in nodes:
        buf += self._deckRow(node, depth, len(nodes))
    if depth == 0:
        buf += self._topLevelDragRow()
    return buf

#based on Anki 2.0.36 aqt/deckbrowser.py DeckBrowser._deckRow
def deckRow(self, node, depth, cnt):
    return node.makeRow(self,depth,cnt)

def refreshDoNothing(self):
    pass

#based on Anki 2.0.45 aqt/main.py AnkiQt.onRefreshTimer
def onRefreshTimer():
    if mw.state == "deckBrowser":
        mw.deckBrowser._renderPage()  #was refresh, but we're disabling that

def addon_reloader_teardown():
    refreshTimer.stop()

#replace rendering functions in DeckBrowser with these new ones
DeckBrowser._renderDeckTree = renderDeckTree
DeckBrowser._deckRow = deckRow

#disable refresh - only ever called from the 10-minute timer
#(intercepting here because the 10-min timer can't be disabled by addon)
DeckBrowser.refresh = refreshDoNothing

#refresh according to the refresh_rate parametr
refreshTimer = mw.progress.timer(userOption["refresh rate"]*1000, onRefreshTimer, True)

