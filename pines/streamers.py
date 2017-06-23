

class double_stream:
	def __init__(self, filename, mode='w'):
		self.file = open(filename, mode)
	def write(self, *args):
		self.file.write(*args)
		print(*args, end="")
	def flush(self):
		self.file.flush()
	def close(self):
		self.file.close()
	def __enter__(self):
		pass
	def __exit__(self, exc_type, exc_val, exc_tb):
		self.flush()
		self.close()