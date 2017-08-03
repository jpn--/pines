#!/usr/bin/env python
import os
import zipfile



def _rec_split(s):
	rest, tail = os.path.split(s)
	if rest in ('', os.path.sep):
		return tail,
	return _rec_split(rest) + (tail,)

def _any_dot(s):
	for i in _rec_split(s):
		if len(i)>0 and i[0]=='.':
			return True
	return False

def _zipdir(path, ziph, skip_dots=True, extra_layer=True):
	# ziph is zipfile handle
	keep_dots = not skip_dots
	for root, dirs, files in os.walk(path):
		folder = os.path.basename(root)
		if keep_dots or not _any_dot(folder):
			print('zipping folder:', folder, "in", root)
			for file in files:
				if keep_dots or not _any_dot(file):
					ziph.write(os.path.join(root, file), os.path.relpath(os.path.join(root, file), os.path.join(path, '..' if extra_layer else '.')))
		else:
			print('not zipping folder:', folder, "in", root)

def zipdir(source_dir, zip_file_name=None, skip_dots=True, extra_layer=False):
	"""

	Parameters
	----------
	source_dir
	zip_file_name : str
		If not given, uses the name of the sourcedir.
	skip_dots : bool, defaults True
		Ignore files and dirs that start with a dot.

	Returns
	-------
	str
		zip_file_name
	"""
	if zip_file_name is None:
		if source_dir[-1] in ('/', '\\'):
			usepath = source_dir[:-1]
		else:
			usepath = source_dir
		zip_file_name = usepath + '.zip'
	with zipfile.ZipFile(zip_file_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
		_zipdir(source_dir, zipf, skip_dots=skip_dots, extra_layer=extra_layer)
	return zip_file_name

def zipmod(module, zip_file_name, skip_dots=True):
	"""
	Create a zipfile from a module

	Parameters
	----------
	module
	zip_file_name
	skip_dots

	Returns
	-------

	"""
	with zipfile.ZipFile(zip_file_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
		_zipdir(module.__path__[0], zipf, skip_dots=skip_dots)


def zipmod_temp(module, skip_dots=True):
	import tempfile
	tempdir = tempfile.TemporaryDirectory()
	zip_file_name = os.path.join(tempdir.name, module.__name__+".zip")
	zipmod(module, zip_file_name, skip_dots=skip_dots)
	return zip_file_name, tempdir