
from . import configure

_time_format = '%b %d %H:%M:%S'
_mess_format = '%(asctime)15s %(name)s %(levelname)s %(message)s'

def new_worker(scheduler=None, name=None, cfg=None, **kwargs):
	if cfg is None:
		cfg = configure.check_config(['cluster.worker_log', 'cluster.scheduler'], window_title="PINES CLUSTER WORKER CONFIG")
	if 'worker_log' in cfg.cluster:
		import logging, logging.handlers
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
	
	t.join()

	logging.getLogger('distributed').critical(f"ending worker {name} for {scheduler_location}")

if __name__=='__main__':
	w=new_worker()

	
