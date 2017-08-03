from .logger import flogger
flog = flogger(label="BUSYDIR")

import os
import time
from contextlib import contextmanager


@contextmanager
def locked_directory(dirname, retry_after=5, timeout=600):
	busy_file = os.path.join(dirname, "__BUSY__")

	# check if there's another lock
	while os.path.exists(busy_file) and timeout>0:
		flog.info(f"waiting on {dirname}")
		timeout -= retry_after
		time.sleep(retry_after)

	if timeout <= 0:
		raise BlockingIOError(f'directory {dirname} is locked')

	# ready to lock
	flog.info(f"locking {dirname}")
	with open(busy_file, 'w') as f1:
		f1.write('busy')

	yield dirname

	flog.info(f"releasing {dirname}")
	os.remove(busy_file)



