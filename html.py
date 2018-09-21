from aqt.qt import *

css="""/* Tooltip container */
        
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
        }"""
######################
#header related html #
######################
start_header="""<tr>"""
deck_header=f"""<th colspan=5 align=left>{_("Deck")}</th>"""
def column_header(heading):
    return f"<th class=count>{_(heading)}</th>"

option_header="<th class=count></th>"
option_name_header="""<td></td>"""
end_header="""</tr>"""


##############
#deck's html #
##############
def start_line(klass,did):
    return "<tr class='{klass}' id='{did}'>"

def collapse_children_html(did,name,prefix):
    return f"""<a class=collapse onclick='pycmd("collapse:{did}")' id="{name}" href="#{name}" >{prefix}</a>"""
collapse_no_child="<span class=collapse></span>"

def deck_name(depth,collapse,extraclass,did,cssStyle,name):
    return f"""
    
        <td class=decktd colspan=5>{"&nbsp;"*6*depth}{collapse}<a class="deck{extraclass}" onclick="pycmd('open:{did}')"><font style='{cssStyle}'>{name}</font></a></td>"""
def number_cell(colour,contents,description):
    return f"<td align='right' class='tooltip'><font color='{colour}'>{contents}</font><span class='tooltiptext'>{description}</span></td>"

deck_button_image="""<img valign=bottom src='/_anki/imgs/gears.svg' class=gears>"""
def deck_button(image):
    return f"<td align=right class=opts>{image}</td>"

def deck_option_name(option):
    return f"<td>{option}</td>"

end_line="</tr>"
