

import sys
import os
try:
	import win32com.client 
except ImportError:
	_is_windows = False
else:
	_is_windows = True

def recursive_path_split(s):
	rest, tail = os.path.split(s)
	if rest in ('', os.path.sep):
		return tail,
	if tail == '':
		return rest,
	return recursive_path_split(rest) + (tail,)



def resolve_shortcut(x):
	"""If the given path is a Windows shortcut, resolve it"""
	if _is_windows:
		shell = win32com.client.Dispatch("WScript.Shell")
		if os.path.splitext(x)[1] not in ('.lnk','.url'):
			xlnk = x+'.lnk'
		if os.path.exists(xlnk):
			shortcut = shell.CreateShortCut(xlnk)
			return (shortcut.Targetpath)
		else:
			return x
	else:
		return x
		

def recursive_resolve_shortcut(x):
	"""Get a (real) file path given a path that may include windows shortcuts."""
	x_parts = recursive_path_split(x)
	built = x_parts[0]
	x_parts = x_parts[1:]
	while len(x_parts)>0:
		built = resolve_shortcut( os.path.join(built, x_parts[0]) )
		x_parts = x_parts[1:]
	return built

	
def exact_import(modulename, filepath, resolve_shortcuts=True):
	"""Import a specific python module or script as if it were a standard module.

	Parameters
	----------
	modulename : str
		The name the new module will receive
	filepath : str
		Where the module file is located
	resolve_shortcuts : bool, default True
		Should windows shortcuts in the path for the module file be resolved?
	"""
	import importlib.util
	if resolve_shortcuts:
		filepath = recursive_resolve_shortcut(filepath)
	spec = importlib.util.spec_from_file_location(modulename, filepath)
	foo = importlib.util.module_from_spec(spec)
	spec.loader.exec_module(foo)
	return foo
