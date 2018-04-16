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

Adds a "mature"/"young" column to show the percent of cards whose
delay is at least/less than 21 days.

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
    #List of columns. Reorder the elements to change the order fo the columns.
    # Remove the symbol # before a line to add a column in anki as described in the line of code
    #-Long name of the column
    #-Header of the column
    #-Color of the number shown in this column
    #-Description of the column
    #-Whether you want absolute number "absolute" or percent "percent"
    #-Whether you want to consider subdeck "subdeck" or not "deck"
    "columns" :[
        ##Learning:
        #This number is the sum of the two numbers below.
        #(_("learning card"), _("Learning")+"<br/>"+_("(card)") ,"orange", _("Cards in learning")+"<br/>"+_("(either new cards you have seen once,")+"<br/>"+_("or cards which you have forgotten recently.")+"<br/>"+_("Assuming those cards didn't graduate)"), "absolute", "subdeck"),
        #(_("learning later"), _("Learning")+"<br/>"+_("later (review)") ,"orange", _("Review which will happen later.")+"<br/>"+_("Either because a review happened recently,")+"<br/>"+_("or because the card have many review left."), "absolute", "subdeck"),
        #(_("learning now"), _("Learning")+"<br/>"+_("now") ,"orange", _("Cards in learning which are due now.")+"<br/>"+_("If there are no such cards,")+"<br/>"+_("the time in minutes")+"<br/>"+_("or seconds until another learning card is due"), "absolute", "subdeck"),
        (_("learning now later"), _("Learning")+"<br/>"+_("now")+"<br/>"+_("(later)"),"orange", _("Cards in learning which are due now")+"<br/>"+_("(and in parenthesis, the number of reviews")+"<br/>"+_("which are due later)"), "absolute", "subdeck"),
        ##Review cards:
        #(_("review due"), _("Due")+"<br/>"+_("all") ,"green", _("Review cards which are due today")+"<br/>"+_("(not counting the one in learning)"), "absolute", "subdeck"),
        #(_("review today"), _("Due")+"<br/>"+_("today") ,"green", _("Review cards you will see today"), "absolute", "subdeck"),
        (_("review"), _("Due")+"<br/>"+_("today (all)"),"green", _("Review cards cards you will see today")+"<br/>"+_("(and the ones you will not see today)"), "absolute", "subdeck"),
        ##Unseen cards
        #(_("unseen"),_("Unseen")+"<br/>"+_("all")  ,"blue", _("Cards that have never been answered"), "absolute", "subdeck"),
        #(_("new"), _("New")+"<br/>"+_("today") ,"blue", _("Unseen cards you will see today")+"<br/>"+_("(what anki calls new cards)"), "absolute", "subdeck"),
        (_("unseen new"),_("New")+"<br/>"+_("(Unseen)"),"blue", _("Unseen cards you will see today")+"<br/>"+_("(and those you will not see today)"), "absolute", "subdeck"),
        ##General count
        (_("buried"), _("Buried"),"grey",_("number of buried cards,")+"<br/>"+_("(cards you decided not to see today)"), "absolute", "subdeck"),        
        (_("suspended"), _("Suspended"),"brown", _("number of suspended cards,")+"<br/>"+_("(cards you will never see")+"<br/>"+_("unless you unsuspend them in the browser)"), "absolute", "subdeck"),
        #(_("total"), _("Total"),"black", _("Number of cards in the deck"), "absolute", "subdeck"),
        (_("total note"), _("Total")+"<br/>"+_("Card/Note"),"black", _("Number of cards/note in the deck"), "absolute", "subdeck"), #percent makes no sens in this line. 
        (_("today"), _("Today"),"red", _("Number of review you will see today")+"<br/>"+_("(new, review and learning)"), "absolute", "subdeck"),
        #(_("undue"), _("Undue"),"purple", _("Number of cards reviewed, not yet due"), "absolute", "subdeck"),
        (_("mature"), _("Mature"),"purple", _("Number of cards reviewed, with interval at least 3 weeks"), _("both"), "subdeck"),
        (_("young"), _("Young"),"pink", _("Number of cards reviewed, with interval less than 3 weeks"), _("both"), "subdeck"),
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

def conditionString(cond,string=None, parenthesis = False):
    res = "(" if parenthesis else ""
    if cond:
        if string is None:
            res += str(cond)
        else:
            res+= str(string)
    else:
        return ""
    res += ")" if parenthesis else ""
    return res

class DeckNode:
    "A node in the new more advanced deck tree."
    def __init__(self, mw, oldNode, ignoreEmptyParent=False):
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

        self.ignoreEmpty = ignoreEmptyParent or (userOption["hide symbol"]  in self.name)
        today = mw.col.sched.today
        #dayCutoff = mw.col.sched.dayCutoff
        self.notesRec = set(mw.col.db.list("""select  nid from cards where did=?""", self.did))
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
            sum(case when queue = 2 and due <= ? then 1 else 0 end),
            --note
            count (distinct nid),
            --review undue
            sum(case when queue = 2 and due >  ? then 1 else 0 end),
            --review young
            sum(case when queue = 2 and due >  ? and ivl <21 then 1 else 0 end),
            --review mature
            sum(case when queue = 2 and due >  ? and ivl >=21 then 1 else 0 end)
            from cards where did=?""", cutoff, today, today, today, today, today, self.did)
        
        #filling the absolute value of each possible column of the table        
        self.count={
            "absolute":{
                "deck":{
                    "learning repetition" : result[0] or 0,
                    "learning card" : result[1] or 0,
                    "learning now count" : result[2] or 0,
                    "learn > day" : result[3] or 0,
                    "buried" : result[4] or 0,
                    "suspended" : result[5] or 0,
                    "unseen" : result[7] or 0,
                    "total" : result[8] or 0,
                    "review due" : result[9] or 0,
                    "note" : result[10] or 0,
                    "undue" : result[11] or 0,
                    "young" : result[12] or 0,
                    "mature" : result[13] or 0,
                }
            }
        }
        self.timeDue= {"deck": result[6], "subdeck":result[6]} #can be null,
        self.count["absolute"]["subdeck"] = {name: self.count["absolute"]["deck"][name] for name in self.count["absolute"]["deck"]}
        self.children = [DeckNode(mw, oldChild, self.ignoreEmpty) for oldChild in oldChildren]
        self.today = self.dueRevCards + self.dueLrnReps+self.count["absolute"]["deck"]["learning repetition"]
        for child in self.children:
            self.notesRec.update(child.notesRec)
            for name in [ "learning repetition", "learning card", "learning now count", "learn > day", "buried", "suspended", "unseen", "total", "review due", "undue", "young", "mature"]:
                self.count["absolute"]["subdeck"][name] += child.count["absolute"]["subdeck"][name]
            if self.timeDue["subdeck"]:
                if child.timeDue["subdeck"]:
                    self.timeDue["subdeck"]= min(self.timeDue["subdeck"],child.timeDue["subdeck"])
            else:
                self.timeDue["subdeck"] = child.timeDue["subdeck"]

        ##is empty
        self.isEmpty = self.count["absolute"]["subdeck"]["unseen"]==0

        #Empty descendant (considering itself)
        self.hasEmptyDescendant = self.isEmpty
        for child in self.children:
            self.hasEmptyDescendant = self.hasEmptyDescendant or (child.hasEmptyDescendant and not child.ignoreEmpty)
        self.count["absolute"]["deck"]["learning later"]= self.count["absolute"]["deck"]["learning repetition"]-self.count["absolute"]["deck"]["learning now count"]
        self.count["absolute"]["subdeck"]["note"]= len(self.notesRec)
       
        if self.ignoreEmpty:
            self.color = userOption["default color"]
        elif self.isEmpty:
            self.color= userOption["color empty"]
        elif self.hasEmptyDescendant:
            self.color = userOption["color empty descendant"]
        else:
            self.color = userOption["default color"]
        for c in ["deck","subdeck"]:
            self.count["absolute"][c]["learning later"]= (self.count["absolute"][c]["learning repetition"]-self.count["absolute"][c]["learning now count"])
            self.count["absolute"][c]["review today"]=(self.dueRevCards)
            self.count["absolute"][c]["review later"]=(self.count["absolute"][c]["review due"]-self.count["absolute"][c]["review today"])
            self.count["absolute"][c]["new"]=self.newCards
            self.count["absolute"][c]["unseen later"] = self.count["absolute"][c]["unseen"]-self.count["absolute"][c]["new"]
            self.count["absolute"][c]["today"] = self.count["absolute"][c]["new"]+self.dueRevCards+self.dueLrnReps

        #filling the relative value of each possible column of the table
        self.count["percent"]={
            kind:{
                column:conditionString(self.count["absolute"][kind][column],str(100*self.count["absolute"][kind][column]/self.count["absolute"][kind]["total"])+ "%") if self.count["absolute"][kind]["total"] else ""
                for column in self.count["absolute"][kind]
            }
            for kind in self.count["absolute"]
        }
        self.count["both"]={
            kind:{
                column:conditionString(self.count["absolute"][kind][column],str(self.count["absolute"][kind][column])+ "|"+self.count["percent"][kind][column])
                for column in self.count["absolute"][kind]
            }
            for kind in self.count["absolute"]
        }
        #The one with text
        for number in self.count:
            self.count[number][c]["review"]=conditionString(self.count[number][c]["review today"])+ conditionString(self.count["absolute"][c]["review later"],parenthesis=True)
            self.count[number][c]["unseen new"] = conditionString(self.count[number][c]["new"])+conditionString(self.count["absolute"][c]["unseen later"], parenthesis=True)
            if not  self.count["absolute"][c]["learning now count"] and self.timeDue[c] is not None:
                remainingSeconds = self.timeDue[c] - intTime()
                if remainingSeconds >= 60:
                    self.count[number][c]["learning now"] = "[%dm]" % (remainingSeconds / 60)
                else :
                    self.count[number][c]["learning now"] = "[%ds]" % remainingSeconds
            else:
                self.count[number][c]["learning now"]=self.count[number][c]["learning now count"]
            self.count[number][c]["total note"] = conditionString(self.count[number][c]["note"] and self.count[number][c]["total"],str(self.count[number][c]["total"])+"/"+ str(self.count[number][c]["note"]))
            self.count[number][c]["learning now later"]= conditionString(self.count[number][c]["learning now"])+conditionString(self.count["absolute"][c]["learning later"],parenthesis=True)
            
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

        for (name, _, colour, description, number, deck) in userOption["columns"]:
                contents = self.count[number][deck][name]
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
        for (__ ,heading, __, __, __, __) in userOption["columns"]:
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

