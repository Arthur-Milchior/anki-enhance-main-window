from anki.utils import intTime
from aqt import mw
from .debug import debug
values = dict()
def computeValues():
    debug("Compute values")
    cutoff = intTime() + mw.col.conf['collapseTime']
    today = mw.col.sched.today
    queriesCardCount = [
        ("learning now from today", f"queue = 1 and due <= {str(cutoff)}" ,""),
        ("learning today from past", f"queue = 3 and due <= {str(today)}" ,""),
        ("learning later today", f"queue = 1 and due > {str(cutoff)}" ,""),
        ("learning future", f"queue = 3 and due > {str(today)}" ,""),
        ("learning today repetition from today", "queue = 1", f"left/1000"),
        ("learning today repetition from past","queue = 3" , f"left/1000"),
        ("learning repetition from today", "queue = 1", f"mod%1000"),
        ("learning repetition from past","queue = 3", f"mod%1000"),
        ("review due", f"queue =  2 and due <= {str(today)}" ,""),
        ("reviewed today", f"due>0 and due-ivl = {str(today)}" ,""),
        ("unseen", f"queue = 0",""),
        ("buried", f"queue = -2  or queue = -3",""),
        ("suspended", f"queue = -1",""),
        ("cards","",""),
        ("undue", f"queue = 2 and due >  {str(today)}",""),
        ("mature", f"ivl >= 21" ,""),
        ("young", f"queue = 2 and 0<ivl and ivl <21" ,""),
    ]
    for name, condition, addend in queriesCardCount:
        if addend:
            element = f" sum({addend})"
        else:
            element = f" count(*)"
        if condition:
            condition = f" where {condition}"
        query = f"select did, {element} from cards {condition} group by did"
        results = mw.col.db.all(query)
        debug("""For {name}: query "{query}".""")
        values[name] = dict()
        for did, value in results:
            debug("In deck {did} there are {value} cards of kind {name}")
            values[name][did] = value

times = dict()
def computeTime():
    debug("Compute times")
    for did, time in mw.col.db.all("select did,min(case when queue = 1 then due else null end) from cards"):
        debug("time for {did} is {time}")
        times[did]=time
