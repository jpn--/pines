

import mysql.connector
import hashlib, cloudpickle



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
			if "already exists" in str(err):
				pass
			else:
				raise
		self.cache_locally = cache_locally
		if cache_locally:
			self.cur.execute("SELECT {0}, {1} FROM {2}".format(key, value, tablename))
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




def hash512(x):
	return hashlib.sha512(cloudpickle.dumps(x)).digest()

class HashStore():

	def __init__(self, username, password, host, database, tablename, *, raise_on_warnings=False,
				 autocommit=True, cache_locally=True, keep_connection_alive=True):
		key = "id"
		key_format = "VARBINARY(64)"
		value = "value"
		value_format = "LONGBLOB"
		self.keycol = key
		self.valuecol = value
		self.keep_connection_alive = keep_connection_alive
		self.db = mysql.connector.connect(user=username, password=password, host=host, database=database,
		                                  raise_on_warnings=raise_on_warnings)
		self.db.connect()
		cur = self.db.cursor()
		self.name = tablename
		self.autocommit = autocommit
		self.cache = {}
		try:
			cur.execute(f"CREATE TABLE IF NOT EXISTS {tablename} ({key} {key_format}, {value} {value_format}, PRIMARY KEY({key}))")
		except mysql.connector.errors.DatabaseError as err:
			if "already exists" in str(err):
				pass
			else:
				raise
		self.cache_locally = cache_locally
		if cache_locally:
			cur.execute("SELECT {0}, {1} FROM {2}".format(key, value, tablename))
			for row in cur:
				self.cache[bytes(row[0])] = row[1]
		if not self.keep_connection_alive:
			self.db.disconnect()

	def __getitem__(self, key):
		try:
			if isinstance(key, bytes) and key in self.cache:
				return cloudpickle.loads(self.cache[key])
			hkey = hash512(key)
			if hkey in self.cache:
				return cloudpickle.loads(self.cache[hkey])
			self.db.reconnect(attempts=30,delay=5)
			cur = self.db.cursor()
			if isinstance(key, bytes) and len(key)==64:
				cur.execute(f"SELECT {self.keycol}, {self.valuecol} FROM {self.name} WHERE {self.keycol}=%s", (key,))
				for row in cur:
					return cloudpickle.loads(row[1])
			cur.execute(f"SELECT {self.keycol}, {self.valuecol} FROM {self.name} WHERE {self.keycol}=%s", (hkey,))
			for row in cur:
				return cloudpickle.loads(row[1])
			raise KeyError(key)
		finally:
			if not self.keep_connection_alive:
				self.db.disconnect()

	def __setitem__(self, key, value):
		try:
			hkey = hash512(key)
			value = cloudpickle.dumps(value)
			self.db.reconnect(attempts=30, delay=5)
			cur = self.db.cursor()
			cur.execute(f"REPLACE INTO {self.name} ({self.keycol},{self.valuecol}) VALUES (%s,%s)",(hkey,value))
			if self.cache_locally:
				self.cache[hkey] = value
			if self.autocommit:
				self.db.commit()
		finally:
			if not self.keep_connection_alive:
				self.db.disconnect()

	def __contains__(self, item):
		try:
			hkey = hash512(item)
			self.db.reconnect(attempts=30, delay=5)
			cur = self.db.cursor()
			cur.execute(f"SELECT 1 FROM {self.name} WHERE {self.keycol}=%s", (hkey,))
			for row in cur:
				return True
			return False
		finally:
			if not self.keep_connection_alive:
				self.db.disconnect()

	def set_by_hash(self, hashval, value):
		try:
			value = cloudpickle.dumps(value)
			self.db.reconnect(attempts=30, delay=5)
			cur = self.db.cursor()
			cur.execute(f"REPLACE INTO {self.name} ({self.keycol},{self.valuecol}) VALUES (%s,%s)",(hashval,value))
			if self.cache_locally:
				self.cache[hashval] = value
			if self.autocommit:
				self.db.commit()
		finally:
			if not self.keep_connection_alive:
				self.db.disconnect()





