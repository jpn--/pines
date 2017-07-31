

from . import egnyte as pe
import re
import time
import json
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

