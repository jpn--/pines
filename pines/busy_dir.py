from .logger import flogger
flog = flogger(label="BUSYDIR")

import os
import time
from contextlib import contextmanager
from threading import Lock

@contextmanager
def locked_directory(dirname, retry_after=5, timeout=600, busy_flag="__BUSY__"):
	busy_file = os.path.join(dirname, busy_flag)

	# check if there's another lock
	while os.path.exists(busy_file) and timeout>0:
		flog.info(f"waiting on {dirname}")
		timeout -= retry_after
		time.sleep(retry_after)

	if timeout <= 0:
		raise BlockingIOError(f'directory {dirname} is locked')

	# ready to lock
	flog.info(f"locking {dirname} by file")
	with open(busy_file, 'w') as f1:
		f1.write('busy')

	try:
		yield dirname
	except:
		raise
	finally:
		flog.info(f"releasing {dirname} by file")
		os.remove(busy_file)




def lock_for_time(dirname, delay=10, retry_after=5, timeout=600, busy_flag="__BUSY__"):
	from threading import Timer

	busy_file = os.path.join(dirname, busy_flag)

	# check if there's another lock
	while os.path.exists(busy_file) and timeout>0:
		flog.info(f"waiting on {dirname}")
		timeout -= retry_after
		time.sleep(retry_after)

	if timeout <= 0:
		raise BlockingIOError(f'directory {dirname} is locked')

	# ready to lock
	flog.info(f"locking {dirname} for {delay}")
	with open(busy_file, 'w') as f1:
		f1.write('busy')

	def release():
		os.remove(busy_file)

	t = Timer(delay, release)
	t.start()


_lockers = {}

@contextmanager
def locker(name, retry_after=15, timeout=300):

	global _lockers
	if name not in _lockers:
		_lockers[name] = Lock()

	while True:
		have_lock = _lockers[name].acquire(timeout=retry_after)
		if have_lock:
			break
		else:
			timeout -= retry_after
			if timeout<=0:
				raise BlockingIOError(f'locked {name} is stuck')
			else:
				flog.info(f"waiting on lock for {name}")

	try:
		# do something...
		flog.info(f"locking {name} by mutex")
		yield name
	finally:
		flog.info(f"releasing {name} by mutex")
		_lockers[name].release()

