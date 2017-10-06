

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
	def __xml__(self):
		from .xhtml import Elem
		x = Elem('div')
		t = x.put('table')
		for k, v in self.items():
			tr = t.put('tr')
			tr.put('td', text=k, style='font-weight:bold;vertical-align:top;')
			try:
				v_xml = v.__xml__()
			except AttributeError:
				tr.put('td').put('pre', text=repr(v))
			else:
				tr.append(v_xml)
		return x
	def _repr_html_(self):
		return self.__xml__().tostring()


class function_cache(dict):
	def __getitem__(self, key):
		if key not in self:
			self[key] = z = dicta()
			return z
		return super().__getitem__(key)




class dictal(dict):
	'''Dictionary with attribute access and lowercase str keys.'''
	def __init__(self, *args, **kwargs):
		super().__init__()
		for arg in args:
			for key,val in arg.items():
				self[key] = val
		for key,val in kwargs.items():
			self[key] = val
	def __setitem__(self, key, val):
		if not isinstance(key,str):
			raise TypeError("dictal keys must be strings")
		return super().__setitem__(key.casefold(), val)
	def __getitem__(self, key):
		if not isinstance(key,str):
			raise TypeError("dictal keys must be strings")
		return super().__getitem__(key.casefold())
	def __delitem__(self, key):
		if not isinstance(key,str):
			raise TypeError("dictal keys must be strings")
		return super().__delitem__(key.casefold())
	def __getattr__(self, name):
		try:
			return self[name]
		except KeyError:
			if '_helper' in self:
				return self['_helper'](name)
			raise AttributeError(name)
	__setattr__ = __setitem__
	__delattr__ = __delitem__
	def __repr__(self):
		if self.keys():
			m = max(map(len, list(self.keys()))) + 1
			return '\n'.join([k.rjust(m) + ': ' + repr(v) for k, v in self.items()])
		else:
			return self.__class__.__name__ + "()"




class quickdot(dicta):
	'''Autoexpanding dictionary with attribute access.'''
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
		for key, val in other.items():
			if isinstance(val,quickdot):
				combo[key] += val
			else:
				combo[key] = val
		return combo
	def __iadd__(self, other):
		if not isinstance(other, quickdot):
			raise TypeError("can only add quickdot to quickdot")
		for key, val in other.items():
			if isinstance(val, quickdot):
				self[key] += val
			else:
				self[key] = val
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
	def __init__(self, *args, **kw):
		super().__init__(*args)
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



qdict = quickdot