This file explains how this add-on works.

# Files
## ChangeFunction
This file is in charge of monkey-patching each function which must be
monkey patched.

## Config
This file is in charge of reading user's configuration. It is also updated
if an outdated configuration file is found.

## Debug
Function which helps debugging. Normally, mayDebug and shouldDebug
must be False in the code distributed, and thus no debugging occurs.

## Html
Contains all of the HTML which is used to generate the list of decks in
the main window. The HTML is either contained in a string variable if
it does not change, or in a small function which takes a parameter and
returns the HTML string.

## Strings
This associates to each column some strings describing it: a short one
used in the header of the column, and a longer one used in the overlay
describing the number.

## Tree
Contains functions used to compute global information, e.g. how
many cards there are of each kind in each deck (not considering the
subdeck), and how much time to wait before the next review.

It's computed globally because it allows a single query instead
of having to do one query per deck.

## Node
Globally, it contains everything else. It contains each computation
which must be done recursively on a deck by deck basis, and the
function to print each deck.
