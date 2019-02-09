# listRequirements =[
#     ("learn soonest",{}),
#     ("learning now from today",{}),
#     ("learning today from past",{}),
#     ("learning now",{"learn soonest","learning now from today","learning today from past"}),#number of cards in learning, ready to be seen again
#     ("learning later today",{}),#number of cards in learning, seen again today, but not now
#     ("learning future",{}),#number of cards in learning, not seen again today
#     ("learning later",{"learning later today","learning future"}),#number of cards in learning, seen again but not now
#     ("learning later today future",{"learning future","learning later today"}),#number of cards in learning, which can't be seen now
#     ("learning today",{"learning later today","learning future","learning now"}),#number of cards in learning, which will be seen today
#     ("learning all",{"learning today","learning future","learning later"}),#number of cards in learning, of all kinds
#     ("learning card", {"learning all"}),

#     ("learning today repetition from today",{}),
#     ("learning today repetition from past",{}),
#     ("learning today repetition",{"learning today repetition from today","learning today repetition from past"}),#Number of repetition of learning cards you'll see today
#     ("learning repetition from today",{}),
#     ("learning repetition from past",{}),
#     ("learning repetition",{"learning repetition from today","learning repetition from past"}),#Number of repetition of learning cards you'll see
#     ("learning future repetition",{"learning repetition","learning today repetition"}),#Number of repetition of learning cards you'll see another day

#     ("review due",{"learning repetition"}),#number of cards which are due today
#     ("reviewed today",{"review due"}),#number of cards which are due and will be seen today (it requires both the review due, and the limit),
#     ("repeated today",{"review due"}),#number of cards which are due and will be seen today (it requires both the review due, and the limit),
#     ("review later",{"review due","review today"}),#number of cards which are due but, because of limits, can't be seen today
#     ("review",{"review today","review later"}),#number of cards which are due today
#     ("unseen",{}),#Number of unseen card
#     ("new",set()),#number of new cards which should be seen today if there are enough unseen cards (Depends only of limit, and not of db),
#     ("unseen later",{"unseen","new"}),#Number of unseen card which will not be seen today
#     ("unseen new",{"unseen later","new"}),#Number of unseen cards, both seen today, and seen another day
#     ("buried",{}),#number of bured card
#     ("suspended",{}),#number of suspended cards
#     ("buried/suspended", {"buried","suspended"}),#number of bured card
#     ("cards",{}),#number of cards
#     ("notes",{}),#number of cards and of note
#     ("notes/cards",{"notes","cards"}),#number of cards and of note
#     ("today", {"new"}),#number of due cards today
#     ("undue",{}),#number of cards which are not due today
#     ("mature",{}),#number of mature cards
#     ("young" ,{}),#number of young cards
#     ("mature/young", {"mature","young"}),#number of mature cards
#     ("marked",{"notes"}),# number of marked cards
# ]

# # Dict: associating to each each number the set of other required numbers
# requirements = dict()
# for name, dependances in listRequirements:
#     """Associate to each field which we want to consider the name of the query we need to query.

#     name -- the value we want to compute
#     dependances -- the set of value required to compute the value name
#     """
#     requirements[name] = {name}
#     for dependance in dependances:
#         #requirements[name]| = {dependance}
#         dep = requirements.get(dependance)
#         if dep is None:
#             raise Exception(name, dependance)
#         requirements[name]|= dep

# started = False


# for name, dependances in listRequirements:
#     addRequirement(name, dependances)

#     #Compute
#     #cards is always useful to calcul percent
#     #unseen is used to see whether a deck has new card or not.
#     valueToCompute = {"cards", "unseen"}
#     for conf in getUserOption()["columns"]:
#       if conf.get("present",True):
#         name = conf["name"]
#         valueToCompute|= requirements[name]
#         valueToCompute|= {name}
