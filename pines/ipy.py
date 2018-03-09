
from IPython.display import display_javascript
from IPython.display import display, Javascript
import os, time

def make_markdown_cell(s):
	display_javascript("""var t_cell = IPython.notebook.get_selected_cell()
    t_cell.set_text('<!--\\n' + t_cell.get_text() + '\\n--> \\n{}');
    var t_index = IPython.notebook.get_cells().indexOf(t_cell);
    IPython.notebook.to_markdown(t_index);
    IPython.notebook.get_cell(t_index).render();""".format(s.replace('\n' ,'\\n')), raw=True)


def notebook_save():
	display(Javascript('IPython.notebook.save_checkpoint();'))


def notebook_execute(notebook_filename, kernel_name='python3', timeout=600, execution_dir='./', output_filemark="", output_timestamp=True):
	import nbformat
	from nbconvert.preprocessors import ExecutePreprocessor

	if output_timestamp:
		output_filemark += time.strftime(".%Y.%m.%d-%H.%M")

	executed_notebook_filename = "{1}{0}{2}".format(
		output_filemark,
		*os.path.splitext(notebook_filename)
	)

	with open(notebook_filename) as f:
		nb = nbformat.read(f, as_version=4)

	ep = ExecutePreprocessor(timeout=timeout, kernel_name=kernel_name)

	ep.preprocess(nb, {'metadata': {'path': execution_dir}})

	with open(executed_notebook_filename, 'wt') as f:
		nbformat.write(nb, f)

