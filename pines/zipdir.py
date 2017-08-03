#!/usr/bin/env python
import os
import zipfile

def _zipdir(path, ziph, skip_dots=True):
	# ziph is zipfile handle
	skips = set()
	for root, dirs, files in os.walk(path):
		folder = os.path.basename(root)
		for s in skips:
			if s in root:
				continue
		if (len(folder) and folder[0] != '.') or not skip_dots:
			print('zipping folder:', folder, "in", root)
			for file in files:
				if file[0]!='.' or not skip_dots:
					ziph.write(os.path.join(root, file), os.path.relpath(os.path.join(root, file), os.path.join(path, '..')))
		else:
			print('not zipping folder:', folder, "in", root)
			skips.add(os.path.join(root,folder))

def zipdir(source_dir, zip_file_name=None, skip_dots=True):
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
		_zipdir(source_dir, zipf, skip_dots=skip_dots)
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