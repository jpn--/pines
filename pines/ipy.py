
from IPython.display import display_javascript

def make_markdown_cell(s):
	display_javascript("""var t_cell = IPython.notebook.get_selected_cell()
    t_cell.set_text('<!--\\n' + t_cell.get_text() + '\\n--> \\n{}');
    var t_index = IPython.notebook.get_cells().indexOf(t_cell);
    IPython.notebook.to_markdown(t_index);
    IPython.notebook.get_cell(t_index).render();""".format(s.replace('\n' ,'\\n')), raw=True)



