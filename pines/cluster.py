

import time
import pandas
import os
from dask.distributed import Client as _Client, Future
from distributed.core import rpc as _rpc

from .timesize import timesize
from .counter import Counter


def heavy_logging():
	from .logger import flogger
	clog = flogger(label='CLUSTER')
	clog("this is cluster log")
	return clog

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

	def workers(self):
		return set(self.scheduler_info()['workers'].keys())

	def retire_workers(self, workers_to_retire):
		"""
		Cleanly retire a worker, moving saved results to other workers first.

		Parameters
		----------
		workers_to_retire

		Returns
		-------

		"""
		super().retire_workers()
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

	def log_viewer(self):
		return ClientLogViewer(self)



import ipywidgets as widgets
import logging
from IPython.display import display

class ClientLogViewer(widgets.VBox):
	def __init__(self, client):
		self.client = client
		self.out = widgets.Output(layout={ 'border': '1px solid red', })
		self.pick = widgets.Dropdown(options=client.workers())
		self.pick.observe(self.picker_action)
		super().__init__([
			self.pick,
			self.out,
		])

	def picker_action(self, action_content):
		if 'name' in action_content and action_content['name'] == 'value':
			worker = action_content['new']
			logs = self.client.get_worker_logs(workers=[worker])
			self.out.clear_output()
			with self.out:
				for worker_id, worker_log in logs.items():
					print("=" * 80)
					print(worker_id)
					print("=" * 80)
					for i in worker_log:
						print(i[1])




