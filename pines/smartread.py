
import gzip, os, struct, zipfile, io




class SmartFileReader(object):
	def __init__(self, file, *args, **kwargs):
		if file[-3:]=='.gz':
			with open(file, 'rb') as f:
				f.seek(-4, 2)
				self._filesize = struct.unpack('I', f.read(4))[0]
			self.file = gzip.open(file, *args, **kwargs)
		elif file[-4:]=='.zip':
			zf = zipfile.ZipFile(file, 'r')
			zf_info = zf.infolist()
			if len(zf_info)!=1:
				raise TypeError("zip archive files must contain a single member file for SmartFileReader")
			zf_info = zf_info[0]
			self.file = zf.open(zf_info.filename, 'r', *args, **kwargs)
			self._filesize = zf_info.file_size
		else:
			self.file = open(file, 'rt', *args, **kwargs)
			self._filesize = os.fstat(self.file.fileno()).st_size
	def __getattr__(self, name):
		return getattr(self.file, name)
	def __setattr__(self, name, value):
		if name in ['file', 'percentread', '_filesize']:
			return object.__setattr__(self, name, value)
		return setattr(self.file, name, value)
	def __delattr__(self, name):
		return delattr(self.file, name)
	def percentread(self):
		try:
			return (float(self.file.tell())/float(self._filesize)*100)
		except io.UnsupportedOperation:
			return 1.0-(float(self.file._left)/float(self._filesize)*100)
	def __iter__(self):
		return self.file.__iter__()
	def bytesread(self):
		try:
			b = float(self.file.tell())
		except:
			return "error in bytesread"
		labels = ['B','KB','MB','GB','TB']
		scale = 0
		while scale < 4 and b > 1024:
			b /= 1024
			scale += 1
		return "{:.2f}{}".format(b,labels[scale])
