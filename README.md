# anki-enhance-main-window
Heavily based on Helen Foster's code, from add-on "Deck_Counts_Now_Later"
Github: https://github.com/Arthur-Milchior/anki-enhance-main-window

Adds a lot of features to the main window. Allows to configure those features. Configurations are explained at the end of this document.

#Features

##Column
Most features offered by this add-on are related to some column. Here is the detail, column by column.

You can usually decide whether you want to have the number of cards in a deck, considering subdeck or not. Except when it would make no sens not to consider subdecks (e.g. the number of new cards seen today is dependant of the number of new cards in subdecks. However the number of unseen cards in a deck is independant of the number of unseen cards in subdecks)

###Name of the (sub)deck
There is not a lot of change in this column. Except that now, if a (sub)deck is empty, it turns red. (You can configure the color.)

This may not be useful for everybody. But if you want to know when a deck is empty in order to add new notes in it, it avoids to check in every deck the number of new cards. For example, if you want to learn guitar chords, it will let you know that it is time to add new chords to anki.

Better ! If you use subdeck, the parents of an empty subdeck becomes blue (also configurable). This allows you to find deck with an empty subdeck. Hence, it helps finding empty subdecks without having to uncollapse every top-level decks.

Note that, in some case, you don't want the name to become red. E.g. you wanted to learn the name of the greek letters. When you know all of them, you won't add any new note ever. You just have to add a semicolon (;) (it is configurable) to the name of the deck, and it will not turn red. 


###Learning
The number of review of cards in learning. By default you will see the number of review that can be done now, and in parenthesis the number of review which can be done later today.

###Review
The number of cards which you have seen in the past, and that you should see today. By default, the number of cards you will see today. And in parenthesis the number of cards you should see today, but that you will not see today because of your limite.


###New
Nothing changed here. New means «number of new cards you will see today». With the caveat that it is not exactly true for subdecks.

###Due
By default, this column is hidden. Indeed, it becames two columns «due now» and «later». We recall that, in Anki, a due card is a card which is not new, and that you have to view again today.

###Unseen
The number of cards which you have never answered. Most of these cards are cards you have never seens. But it also consider cards you have seens and buried. You may have seen it and buried it. By default, the number of unseen cards which you will discover today, and in parenthesis the number of unseen cards you will not see today.


###Buried
The number of Buried cards. Recall that a buried card is a card you will never see again, unless you unbury it manually (using the browser)

###Suspended
The number of Buried cards. Recall that a buried card is a card you will not see today. Either because you did press the «bury» button. Or because you saw another card of the same note, so it was automatically buried.

###Total
The number of cards in this deck. It is not the sum of the preceding column, since it contains also cards you have already seen and which are not yet due. (and it counts only once a card with multiple reviews)

###Today
The total number of review you will see today (assuming you always press good)

###Configuration
The last column states which configurations is used for the current deck. This avoids the pain to open the menu to see the option names. Really usefull when you have a lot of decks and want to see which is the last deck which used this old configuration you want to delete.

##Capping
By default, Anki does not show any number greater than 1000. Instead it shows 1000+.
You can now edit this limit. Or remove it entirely (by using a negative number). If you set the limit to 0, you will either see a 0, or "+".


How to configure this add-on
===========================
Most options are configurable. If some option is not, send me an email, I'll see what I can do.

In order to configure this add-on,(hence, to configure what is shown in the main window) Go to Tools>add-ons>[name of this add-on]>Edit. Find the line called
«USER CONFIGURATION». Below it, you will see a few options. Each are
explained in plain english. 