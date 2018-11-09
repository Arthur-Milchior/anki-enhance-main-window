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
unseen cards (by default, red). To the deck which have a subdeck have
no unseen card (by default blue). To the deck which have marked card
(by default, backgroud blue) assuming the previous conditions are not
met. Allows to turn off this coloring by adding a special symbol in
the name of the deck (by default ";")

"""
debug=False
import time
from aqt.deckbrowser import DeckBrowser
from aqt.qt import *
from aqt.utils import downArrow
from anki.utils import intTime, ids2str
from aqt import mw
from anki.notes import Note
from anki.decks import DeckManager
import copy
from anki.sched import Scheduler

####################
#USER CONFIGURATION#
####################
#If you were used to do user configuration here, be happy. You won't have to edit this file every single time an update occur ! Now you just have to use the add-on manager and do the edition there once.


########################################################################################
########################################################################################
#HTML code here (so, if you know html, you can edit the html part without knowing python)
########################################################################################
########################################################################################
css="""/* Tooltip container */
        a:hover{
         cursor: pointer;
        }        

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

	/* padding-left for header columns except deck-column */
	th.count {padding-left:15px;
	}
	
	"""
######################
#header related html #
######################
start_header="""<tr style="vertical-align:text-top">"""
deck_header=f"""<th colspan=5 align=left>{_("Deck")}</th>"""
def column_header(heading):
    return f"<th class=count>{_(heading)}</th>"

option_header="<th class=count></th>"
option_name_header="""<td></td>"""
end_header="""</tr>"""



##############
#deck's html #
##############
def start_line(klass,did):
    return f"<tr class='{klass}' id='{did}'>"

def collapse_children_html(did,name,prefix):
    return f"""<a class=collapse onclick='pycmd("collapse:{did}")' id="{name}" href="#{name}" >{prefix}</a>"""
collapse_no_child="<span class=collapse></span>"

def deck_name(depth,collapse,extraclass,did,cssStyle,name):
    return f"""
    
        <td class=decktd colspan=5>{"&nbsp;"*6*depth}{collapse}<a class="deck{extraclass}" onclick="pycmd('open:{did}')"><font style='{cssStyle}'>{name}</font></a></td>"""
def number_cell(colour,contents,description):
    return f"<td align='right' class='tooltip'><font color='{colour}'>{contents}</font><span class='tooltiptext'>{description}</span></td>"


def gear(did):
    return f"""<td align=center class=opts><a onclick='pycmd(\"opts:{int(did)}\");'><img src='/_anki/imgs/gears.svg' class=gears></a></td>"""

def deck_option_name(option):
    return f"<td>{option}</td>"

end_line="</tr>"
###########################
#Associating default header and description
###########################
header={
    "learning card":_("Learning")+"<br/>"+_("(card)"), 
    "learning later":_("Learning")+"<br/>"+_("later")+" ("+_("review")+")" ,
    "learning now":_("Learning")+"<br/>"+_("now") ,
    "learning all":_("Learning")+"<br/>"+_("now")+"<br/>("+_("later today")+"<br/>("+_("other day")+"))",
    "review due":_("Due")+"<br/>"+_("all") ,
    "review today":_("Due")+"<br/>"+_("today") ,
    "review":_("Due")+"<br/>"+_("today")+" ("+_("all")+")",
    "unseen":_("Unseen")+"<br/>"+_("all")  ,
    "new":_("New")+"<br/>"+_("today") ,
    "unseen new":_("New")+"<br/>"+"("+_("Unseen")+")",
    "buried":_("Buried"),
    "suspended":_("Suspended"),
    "cards":_("Total"),
    "notes/cards":_("Total")+"<br/>"+_("Card/Note"),
    "notes":_("Total")+"<br/>"+_("Note"),
    "today":_("Today"),
    "undue":_("Undue"),
    "mature":_("Mature"),
    "young": _("Young"),
    "marked":_("Marked"),
}
def getConfAux(conf,field,dic):
    headerConf=conf.get(field)
    if headerConf is not None:
        return headerConf
    else:
        return dic[conf["name"]]

def getHeader(conf):
    return getConfAux(conf,"header",header)

overlay={
    "learning card":_("Cards in learning")+"<br/>"+_("""(either new cards you see again,""")+"<br/>"+_("or cards which you have forgotten recently.")+"<br/>"+_("""Assuming those cards didn't graduate)"""),
    "learning later":_("Review which will happen later.")+"<br/>"+_("Either because a review happened recently,")+"<br/>"+_("or because the card have many review left."),
    "learning now":_("Cards in learning which are due now.")+"<br/>"+_("If there are no such cards,")+"<br/>"+_("the time in minutes")+"<br/>"+_("or seconds until another learning card is due"),
    "learning all":_("Cards in learning which are due now")+"<br/>"+_("(and in parenthesis, the number of reviews")+"<br/>"+_("which are due later)"),
    "review due":_("Review cards which are due today")+"<br/>"+_("(not counting the one in learning)"),
    "review today":_("Review cards you will see today"),
    "review":_("Review cards cards you will see today")+"<br/>"+_("(and the ones you will not see today)"),
    "unseen":_("Cards that have never been answered"),
    "new":_("Unseen")+ _("cards")+ _("you will see today")+"<br/>"+_("(what anki calls ")+_("new cards"),
    "unseen new":_("Unseen cards you will see today")+"<br/>"+_("(and those you will not see today)"),
    "buried":_("number of buried cards,")+"<br/>"+_("(cards you decided not to see today)"),
    "suspended":_("number of suspended cards,")+"<br/>"+_("(cards you will never see")+"<br/>"+_("unless you unsuspend them in the browser)"),
    "cards":_("Number of cards in the deck"),
    "notes/cards":_("Number of cards/note in the deck"),
    "notes":_("Number of cards/note in the deck"),
    "today":_("Number of review you will see today")+"<br/>"+_("(new, review and learning)"),
    "undue":_("Number of cards reviewed, not yet due"),
    "mature":_("Number of cards reviewed, with interval at least 3 weeks"),
    "young": _("Number of cards reviewed, with interval less than 3 weeks"), 
    "marked":_("Number of marked note")
}
def getOverlay(conf):
    return getConfAux(conf,"overlay",overlay)

###########################
#Python code beginning
#################

globalCount = dict()

requirements = dict()
def addRequirement(name, dependances=set()):
    """Associate to each field which we want to consider the name of the query we need to query.

    name -- the value we want to compute
    dependances -- the set of value required to compute the value name
    """
    requirements[name]={name}
    for dependance in dependances:
        #requirements[name]|={dependance}
        dep=requirements.get(dependance)
        if dep is None:
            raise Exception(name, dependance)
        requirements[name]|=dep

started=False
def start():
    global userOption, started, valueToCompute
    if started:
        return
    started=True
    userOption=mw.addonManager.getConfig(__name__)
    refreshTimer = mw.progress.timer(userOption.get("refresh rate",30)*1000, onRefreshTimer, True)
    addRequirement("learn soonest")
    addRequirement("learning now from today")
    addRequirement("learning today from past")
    addRequirement("learning now",dependances={"learn soonest","learning now from today","learning today from past"})#number of cards in learning, ready to be seen again
    addRequirement("learning later today")#number of cards in learning, seen again today, but not now
    addRequirement("learning future")#number of cards in learning, not seen again today
    addRequirement("learning later",dependances=["learning later today","learning future"])#number of cards in learning, seen again but not now
    addRequirement("learning later today future",dependances=["learning future","learning later today"])#number of cards in learning, which can't be seen now
    addRequirement("learning today",dependances=["learning later today","learning future","learning now"])#number of cards in learning, which will be seen today
    addRequirement("learning all",dependances=["learning today","learning future","learning later"])#number of cards in learning, of all kinds
    addRequirement("learning card", dependances=["learning all"])
    
    addRequirement("learning today repetition from today")
    addRequirement("learning today repetition from past")
    addRequirement("learning today repetition",dependances={"learning today repetition from today","learning today repetition from past"})#Number of repetition of learning cards you'll see today
    addRequirement("learning repetition from today")
    addRequirement("learning repetition from past")
    addRequirement("learning repetition",dependances={"learning repetition from today","learning repetition from past"})#Number of repetition of learning cards you'll see
    addRequirement("learning future repetition",dependances={"learning repetition","learning today repetition"})#Number of repetition of learning cards you'll see another day
    
    addRequirement("review due",dependances=["learning repetition"])#number of cards which are due today 
    addRequirement("review today",dependances={"review due"})#number of cards which are due and will be seen today (it requires both the review due, and the limit)
    addRequirement("review later",dependances=["review due","review today"])#number of cards which are due but, because of limits, can't be seen today
    addRequirement("review",dependances=["review today","review later"])#number of cards which are due today
    addRequirement("unseen")#Number of unseen card
    addRequirement("new",set())#number of new cards which should be seen today if there are enough unseen cards (Depends only of limit, and not of db)
    addRequirement("unseen later",dependances={"unseen","new"})#Number of unseen card which will not be seen today
    addRequirement("unseen new",dependances=["unseen later","new"])#Number of unseen cards, both seen today, and seen another day
    addRequirement("buried")#number of bured card
    addRequirement("suspended")#number of suspended cards
    addRequirement("cards")#number of cards
    addRequirement("notes")#number of cards and of note
    addRequirement("notes/cards",dependances=["notes","cards"])#number of cards and of note
    addRequirement("today", dependances=["new"])#number of due cards today
    addRequirement("undue")#number of cards which are not due today
    addRequirement("mature")#number of mature cards
    addRequirement("young" )#number of young cards
    addRequirement("marked",dependances={"notes"})# number of marked cards


    #Compute 
    #cards is always useful to calcul percent
    #unseen is used to see whether a deck has new card or not.
    valueToCompute={"cards", "unseen"}
    for conf in userOption["columns"]:
      if conf.get("present",True):
        name=conf["name"]
        valueToCompute|=requirements[name]
        valueToCompute|={name}
        

def idFromOldNode(node):
    #Look at aqt/deckbrowser.py for a description of node
    (_,did,_,_,_,_)=node
    return did

def cap(n):
    capValue=userOption.get("cap value",0)
    if capValue==0:
        if n==0:
            return "0"
        else:
            return "+"
        if n >= capValue and capValue >0:
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
    def __init__(self, mw, oldNode, endedParent=False, givenUpParent=False, pauseParent=False):
        #Look at aqt/deckbrowser.py for a description of oldNode
        "Build the new deck tree or subtree (with extra info) by traversing the old one."
        cutoff = intTime() + mw.col.conf['collapseTime']
        today = mw.col.sched.today
        self.param=dict()
        queries=[(name, query) for (name,query) in [
            ("learning now from today", "sum(case when queue = 1 and due <= "+str(cutoff)+" then 1 else 0 end)" ),
            ("learning today from past", "sum(case when queue = 3 and due <= "+str(today)+" then 1 else 0 end)" ),#"cards in learning to see today and which have waited at least a day"
            ("learning later today", "sum(case when queue = 1 and due > "+str(cutoff)+" then 1 else 0 end)" ),
            ("learning future", "sum(case when queue = 3 and due > "+str(today)+" then 1 else 0 end)" ),#"cards in learning such that this review will occur at least tomorrow"
            ("learning today repetition from today", "sum(case when queue = 1 then left/1000 else 0 end)"),
            ("learning today repetition from past", "sum(case when queue = 3 then left/1000 else 0 end)"),
            ("learning repetition from today", "sum(case when queue = 1 then mod%1000 else 0 end)"),
            ("learning repetition from past", "sum(case when queue = 3 then mod%1000 else 0 end)"),
            ("review due","sum(case when queue = 2 and due <= "+str(today)+" then 1 else 0 end)" ),
            ("unseen","sum(case when queue = 0 then 1 else 0 end)"),
            ("buried", "sum(case when queue = -2  or queue = -3 then 1 else 0 end)"),
            ("suspended", "sum(case when queue = -1 then 1 else 0 end)"),
            ("cards","sum(1)"),
            ("notes","count (distinct nid)"),
            ("undue","sum(case when queue = 2 and due >  "+str(today)+" then 1 else 0 end)"), #Sum of the two next
            ("mature","sum(case when queue = 2 and due >  "+str(today)+" and ivl >=21 then 1 else 0 end)" ),
            ("young","sum(case when queue = 2 and due >  "+str(today)+" and ivl <21 then 1 else 0 end)" ),
            ("learn soonest", "min(case when queue = 1 then due else null end)"),
        ] if name in valueToCompute]
         
        self.mw = mw
        self.name, self.did, self.dueRevCards, self.dueLrnReps, self.newCards, oldChildren = oldNode
        self.deck = mw.col.decks.get(self.did)
        if "conf" in self.deck:#a classical deck
            confId = str(self.deck["conf"])
            conf = mw.col.decks.dconf[confId]
            self.param["isFiltered"] = False
            self.param["confName"]=conf['name']
        else:
            self.param["isFiltered"] = True
            self.param["confName"]="Filtered"

        self.param["containsEndSymbol"] = "end symbol" in userOption and userOption["end symbol"]  in self.name
        self.param["containsPauseSymbol"] = "pause symbol" in userOption and userOption["pause symbol"]  in self.name
        self.param["containsBookSymbol"] = "book symbol" in userOption and userOption["book symbol"]  in self.name
        self.param["containsGivenUpSymbol"] = "given up symbol" in userOption and userOption["given up symbol"]  in self.name
        self.param["endedParent"] = endedParent
        self.param["givenUpParent"] = givenUpParent
        self.param["pauseParent"] = pauseParent
        self.param["ended"] = endedParent or self.param["containsEndSymbol"]
        self.param["givenUp"] = givenUpParent or self.param["containsGivenUpSymbol"]
        self.param["pause"] = pauseParent or self.param["containsPauseSymbol"]
        #dayCutoff = mw.col.sched.dayCutoff
        query = "select " + ",".join ([query for (name,query) in queries])+"            from cards where did="+str(self.did)
        result = mw.col.db.first(query)
       
        #filling the absolute value of each possible column of the table        
        self.count={
            "absolute":{
                "deck":{
                    name: (0 if result[index] is None else result[index]) for  index, (name,query ) in enumerate(queries)
                }
            }
        }
        if "notes" in valueToCompute: 
            self.notes = set(mw.col.db.list("""select  nid from cards where did=?""", self.did))
            self.notesRec = self.notes
            self.addCount("absolute","deck","notes", len(self.notes))
        #we now compute the interesting value using the queried values
        if "learning now" in valueToCompute:
            self.addCount("absolute","deck","learning now",self.count["absolute"]["deck"]["learning now from today"]+self.count["absolute"]["deck"]["learning today from past"])
        if "learning later" in valueToCompute:
            self.addCount("absolute","deck","learning later",self.count["absolute"]["deck"]["learning later today"]+self.count["absolute"]["deck"]["learning future"])
        if "learning card" in valueToCompute:
            self.addCount("absolute","deck","learning card",self.count["absolute"]["deck"]["learning now"]+self.count["absolute"]["deck"]["learning later"])
        if "learning today" in valueToCompute:
            self.addCount("absolute","deck","learning today",self.count["absolute"]["deck"]["learning later today"]+self.count["absolute"]["deck"]["learning now"])
        if "learning all" in valueToCompute:
            self.addCount("absolute","deck","learning all",self.count["absolute"]["deck"]["learning today"]+self.count["absolute"]["deck"]["learning future"])

        if "learning today repetition" in valueToCompute:
            self.addCount("absolute","deck","learning today repetition",self.count["absolute"]["deck"]["learning today repetition from today"]+self.count["absolute"]["deck"]["learning today repetition from past"])
        if "learning repetition" in valueToCompute:
            self.addCount("absolute","deck","learning repetition",self.count["absolute"]["deck"]["learning repetition from today"]+self.count["absolute"]["deck"]["learning repetition from past"])
        if "learning future repetition" in valueToCompute:
            self.addCount("absolute","deck","learning future repetition",self.count["absolute"]["deck"]["learning repetition"]-self.count["absolute"]["deck"]["learning today repetition"])
            
        if "marked" in valueToCompute: 
            self.markedNotesRec = set()
            self.param["endedMarkedDescendant"] = False
            self.addCount("absolute","deck","marked", 0)
        if "learn soonest" in valueToCompute:
            learn_soonest = self.count["absolute"]["deck"]["learn soonest"]
            self.count["absolute"]["deck"].pop("learn soonest")
            self.timeDue= {"deck": learn_soonest, "subdeck":learn_soonest} #can be null,
        self.count["absolute"]["subdeck"] = {name: self.count["absolute"]["deck"][name] for name in self.count["absolute"]["deck"]}
        self.children=list()
        for oldChild in oldChildren:
            childNode = make(mw, oldChild, self.param["ended"], self.param["givenUp"], self.param["pause"]) 
            self.children.append(childNode)
        for child in self.children:
            if "notes" in valueToCompute:
                child_notesRec=child.notesRec
                self.notesRec.update(child_notesRec)
            if "marked" in valueToCompute: 
                self.markedNotesRec.update(child.markedNotesRec)
                self.param["endedMarkedDescendant"] = self.param["endedMarkedDescendant"] or child.param["endedMarkedDescendant"]
            for name in {"learning now",
                         "learning now from today",
                         "learning today from past",
                         "learning later today",
                         "learning future",
                         "learning later",
                         "learning later today future",
                         "learning today",
                         "learning all",
                         "learning today repetition",
                         "learning today repetition from today",
                         "learning today repetition from past",
                         "learning repetition",
                         "learning repetition from today",
                         "learning repetition from past",
                         "learning future repetition", 
                         "buried",
                         "suspended",
                         "unseen",
                         "cards",
                         "review due",
                         "undue",
                         "young",
                         "mature",}& valueToCompute:
                self.addCount("absolute","subdeck",name , self.count["absolute"]["subdeck"][name]+child.count["absolute"]["subdeck"][name])
            if "learn soonest" in valueToCompute:
              if self.timeDue["subdeck"]:
                if child.timeDue["subdeck"]:
                    self.timeDue["subdeck"]= min(self.timeDue["subdeck"],child.timeDue["subdeck"])
              else:
                self.timeDue["subdeck"] = child.timeDue["subdeck"]

        ##is empty
        self.param["isEmpty"] = self.count["absolute"]["subdeck"]["unseen"]==0
        self.param["someMarked"] = False
        #Empty descendant (considering itself)
        self.param["hasEmptyDescendant"] = self.param["isEmpty"]
        for child in self.children:
            self.param["hasEmptyDescendant"] = self.param["hasEmptyDescendant"] or (child.param["hasEmptyDescendant"] and (not child.param["ended"]) and (not child.param["givenUp"]) and (not child.param["pause"]))
        if "notes" in valueToCompute: 
            self.addCount("absolute","subdeck","notes", len(self.notesRec))
        if "marked" in valueToCompute:
            self.markedNotes = set(mw.col.db.list("""select  id from notes where tags like '%marked%' and (not (tags like '%notMain%')) and id in """+ ids2str(self.notes)))
            self.markedNotesRec |= self.markedNotes
            #If it contains a book symbol, stop propagating the "marked" information. Unless the book is also ended.
            if self.param["containsBookSymbol"]:
                self.param["endedMarkedDescendant"] = self.param["endedMarkedDescendant"] and self.param["containsEndSymbol"] and self.param["isEmpty"] 
            if self.markedNotes and self.param["containsEndSymbol"] and self.param["isEmpty"]:
                self.param["endedMarkedDescendant"] = True
            self.addCount("absolute","deck","marked", len(self.markedNotes))
            self.addCount("absolute","subdeck","marked", len(self.markedNotesRec))
            self.param["someMarked"] = self.count["absolute"]["subdeck"]["marked"]>0
       
        self.style = dict()
        if not self.param["isFiltered"]:
          if not self.param["ended"] and not self.param["givenUp"] and not self.param["pause"]:
            if self.param["isEmpty"]:
                self.style["color"]=userOption.get("color empty","black")
            elif self.param["hasEmptyDescendant"]:
                self.style["color"]=userOption.get("color empty descendant","black")
          if self.param["someMarked"]:
            if self.param["endedMarkedDescendant"]:
                self.style["background-color"]=userOption.get("ended marked background color")
            else:
                self.style["background-color"]=userOption.get("marked backgroud color")
        for c in ["deck","subdeck"]:
            self.addCount("absolute",c,"review today",(self.dueRevCards))
            self.addCount("absolute",c,"review later",(self.count["absolute"][c]["review due"]-self.count["absolute"][c]["review today"]))
            if "learning future" in valueToCompute:
                self.addCount("absolute","deck","learning future",self.count["absolute"]["deck"]["learning now from today"]+self.count["absolute"]["deck"]["learning today from past"])

            self.addCount("absolute",c,"new",self.newCards)
            self.addCount("absolute",c,"unseen later" , self.count["absolute"][c]["unseen"]-self.count["absolute"][c]["new"])
            self.addCount("absolute",c,"today" , self.count["absolute"][c]["new"]+self.dueRevCards+self.dueLrnReps)

        if not userOption.get("color empty",False):
            self.style["color"]="black"
        if "background-color" in self.style and not userOption.get("color marked",False):
            del self.style["background-color"]
        #filling the relative value of each possible column of the table
        self.count["percent"]={}
        for kind in self.count["absolute"]:
            self.count["percent"][kind]={}
            for column in self.count["absolute"][kind]:
                s1=self.count["absolute"][kind][column]
                if self.count["absolute"][kind]["cards"]:
                    s2=str((100*self.count["absolute"][kind][column])//self.count["absolute"][kind]["cards"]) + "%"
                else:
                    s2= ""
                s=conditionString(s1,s2)
                self.count["percent"][kind][column]=s
        self.count["both"]={
            kind:{
                column:conditionString(self.count["absolute"][kind][column],str(self.count["absolute"][kind][column])+ "|"+self.count["percent"][kind][column])
                for column in self.count["absolute"][kind]
            }
            for kind in self.count["absolute"]
        }
        #The one with text
        self.text = copy.deepcopy(self.count)
        for absoluteOrPercent in self.text:
            self.text[absoluteOrPercent][c]["review"]=conditionString(self.text[absoluteOrPercent][c]["review today"])+ conditionString(self.text[absoluteOrPercent][c]["review later"],parenthesis=True)
            self.text[absoluteOrPercent][c]["unseen new"] = conditionString(self.text[absoluteOrPercent][c]["new"])+conditionString(self.text[absoluteOrPercent][c]["unseen later"], parenthesis=True)
            if (("learning now" in valueToCompute) and (not  self.text["absolute"][c]["learning now"])) and ("learn soonest" in valueToCompute) and (self.timeDue[c] is not 0):
                remainingSeconds = self.timeDue[c] - intTime()
                if remainingSeconds >= 60:
                    self.text[absoluteOrPercent][c]["learning now"] = "[%dm]" % (remainingSeconds // 60)
                else :
                    self.text[absoluteOrPercent][c]["learning now"] = "[%ds]" % remainingSeconds
            if "notes/cards" in valueToCompute:
                self.text[absoluteOrPercent][c]["notes/cards"] = conditionString(self.text[absoluteOrPercent][c]["notes"] and self.text[absoluteOrPercent][c]["cards"],str(self.text[absoluteOrPercent][c]["cards"])+"/"+ str(self.text[absoluteOrPercent][c]["notes"]))
            if "learning today" in valueToCompute:
                self.text[absoluteOrPercent][c]["learning today"]= conditionString(self.text[absoluteOrPercent][c]["learning now"])+conditionString(self.text[absoluteOrPercent][c]["learning later today"],parenthesis=True)
            if "learning future" in valueToCompute:
              future = self.text[absoluteOrPercent][c]["learning future"]
              if future:
                later=conditionString(str(self.text[absoluteOrPercent][c]["learning later today"])+conditionString(future,parenthesis=True),parenthesis=True)
              else:
                later=conditionString(self.text[absoluteOrPercent][c]["learning later today"],parenthesis=True)
            if "learning all" in valueToCompute:
                self.text[absoluteOrPercent][c]["learning all"]=(
                    conditionString(self.text[absoluteOrPercent][c]["learning now"])+
                    later
                )

    def addCount(self,absoluteOrPercent,c,name,value):
        # if absoluteOrPercent=="absolute":
        #     print(f"Adding {c} {name}= {value}")
        #     pass
        self.count[absoluteOrPercent][c][name]=value

    def objectDescription(self):
        "A description of the object, used to debug"
        d=""
        for dic in [self.param,self.style]:
          for key in dic:
            d+= "%s:%s<br/>" %(key,dic[key])
        return d
            
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
        if deck['collapsed']:
            prefix = "+"
    
        if did == col.mw.col.conf['curDeck']:
            klass = 'deck current'
        else:
            klass = 'deck'
        buf = start_line(klass,did)
        # deck link
        if children:
            collapse = collapse_children_html(did,deck["name"],prefix) 
        else:
            collapse = collapse_no_child
        if deck['dyn']:
            extraclass = " filtered"
        else:
            extraclass = ""
        cssStyle = ""
        for name, value in node.style.items():
            cssStyle +="%s:%s;" %(name,value)
        buf += deck_name(depth,collapse,extraclass,did,cssStyle,node.name)

        for conf in userOption["columns"]:
          if conf.get("present",True):
            name=conf["name"]
            if conf.get("percent",False):
                if conf.get("absolute",False):
                    number= "both"
                else:
                    number="percent"
            else:
                number="absolute"
            contents = self.text[number]["subdeck" if conf.get("subdeck",False) else "deck"][conf["name"]]
            if contents == 0 or contents == "0":
                colour = "#e0e0e0"
            buf +=number_cell(conf.get("color","black"), contents, getOverlay(conf))

        # options
        buf += gear(did)
        if userOption.get("option"):
            buf += deck_option_name(self.param["confName"])
        # children
        buf += end_line
        buf += col._renderDeckTree(children, depth+1)
        return buf

def make(mw, oldNode, endedParent=False, givenUpParent=False, pauseParent = False):
    did = idFromOldNode(oldNode)
    if did in globalCount:
       return globalCount[did]
    else:
       node = DeckNode(mw, oldNode, endedParent, givenUpParent, pauseParent)
       globalCount[did]= node
       return node
        
#based on Anki 2.0.36 aqt/deckbrowser.py DeckBrowser._renderDeckTree
def renderDeckTree(self, nodes, depth=0):
    start()
    #Look at aqt/deckbrowser.py for a description of oldNode
    if not nodes:
        return ""
    if depth == 0:
                
        buf = f"""<style>{css}</style>{start_header}{deck_header}"""
        for conf in userOption["columns"]:
          if conf.get("present",True):
                buf += column_header(getHeader(conf))
        buf += option_header #for deck's option
        if userOption.get("option"):
            buf += option_name_header
        buf +=end_header
        
        #convert nodes
        nodes = [make(self.mw, node) for node in nodes]
    
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

oldNoteFluh =Note.flush
def noteFlush(note, mod=None):
    globalCount.clear()
    print("flush")
    oldNoteFluh(note,mod=mod)
Note.flush = noteFlush
oldDeckSave =DeckManager.save
def deckSave(self, g=None, mainChange=True):
    if mainChange:
        print("change main deck")
        globalCount.clear()
    oldDeckSave(self,g=g)

DeckManager.save = deckSave
oldCollapse =DeckManager.collapse
def collapse(self,did):
        deck = self.get(did)
        deck['collapsed'] = not deck['collapsed']
        self.save(deck,mainChange=False)
    
DeckManager.collapse=collapse

oldRebuildDyn=Scheduler.rebuildDyn
def rebuidDyn(self, did=None):
    globalCount.clear()
    return oldRebuildDyn(self, did=None)

# oldExecute =DB.execute
# def execute(self, sql, *a, **ka):
#     globalCount.clear()
#     print("reset globalCount")
#     return oldExecute(self, sql, *a, **ka)

# DB.execute = execute
# oldExecutemany =DB.executemany
# def executemany(self, sql, l):
#     globalCount.clear()
#     print("reset globalCount")
#     return oldExecutemany(self, sql, l)

# DB.executemany = executemany

