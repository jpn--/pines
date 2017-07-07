import os
import traceback
import concurrent.futures as cf


def _spin_up_single_thread(work_func, cfgs, log, pass_n):
	if log is not None: log('=== pines.multirunner.spin_up [single thread] begins ===')
	for n,cfg in enumerate(cfgs):
		if pass_n:
			work_func(cfg, n)
		else:
			work_func(cfg)
	if log is not None: log('=== pines.multirunner.spin_up [single thread] begins ===')


def spin_up(work_func, cfgs, max_workers = 8, log=None, single_thread=False, pass_n=True):
	"""
	Run a threadable function (typically a subprocess) in parallel.
	
	Parameters
	----------
	work_func : callable
		This does the work.	 It gets called with one or two arguments.	The first
		argument in always a config item from the cfgs list; the second is the integer
		enumeration (if `pass_n` is True). 
	cfgs : iterable
		An iterator of config items to pass to the workers.
	max_workers : int
		Maximum number of worker threads.
	log : logging.logger, default None
		If not None, log to this logger.
	single_thread : bool, default False
		If True, the work_func is not multithreaded, just run in sequence.	Useful for debugging.
	pass_n : bool, default True
		Should the enumerator be passed to the worker function?
	"""
	if single_thread:
		return _spin_up_single_thread(work_func, cfgs, log, pass_n)
	if log is not None: log('=== pines.multirunner.spin_up begins ===')
	with cf.ThreadPoolExecutor(max_workers=max_workers) as executor:
		exec_futures = {}
		for n,cfg in enumerate(cfgs):
			if log is not None: log(f'	= ThreadPoolExecutor {n} =')
			try:
				skip = cfg.skip
			except AttributeError:
				skip = False
			if not skip:
				if pass_n:
					fut = executor.submit(work_func, cfg, n)
				else:
					fut = executor.submit(work_func, cfg)
				exec_futures[fut] = n

		for future in cf.as_completed(exec_futures):
			n_future = exec_futures[future]
			try:
				data = future.result()
			except Exception as exc:
				if log is not None: 
					log(f'=== Thread {n_future} generated an exception ===')
					y = ("".join(traceback.format_exception(type(exc), exc, exc.__traceback__)))
					log(y)

	if log is not None: log('=== pines.multirunner.spin_up complete ===')



if __name__ == '__main__':

	from pines.qlog import qlog
	
	def bimp(*a, **k):
		raise TypeError('BIMP')

		
	cfg = [1,2,3,4,5,6]
	spin_up(bimp, cfg, max_workers = 8, log=qlog)

#	try:
#		raise TypeError('Blorf')
#	except Exception as e:
#		print(sys.exc_info())
#		print("".join(traceback.format_exception(type(e), e, e.__traceback__)))
#		
		
			
