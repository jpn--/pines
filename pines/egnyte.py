import os.path
import egnyte


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

def batch_upload_file(local_files, egnyte_path):
	for local_file in local_files:
		upload_file(local_file, egnyte_path)

def batch_upload_directory(local_dir, egnyte_path):
	for root, dirs, files in os.walk(local_dir):
		fo = create_folder( pth(egnyte_path,os.path.relpath(root, local_dir)) )
		batch_upload_file((os.path.join(root, fi) for fi in files), fo)


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
