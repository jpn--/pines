
from . import configure
import os
import logging, logging.handlers

_time_format = '%b %d %H:%M:%S'
_mess_format = '%(asctime)15s %(name)s %(levelname)s %(message)s'


_worker_local_dir = None


def new_worker(scheduler=None, name=None, cfg=None, gui_loop_callback=None, **kwargs):
	global _worker_local_dir
	if cfg is None:
		cfg = configure.check_config(['cluster.worker_log', 'cluster.scheduler'], window_title="PINES CLUSTER WORKER CONFIG")
	if 'worker_log' in cfg.cluster:
		handler = logging.handlers.RotatingFileHandler(cfg.cluster['worker_log'], 'a', 10000, 10)
		formatter = logging.Formatter(fmt=_mess_format, datefmt=_time_format)
		handler.setFormatter(formatter)
		logging.getLogger('distributed').addHandler(handler)
		logging.getLogger('distributed').setLevel(logging.DEBUG)
		logging.getLogger('distributed').info(f"opening log for {name}")

	if scheduler is None:
		scheduler = cfg.cluster['scheduler']

	if scheduler is None: # still...
		raise ValueError('no scheduler known, set one in pines.configure .cluster')

	from distributed import Worker
	from tornado.ioloop import IOLoop
	from threading import Thread

	if name is None:
		if 'worker_name' in cfg.cluster:
			name = cfg.cluster['worker_name']
		else:
			import socket
			name = socket.getfqdn()

	loop = IOLoop.current()
	t = Thread(target=loop.start, daemon=True)
	t.start()

	scheduler_location = f'tcp://{scheduler}:8786'
	logging.getLogger('distributed').info(f"starting worker {name} for {scheduler_location}")

	w = Worker(scheduler_location, loop=loop, name=name, **kwargs)
	w.start()  # choose randomly assigned port

	_worker_local_dir = w.local_dir

	if gui_loop_callback is not None:
		gui_loop_callback(w, cfg)

	t.join()

	logging.getLogger('distributed').critical(f"ending worker {name} for {scheduler_location}")



def receive_tar_package(s, packagename=None):
	global _worker_local_dir
	from .tar import extract_targz_string
	use_path = _worker_local_dir or "."
	result = extract_targz_string(s, path=use_path)
	mod = None
	if packagename is not None:
		import sys, importlib
		importlib.invalidate_caches()
		if packagename in sys.modules:
			mod = importlib.reload(sys.modules[packagename])
		else:
			mod = importlib.import_module(packagename)
	return result, mod


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
	from .tar import directory_to_targz_string
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
	package_name = os.path.basename( directory.rstrip("/").rstrip("\\") )
	s = directory_to_targz_string(directory)
	client.run(receive_tar_package, s, package_name)
	# versions = client.get_versions()
	# if 'workers' in versions:
	# 	workers = versions['workers'].keys()
	# 	futures = []
	# 	for w in workers:
	# 		logging.getLogger('distributed').info(f"sending {package_name} to {w}")
	# 		futures.append(client.run(receive_tar_package, s, package_name, workers=[w.strip('tcp://').split(':')[0]]) )
	# 	wait(futures)
	# 	return futures
	# else:
	# 	raise ValueError('no workers')




if __name__=='__main__':
	w=new_worker()

	
