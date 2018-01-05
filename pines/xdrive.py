import os.path
import re
import time
import hashlib
import pickle
import io, gzip
import shutil
import json
import fnmatch
import glob
import sys

from .logger import flogger
from .bytesize import bytes_scaled
from .codex import phash
from .configure import load as load_config

elog = flogger(label='XDRIVE')


## init

_updates = False

config = load_config()

if 'root_dir' in config.xdrive:
	ROOT = config.xdrive.root_dir
else:
	ROOT = "X:"

class Folder():
	def __init__(self, path=None):
		self.path = os.path.join(ROOT, path)
		_, self.folders, self.files = next(os.walk(self.path, topdown=True))
		self.is_folder = True
	def folder(self, f):
		return Folder(os.path.join(self.path, f))
	def file(self, f, **kwargs):
		return File(os.path.join(self.path, f))
	def create(self, *args):
		os.makedirs(self.path, exist_ok=True)

class File():
	def __init__(self, path=None):
		self.path = os.path.join(ROOT, path)
		self.is_folder = False
	def upload(self, in_stream):
		os.makedirs(os.path.dirname(self.path),exist_ok=True)
		with open(self.path, mode='wb') as f:
			shutil.copyfileobj(in_stream, f)
	def download(self, out_stream):
		with open(self.path, mode='rb') as f:
			shutil.copyfileobj(f, out_stream)
	@property
	def size(self):
		return os.path.getsize(self.path)
	@property
	def checksum(self):
		return _sha512_checksum(self.path)

def FileOrFolder(path):
	if os.path.isdir(path):
		return Folder(path)
	else:
		return File(path)


def _folder_to_path(f):
	if isinstance(f,Folder):
		return f.path
	if isinstance(f,File):
		return f.path
	return f

def pth(*arg):
	return "/".join(_folder_to_path(f) for f in arg).replace('//','/').replace('\\','/')



def create_folder(folder_path, retries=10, interval=1):
	"""
	Create a new folder within Egnyte.

	:param folder_path:
	:return: egnyte.resources.Folder
	"""
	if not os.path.exists(folder_path):
		os.makedirs(folder_path, exist_ok=True)
	return Folder(folder_path)

def create_subfolder(folder, subfoldername):
	f = pth(folder,subfoldername)
	os.makedirs(f, exist_ok=True)
	return Folder(f)

def upload_file(local_file, xdrive_path, rename=None, add_suffix=None):
	if rename is None:
		basename = os.path.basename(local_file)
	else:
		basename = rename
	if add_suffix:
		basename = "{1}{0}{2}".format(add_suffix, *os.path.splitext(basename))
	file_obj = File( pth(xdrive_path,basename) )
	with open(local_file, "rb") as fp:
		file_obj.upload(fp)
	return

def upload_file_gz(local_file, egnyte_path, progress_callbacks=None):
	if progress_callbacks is None:
		progress_callbacks = ProgressCallbacks()
	basename = os.path.basename(local_file)+'.gz'
	file_obj = File(pth(egnyte_path, basename))
	buffer = io.BytesIO()
	with open(local_file, 'rb') as f_in:
		with gzip.open(buffer, 'wb') as buffer_out:
			shutil.copyfileobj(f_in, buffer_out)
	progress_callbacks.upload_start(local_file, file_obj, buffer.tell())
	buffer.seek(0)
	file_obj.upload(buffer)
	progress_callbacks.upload_finish(file_obj)


def upload_dict_json(dictionary, filename, egnyte_path, progress_callbacks=None):
	"""

	Parameters
	----------
	dictionary : dict
		The dictionary to convert to json and upload to egnyte
	filename : str
		A filename for the file that will be created in egnyte
	egnyte_path : str
		The (existing) folder in egnyte where the file will be created
	progress_callbacks

	"""
	if progress_callbacks is None:
		progress_callbacks = ProgressCallbacks()
	basename = os.path.basename(filename)
	if basename[-5:] != '.json':
		basename += '.json'
	file_obj = File(pth(egnyte_path, basename))
	buffer = io.BytesIO(json.dumps(dictionary).encode('UTF-8'))
	progress_callbacks.upload_start("dictionary", file_obj, buffer.tell())
	file_obj.upload(buffer)
	progress_callbacks.upload_finish(file_obj)



def download_file(egnyte_file, local_path, overwrite=False, mkdir=True, progress_callbacks=None):
	if not os.path.exists(local_path) and mkdir:
		os.makedirs(local_path)
	bulk_download([egnyte_file], local_path, overwrite=overwrite, log=(progress_callbacks is not None))


def download_file_gz(egnyte_file, local_path, overwrite=False, mkdir=True, progress_callbacks=None, retries=10, interval=1):
	if progress_callbacks is None:
		progress_callbacks = ProgressCallbacks()
	if not os.path.exists(local_path) and mkdir:
		os.makedirs(local_path)
	if isinstance(egnyte_file, str) and egnyte_file[-3:] != '.gz':
		egnyte_file = egnyte_file+'.gz'
	basename = os.path.basename(egnyte_file)[:-3]
	if not overwrite and os.path.exists(os.path.join(local_path, basename)):
		raise FileExistsError(os.path.join(local_path, basename))
	file_obj = File(pth(egnyte_file))
	buffer = io.BytesIO()
	progress_callbacks.download_start(local_path, file_obj, file_obj.size)
	file_obj.download(buffer)
	buffer.seek(0)
	with gzip.open(buffer, 'rb') as buffer_in:
		with open(os.path.join(local_path, basename), 'wb') as f_out:
			shutil.copyfileobj(buffer_in, f_out)
	progress_callbacks.download_finish(file_obj)
	from .zipdir import verify_hash_file
	if os.path.exists(egnyte_file[:-3] + ".sha256.txt"):
		verify_hash_file(os.path.join(local_path, basename), hash_dir=os.path.dirname(egnyte_file))

def download_dict_json(egnyte_file, progress_callbacks=None, retries=10, interval=1):
	"""

	Parameters
	----------
	egnyte_file : str
		The location in egnyte for the json file to be loaded.
	progress_callbacks

	Returns
	-------
	dict
	"""
	if progress_callbacks is None:
		progress_callbacks = ProgressCallbacks()
	import json, io
	if isinstance(egnyte_file, str) and egnyte_file[-5:] != '.json':
		egnyte_file = egnyte_file+'.json'
	file_obj = File(pth(egnyte_file))
	buffer = io.BytesIO()
	progress_callbacks.download_start('dictionary', file_obj, file_obj.size)
	file_obj.download(buffer)
	buffer.seek(0)
	result = json.loads(buffer.getvalue().decode('UTF-8'))
	progress_callbacks.download_finish(file_obj)
	return result





class ProgressCallbacks():
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
		elog("downloading {1} ({2})".format(local_path, cloud_file.path, bytes_scaled(size)))

	def download_progress(self, cloud_file, size, downloaded):
		"""Some progress in file download."""

	def download_finish(self, cloud_file):
		"""Finished downloading a file."""

	def upload_start(self, local_path, cloud_file, size):
		"""Starting to upload a file."""
		elog("uploading {1} ({2})".format(local_path, cloud_file.path, bytes_scaled(size)))

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

DEFAULT_EXCLUDES = fnmatch.translate(".*")
DEFAULT_EXCLUDES_RE = re.compile(DEFAULT_EXCLUDES).match


def make_excluded(excludes=None):
	if excludes is None:
		return DEFAULT_EXCLUDES_RE
	patterns = [DEFAULT_EXCLUDES]
	patterns.extend(fnmatch.translate(x) for x in excludes)
	return re.compile("|".join(patterns)).match

def generate_paths(roots, excludes=None):
	"""
	Walk set of paths in local filesystem, and for each file and directory generate a tuple of
	(is directory, absolute path, path relative root used to get to that file)
	"""
	excluded = make_excluded(excludes)
	for root in roots:
		base = os.path.basename(root)
		if not excluded(base):
			is_dir = os.path.isdir(root)
			yield is_dir, root, base
			if is_dir:
				prefix_len = len(os.path.dirname(root))
				for dirpath, dirnames, filenames in os.walk(root, topdown=True, followlinks=True):
					relpath = dirpath[prefix_len:].strip('/')
					for is_dir, names in ((False, filenames), (True, dirnames)):
						for name in names:
							if not excluded(name):
								yield is_dir, os.path.join(dirpath, name), "%s/%s" % (relpath, name)



def bulk_upload(local_dir, xdrive_path, exclude=None, progress_callbacks=None):
	"""
    Transfer many files or directories to Cloud File System.

    * paths - list of local file paths
    * target - Path in CFS to upload to
    * progress_callbacks - Callback object (see ProgressCallbacks)
    """
	if not local_dir:
		return
	if progress_callbacks is None:
		progress_callbacks = ProgressCallbacks()  # no-op callbacks
	target_folder = Folder(xdrive_path)
	progress_callbacks.creating_directory(target_folder)
	target_folder.create(True)
	for is_dir, local_path, cloud_path in generate_paths(local_dir, exclude):
		if is_dir:
			cloud_dir = target_folder.folder(cloud_path)
			progress_callbacks.creating_directory(cloud_dir)
			cloud_dir.create(True)
		else:
			size = os.path.getsize(local_path)
			if size:  # empty files cannot be uploaded
				cloud_file = target_folder.file(cloud_path, size=size)
				with open(local_path, "rb") as fp:
					progress_callbacks.upload_start(local_path, cloud_file, size)
					cloud_file.upload(fp)
				progress_callbacks.upload_finish(cloud_file)
	progress_callbacks.finished()



def _sha512_checksum(filename, block_size=65536):
	sha512 = hashlib.sha512()
	with open(filename, 'rb') as f:
		for block in iter(lambda: f.read(block_size), b''):
			sha512.update(block)
	return sha512.hexdigest()

def _pines_bulk_download_worker(items, root_path, local_dir, overwrite, progress_callbacks):
	import collections, shutil
	any_updates = False
	root_len = len(root_path.rstrip('/')) + 1
	queue = collections.deque(items)
	while True:
		try:
			obj = queue.popleft()
		except IndexError:
			break
		relpath = obj.path[root_len:].strip('/')
		local_path = os.path.join(local_dir, relpath.replace('/', os.sep))
		dir_path = os.path.dirname(local_path)
		if not os.path.isdir(dir_path):
			if os.path.exists(dir_path):
				if overwrite:
					os.unlink(local_path)
				else:
					progress_callbacks.skipped(obj, "Existing file conflicts with cloud folder")
					continue
			os.makedirs(dir_path)
		if obj.is_folder:
			# schedule contents for later, files first
			if obj.files is None:
				progress_callbacks.getting_info(obj.path)
				obj.list()
				progress_callbacks.got_info(obj)
			queue.extend(obj.files)
			queue.extend(obj.folders)
		else:
			if os.path.exists(local_path):
				if overwrite:
					# read local checksum
					if _sha512_checksum(local_path) != obj.checksum:
						if os.path.isdir(local_path) and not os.path.islink(local_path):
							shutil.rmtree(local_path)
						else:
							os.unlink(local_path)
					else:
						continue
				else:
					progress_callbacks.skipped(obj, "Existing file conflicts with cloud file")
					continue
			progress_callbacks.download_start(local_path, obj, obj.size)
			obj.download(local_path)
			any_updates = True
			progress_callbacks.download_finish(obj)
	return any_updates


def _pines_bulk_download( paths, local_dir, overwrite=False, progress_callbacks=None):
	"""
	Transfer many files or directories to Cloud File System.

	* paths - list of local file paths
	* target - Path in CFS to upload to
	* progress_callbacks - Callback object (see ProgressCallbacks)
	"""
	any_updates = False
	if progress_callbacks is None:
		progress_callbacks = ProgressCallbacks()
	for path in paths:
		progress_callbacks.getting_info(path)
		obj = FileOrFolder(path)
		root_path = path[:path.rstrip('/').rfind('/')]  # take all segments expect last one
		if obj.is_folder:
			items = obj.files + obj.folders
		else:
			items = (obj,)
		any_updates = _pines_bulk_download_worker(items, root_path, local_dir, overwrite, progress_callbacks)
	progress_callbacks.finished()
	return any_updates

def bulk_download( egnyte_path, local_dir, log=True, overwrite=False, progress_callbacks=None ):
	p_callbacks = progress_callbacks or (ProgressCallbacks() if log else None)
	if isinstance(egnyte_path, str):
		return _pines_bulk_download([egnyte_path], local_dir, overwrite=overwrite, progress_callbacks=p_callbacks)
	else:
		return _pines_bulk_download(egnyte_path, local_dir, overwrite=overwrite, progress_callbacks=p_callbacks)



def import_remote_python_package( egnyte_path, package_name=None, log=True ):
	if package_name is None:
		if egnyte_path[-1] in ('/','\\'):
			package_name = os.path.basename(egnyte_path[:-1])
		else:
			package_name = os.path.basename(egnyte_path[:])
	import sys, importlib
	from .temporary import TemporaryDirectory
	tempdir = TemporaryDirectory()
	any_updates = bulk_download([egnyte_path], tempdir.name, overwrite=True, log=log)
	if tempdir.name not in sys.path:
		sys.path.insert(0, tempdir.name)
	importlib.invalidate_caches()
	if package_name in sys.modules:
		if any_updates:
			return importlib.reload(sys.modules[package_name])
		else:
			return sys.modules[package_name]
	else:
		return importlib.import_module(package_name)

# from pines.egnyte import import_remote_python_package
# import_remote_python_package('/Private/jnewman/PyAccess/werter', 'werter')

def glob_upload_gz(pattern, egnyte_path, log=True, dryrun=False):
	"""
	Upload a gzipped version of all files matching pattern into egynte.

	Parameters
	----------
	pattern : str
		A glob pattern
	egnyte_path : str or egnyte.Folder
	log : bool, default True
		Log the results
	dryrun : bool, default False
		If true, just log what would be done, don't actually upload the files.

	"""
	for filename in glob.glob(pattern):
		if log:
			elog(f"found file for upload:{filename}")
		if not dryrun:
			upload_file_gz(filename, egnyte_path, progress_callbacks=ProgressCallbacks() if log else None)

def pip_install_1(xdrive_python_package_file):
	import pip
	pip.main(['install', xdrive_python_package_file])

def pip_install(package_names=None, xdrive_repo="X:/Share/CHI/Shared/JPN/PythonRepo/simple/"):
	import pip
	if package_names is None:
		if len(sys.argv)>0 and (('pines_pip' in sys.argv[0]) or ('pines-pip' in sys.argv[0])):
			if len(sys.argv)>1 and sys.argv[1]=='install': # ignore install command, it is implied here
				package_names = " ".join(sys.argv[2:])
			else:
				package_names = " ".join(sys.argv[1:])
	try:
		pkgs = package_names.split()
	except AttributeError:
		print("NO PACKAGES GIVEN")
	else:
		for pkg in pkgs:
			result = pip.main(["install", "--upgrade", f'--index-url=file:///{xdrive_repo}', pkg])
			if result!=0:
				# failure
				raise ModuleNotFoundError(pkg)

def _pip_install_entry(args=None):
	return pip_install()


def pip_rebuild(xdrive_repo="X:/Share/CHI/Shared/JPN/PythonRepo", private_repo=r"\\camtdm01\c$\Apache24\htdocs"):
	import libpip2pi.commands
	libpip2pi.commands.dir2pi(argv=["dir2pi",xdrive_repo, '-S'])
	import shutil, os
	shutil.copytree(os.path.join(xdrive_repo, 'simple'), private_repo)

