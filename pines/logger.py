
import logging
import logging.handlers
import sys
import traceback

from logging import DEBUG, INFO, ERROR, WARNING, CRITICAL

_base_log_class = logging.getLoggerClass()

_time_format = '%H:%M:%S'
_mess_format = '%(asctime)8s %(name)s %(message)s'

def log_to_stream(stream=sys.stdout, log="π", message_fmt=None, date_fmt=None):
	s = logging.getLogger(log)
	h = logging.StreamHandler(stream)
	f = logging.Formatter(fmt=message_fmt or _mess_format, datefmt=date_fmt or _time_format)
	h.setFormatter(f)
	s.addHandler(h)
	s.critical("Connected log to stream %s",str(stream))


def getLogger(name="π",*args,**kwargs):
	return logging.getLogger(name,*args,**kwargs)



_ROOT = getLogger()


def setLevel(x):
	_ROOT.setLevel(x)



import collections
try:
	levels = collections.OrderedDict()
except:
	levels = {}
levels['DEBUG'] = 10
levels['INFO'] = 20
levels['WARNING'] = 30
levels['ERROR'] = 40
levels['CRITICAL'] = 50

revLevel = {}
revLevel[10]='DEBUG'
revLevel[20]='INFO'
revLevel[30]='WARNING'
revLevel[40]='ERROR'
revLevel[50]='CRITICAL'


def log_level_number(lvl):
	if isinstance(lvl, str):
		return levels[lvl]
	return lvl

def log_level_name(lvl):
	if isinstance(lvl, str):
		return lvl
	return revLevel[lvl]



def pines_log_level(newLevel, silently=False):
	newLevel = log_level_number(newLevel)
	_ROOT.setLevel(newLevel)
	if not silently:
		if newLevel in revLevel:
			_ROOT.info('Changing log level to %s',revLevel[newLevel])
		else:
			_ROOT.info('Changing log level to %i',newLevel)

def check_pines_log_level():
	return _ROOT.getEffectiveLevel()

try:
	fileHandler
except NameError:
	fileHandler = None

def default_formatter():
	return logging.Formatter(fmt=_mess_format,datefmt=_time_format)

def log_to_file(filename, residual=None, overwrite=False, *, fmt=None, datefmt=None, encoding=None):
	global fileHandler
	if fileHandler:
		fileHandler.flush()
		_ROOT.removeHandler(fileHandler)
		fileHandler.close()
		fileHandler = None
	if overwrite:
		mode = 'w'
	else:
		mode = 'a'
	if filename is None or filename=="": return
	if residual:
		f = open(filename, mode)
		f.write(residual)
		f.close()
		mode = 'a'
	fileHandler = logging.FileHandler(filename, mode, encoding=encoding)
	if fmt is None:
		fmt=_mess_format
	if datefmt is None:
		datefmt=_time_format
	fileHandler.setFormatter(logging.Formatter(fmt=fmt,datefmt=datefmt))
	_ROOT.addHandler(fileHandler)
	_ROOT.critical("Connected log to %s",filename)




def spew(level=10):
	log_to_stream()
	setLevel(level)
	return logging.getLogger("π")


_easy_logger = None

def easy(level=-1, label="π", *, filename=None, file_fmt='[%(name)s] %(message)s'):
	global _easy_logger
	if file_fmt is None:
		file_fmt = _mess_format
	if filename:
		log_to_file(filename, fmt=file_fmt)
	if isinstance(level, str):
		label_ = level
		level = label if isinstance(label, int) else -1
		label = label_
	if isinstance(label, int):
		level_ = label
		label = level if isinstance(level, str) else ""
		level = level_
	if _easy_logger is None:
		log_to_stream(log="")
		_easy_logger = 1
	if level>0: setLevel(level)
	return getLogger(label).critical

def easy_debug(label="π"):
	global _easy_logger
	if _easy_logger is None:
		log_to_stream()
		_easy_logger = 1
	setLevel(10)
	return logging.getLogger(label).debug

def easy_logging_active():
	global _easy_logger
	if _easy_logger is None:
		return False
	else:
		return True

class Flogger:
	def __init__(self, logger, indenter=11):
		self.logger = logger
		self.buffer = ""
		self.indenter = indenter
	def __call__(self, base="", *args, end="\n", lvl=50, **kwargs):
		if end=="\n":
			if isinstance(base,str) and "{" in base:
				out_str = self.buffer + base.format(*args,**kwargs)
			else:
				out_str = self.buffer + " ".join( str(i) for i in (base,)+args )
			self.logger.log(lvl, out_str.replace('\n','\n'+' '*self.indenter))
			self.buffer = ""
		else:
			if isinstance(base,str) and "{" in base:
				self.buffer += base.format(*args,**kwargs)
			else:
				self.buffer += " ".join( str(i) for i in (base,)+args )
	def critical(self, base="", *args, end="\n", **kwargs):
		return self(base, *args, end=end, lvl=50, **kwargs)
	def error(self, base="", *args, end="\n", **kwargs):
		return self(base, *args, end=end, lvl=40, **kwargs)
	def warn(self, base="", *args, end="\n", **kwargs):
		return self(base, *args, end=end, lvl=30, **kwargs)
	def info(self, base="", *args, end="\n", **kwargs):
		return self(base, *args, end=end, lvl=20, **kwargs)
	def debug(self, base="", *args, end="\n", **kwargs):
		return self(base, *args, end=end, lvl=10, **kwargs)




def flogger(level=-1, label="π", *, filename=None, file_fmt='[%(name)8s] %(message)s', threshold=None):
	"This returns a formatted logger that accepts new-style formatting, and sets logging to maximum"
	easy(level=level, label=label, filename=filename, file_fmt=file_fmt)
	if threshold:
		pines_log_level(threshold, silently=True)
	return Flogger(getLogger(label))
