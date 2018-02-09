# anki-enhance-main-window
Heavily based on Helen Foster's code, from add-on "Deck_Counts_Now_Later"
Github: https://github.com/Arthur-Milchior/anki-enhance-main-window

Adds a lot of features to the main window. Allows to configure those features. Configurations are explained at the end of this document.

#Features

##Column
Most features offered by this add-on are related to some column. Here is the detail, column by column

###Name of the (sub)deck
There is not a lot of change in this column. Except that now, if a (sub)deck is empty, it turns red. (You can configure the color.)

This may not be useful for everybody. But if you want to know when a deck is empty in order to add new notes in it, it avoids to check in every deck the number of new cards. For example, if you want to learn guitar chords, it will let you know that it is time to add new chords to anki.

Better ! If you use subdeck, the parents of an empty subdeck becomes blue (also configurable). This allows you to find deck with an empty subdeck. Hence, it helps finding empty subdecks without having to uncollapse every top-level decks.

Note that, in some case, you don't want the name to become red. E.g. you wanted to learn the name of the greek letters. When you know all of them, you won't add any new note ever. You just have to add a semicolon (;) (it is configurable) to the name of the deck, and it will not turn red. 

###New
Nothing changed here. New means «number of new cards you will see today». With the caveat that it is not exactly true for subdecks.

###Due
By default, this column is hidden. Indeed, it becames two columns «due now» and «later». We recall that, in Anki, a due card is a card which is not new, and that you have to view again today.

###Due now
This column is due to Helen Foster. Thank you ! This column contains the number of cards which are due (you must see it today), and that, in fact, you can view now. If you pressed «Again», (or  «good» on new cards), you will have cards you must see today, but not in the next 10 minutes. Hence those cards are due, but not due now.

If there are no «due now» cards but there are «due» cards, this columns will tell you in how many minutes is the next due cards. I.e. when you should come back to resume the study of this deck.

###Later
If you understood last section, this one should be easy to understand. It just lists the number of cards you'll have to review today, but that you can't review right now.

###Buried
The number of Buried cards. Recall that a buried card is a card you will never see again, unless you unbury it manually (using the browser)

###Suspended
The number of Buried cards. Recall that a buried card is a card you will not see today. Either because you did press the «bury» button. Or because you saw another card of the same note, so it was automatically buried.

###Unseen
The number of cards which you have never answered. Most of these cards are cards you have never seens. But it also consider cards you have seens and buried. You may have seen it and buried it

###Configuration
The last column states which configurations is used for the current deck. This avoids the pain to open the menu to see the option names. Really usefull when you have a lot of decks and want to see which is the last deck which used this old configuration you want to delete.

##Capping
By default, Anki does not show any number greater than 1000. Instead it shows 1000+.
You can now edit this limit. Or remove it entirely (by using a negative number). If you set the limit to 0, you will either see a 0, or "+".

##Column colouring
The numbers in each colours are colored. If you really want it to be configurable, send me an email. I don't really see the point in doing it right now.


How to configure this add-on
===========================
Most options are configurable. If some option is not, send me an email, I'll see what I can do.

In order to configure this add-on,(hence, to configure what is shown in the main window) Go to Tools>add-ons>[name of this add-on]>Edit. Find the line called
«USER CONFIGURATION». Below it, you will see a few options. Each are
explained in plain english.