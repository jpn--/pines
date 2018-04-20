import psycopg2
import hashlib, cloudpickle, uuid
from collections.abc import MutableMapping


import psycopg2.extras
psycopg2.extras.register_uuid()

def _hash128(x):
	return hashlib.shake_128(cloudpickle.dumps(x)).digest(16)

def _uhash(x):
	return uuid.UUID(bytes=_hash128(x))



class PostgresHashStore(MutableMapping):

	def __init__(self, *args, tablename='vault', **kwargs):
		self.keycol = "id"
		self.key_format = "UUID"
		self.valuecol = "value"
		self.value_format = "BYTEA"
		self.tablename = tablename
		self.connection = psycopg2.connect(*args, **kwargs)
		with self.connection.cursor() as cur:
			cur.execute(f"""
			CREATE TABLE IF NOT EXISTS {self.tablename} (
				{self.keycol} {self.key_format}, 
				{self.valuecol} {self.value_format}, 
				PRIMARY KEY({self.keycol})
			)""")
			cur.execute("END TRANSACTION")

	def __getitem__(self, key):
		try:
			if not isinstance(key, uuid.UUID):
				key = _uhash(key)
			cur = self.connection.cursor()
			cur.execute(f"SELECT {self.valuecol} FROM {self.tablename} WHERE {self.keycol}=%s", (key,))
			for row in cur:
				return cloudpickle.loads(row[0])
			raise KeyError(key)
		finally:
			pass

	def __setitem__(self, key, value):
		try:
			if not isinstance(key, uuid.UUID):
				key = _uhash(key)
			value = cloudpickle.dumps(value)
			cur = self.connection.cursor()
			cur.execute(f"""
			INSERT INTO {self.tablename} ({self.keycol},{self.valuecol}) VALUES (%s,%s)
			ON CONFLICT ({self.keycol}) 
			DO UPDATE SET {self.valuecol} = EXCLUDED.{self.valuecol}
			""", (key, value))
		finally:
			pass

	def __delitem__(self, key):
		if not isinstance(key, uuid.UUID):
			key = _uhash(key)
		cur = self.connection.cursor()
		cur.execute(f"""
		DELETE FROM {self.tablename} 
		WHERE {self.keycol} = %s
		""", (key, ))

	def __iter__(self):
		cur = self.connection.cursor()
		cur.execute(f"""
		SELECT {self.keycol}, {self.valuecol} FROM {self.tablename} 
		""")
		for row in cur:
			yield row

	def __len__(self):
		cur = self.connection.cursor()
		cur.execute(f"""
		SELECT count(*) FROM {self.tablename} 
		""")
		for row in cur:
			return row[0]
