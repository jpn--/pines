from . import configure
from . import egnyte as pe
from distributed import Worker, Nanny as _Nanny

import os
import logging, logging.handlers

_time_format = '%b %d %H:%M:%S'
_mess_format = '%(asctime)15s %(name)s %(levelname)s %(message)s'

_worker_local_dir = None


class Nanny(_Nanny):
	def change_ncores(self, *arg, **kwarg):
		new_ncores = kwarg.pop('new_ncores')
		logging.getLogger('distributed').info(f"changing ncores to {new_ncores}")
		if new_ncores is not None:
			self.ncores = new_ncores
			if self.process:
				self.process.worker_kwargs['ncores'] = new_ncores

	def __init__(self, *arg, **kwarg):
		super().__init__(*arg, **kwarg)
		self.handlers['change_ncores'] = self.change_ncores


def new_worker(scheduler=None, name=None, cfg=None, gui_loop_callback=None, resources=None, **kwargs):
	global _worker_local_dir
	if cfg is None:
		cfg = configure.check_config(['cluster.worker_log', 'cluster.scheduler'],
		                             window_title="PINES CLUSTER WORKER CONFIG")
	if 'worker_log' in cfg.cluster:
		handler = logging.handlers.RotatingFileHandler(cfg.cluster['worker_log'], 'a', 1000000, 10)
		formatter = logging.Formatter(fmt=_mess_format, datefmt=_time_format)
		handler.setFormatter(formatter)
		logging.getLogger().addHandler(handler)
		logging.getLogger().setLevel(logging.INFO)
		logging.getLogger('distributed').info(f"opening log for {name}")

	if scheduler is None:
		scheduler = cfg.cluster['scheduler']

	if scheduler is None:  # still...
		raise ValueError('no scheduler known, set one in pines.configure .cluster')

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

	if resources:
		logging.getLogger('distributed').info(f"worker {name} has resources {str(resources)}")

	w = Nanny(scheduler_location, loop=loop, name=name, resources=resources, **kwargs)
	w.start()  # choose randomly assigned port

	w.cfg = cfg

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
		logging.getLogger('distributed').critical(f"received package {packagename} attempting to import")
		import sys, importlib
		importlib.invalidate_caches()
		import importlib.util
		spec = importlib.util.find_spec(packagename)
		print("spec", spec)
		if packagename in sys.modules:
			logging.getLogger('distributed').critical(f"received package {packagename} already exists, reloading")
			mod = importlib.reload(sys.modules[packagename])
		else:
			logging.getLogger('distributed').critical(
				f"received package {packagename} does not already exist, importing")
			try:
				mod = importlib.import_module(packagename)
			except ModuleNotFoundError:
				logging.getLogger('distributed').critical(f"ModuleNotFoundError on {packagename}")
				mod = None
		if mod is not None:
			logging.getLogger('distributed').critical(f"Adding {packagename} to sys.modules")
			import sys
			sys.modules[packagename] = mod
		importlib.invalidate_caches()
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
	package_name = os.path.basename(directory.rstrip("/").rstrip("\\"))
	s = directory_to_targz_string(directory)
	return client.run(receive_tar_package, s, package_name)


def new_worker_with_egnyte():
	cfg = configure.check_config(
		['cluster.worker_name', 'cluster.worker_log', 'cluster.working_dir', 'cluster.scheduler',
		 'cluster.ncores', 'cluster.ratelimit', 'egnyte.access_token', 'private_pip.python_packages'],
		secrets=['egnyte.username', 'egnyte.password', ],
		window_title="CLUSTER WORKER CONFIG")

	if not cfg['egnyte.access_token']:
		token = pe.get_access_token(username=cfg.egnyte.username, password=cfg.egnyte.password, return_token=True)
		cfg['egnyte.access_token'] = token
		configure.add('egnyte.access_token', token)
	else:
		pe.set_access_token(cfg['egnyte.access_token'])

	if cfg.private_pip.python_packages:
		from .private_pip import pip_install
		pip_install(cfg.private_pip.python_packages)

	try:
		ncores = int(cfg.cluster.ncores)
	except:
		ncores = None

	new_worker(cfg=cfg, gui_loop_callback=None, ncores=ncores)


if __name__ == '__main__':
	w = new_worker()


