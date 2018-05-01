
import numpy, pandas
from sklearn.preprocessing import StandardScaler



class StandardDataFrameScaler(StandardScaler):

	def __init__(self, copy=True, with_mean=True, with_std=True):
		super().__init__(copy=copy, with_mean=with_mean, with_std=with_std)

	def fit(self, X, y=None):
		return super().fit(numpy.log1p(X), y)

	def transform(self, X, y='deprecated', copy=None):
		result = super().transform(X, y, copy)
		if isinstance(X, pandas.DataFrame):
			return pandas.DataFrame(
				data=result,
				index=X.index,
				columns=[f'{i}∫' for i in X.columns]
			)
		return result

	def inverse_transform(self, X, copy=None):
		result = super().inverse_transform(X)
		if isinstance(X, pandas.DataFrame):
			return pandas.DataFrame(
				data=result,
				index=X.index,
				columns=[i.rstrip('∫') for i in X.columns]
			)
		return result


class Log1pStandardScaler(StandardScaler):

	def __init__(self, copy=True, with_mean=True, with_std=True):
		super().__init__(copy=copy, with_mean=with_mean, with_std=with_std)

	def fit(self, X, y=None):
		return super().fit(numpy.log1p(X), y)

	def transform(self, X, y='deprecated', copy=None):
		result = super().transform(numpy.log1p(X), y, copy)
		if isinstance(X, pandas.DataFrame):
			return pandas.DataFrame(
				data=result,
				index=X.index,
				columns=[f'{i}†' for i in X.columns]
			)
		return result

	def inverse_transform(self, X, copy=None):
		result = super().inverse_transform(X)
		result = numpy.expm1(result)
		if isinstance(X, pandas.DataFrame):
			return pandas.DataFrame(
				data=result,
				index=X.index,
				columns=[i.rstrip('†') for i in X.columns]
			)
		return result
