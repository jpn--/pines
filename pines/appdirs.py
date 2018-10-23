
from appdirs import *
import os

def user_cache_file(filename, appname=None, appauthor=None, version=None, opinion=True):
	d = user_cache_dir(appname=appname, appauthor=appauthor, version=version, opinion=opinion)
	os.makedirs(d, exist_ok=True)
	return os.path.join(d, filename)

