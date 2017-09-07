

from . import egnyte as pe
import re
import time
import json
import pandas
import os
from .logger import flogger
from dask.distributed import Client as _Client, Future
from distributed.core import rpc as _rpc

from .timesize import timesize
from .counter import Counter

clog = flogger(label='CLUSTER')

clog("this is cluster log")

from .hardware_info import node, processor_name
_computer = node()
_processor = processor_name()

class Client(_Client):

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self._futures_bank = []
		self.suspended_nannies = set()

	def submit(self, *args, **kwargs):
		i = super().submit(*args, **kwargs)
		self._futures_bank.append(i)
		return i

	def task_status(self):
		count = Counter()
		for f in self._futures_bank:
			if isinstance(f,Future):
				kind = f.key.rsplit('-',1)[0]
				count.one(f'{kind}.{f.status}')
			else:
				count.one('?')
		return count

	def worker_status(self):
		worker_info = self.scheduler_info()['workers']
		now = time.time()
		worker_data = [(
			ip,
			i['name'] if 'name' in i else "n/a",
			i['ncores'] if 'ncores' in i else -999,
			i['executing'] if 'executing' in i else -999,
			i['ready'] if 'ready' in i else -999,
			i['in_memory'] if 'in_memory' in i else -999,
			timesize(now-i['last-seen'])+" ago" if 'last-seen' in i else "n/a",
			timesize(now-i['last-task'])+" ago" if 'last-task' in i else "n/a",
		) for ip,i in worker_info.items()]
		result = pandas.DataFrame(
			columns=['address','name','ncores','executing','ready','in-memory','last-seen','last-task'],
			data=worker_data
		)
		return result

	def retire_workers(self, workers_to_retire):
		"""
		Cleanly retire a worker, moving saved results to other workers first.

		Parameters
		----------
		workers_to_retire

		Returns
		-------

		"""
		def retirements(w, dask_scheduler=None):
			dask_scheduler.retire_workers(workers=w)
		self.run_on_scheduler(retirements, workers_to_retire)

	def change_worker_ncores(self, worker, new_ncores):
		"""
		Change the ncores on a worker.

		The worker must have a nanny.  Using this function will restart the worker.

		Parameters
		----------
		worker : str
			address of the worker to modify
		new_ncores : int
			new ncores to relaunch the worker with

		Returns
		-------

		"""
		def delta_ncores(worker_, ncores_, dask_scheduler=None):
			nanny_addr = dask_scheduler.get_worker_service_addr(worker_, 'nanny')
			if nanny_addr is None:
				raise ValueError(f'worker {worker_} must have a nanny to use change_worker_ncores')
			nanny = _rpc(nanny_addr)
			nanny.change_ncores(new_ncores=ncores_)
			nanny.restart(close=True)
			nanny.close_rpc()
		return self.run_on_scheduler(delta_ncores, worker, new_ncores)

	def change_resources(self, worker, new_resources=None):

		def delta_resource(worker_, resources, dask_scheduler=None):
			# remove_resources(self, worker):
			if worker_ in dask_scheduler.worker_resources:
				del dask_scheduler.used_resources[worker_]
				for resource, quantity in dask_scheduler.worker_resources.pop(worker_).items():
					del dask_scheduler.resources[resource][worker_]
			# add_resources(self, stream=None, worker=None, resources=None):
			if worker_ not in dask_scheduler.worker_resources:
				dask_scheduler.worker_resources[worker_] = resources.copy()
				dask_scheduler.used_resources[worker_] = resources.copy()
				for resource, quantity in resources.items():
					dask_scheduler.used_resources[worker_][resource] = 0
					dask_scheduler.resources[resource][worker_] = quantity


		new_resources = new_resources or {}
		self.run_on_scheduler(delta_resource, worker, new_resources)

	def get_worker_address_by_name(self, name):
		worker_info = self.scheduler_info()['workers']
		for addr, i in worker_info.items():
			if 'name' in i:
				if i['name']==name:
					return addr

	def suspend_workers(self, workers):
		### run this on the scheduler
		def _prepare_workers_for_disconnect(workers, dask_scheduler=None):
			workers = set(workers)
			if len(workers) > 0:
				keys = set.union(*[dask_scheduler.has_what[w] for w in workers])
				keys = {k for k in keys if dask_scheduler.who_has[k].issubset(workers)}
			else:
				keys = set()

			other_workers = set(dask_scheduler.worker_info) - workers
			if keys:
				if other_workers:
					yield dask_scheduler.replicate(keys=keys, workers=other_workers, n=1, delete=False)
			# get nanny addresses
			nannie_addresses = {addr: dask_scheduler.get_worker_service_addr(addr, 'nanny')
								for addr in workers}

			nannies = [_rpc(nanny_address)
						for nanny_address in nannie_addresses.values()
						if nanny_address is not None]
			# kill worker
			try:
				[nanny.restart(close=True) for nanny in nannies]
			finally:
				for nanny in nannies:
					nanny.close_rpc()
			# return nanny address
			return [nanny_address for nanny_address in nannie_addresses.values()]
		self.suspended_nannies += set( self.run_on_scheduler(_prepare_workers_for_disconnect, workers) )

# OLD CLUSTER ...
#
# def _claim_job(results_dir, job_no, job_descrip, job_file):
# 	clog(f"attempting to claim job {job_no}: {job_descrip}")
# 	claimed_result_folder = pe.create_folder(pe.pth(results_dir, f'{job_no} {job_descrip} {_computer}'))
# 	# Write a short summary of the claim
# 	this_claim = {
# 		'claimtime': time.strftime('%Y %B %d, %I:%M:%S %p (%Z %z)'),
# 		'computer': _computer,
# 		'cpu': _processor,
# 	}
# 	pe.upload_dict_json(this_claim, f'_claim_{_computer}.json', claimed_result_folder)
# 	job_json = pe.download_dict_json(job_file)
# 	clog(f"claimed job {job_no}: {job_descrip}")
# 	return job_json, claimed_result_folder
#
#
# def claim_next_unclaimed_job(jobs_dir, results_dir=None):
# 	if results_dir is None:
# 		results_dir = jobs_dir
#
# 	if isinstance(jobs_dir, str) and jobs_dir[-1] != '/':
# 		raise TypeError('jobs_dir must be a folder path ending in a slash')
# 	if isinstance(results_dir, str) and results_dir[-1] != '/':
# 		raise TypeError('results_dir must be a folder path ending in a slash')
#
# 	is_job = re.compile('^([0-9]+)\\s+(.+)\.json$')
# 	job_folder = pe.client.folder(pe.pth(jobs_dir))
# 	results_folder = pe.client.folder(pe.pth(results_dir))
#
# 	pe._load_obj(job_folder)
# 	pe._load_obj(results_folder)
# 	for fi in job_folder.files:
# 		clog(f'checking {fi.name} to see if it is a job')
# 		match = is_job.match(fi.name)
# 		if match:
# 			clog(f'yes {fi.name} is a job')
# 			# a job .json config file is found, see if it is claimed
# 			job_no = match.group(1)
# 			job_descrip = match.group(2)
# 			is_job_result = re.compile(f'^({job_no})\\s+')
#
# 			if len(results_folder.folders)==0:
# 				# no jobs are claimed, so can claim this job
# 				return _claim_job(results_dir, job_no, job_descrip, fi)
# 			else:
# 				already_claimed = False
# 				for fo in results_folder.folders:
# 					result_match = is_job_result.match(fo.name)
# 					if result_match is not None:
# 						clog(f"job {job_no} is already claimed")
# 						already_claimed = True
# 				if not already_claimed:
# 					# This is an available job, claim it
# 					return _claim_job(results_dir, job_no, job_descrip, fi)
# 		else:
# 			clog(f'no, {fi.name} is not a job')
# 	return None, None
#
#
# def unclaimed_jobs(jobs_dir, results_dir=None):
#
# 	if results_dir is None:
# 		results_dir = jobs_dir
#
# 	if isinstance(jobs_dir, str) and jobs_dir[-1] != '/':
# 		raise TypeError('jobs_dir must be a folder path ending in a slash')
# 	if isinstance(results_dir, str) and results_dir[-1] != '/':
# 		raise TypeError('results_dir must be a folder path ending in a slash')
#
# 	is_job = re.compile('^([0-9]+)\\s+(.+)\.json$')
# 	job_folder = pe.client.folder(pe.pth(jobs_dir))
# 	results_folder = pe.client.folder(pe.pth(results_dir))
#
# 	scan_for_jobs = True # initial condition
#
# 	while scan_for_jobs:
#
# 		pe._load_obj(job_folder)
# 		pe._load_obj(results_folder)
#
# 		scan_for_jobs = False # won't scan again unless we find new work
# 		for fi in job_folder.files:
# 			clog.debug(f'checking {fi.name} to see if it is a job')
# 			match = is_job.match(fi.name)
# 			if match:
# 				clog(f'{fi.name} is a job, checking if it is claimed')
# 				# a job .json config file is found, see if it is claimed
# 				job_no = match.group(1)
# 				job_descrip = match.group(2)
# 				is_job_result = re.compile(f'^({job_no})\\s+')
#
# 				if len(results_folder.folders)==0:
# 					# double check this is not changed since the results folder was cached
# 					pe._load_obj(results_folder)
# 					if len(results_folder.folders) == 0:
# 						# no jobs are claimed, so can claim this job
# 						scan_for_jobs = True
# 						yield _claim_job(results_dir, job_no, job_descrip, fi)
#
# 				if len(results_folder.folders) != 0:
# 					already_claimed = False
# 					for fo in results_folder.folders:
# 						result_match = is_job_result.match(fo.name)
# 						if result_match is not None:
# 							clog(f"job {job_no} is already claimed")
# 							already_claimed = True
# 					if not already_claimed:
# 						# double check this is not changed since the results folder was cached
# 						pe._load_obj(results_folder)
# 						for fo in results_folder.folders:
# 							result_match = is_job_result.match(fo.name)
# 							if result_match is not None:
# 								clog(f"job {job_no} is already claimed")
# 								already_claimed = True
# 					if not already_claimed:
# 						# This is an available job, claim it
# 						scan_for_jobs = True
# 						yield _claim_job(results_dir, job_no, job_descrip, fi)
# 			else:
# 				clog(f'{fi.name} is not a job')
# 	raise StopIteration
#
#
# from .repeater import create_csv_repeat_set, external_repeater, call_me
#
#
# def next_job_number(egnyte_path):
# 	c = re.compile('^([0-9]+)\\s.+')
# 	seen_max = 0
# 	eg_folder = pe.client.folder(pe.pth(egnyte_path))
# 	pe._load_obj(eg_folder)
# 	for fo in eg_folder.folders:
# 		match = c.match(fo.name)
# 		if match:
# 			seen_max = max(seen_max, int(match.group(1)))
# 	for fi in eg_folder.files:
# 		match = c.match(fi.name)
# 		if match:
# 			seen_max = max(seen_max, int(match.group(1)))
# 	return seen_max+1
#
#
#
# def json_emitter(kwarg_file, **kwargs):
# 	"""
# 	Use an external CSV file to iterate over keyword args passed to a function.
#
# 	Parameters
# 	----------
# 	func : callable
# 		This function gets called once for each row of the CSV file
# 	kwarg_file : str or file-like
# 		A csv file containing keywork args (simple data types as read by pandas)
#
# 	Other Parameters
# 	----------------
# 	args
# 		Positional arguments always passed to `func`
# 	kwargs
# 		Common keyword arguments always passed to `func`
#
# 	Returns
# 	-------
# 	list
# 		A list containing the return value of `func` for each row
# 		of the csv file.
# 	"""
# 	result = []
# 	df = pandas.read_csv(kwarg_file)
# 	direct_kw = {}
# 	indirect_kw = {}
# 	for k, v in kwargs.items():
# 		if isinstance(v, call_me):
# 			indirect_kw[k] = v
# 		else:
# 			direct_kw[k] = v
# 	for row in df.iterrows():
# 		local_kwargs = row[1].to_dict()
# 		indirect_kwargs = {k: v() for k, v in indirect_kw.items()}
# 		to_json = dict(**direct_kw, **indirect_kwargs, **local_kwargs)
# 		result.append(to_json)
# 	return result
#
#
# def looping_json_emitter(egnyte_dir, descrip, *loopers, **kwargs):
# 	buffer = create_csv_repeat_set(*loopers, filename=None, return_buffer=True)
# 	jsons = json_emitter(buffer, **kwargs)
# 	min_job_number = next_job_number(egnyte_dir)
# 	for jobnum, j in enumerate(jsons):
# 		clog(f'uploading job {min_job_number+jobnum}')
# 		pe.upload_dict_json(j, f'{min_job_number+jobnum} {descrip}.json', egnyte_dir)
# 	clog(f'looping_json_emitter complete')
#
#
# def looping_json_emitter_local(local_dir, min_job_number, descrip, *loopers, **kwargs):
# 	buffer = create_csv_repeat_set(*loopers, filename=None, return_buffer=True)
# 	jsons = json_emitter(buffer, **kwargs)
# 	for jobnum, j in enumerate(jsons):
# 		clog(f'local writing job {min_job_number+jobnum}')
# 		with open(os.path.join(local_dir, f'{min_job_number+jobnum} {descrip}.json'), 'w') as jfile:
# 			jfile.write(json.dumps(j))
# 	clog(f'looping_json_emitter_local complete')
