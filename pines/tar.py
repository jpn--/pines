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

def extract_targz_string(s, path=".", members=None, return_listdir=True):
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
	import io,tarfile
	with io.BytesIO() as bt:
		bt.write(s)
		bt.seek(0)
		with tarfile.open(fileobj=bt,mode='r:gz') as tf:
			tf.extractall(path=path, members=members)
	if return_listdir:
		if path==".":
			return os.getcwd(), os.listdir(path)
		else:
			return path, os.listdir(path)


def send_package_to_dask_workers(directory, scheduler_ip=None, client=None):
	"""
	Send a package to all workers

	One of client and scheduler_ip should be given.

	Parameters
	----------
	directory : str
	scheduler_ip : str
		ignored if client is given
	client : dask.distributed.Client

	"""
	if client is None:
		if scheduler_ip is None:
			raise ValueError("must give scheduler or client")
		from dask.distributed import Client
		if isinstance(scheduler_ip, Client):
			client = scheduler_ip
		elif isinstance(scheduler_ip, str):
			client = Client(f"{scheduler_ip}:8786")
		else:
			raise TypeError("bad scheduler")
	from dask.distributed import wait
	s = directory_to_targz_string(directory)
	versions = client.get_versions()
	if 'workers' in versions:
		workers = versions['workers'].keys()
		futures = [client.submit(extract_targz_string, s, workers=[w]) for w in workers]
		wait(futures)
		return futures
	else:
		raise ValueError('no workers')