from anki.decks import DeckManager
from anki.notes import Note
from anki.sched import Scheduler
from aqt.deckbrowser import DeckBrowser

from .column import _linkHandler
from .debug import debug
from .node import idToNode, renderDeckTree


# based on Anki 2.0.36 aqt/deckbrowser.py DeckBrowser._deckRow
def deckRow(self, node, depth, cnt):
    return node.htmlRow(self, depth, cnt)


DeckBrowser._deckRow = deckRow

DeckBrowser._renderDeckTree = renderDeckTree

DeckBrowser._linkHandler = _linkHandler
