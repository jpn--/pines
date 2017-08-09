import os, io, tarfile, hashlib, json
from .busy_dir import locker

def _sha512_checksum(s):
	sha512 = hashlib.sha512()
	sha512.update(s)
	return sha512.hexdigest()


def _save_hashes(hashes, path="."):
	"""
	Save configuration to a JSON file.
	If filename is not an absolute path, it will be prefixed with ~/.pines/
	"""
	filename = os.path.join(path, 'hashes.json')
	with open(filename, "w") as f:
		json.dump(hashes, f, indent=2, sort_keys=True)


def _load_hashes(path="."):
	filename = os.path.join(path, 'hashes.json')
	with open(filename, "r") as f:
		hashes = json.load(f)
	return hashes



def directory_to_targz_string(directory):
	"""
	tar and gzip a directory into a bytes string

	Parameters
	----------
	directory : str

	Returns
	-------
	bytes
	"""
	with io.BytesIO() as bt:
		with tarfile.open(fileobj=bt,mode='w:gz') as tf:
			tf.add(directory,arcname=os.path.basename(directory))
		bt.seek(0)
		s=bt.read()
	return s

def extract_targz_string(s, path=".", members=None, return_listdir=True, package_name=None):
	"""
	restore a tar-gzipped directory

	Parameters
	----------
	s : bytes
		Content to ungzip and untar
	path : str
		Where to extract, defaults to current working directory.
	members : list
		see tarfile.extractall

	"""

	skip_rewrite = False
	hashes = {}
	checksum = None

	with locker(path):

		if package_name is not None:
			hashes = _load_hashes(path=path)
			if package_name in hashes:
				checksum = _sha512_checksum(s)
				if checksum==hashes[package_name]:
					skip_rewrite = True

		if not skip_rewrite:
			with io.BytesIO() as bt:
				bt.write(s)
				bt.seek(0)
				with tarfile.open(fileobj=bt,mode='r:gz') as tf:
					tf.extractall(path=path, members=members)
			if package_name is not None:
				hashes[package_name] = checksum
				_save_hashes(hashes, path=path)

	if return_listdir:
		if path==".":
			return os.getcwd(), os.listdir(path)
		else:
			return path, os.listdir(path)


