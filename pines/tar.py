import os, io, tarfile

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

def extract_targz_string(s,*args,**kwargs):
	"""

	Parameters
	----------
	s : bytes
		Content to ungzip and untar
	path : str
		Where to extract, defaults to current working directory.

	"""
	import io,tarfile
	with io.BytesIO() as bt:
		bt.write(s)
		bt.seek(0)
		with tarfile.open(fileobj=bt,mode='r:gz') as tf:
			tf.extractall(*args,**kwargs)


