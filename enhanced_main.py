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
    #Show the name of the deck's option:
    "option" : True ,
    #number of cards which are due now
    "due now" : True,
    #number of buried cards
    "buried" : True ,
    #number of suspended cards
    "suspended" : True ,
    #number of due cards which are due later:
    "later" : True,
    #number of cards in learning (a card may required to be reviewed  many times):
    "learning" : True,
    #number of new cards that will be shown today:
    "new" : True,
    #number of unseen cards:
    "unseen" : True ,
    #number of due cards (to see now or later)
    "due" : False,
    #Change the color of (sub)decks without new cards to color_empty (you can edit it below)
    #change also the color of the (sub)decks with a descendant without new cards to color_empty_descendant (you can edit it below)
    "no_new": True,
}

hide_symbol =";"
#
default_color ="black"
color_empty = "red"
color_empty_descendant = "blue"

#the number of seconds between two refresh of the screen
refresh_rate= 30

#To which value numbers should be capped.
#If this value is 0, you only see 0 or +
#If this value is negative, there is no capping
cap_value = -1
###########################
#code beginning
#################







import time
from aqt.deckbrowser import DeckBrowser
from aqt.qt import *
from aqt.utils import downArrow
from anki.utils import intTime
from aqt import mw

class DeckNode:
    "A node in the new more advanced deck tree."
    def __init__(self, mw, oldNode):
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

        today = mw.col.sched.today
        #dayCutoff = mw.col.sched.dayCutoff
        result = mw.col.db.first("""select
            --lrnReps
            sum(case when queue=1 then left/1000 else 0 end),
            --lrnCards
            sum(case when queue=1 then 1 else 0 end),
            --dueLrnCards
            sum(case when queue=1 and due<=? then 1 else 0 end),
            --lrnDayCards
            sum(case when queue=3 and due<=? then 1 else 0 end),
            --buriedCards
            sum(case when queue=-2  or queue=-3 then 1 else 0 end),
            --suspendedCards
            sum(case when queue=-1 then 1 else 0 end),
            --lrnSoonest
            min(case when queue=1 then due else null end),
            --unseen
            sum(case when queue=0 then 1 else 0 end)
            from cards where did=?""", cutoff, today, self.did)
        self.lrnReps = result[0] or 0
        self.lrnCards = result[1] or 0
        self.dueLrnCards = result[2] or 0
        self.lrnDayCards = result[3] or 0
        self.buriedCards = result[4] or 0
        self.suspendedCards = result[5] or 0
        self.lrnSoonest = result[6] #can be null
        self.unseenCards = result[7] or 0
        self.children = [DeckNode(mw, oldChild) for oldChild in oldChildren]
        self.isEmpty = self.unseenCards==0
        self.hasEmptyDescendant = False
        for child in self.children:
            self.lrnReps += child.lrnReps
            self.lrnCards += child.lrnCards
            self.dueLrnCards += child.dueLrnCards
            self.lrnDayCards += child.lrnDayCards
            self.buriedCards += child.buriedCards
            self.suspendedCards += child.suspendedCards
            self.unseenCards += child.unseenCards
            if self.lrnSoonest is None:
                self.lrnSoonest = child.lrnSoonest
            elif child.lrnSoonest is not None:
                self.lrnSoonest = min(self.lrnSoonest, child.lrnSoonest)
            self.isEmpty = self.isEmpty and child.isEmpty
            self.hasEmptyDescendant = self.hasEmptyDescendant or child.hasEmptyDescendant or child.isEmpty
        if hide_symbol in self.name:
            self.color = default_color
        elif self.isEmpty:
            self.color= color_empty
        elif self.hasEmptyDescendant:
            self.color = color_empty_descendant
        else :
            self.color = default_color
            
    def test(self, node, depth, cnt):
        deckRow(self, node, depth, cnt)
        
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

        
        def cap(n):
            if cap_value==0:
                if n==0:
                    return "0"
                else:
                    return "+"
            if n >= cap_value and cap_value >0:
                return str(c) + "+"
            return str(n)
        
        def makeCell(contents, colour):
            if contents == 0 or contents == "0":
                colour = "#e0e0e0"
            cell = "<td align=right><font color='%s'>%s</font></td>"
            return cell % (colour, contents)
        
        due = self.dueRevCards + self.lrnDayCards + self.dueLrnCards
        if due == 0 and self.lrnSoonest is not None:
            wait = (self.lrnSoonest - intTime()) / 60
            dueNow = "[" + str(wait) + "m]"
        else:
            dueNow = cap(due)
        laterCards = self.lrnCards - self.dueLrnCards
        laterReps = self.lrnReps - self.dueLrnCards
        if laterReps == laterCards:
            later = cap(laterReps)
        elif laterCards == 0:
            later = "(" + cap(laterReps) + ")"
        elif laterReps >= 1000:
            later = cap(laterCards) + " (+)"
        else:
            later = str(laterCards) + " (" + str(laterReps) + ")"
        if userOption["new"]:
            buf += makeCell(cap(self.newCards), "#000099")
        if userOption["due"]:
            buf += makeCell(due, "#007700")
        if userOption["due now"]:
            buf += makeCell(dueNow, "#007700")
        if userOption["later"]:
            buf += makeCell(later, "#770000")
        if userOption["buried"]:
            buf += makeCell(cap(self.buriedCards), "#997700")
        if userOption["suspended"]:
            buf += makeCell(cap(self.buriedCards), "#990077")
        if userOption["unseen"]:
            buf += makeCell(cap(self.unseenCards), "#009977")
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
    
        #new headings
        headings = []
        if userOption["new"]:
            headings.append("New")
        if userOption["due"]:
            headings.append("Due")
        if userOption["due now"]:
            headings.append("Due now")
        if userOption["later"]:
            headings.append("Later")
        if userOption["buried"]:
            headings.append("Buried")
        if userOption["suspended"]:
            headings.append("Suspended")
        if userOption["unseen"]:
            headings.append("Unseen")
        buf = "<tr><th colspan=5 align=left>%s</th>" % (_("Deck"),)
        for heading in headings:
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
refreshTimer = mw.progress.timer(refresh_rate*1000, onRefreshTimer, True)

