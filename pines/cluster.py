

from . import egnyte as pe
import re
import time
import json
import pandas
import os
from .logger import flogger

clog = flogger(label='CLUSTER')

clog("this is cluster log")

from .hardware_info import node, processor_name
_computer = node()
_processor = processor_name()



def _claim_job(results_dir, job_no, job_descrip, job_file):
	clog(f"attempting to claim job {job_no}: {job_descrip}")
	claimed_result_folder = pe.create_folder(pe.pth(results_dir, f'{job_no} {job_descrip} {_computer}'))
	# Write a short summary of the claim
	this_claim = {
		'claimtime': time.strftime('%Y %B %d, %I:%M:%S %p (%Z %z)'),
		'computer': _computer,
		'cpu': _processor,
	}
	pe.upload_dict_json(this_claim, f'_claim_{_computer}.json', claimed_result_folder)
	job_json = pe.download_dict_json(job_file)
	clog(f"claimed job {job_no}: {job_descrip}")
	return job_json, claimed_result_folder


def claim_next_unclaimed_job(jobs_dir, results_dir=None):
	if results_dir is None:
		results_dir = jobs_dir

	if isinstance(jobs_dir, str) and jobs_dir[-1] != '/':
		raise TypeError('jobs_dir must be a folder path ending in a slash')
	if isinstance(results_dir, str) and results_dir[-1] != '/':
		raise TypeError('results_dir must be a folder path ending in a slash')

	is_job = re.compile('^([0-9]+)\\s+(.+)\.json$')
	job_folder = pe.client.folder(pe.pth(jobs_dir))
	results_folder = pe.client.folder(pe.pth(results_dir))

	pe._load_obj(job_folder)
	pe._load_obj(results_folder)
	for fi in job_folder.files:
		clog(f'checking {fi.name} to see if it is a job')
		match = is_job.match(fi.name)
		if match:
			clog(f'yes {fi.name} is a job')
			# a job .json config file is found, see if it is claimed
			job_no = match.group(1)
			job_descrip = match.group(2)
			is_job_result = re.compile(f'^({job_no})\\s+')

			if len(results_folder.folders)==0:
				# no jobs are claimed, so can claim this job
				return _claim_job(results_dir, job_no, job_descrip, fi)
			else:
				already_claimed = False
				for fo in results_folder.folders:
					result_match = is_job_result.match(fo.name)
					if result_match is not None:
						clog(f"job {job_no} is already claimed")
						already_claimed = True
				if not already_claimed:
					# This is an available job, claim it
					return _claim_job(results_dir, job_no, job_descrip, fi)
		else:
			clog(f'no, {fi.name} is not a job')
	return None, None


def unclaimed_jobs(jobs_dir, results_dir=None):

	if results_dir is None:
		results_dir = jobs_dir

	if isinstance(jobs_dir, str) and jobs_dir[-1] != '/':
		raise TypeError('jobs_dir must be a folder path ending in a slash')
	if isinstance(results_dir, str) and results_dir[-1] != '/':
		raise TypeError('results_dir must be a folder path ending in a slash')

	is_job = re.compile('^([0-9]+)\\s+(.+)\.json$')
	job_folder = pe.client.folder(pe.pth(jobs_dir))
	results_folder = pe.client.folder(pe.pth(results_dir))

	scan_for_jobs = True # initial condition

	while scan_for_jobs:

		pe._load_obj(job_folder)
		pe._load_obj(results_folder)

		scan_for_jobs = False # won't scan again unless we find new work
		for fi in job_folder.files:
			clog.debug(f'checking {fi.name} to see if it is a job')
			match = is_job.match(fi.name)
			if match:
				clog(f'{fi.name} is a job, checking if it is claimed')
				# a job .json config file is found, see if it is claimed
				job_no = match.group(1)
				job_descrip = match.group(2)
				is_job_result = re.compile(f'^({job_no})\\s+')

				if len(results_folder.folders)==0:
					# double check this is not changed since the results folder was cached
					pe._load_obj(results_folder)
					if len(results_folder.folders) == 0:
						# no jobs are claimed, so can claim this job
						scan_for_jobs = True
						yield _claim_job(results_dir, job_no, job_descrip, fi)

				if len(results_folder.folders) != 0:
					already_claimed = False
					for fo in results_folder.folders:
						result_match = is_job_result.match(fo.name)
						if result_match is not None:
							clog(f"job {job_no} is already claimed")
							already_claimed = True
					if not already_claimed:
						# double check this is not changed since the results folder was cached
						pe._load_obj(results_folder)
						for fo in results_folder.folders:
							result_match = is_job_result.match(fo.name)
							if result_match is not None:
								clog(f"job {job_no} is already claimed")
								already_claimed = True
					if not already_claimed:
						# This is an available job, claim it
						scan_for_jobs = True
						yield _claim_job(results_dir, job_no, job_descrip, fi)
			else:
				clog(f'{fi.name} is not a job')
	raise StopIteration


from .repeater import create_csv_repeat_set, external_repeater, call_me


def next_job_number(egnyte_path):
	c = re.compile('^([0-9]+)\\s.+')
	seen_max = 0
	eg_folder = pe.client.folder(pe.pth(egnyte_path))
	pe._load_obj(eg_folder)
	for fo in eg_folder.folders:
		match = c.match(fo.name)
		if match:
			seen_max = max(seen_max, int(match.group(1)))
	for fi in eg_folder.files:
		match = c.match(fi.name)
		if match:
			seen_max = max(seen_max, int(match.group(1)))
	return seen_max+1



def json_emitter(kwarg_file, **kwargs):
	"""
	Use an external CSV file to iterate over keyword args passed to a function.

	Parameters
	----------
	func : callable
		This function gets called once for each row of the CSV file
	kwarg_file : str or file-like
		A csv file containing keywork args (simple data types as read by pandas)

	Other Parameters
	----------------
	args
		Positional arguments always passed to `func`
	kwargs
		Common keyword arguments always passed to `func`

	Returns
	-------
	list
		A list containing the return value of `func` for each row
		of the csv file.
	"""
	result = []
	df = pandas.read_csv(kwarg_file)
	direct_kw = {}
	indirect_kw = {}
	for k, v in kwargs.items():
		if isinstance(v, call_me):
			indirect_kw[k] = v
		else:
			direct_kw[k] = v
	for row in df.iterrows():
		local_kwargs = row[1].to_dict()
		indirect_kwargs = {k: v() for k, v in indirect_kw.items()}
		to_json = dict(**direct_kw, **indirect_kwargs, **local_kwargs)
		result.append(to_json)
	return result


def looping_json_emitter(egnyte_dir, descrip, *loopers, **kwargs):
	buffer = create_csv_repeat_set(*loopers, filename=None, return_buffer=True)
	jsons = json_emitter(buffer, **kwargs)
	min_job_number = next_job_number(egnyte_dir)
	for jobnum, j in enumerate(jsons):
		clog(f'uploading job {min_job_number+jobnum}')
		pe.upload_dict_json(j, f'{min_job_number+jobnum} {descrip}.json', egnyte_dir)
	clog(f'looping_json_emitter complete')


def looping_json_emitter_local(local_dir, min_job_number, descrip, *loopers, **kwargs):
	buffer = create_csv_repeat_set(*loopers, filename=None, return_buffer=True)
	jsons = json_emitter(buffer, **kwargs)
	for jobnum, j in enumerate(jsons):
		clog(f'local writing job {min_job_number+jobnum}')
		with open(os.path.join(local_dir, f'{min_job_number+jobnum} {descrip}.json'), 'w') as jfile:
			jfile.write(json.dumps(j))
	clog(f'looping_json_emitter_local complete')
