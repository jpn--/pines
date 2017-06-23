
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