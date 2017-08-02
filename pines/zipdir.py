#!/usr/bin/env python
import os
import zipfile

def _zipdir(path, ziph, skip_dots=True):
	# ziph is zipfile handle
	for root, dirs, files in os.walk(path):
		folder = os.path.basename(root)
		if (len(folder) and folder[0] != '.') or not skip_dots:
			for file in files:
				if file[0]!='.' or not skip_dots:
					ziph.write(os.path.join(root, file), os.path.relpath(os.path.join(root, file), os.path.relpath(os.path.join(root, file), os.path.join(path, '..'))))

def zipdir(source_dir, zip_file_name, skip_dots=True):
	with zipfile.ZipFile(zip_file_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
		_zipdir(source_dir, zipf, skip_dots=skip_dots)

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