values = dict()
def computeValues():
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
            condition = f" having {condition}"
        query = f"select did, {element} from cards group by did {condition}"
        results = mw.col.db.all(query)
        values[name] = dict()
        for did, value in results:
            values[name][did] = value

times = dict()
def computeTime():
    for did, time in mw.col.db.all("select did,min(case when queue = 1 then due else null end) from cards"):
        times[did]=time
