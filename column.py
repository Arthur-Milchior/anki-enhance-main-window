from aqt.deckbrowser import DeckBrowser
from .config import writeConfig, getUserOption

lastHandler = DeckBrowser._linkHandler
def  _linkHandler(self,url):
    if ":" in url:
        (cmd, arg) = url.split(":")
        if cmd=="dragColumn":
            return columnHandler(self, arg)
    return lastHandler(self,url)


def columnHandler(self, arg):
    draggedDeckId, ontoDeckId = arg.split(",")
    draggedDeckId = int(draggedDeckId)
    ontoDeckId = int(ontoDeckId)
    columns = getUserOption("columns")
    columns.insert(draggedDeckId, columns.pop(ontoDeckId))
    writeConfig()
    self.show()
