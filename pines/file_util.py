
import os
import glob
import time
import gzip

def unused_filename(basename, basepath=None):
	"Generate a filename based on the basename, but which does not yet exist"
	if basepath is None:
		base_full = basename
	else:
		base_full = os.path.join(basepath, basename)
	outfilename = base_full
	out_n = 1
	while os.path.exists(outfilename):
		head, tail = os.path.splitext(base_full)
		outfilename = '{}_{}{}'.format(head,out_n,tail)
		out_n += 1
	return outfilename


def filename_split(filename):
	pathlocation, basefile = os.path.split(filename)
	basefile_list = basefile.split(".")
	if len(basefile_list) > 1:
		basename = ".".join(basefile_list[:-1])
		extension = "." + basefile_list[-1]
	else:
		basename = basefile_list[0]
		extension = ""
	return (pathlocation, basename, extension)


def filename_fuse(pathlocation, basename, extension):
	x = os.path.join(pathlocation, basename)
	if extension != "": x += "." + extension
	return x


def rotate_file(filename, format="%(basename)s.%(number)03i%(extension)s"):
	"""
	Renames all existing files matching the pattern by increasing the number by 1.
	:param filename:
	:param format:
	:return:
	"""
	if os.path.exists(filename):
		pathlocation, basename, extension = filename_split(filename)
		fn = lambda n: os.path.join(pathlocation,format%{'basename':basename, 'extension':extension, 'number':n})
		n = 1
		while os.path.exists(fn(n)):
			n += 1
		while n > 1:
			os.rename(fn(n-1),fn(n))
			n -= 1
		os.rename(filename,fn(1))
	else:
		raise FileNotFoundError("File %s does not exist"%filename)


def next_filename(filename, format="{basename:s}.{number:03d}{extension:s}", suffix=None, plus=0, allow_natural=False,
               demand_natural=False):
	"""Finds the next file name in this stack that does not yet exist.

	Parameters
	----------
	filename : str or None
		The base file name to use for this stack.  New files would have a number
		appended after the basename but before the dot extension.  For example,
		if the filename is "/tmp/boo.txt", the first file created will be named
		"/tmp/boo.001.txt".  If None, then a temporary file is created instead.


	Other Parameters
	----------------
	suffix : str, optional
		If given, use this file extension instead of any extension given in the filename
		argument.  The usual use case for this parameter is when filename is None,
		and a temporary file of a particular kind is desired.
	format : str, optional
		If given, use this format string to generate new stack file names in a
		different format.
	plus : int, optional
		If given, increase the returned filenumber by this amount more than what
		is needed to generate a new file.  This can be useful with pytables, which can
		create pseudo-files that don't appear on disk but should all have unique names.
	allow_natural : bool
		If true, this function will return the unedited	`filename` parameter
		if that file does not already exist. Otherwise will always have a
		number appended to the name.
	demand_natural : bool
		If true, this function will just throw a FileExistsError instead of spooling
		if the file already exists.

	"""
	if filename is not None:
		filename = os.path.expanduser(filename)
	if demand_natural and os.path.exists(filename):
		raise FileExistsError(filename)
	if allow_natural and not os.path.exists(filename):
		return filename
	pathlocation, basename, extension = filename_split(filename)
	if suffix is not None:
		extension = "." + suffix
	fn = lambda n: os.path.join(pathlocation, format.format(basename=basename, extension=extension, number=n))
	n = 1
	while os.path.exists(fn(n)):
		n += 1
	return fn(n + plus)


def latest_matching(pattern, echo=False):
	"Get the most recently modified file matching the glob pattern"
	files = glob.glob(pattern)
	propose = None
	propose_mtime = 0
	for file in files:
		(mode, ino, dev, nlink, uid, gid, size, atime, mtime, ctime) = os.stat(file)
		if echo:
			print (file,"last modified: %s" % time.ctime(mtime))
		if mtime > propose_mtime:
			propose_mtime = mtime
			propose = file
	return propose


def single_matching(pattern):
	"Get the only file matching a glob pattern, if 0 or 2+ matches raise NameError"
	files = glob.glob(pattern)
	if len(files)>1:
		raise NameError("More than one file matches pattern '{}'".format(pattern))
	if len(files)<1:
		raise NameError("No file matches pattern '{}'".format(pattern))
	return files[0]


def head(filename, n=10):
	"""Print the top N lines of a file from disk.
	
	The file can be gzipped, if it has a .gz extension.
	"""
	print("[HEAD {}] {}".format(n,filename))
	if filename[-3:].casefold()=='.gz':
		with gzip.open(filename, 'rt') as previewfile:
			print(*(next(previewfile) for x in range(n)))
	else:
		with open(filename, 'r') as f:
			for linenumber in range(n):
				line = f.readline()
				print(line)
	print("[END HEAD]")

def get_headers(filename, delim=','):
	"""Get the header line from a CSV type text file on disk.
	
	The file can be gzipped, if it has a .gz extension.
	"""
	if filename[-3:].casefold() == '.gz':
		with gzip.open(filename, 'rt') as file:
			firstline= next(previewfile)
	else:
		with open(filename, 'r') as f:
			firstline = f.readline()
	firstline = firstline.strip()
	return firstline.split(delim)