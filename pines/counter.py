

from pines.attribute_dict import dicta

class Counter(dicta):

	def one(self, key):
		if key in self:
			self[key] += 1
		else:
			self[key] = 1

	def add(self, other_counter):
		for key, val in other_counter.items():
			if key in self:
				self[key] += val
			else:
				self[key] = val


