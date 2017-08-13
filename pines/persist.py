



class stored_dict(dict):
	'''Provide a persistent storage mechanism for use with DB objects.'''
	def __init__(self, db, name, *, reverse_index=False, key="id", value="value", key_format="", value_format="", overwrite_mechanism="REPLACE", autocommit=True):
		super().__init__()
		self.keycol = key
		self.valuecol = value
		self.db = db
		self.name = name
		self.cur = db.cursor()
		self.overwrite_mechanism = overwrite_mechanism
		self.autocommit = autocommit
		self.cur.execute("CREATE TABLE IF NOT EXISTS {0} ({1} {2} PRIMARY KEY, {3} {4})".format(name,key,key_format,value,value_format))
		for row in self.cur.execute("SELECT {0}, {1} FROM {2}".format(key,value,name)):
			super().__setitem__(row[0], row[1])
		if reverse_index:
			self.reverse_index()
	def add(self,key):
		if key not in self:
			self[key] = len(self)+1
		return self[key]
	def __getattr__(self, item):
		return self[item]
	def __getitem__(self, key):
		try:
			return super().__getitem__(key)
		except KeyError:
			for row in self.cur.execute("SELECT {0}, {1} FROM {2}".format(self.keycol,self.valuecol,self.name)):
				super().__setitem__(row[0], row[1])
			return super().__getitem__(key)
	def __setitem__(self, key, value):
		if key not in self:
			self.cur.execute("INSERT OR {} INTO {} ({},{}) VALUES (?,?)".format(self.overwrite_mechanism,self.name,self.keycol,self.valuecol),(key,value))
			super().__setitem__(key, value)
		elif (key in self and self[key] != value):
			self.cur.execute("UPDATE {0} SET {2}=? WHERE {1}=?".format(self.name,self.keycol,self.valuecol),(value,key))
			super().__setitem__(key, value)
		if self.autocommit:
			self.db.commit()
	def begin_transaction(self):
		self.cur.execute("BEGIN TRANSACTION;")
	def end_transaction(self):
		self.cur.execute("END TRANSACTION;")
	def reverse_index(self):
		self.cur.execute("CREATE INDEX IF NOT EXISTS {name}_reverse ON {name} ({val})".format(name=self.name, val=self.valuecol))
	def reverse_lookup(self, value, all=False):
		cur = self.cur.execute("SELECT {1} FROM {0} WHERE {2}==?".format(self.name,self.keycol,self.valuecol),(value,))
		if all:
			return [i[0] for i in cur]
		else:
			return next(cur,[None])[0]




def open_persist_dict(filename, tablename='persist', **kwarg):
	import sqlite3
	conn = sqlite3.connect(filename)
	sd = stored_dict(conn, tablename, **kwarg)
	return sd




class stored_dict_mysql(dict):
	'''Provide a persistent storage mechanism for use with DB objects.'''
	def __init__(self, db, name, *, reverse_index=False, key="id", value="value", value_format="LONGBLOB", overwrite_mechanism="REPLACE", autocommit=True, cache_locally=True):
		super().__init__()
		key_format = "VARCHAR(1024)"
		self.keycol = key
		self.valuecol = value
		self.db = db
		self.db.connect()
		self.name = name
		self.cur = db.cursor()
		self.overwrite_mechanism = overwrite_mechanism
		self.autocommit = autocommit
		self.cur.execute(f"CREATE TABLE IF NOT EXISTS {name} ({key} {key_format}, {value} {value_format}, PRIMARY KEY({key}))")
		self.cache_locally = cache_locally
		if cache_locally:
			self.cur.execute("SELECT {0}, {1} FROM {2}".format(key, value, name))
			for row in self.cur:
				super().__setitem__(row[0], row[1])
		if reverse_index:
			self.reverse_index()
	def add(self,key):
		if key not in self:
			self[key] = len(self)+1
		return self[key]
	def __getattr__(self, item):
		return self[item]
	def __getitem__(self, key):
		try:
			return super().__getitem__(key)
		except KeyError:
			self.cur.execute("SELECT {0}, {1} FROM {2} WHERE {0}=%s".format(self.keycol, self.valuecol, self.name), (key,))
			for row in self.cur:
				super().__setitem__(row[0], row[1])
			return super().__getitem__(key)
	def __setitem__(self, key, value):
		if key not in self:
			self.cur.execute("INSERT OR {} INTO {} ({},{}) VALUES (%s,%s)".format(self.overwrite_mechanism,self.name,self.keycol,self.valuecol),(key,value))
			if self.cache_locally:
				super().__setitem__(key, value)
		elif (key in self and self[key] != value):
			self.cur.execute("UPDATE {0} SET {2}=%s WHERE {1}=%s".format(self.name,self.keycol,self.valuecol),(value,key))
			if self.cache_locally:
				super().__setitem__(key, value)
		if self.autocommit:
			self.db.commit()
	def begin_transaction(self):
		self.cur.execute("START TRANSACTION;")
	def end_transaction(self):
		self.cur.execute("COMMIT;")
	def reverse_index(self):
		self.cur.execute("CREATE INDEX IF NOT EXISTS {name}_reverse ON {name} ({val})".format(name=self.name, val=self.valuecol))
	def reverse_lookup(self, value, all=False):
		cur = self.cur.execute("SELECT {1} FROM {0} WHERE {2}==%s".format(self.name,self.keycol,self.valuecol),(value,))
		if all:
			return [i[0] for i in cur]
		else:
			return next(cur,[None])[0]
