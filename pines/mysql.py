

import mysql.connector



class stored_dict(dict):
	'''Provide a persistent storage mechanism for use with DB objects.'''
	def __init__(self, username, password, host, database, tablename, *, raise_on_warnings=True, reverse_index=False, key="id", key_format = "VARCHAR(1024)", value="value", value_format="LONGBLOB", autocommit=True, cache_locally=True):
		super().__init__()
		self.keycol = key
		self.valuecol = value
		self.db = mysql.connector.connect(user=username, password=password, host=host, database=database, raise_on_warnings=raise_on_warnings)
		self.db.connect()
		self.name = tablename
		self.cur = self.db.cursor()
		self.autocommit = autocommit
		try:
			self.cur.execute(f"CREATE TABLE IF NOT EXISTS {tablename} ({key} {key_format}, {value} {value_format}, PRIMARY KEY({key}))")
		except mysql.connector.errors.DatabaseError as err:
			if "already exists" in err:
				pass
			else:
				raise
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
			self.cur.execute("REPLACE INTO {} ({},{}) VALUES (%s,%s)".format(self.name,self.keycol,self.valuecol),(key,value))
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
