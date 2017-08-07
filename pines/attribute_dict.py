

class dicta(dict):
	'''Dictionary with attribute access.'''
	def __getattr__(self, name):
		try:
			return self[name]
		except KeyError:
			if '_helper' in self:
				return self['_helper'](name)
			raise AttributeError(name)
	__setattr__ = dict.__setitem__
	__delattr__ = dict.__delitem__
	def __repr__(self):
		if self.keys():
			m = max(map(len, list(self.keys()))) + 1
			return '\n'.join([k.rjust(m) + ': ' + repr(v) for k, v in self.items()])
		else:
			return self.__class__.__name__ + "()"







class function_cache(dict):
	def __getitem__(self, key):
		if key not in self:
			self[key] = z = dicta()
			return z
		return super().__getitem__(key)





class quickdot(dict):
	'''Autoexpanding dictionary with attribute access.'''
	def __getattr__(self, name):
		try:
			return self[name]
		except KeyError:
			if '_helper' in self:
				return self['_helper'](name)
			raise AttributeError(name)
	__setattr__ = dict.__setitem__
	__delattr__ = dict.__delitem__
	def __repr__(self):
		if self.keys():
			m = max(map(len, list(self.keys()))) + 1
			return '\n'.join(['┣'+k.rjust(m) + ': ' + repr(v).replace('\n','\n┃'+' '*(m+2)) for k, v in self.items()])
		else:
			return self.__class__.__name__ + "()"
	def __getitem__(self, key):
		if "." not in key:
			if key not in self:
				self[key] = z = quickdot()
				return z
			else:
				return super().__getitem__(key)
		else: # dot in key
			keys = key.split('.')
			if keys[0] not in self:
				self[keys[0]] = z = quickdot()
				return z[".".join(keys[1:])]
			else: # first key found
				return self[keys[0]][".".join(keys[1:])]
	def __setitem__(self, key, val):
		if "." not in key:
			super().__setitem__(key, val)
		else: # dot in key
			keys = key.split('.')
			if keys[0] not in self:
				self[keys[0]] = quickdot()
			self[keys[0]][".".join(keys[1:])] = val
	def __init__(self, *arg, **kwargs):
		super().__init__()
		a = []
		for i in arg:
			if isinstance(i,dict):
				for key, val in i.items():
					if isinstance(val, dict):
						self[key] = quickdot(val)
					else:
						self[key] = val
			else:
				raise TypeError('cannot init from not-a-dict')
		for key,val in kwargs.items():
			if isinstance(val,dict):
				self[key] = quickdot(val)
			else:
				self[key] = val
	def __contains__(self, item):
		try:
			if super().__contains__(item):
				return True
		except TypeError:
			pass
		if isinstance(item,str):
			keys = item.split('.')
		else:
			keys = item
		if len(keys) > 1:
			if super().__contains__(keys[0]):
				return (keys[1:]) in (self[keys[0]])
			else:
				return False
		else:
			return super().__contains__(keys[0])
	def __add__(self, other):
		if not isinstance(other, quickdot):
			raise TypeError("can only add quickdot to quickdot")
		combo = quickdot(self)
		combo.update(other)
		return combo
	def __iadd__(self, other):
		if not isinstance(other, quickdot):
			raise TypeError("can only add quickdot to quickdot")
		super().update(other)
		return self

def add_to_quickdot(qdot,tag,value):
	if isinstance(tag,str):
		keys = tag.split('.')
	else:
		keys = tag
	if len(keys) > 1:
		add_to_quickdot(qdot[keys[0]], keys[1:], value)
	else:
		qdot[keys[0]] = value
	return qdot


class fdict(dicta):
	def __init__(self, **kw):
		for key,val in kw.items():
			if not isinstance(val,str):
				self[key] = val
		temp = {}
		for key,val in kw.items():
			if isinstance(val,str):
				try:
					self[key] = val.format(**self)
				except KeyError:
					temp[key] = val
		temp1 = {}
		for key,val in temp.items():
			try:
				self[key] = val.format(**self)
			except KeyError:
				temp1[key] = val
		for key,val in temp1.items():
			self[key] = val.format(**self)

