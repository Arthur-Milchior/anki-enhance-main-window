from .config import getUserOption
from anki.lang import _

## CSS

defaultCSS = """/* Tooltip container */
        a:hover{
         cursor: pointer;
        }

        /* Tooltip text */
        .tooltip .tooltiptext {
            visibility: hidden;
            background-color: black;
            color: #fff;
            text-align: center;
            padding: 5px 0;
            border-radius: 6px;

            /* Position the tooltip text - see examples below! */
            position: absolute;
            z-index: 1;
        }

        /* Show the tooltip text when you mouse over the tooltip container */
        .tooltip:hover .tooltiptext {
            visibility: visible;
        }

	/* padding-left for header columns except deck-column */
	th.count {
          padding-left:15px;
          cursor: pointer;
	}

	"""
css = getUserOption("css", defaultCSS)

## JS
js = """/* Copyright: Ankitects Pty Ltd and contributors
 * License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html */


function init() {


    $("tr.deck").draggable({
        scroll: false,

        // can't use "helper: 'clone'" because of a bug in jQuery 1.5
        helper: function (event) {
            return $(this).clone(false);
        },
        delay: 200,
        opacity: 0.7
    });
    $("th.count").draggable({
        scroll: false,

        // can't use "helper: 'clone'" because of a bug in jQuery 1.5
        helper: function (event) {
            return $(this).clone(false);
        },
        delay: 200,
        opacity: 0.7
    });
    $("tr.deck").droppable({
        drop: handleDropEvent,
        hoverClass: 'drag-hover'
    });
    $("th.count").droppable({
        drop: columnDropEvent,
        hoverClass: 'drag-hover'
    });
    $("tr.top-level-drag-row").droppable({
        drop: handleDropEvent,
        hoverClass: 'drag-hover'
    });
}
$(init);

function handleDropEvent(event, ui) {
    var draggedDeckId = ui.draggable.attr('id');
    var ontoDeckId = $(this).attr('id') || '';

    pycmd("drag:" + draggedDeckId + "," + ontoDeckId);
}

function columnDropEvent(event, ui) {
    var draggedDeckId = ui.draggable.attr('colpos');
    var ontoDeckId = $(this).attr('colpos') || '';
    pycmd("dragColumn:" + draggedDeckId + "," + ontoDeckId);
}
"""

######################
#header related html #
######################
start_header = """
  <tr style = "vertical-align:text-top">"""

deck_header = f"""
    <th colspan = 5 align = left>
      {_("Deck")}
    </th>"""
def column_header(heading, colpos):
    return f"""
    <th class = "count ui-draggable ui-draggable-handle ui-droppable" colpos = "{colpos}">
      <a onclick = "return pycmd('optsColumn:{colpos}');">
        {_(heading)}
      </a>
    </th>"""

option_header = """
    <th></th>"""

option_name_header = """
    <td></td>"""

end_header = """
  </tr>"""



##############
#deck's html #
##############
def start_line(klass,did):
    return f"""
  <tr class = '{klass}' id = '{did}'>"""

def collapse_children_html(did,name,prefix):
    return f"""
      <a class = collapse onclick = 'return pycmd("collapse:{did}")' id = "{name}" href = "#{name}" >
         {prefix}
      </a>"""
collapse_no_child = """
      <span class = collapse></span>"""

def deck_name(depth,collapse,extraclass,did,cssStyle,name):
    return f"""
    <td class = decktd colspan = 5>
      {"&nbsp;"*6*depth}{collapse}
      <a class = "deck{extraclass}" onclick = "return pycmd('open:{did}')">
        <font style = '{cssStyle}'>
          {name}
        </font>
      </a>
    </td>
"""

def number_cell(colour, number, description):
    if description is None or description is False:
        description = ""
        t= f"""
    <td align = 'right'>"""
    else:
        description = f"""
      <span class = 'tooltiptext'>
        {description}
      </span>"""
        t= f"""
    <td align = 'right' class = 'tooltip'>"""
    # if number:
    t+=f"""
      <font color = '{colour}'>
        {number}
      </font>"""
    if description:
        t+=f"""
      {description}"""
    t+="""
    </td>"""
    return t


def gear(did):
    return f"""
    <td align = center class = opts>
      <a onclick = 'return pycmd(\"opts:{int(did)}\");'>
        <img src = '/_anki/imgs/gears.svg' class = gears>
      </a>
    </td>"""

def deck_option_name(option):
    return f"""
    <td>
      {option}
    </td>"""

end_line = """
  </tr>"""

def bar(name, width, left, color, overlay):
    return f"""
          <div class="tooltip bar" style="position:absolute; height:100%; width:{width}%; background-color:{color}; left :{left}% ;">
            <!-- {name}-->
            <span class="tooltiptext">
              {overlay}
            </span>
          </div>"""

def progress(content):
    return f"""
      <div class="progress" style="position:relative;	height:1em;	display:inline-block;	width:100px;		">{content}
      </div>"""
