# Configuration of Anki's addon Enhanced Main

1. We first discuss the various small configurations related to the whole add-on.
1. We then explain how to configure each column.
1. We then explain how to configure coloring related to empty decks.
1. We finally explain how to configure coloring related to marked cards.

## Miscelaneous
In this section, we describe various small configurations related to the whole add-on.

### Option
Whether you want to display the deck option's name at the end of its line.


### cap value
By default, without an add-on, Anki never shows numbers greater than a thousand. Instead, it shows 1000+. You can decide to change the thousand to an arbitrary number, or leave this value to null which always show the real value.

Note that capping to a thousand does not usually make the rendering quicker.

### Dot in number
Whether you want a thousand separator for big numbers, such as 34968, to be shown as "34.968" or as "34968".

### hide values of parent decks
If a deck has children, its number are not shown.

### hide values of parent decks when subdecks are shown
Similar to last option, but it hides number only if the subdecks are shown.

### color zero
The color to use for the zero. If it's a string, use always this color. By default in Anki, it's a kind of grey. If you set it to false (default in this add-on), then the zero is not shown at all. You can remove this line or set it to `null` to ensure that the default column is used. To obtain the grey which is the default value in Anki, you can set the color to "#e0e0e0".

## Columns

Each column should occur after the line "columns" :[, and before the line with a closing bracket ]. The order of the lines is important, since it's the order in which columns will be displayed by Anki. This means that you can reorder columns in Anki by reordering the lines in the configuration. You can copy a line to display a column multiple times (for example, once using percent, and another time using absolute number).

Each column is represented between an opening curly bracket {, and a closing curly bracket }. Each column uses 8 parameters, each represented as a pair.
>>key:value
We'll tell you the meaning of each key, whether you can change its value, and what this change will do.

### Name
The first value is a description, which will tell you what the column represents. Do NOT alter this value, or the add-on will raise an error.

### Description
A description of the content of the column. This is not used by Anki. It allows you to decide whether you want the column while you edit the configuration.


### Present
The value for the key "present" is either true or false. If the value is set to true, the column will be displayed. Otherwise, it will not. Note that you can also delete the entire column from the configuration, instead of changing the value to false.

If this value is absent, by default, it is assumed that it should be set to true.

### Header
The header of the column. If you leave `null` then the default header will be used. This description will be translated as much as it is possible to do it automatically. However, you can also choose to write your own description. You can use HTML in this description. You should use "<br/>" when you want a newline.

### Overlay
The text shown when your mouse is over a number. It will describe what this number represents. You can set this key to false if you want no description to be present. And leave this value to `null` if you want to use the default value.

### Color
The color in which the number is written in this column. You can use any color acceptable in an HTML document. Most standard color names should work. `null` means that it should use the same color as in the statistic window, if this color exists, or the default color otherwise.

###  Percent
true or false whether you want to show the percent of cards satisfying this column condition. For example, 23% of cards are new. Note that sometimes this would not make sense. For example, for the column «cards», the value will always be 100% (unless the deck is empty). For the column notes, the number would not really make any sense (formally, you'd get the percent of cards which is the first of its siblings in this deck).

By default, the percent is assumed to be false if absent.

### Absolute
Whether you want an absolute number in your column. That is, a number which is not a percentage, but an exact number.

By default, this value is false if Percent is set to true, otherwise its default value is true.

### Subdecks
When you consider a deck which has subdecks, a true value considers cards in its subdecks; a false value ignores cards in its child subdecks.

## Coloring decks
The author of this add-on wants to know when a deck is empty. This is very important to him, because he wants to add new cards in them as soon as possible. Thus, this add-on changes the color of the names of empty decks, and of the names of decks with an empty descendant.

The author also wants to know which deck has marked cards. Thus, the background of the deck's name having marked cards changes color.

Both of these configurations can be changed as explained in this section. In particular, you can turn one or both of these options off by setting "color empty" and "color marked" to false.

### Choice of color
#### Color empty
The color of the names of decks without new cards

#### Color empty descendant
The color of the names of decks with a descendant without new cards

#### Default color
The color of a deck which every descendant has new cards.

#### Default column color
The color of the content of a deck, if no other color is specified.

#### ended marked background color
The color of the decks which have an ended deck with marked cards. The notion of ended deck will be explained in the next section of this documentation.

#### Marked background color
The color of decks who have marked cards but none of its descendants are both ended and have marked cards.

### Deck modifier
A deck modifier is a symbol (or a word, etc.) whose presence in a deck name changes the meaning of the deck. When the meaning is changed, the coloration is also changed. It's not clear to the author of this add-on whether anyone apart from himself will need those, but if you want to use them, here is the explanation.

The first three symbols currently have the same effect, but one day this effect may change, according to what the author wants to do.

#### End symbol
By default, this symbol is ";". It means that the deck is definitively done, and no new card may ever be added to it. When a deck has this symbol, neither itself nor its descendants will ever be colored.

#### Given up symbol
By default, this symbol is "/". To the author, it means that no new card will be added because this deck is either too hard, or not interesting enough.

#### Pause symbol"
By default, this symbol is "=". To the author, it means that more new cards will be added later, but right now it does not want Anki to change the color of the deck's name. In a future version, there may be an option to change the color of these decks.
