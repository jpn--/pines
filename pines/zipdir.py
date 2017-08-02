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
					ziph.write(os.path.join(root, file))

def zipdir(source_dir, zip_file_name, skip_dots=True):
	with zipfile.ZipFile(zip_file_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
		_zipdir(source_dir, zipf)

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
		_zipdir(module.__path__[0], zipf)


