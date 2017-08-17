

from pines.attribute_dict import dicta

class Counter(dicta):

	def one(self, key):
		if key in self:
			self[key] += 1
		else:
			self[key] = 1

