from .node import idToNode, renderDeckTree
from anki.notes import Note
from anki.decks import DeckManager
from anki.sched import Scheduler
from aqt.deckbrowser import DeckBrowser
from .debug import debug

oldNoteFluh = Note.flush
def noteFlush(note, mod = None):
    debug("flush")
    oldNoteFluh(note,mod = mod)
Note.flush = noteFlush

oldDeckSave = DeckManager.save
def deckSave(self, g = None, mainChange = True):
    if mainChange:
        debug("change main deck")
    oldDeckSave(self,g = g)
DeckManager.save = deckSave

oldRebuildDyn = Scheduler.rebuildDyn
def rebuidDyn(self, did = None):
    return oldRebuildDyn(self, did = None)

oldCollapse = DeckManager.collapse
def collapse(self,did):
    deck = self.get(did)
    deck['collapsed'] = not deck['collapsed']
    self.save(deck,mainChange = False)

DeckManager.collapse = collapse

#based on Anki 2.0.36 aqt/deckbrowser.py DeckBrowser._deckRow
def deckRow(self, node, depth, cnt):
    return node.htmlRow(self,depth,cnt)
DeckBrowser._deckRow = deckRow

DeckBrowser._renderDeckTree = renderDeckTree
