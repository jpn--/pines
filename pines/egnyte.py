import os.path
import egnyte

from .logger import flogger

elog = flogger('EGNYTE')


## init

_updates = False

config = egnyte.configuration.load()

if "api_key" not in config:
	config["api_key"] = "zxuez95f5utrrf7v2ukyex6y"
	_updates = True

if "client_id" not in config:
	config["client_id"] = "zxuez95f5utrrf7v2ukyex6y"
	_updates = True

if "domain" not in config:
	config["domain"] = "camsys"
	_updates = True

if _updates:
	egnyte.configuration.save(config)


client = egnyte.EgnyteClient(config)


def _folder_to_path(f):
	if isinstance(f,egnyte.resources.Folder):
		return f.path
	return f

def pth(*arg):
	return "/".join(_folder_to_path(f) for f in arg).replace('//','/').replace('\\','/')


def create_folder(folder_path):
	"""
	Create a new folder within Egnyte.

	:param folder_path:
	:return: egnyte.resources.Folder
	"""
	folder = client.folder(pth(folder_path)).create(ignore_if_exists=True)
	return folder

def create_subfolder(folder, subfoldername):
	f = client.folder(pth(folder,subfoldername)).create(ignore_if_exists=True)
	return f

def upload_file(local_file, egnyte_path):
	basename = os.path.basename(local_file)
	file_obj = client.file( pth(egnyte_path,basename) )
	with open(local_file, "rb") as fp:
		file_obj.upload(fp)

# def batch_upload_file(local_files, egnyte_path):
# 	for local_file in local_files:
# 		upload_file(local_file, egnyte_path)
#
# def batch_upload_directory(local_dir, egnyte_path):
# 	for root, dirs, files in os.walk(local_dir):
# 		fo = create_folder( pth(egnyte_path,os.path.relpath(root, local_dir)) )
# 		batch_upload_file((os.path.join(root, fi) for fi in files), fo)





class ProgressCallbacks(egnyte.client.ProgressCallbacks):
	"""
	This object is used for bulk transfers (uploads and downloads)
	Inherit this and add override any of the callabcks you'd like to handle.
	"""

	def getting_info(self, cloud_path):
		"""Getting information about an object. Called for directories and unknown paths."""
		elog("getting info on {}".format(cloud_path))

	def got_info(self, cloud_obj):
		"""Got information about an object."""

	def creating_directory(self, cloud_folder):
		"""Creating a directory."""
		elog("creating directory {}".format(cloud_folder))

	def download_start(self, local_path, cloud_file, size):
		"""Starting to download a file."""
		elog("downloading {1} ({2} bytes)".format(local_path, cloud_file, size))

	def download_progress(self, cloud_file, size, downloaded):
		"""Some progress in file download."""

	def download_finish(self, cloud_file):
		"""Finished downloading a file."""

	def upload_start(self, local_path, cloud_file, size):
		"""Starting to upload a file."""
		elog("uploading {1} ({2} bytes)".format(local_path, cloud_file, size))

	def upload_progress(self, cloud_file, size, uploaded):
		"""Some progress in file upload."""

	def upload_finish(self, cloud_file):
		"""Finished uploading a file."""

	def finished(self):
		"""Called after all operations."""
		elog("finished")

	def skipped(self, cloud_obj, reason):
		"""Object has been skipped because of 'reason'"""
		elog("skipped {} ({})".format(cloud_obj, reason))




def bulk_upload( local_dir, egnyte_path, log=True ):
	if isinstance(local_dir, str):
		client.bulk_upload([local_dir], egnyte_path, ProgressCallbacks if log else None)
	else:
		client.bulk_upload(local_dir, egnyte_path, ProgressCallbacks if log else None)

def bulk_download( egnyte_path, local_dir, log=True, overwrite=False ):
	if isinstance(egnyte_path, str):
		client.bulk_download([egnyte_path], local_dir, overwrite=overwrite, progress_callbacks=ProgressCallbacks if log else None)
	else:
		client.bulk_upload(egnyte_path, local_dir, overwrite=overwrite, progress_callbacks=ProgressCallbacks if log else None)





def get_access_token():
	import requests, getpass
	headers = {
		'Content-Type': 'application/x-www-form-urlencoded',
	}
	data = [
		('grant_type', 'password'),
		('username', getpass.getpass("Username (not email, just name): ")),
		('password', getpass.getpass("Password: ")),
		('client_id', 'zxuez95f5utrrf7v2ukyex6y'),
	]
	response = requests.post('https://camsys.egnyte.com/puboauth/token', headers=headers, data=data)
	response_json = response.json()
	if 'access_token' in response_json:
		client.config['access_token'] = response_json['access_token']
	egnyte.configuration.save(client.config)
