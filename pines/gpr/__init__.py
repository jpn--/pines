
from sklearn.linear_model import LinearRegression as _sklearn_LinearRegression
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn import preprocessing
from sklearn.base import TransformerMixin
from sklearn.gaussian_process.kernels import RBF, ConstantKernel as C, RationalQuadratic as RQ
from sklearn.base import RegressorMixin, BaseEstimator
from sklearn.model_selection import cross_val_score, cross_val_predict
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import r2_score

from sklearn.feature_selection import SelectKBest
from sklearn.feature_selection import f_regression, mutual_info_regression

from sklearn.exceptions import DataConversionWarning

import numpy, pandas
import scipy.stats
import warnings
import contextlib

from pines.attribute_dict import dicta




def feature_concat(*args):
	if all(isinstance(a, pandas.DataFrame) for a in args):
		return pandas.concat(args, axis=1)
	if any(isinstance(a, pandas.DataFrame) for a in args):
		ref = 0
		while not isinstance(args[ref], pandas.DataFrame):
			ref += 1
		ix = args[ref].index
		return pandas.concat([pandas.DataFrame(a, index=ix) for a in args], axis=1)
	return numpy.concatenate(args, axis=1)



class LinearRegression(_sklearn_LinearRegression):

	def fit(self, X, y, sample_weight=None):
		# print(" LR FIT on",len(X))
		super().fit(X, y, sample_weight=sample_weight)

		if isinstance(X, pandas.DataFrame):
			self.names_ = X.columns.copy()

		sse = numpy.sum((self.predict(X) - y) ** 2, axis=0) / float(X.shape[0] - X.shape[1])

		if sse.shape == ():
			sse = sse.reshape(1,)

		inv_X_XT = numpy.linalg.inv(numpy.dot(X.T, X))

		with warnings.catch_warnings():
			warnings.simplefilter("ignore", category=RuntimeWarning)

			try:
				se = numpy.array([
					numpy.sqrt(numpy.diagonal(sse[i] * inv_X_XT))
					for i in range(sse.shape[0])
				])
			except:
				print("sse.shape",sse.shape)
				print(sse)
				raise

			self.t_ = self.coef_ / se
			self.p_ = 2 * (1 - scipy.stats.t.cdf(numpy.abs(self.t_), y.shape[0] - X.shape[1]))

		# try:
		# 	print(y.values[0])
		# except AttributeError:
		# 	print(y[0])
		return self

	def predict(self, X):
		# print(" "*55,"LR PREDICT on", len(X))
		return super().predict(X)


class GaussianProcessRegressor_(GaussianProcessRegressor):

	def fit(self, X, y):
		# print(" GPR FIT on",len(X))
		q = super().fit(X,y)
		# try:
		# 	print(y.values[0])
		# except AttributeError:
		# 	print(y[0])
		return q

	def predict(self, X, return_std=False, return_cov=False):
		#print(" "*55,"GPR PREDICT on", len(X))
		return super().predict(X, return_std=return_std, return_cov=return_cov)

def _make_as_vector(y):
	# if isinstance(y, (pandas.DataFrame, pandas.Series)):
	# 	y = y.values.ravel()
	return y

@contextlib.contextmanager
def ignore_warnings(category=Warning):
	with warnings.catch_warnings():
		warnings.simplefilter("ignore", category=category)
		yield


class LinearAndGaussianProcessRegression(
		BaseEstimator,
		RegressorMixin,
):

	def __init__(self, core_features=None, keep_other_features=3, use_linear=True):
		"""

		Parameters
		----------
		core_features
			feature columns to definitely keep for both LR and GPR

		"""

		self.core_features = core_features
		self.keep_other_features = keep_other_features
		self.lr = LinearRegression()
		self.gpr = GaussianProcessRegressor_(n_restarts_optimizer=9)
		self.y_residual = None
		self.kernel_generator = lambda dims: C() * RBF([1.0] * dims)
		self.use_linear = use_linear


	def _feature_selection(self, X, y=None):
		"""

		Parameters
		----------
		X : pandas.DataFrame
		y : ndarray
			If given, the SelectKBest feature selector will be re-fit to find the best features. If not given,
			then the previously fit SelectKBest will be used; if it has never been fit, an error is raised.

		Returns
		-------
		pandas.DataFrame
			Contains all the core features plus the K best other features.
		"""

		if not isinstance(X, pandas.DataFrame):
			raise TypeError('must use pandas.DataFrame for X')

		if self.core_features is None:
			return X

		y = _make_as_vector(y)
		X_core = X.loc[:,self.core_features]
		X_other = X.loc[:, X.columns.difference(self.core_features)]
		if X_other.shape[1] <= self.keep_other_features:
			return X

		# If self.keep_other_features is zero, there is no feature selecting to do and we return only the core.
		if self.keep_other_features == 0:
			return X_core

		if y is not None:
			self.feature_selector = SelectKBest(mutual_info_regression, k=self.keep_other_features).fit(X_other, y)

		try:
			X_other = pandas.DataFrame(
				self.feature_selector.transform(X_other),
				columns=X_other.columns[self.feature_selector.get_support()],
				index=X_other.index,
			)
		except:
			print("X_other.info")
			print(X_other.info(1))
			print("X_other")
			print(X_other)
			raise

		try:
			return pandas.concat([X_core, X_other], axis=1)
		except:
			print("X_core")
			print(X_core)
			print("X_other")
			print(X_other)
			print(X_core.info())
			print(X_other.info())
			raise


	def fit(self, X, y):
		"""
		Fit linear and gaussian model.

		Parameters
		----------
		X : numpy array or sparse matrix of shape [n_samples, n_features]
			Training data
		y : numpy array of shape [n_samples, n_targets]
			Target values.

		Returns
		-------
		self : returns an instance of self.
		"""
		# print("META FIT on",len(X))

		# if not isinstance(X, pandas.DataFrame):
		# 	# X = pandas.DataFrame(X)
		# 	raise TypeError('must use pandas.DataFrame for X')
		#
		# if self.core_features is None:
		# 	X_core = X
		# 	X_other = X.loc[:,[]]
		# else:
		# 	X_core = X.loc[:,self.core_features]
		# 	X_other = X.loc[:, X.columns.difference(self.core_features)]
		#
		# self.feature_selector = SelectKBest(mutual_info_regression, k=self.keep_other_features).fit(X_other, y)
		#
		# X_other = self.feature_selector.transform(X_other)

		with ignore_warnings(DataConversionWarning):

			if isinstance(y, pandas.DataFrame):
				self.Y_columns = y.columns
			elif isinstance(y, pandas.Series):
				self.Y_columns = [y.name]
			else:
				self.Y_columns = None

			y = _make_as_vector(y)
			X_core_plus = self._feature_selection(X, y)

			if self.use_linear:
				try:
					self.lr.fit(X_core_plus, y)
				except:
					print("X_core_plus.shape",X_core_plus.shape)
					print("y.shape",y.shape)
					print(X_core_plus)
					print(y)
					raise
				self.y_residual = y - self.lr.predict(X_core_plus)
			else:
				self.y_residual = y
			dims = X_core_plus.shape[1]
			self.gpr.kernel = self.kernel_generator(dims)
			self.gpr.fit(X_core_plus, self.y_residual)
			# print(self.y_residual.values[0])

		return self


	def predict(self, X, return_std=False, return_cov=False):
		"""Predict using the model

		Parameters
		----------
		X : {array-like, sparse matrix}, shape = (n_samples, n_features)
			Samples.

		Returns
		-------
		C : array, shape = (n_samples,)
			Returns predicted values.
		"""

		if not isinstance(X, pandas.DataFrame):
			raise TypeError('must use pandas.DataFrame for X')
		X_core_plus = self._feature_selection(X)

		if self.use_linear:
			y_hat_lr = self.lr.predict(X=X_core_plus)
		else:
			y_hat_lr = 0

		if return_std:
			y_hat_gpr, y_hat_std = self.gpr.predict(X_core_plus, return_std=True)

			if self.Y_columns is not None:
				y_result = pandas.DataFrame(
					y_hat_lr + y_hat_gpr,
					columns=self.Y_columns,
					index=X.index,
				)
			else:
				y_result = y_hat_lr + y_hat_gpr

			return y_result, y_hat_std
		else:
			y_hat_gpr = self.gpr.predict(X_core_plus)

			if self.Y_columns is not None:
				y_result = pandas.DataFrame(
					y_hat_lr + y_hat_gpr,
					columns=self.Y_columns,
					index=X.index,
				)
			else:
				y_result = y_hat_lr + y_hat_gpr

			return y_result

	def cross_val_scores(self, X, Y, cv=3):
		p = self.cross_val_predict(X, Y, cv=cv)
		return pandas.Series(
			r2_score(Y, p, sample_weight=None, multioutput='raw_values'),
			index=Y.columns
		)
	#
	# def cross_val_scores(self, X, y, cv=3):
	# 	with ignore_warnings(DataConversionWarning):
	# 		y = _make_as_vector(y)
	# 		X_core_plus = self._feature_selection(X, y)
	# 		total = cross_val_score(self, X_core_plus, y, cv=cv)
	# 	return total

	def cross_val_scores_full(self, X, y, cv=3, alt_y=None):

		with ignore_warnings(DataConversionWarning):
			y = _make_as_vector(y)

			X_core_plus = self._feature_selection(X, y)

			total = cross_val_score(self, X_core_plus, y, cv=cv)

			if self.use_linear:
				linear_cv_score = cross_val_score(self.lr, X_core_plus, y, cv=cv)
				linear_cv_predict = cross_val_predict(self.lr, X_core_plus, y, cv=cv)
				linear_cv_residual = y-linear_cv_predict
				gpr_cv_score = cross_val_score(self.gpr, X_core_plus, linear_cv_residual, cv=cv)

				self.lr.fit(X_core_plus, y)
				y_residual = y - self.lr.predict(X_core_plus)
				gpr_cv_score2 = cross_val_score(self.gpr, X_core_plus, y_residual, cv=cv)

				result = dicta(
					total=total,
					linear=linear_cv_score,
					net_gpr=total-linear_cv_score,
					gpr=gpr_cv_score,
					gpr2=gpr_cv_score2,
				)
			else:
				result = dicta(
					total=total,
				)

			if alt_y is not None:
				result['gpr_alt'] = cross_val_score(self.gpr, X, alt_y, cv=cv)
				# print()
				# print(numpy.concatenate([y_residual, alt_y, y_residual-alt_y], axis=1 ))
				# print()
				# print(result['gpr_alt'])
				# print(result['gpr2'])
				# print()
		return result

	def cross_val_predict(self, X, y, cv=3):

		with ignore_warnings(DataConversionWarning):

			X_core_plus = self._feature_selection(X, y)

			if isinstance(y, pandas.DataFrame):
				y_columns = y.columns
			elif isinstance(y, pandas.Series):
				y_columns = [y.name]
			else:
				y_columns = ['Unnamed']

			total = cross_val_predict(self, X_core_plus, y, cv=cv)
			return pandas.DataFrame(
				total,
				index=y.index,
				columns=y_columns,
			)

	def cross_val_predicts(self, X, y, cv=3):

		with ignore_warnings(DataConversionWarning):
			y = _make_as_vector(y)

			X_core_plus = self._feature_selection(X, y)

			total = cross_val_predict(self, X_core_plus, y, cv=cv)
			if self.use_linear:
				linear_cv_predict = cross_val_predict(self.lr, X_core_plus, y, cv=cv)
				linear_cv_residual = y-linear_cv_predict
				gpr_cv_predict_over_cv_linear = cross_val_predict(self.gpr, X_core_plus, linear_cv_residual, cv=cv)

				self.lr.fit(X_core_plus, y)
				linear_full_predict = self.lr.predict(X_core_plus)
				y_residual = y - linear_full_predict
				gpr_cv_predict_over_full_linear = cross_val_predict(self.gpr, X_core_plus, y_residual, cv=cv)

				return dicta(
					total=total,
					linear=linear_cv_predict,
					net_gpr=total-linear_cv_predict,
					gpr=gpr_cv_predict_over_cv_linear+linear_cv_predict,
					gpr2=gpr_cv_predict_over_full_linear+linear_full_predict,
				)
			else:
				return dicta(
					total=total,
				)




def cross_val_scores(pipe, X, y, cv=3):
	# For pipelines

	y = _make_as_vector(y)

	self = pipe.steps[-1][1]

	total = cross_val_score(self, X, y, cv=cv)
	linear_cv_score = cross_val_score(self.lr, X, y, cv=cv)
	linear_cv_predict = cross_val_predict(self.lr, X, y, cv=cv)
	linear_cv_residual = y-linear_cv_predict
	gpr_cv_score = cross_val_score(self.gpr, X, linear_cv_residual, cv=cv)

	self.lr.fit(X, y)
	y_residual = y - self.lr.predict(X)
	gpr_cv_score2 = cross_val_score(self.gpr, X, y_residual, cv=cv)

	return dicta(
		total=total,
		linear=linear_cv_score,
		net_gpr=total-linear_cv_score,
		gpr=gpr_cv_score,
		gpr2=gpr_cv_score2,
	)


class PartialStandardScaler(StandardScaler):

	def __init__(self, copy=True, with_mean=True, with_std=True, omit=()):
		super().__init__(copy=copy, with_mean=with_mean, with_std=with_std)
		self._omit = omit
		self._names = None

	def fit(self, X, y=None):
		result = super().fit(X, y)
		omit = [i for i in self._omit]
		if isinstance(X, pandas.DataFrame):
			self._names = X.columns.copy()
			for n,k in enumerate(omit):
				if isinstance(k, str):
					omit[n] = X.columns.get_loc(k)
		for k in omit:
			if self.with_mean:
				self.mean_[k] = 0
			if self.with_std:
				self.scale_[k] = 1
		return result

	def transform(self, X, y='deprecated', copy=None):
		result = super().transform(X, y, copy)
		if isinstance(X, pandas.DataFrame):
			return pandas.DataFrame(
				data=result,
				index=X.index,
				columns=[(f'{i}†' if i not in self._omit else i) for i in X.columns]
			)
		return result

	def inverse_transform_by_name(self, X, name):
		ix = self._names.get_loc(name)
		if self.with_std:
			X *= self.scale_[ix]
		if self.with_mean:
			X += self.mean_[ix]
		return X

	def transform_by_name(self, X, name):
		ix = self._names.get_loc(name)
		if self.with_mean:
			X -= self.mean_[ix]
		if self.with_std:
			X /= self.scale_[ix]
		return X

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


class ExponentialFeatures(BaseEstimator, TransformerMixin):

	def __init__(self):
		pass

	def fit(self, X, y=None):
		"""
		Compute number of output features.

		Parameters
		----------
		X : array-like, shape (n_samples, n_features)
			The data.

		Returns
		-------
		self : instance
		"""
		return self

	def transform(self, X):
		"""Transform data to add exponential features

		Parameters
		----------
		X : array-like, shape [n_samples, n_features]
			The data to transform, row by row.

		Returns
		-------
		XP : np.ndarray shape [n_samples, NP]
			The matrix of features, where NP is the number of polynomial
			features generated from the combination of inputs.
		"""
		from sklearn.utils import check_array
		from sklearn.utils.validation import check_is_fitted, check_random_state, FLOAT_DTYPES

		from scipy.stats.stats import pearsonr

		X = check_array(X, dtype=FLOAT_DTYPES)
		n_samples, n_features = X.shape

		# allocate output data
		XP = numpy.empty((n_samples, n_features*2), dtype=X.dtype)
		XP_use = numpy.ones((n_features*2,), dtype=bool)

		for i in range(n_features):
			XP[:, i] = X[:, i]
			exp_x = numpy.exp(X[:, i])
			correlation = pearsonr(X[:, i], exp_x)[0]
			# print("correlation is",correlation)
			if numpy.fabs(correlation) < 0.99:
				XP[:, i+n_features] = exp_x
			else:
				XP_use[i+n_features] = 0

		if isinstance(X, pandas.DataFrame):
			result = pandas.DataFrame(
				data=XP,
				columns=list(X.columns) + [f'exp({c})' for c in X.columns],
				index=X.index,
			)
			return result.iloc[:, XP_use]

		return XP[:,XP_use]


class InteractionFeatures(BaseEstimator, TransformerMixin):

	def __init__(self, interaction_point):
		self._interaction_name = interaction_point

	def fit(self, X, y=None):
		"""
		Compute number of output features.

		Parameters
		----------
		X : array-like, shape (n_samples, n_features)
			The data.

		Returns
		-------
		self : instance
		"""
		return self

	def transform(self, X):
		"""Transform data to add exponential features

		Parameters
		----------
		X : array-like, shape [n_samples, n_features]
			The data to transform, row by row.

		Returns
		-------
		XP : np.ndarray shape [n_samples, NP]
			The matrix of features, where NP is the number of polynomial
			features generated from the combination of inputs.
		"""
		from sklearn.utils import check_array
		from sklearn.utils.validation import check_is_fitted, check_random_state, FLOAT_DTYPES

		from scipy.stats.stats import pearsonr

		interact_point = None

		if isinstance(self._interaction_name, int):
			interact_point = self._interaction_name
		else:
			if isinstance(X, pandas.DataFrame):
				interact_point = X.columns.get_loc(self._interaction_name)
			else:
				raise TypeError("X must be DataFrame when interaction_name is string")

		if interact_point is None:
			raise TypeError('interact_point is None')


		Xa = check_array(X, dtype=FLOAT_DTYPES)
		n_samples, n_features = Xa.shape

		# allocate output data
		XP = numpy.empty((n_samples, n_features*2), dtype=Xa.dtype)
		XP_use = numpy.ones((n_features*2,), dtype=bool)
		XP_fresh = numpy.zeros((n_features*2,), dtype=bool)

		for i in range(n_features):
			XP[:, i] = Xa[:, i]
			exp_x = Xa[:, i] * Xa[:, interact_point]
			#correlation = pearsonr(Xa[:, i], exp_x)[0]
			correlation1 = numpy.corrcoef(Xa, exp_x, rowvar=False)[-1, :-1]
			if XP_fresh.sum():
				correlation2 = numpy.corrcoef(XP[:,XP_fresh], exp_x, rowvar=False)[-1, :-1]
			else:
				correlation2 = [0]
			correlation = max( numpy.fabs(correlation1).max(), numpy.fabs(correlation2).max())
			if numpy.fabs(correlation) < 0.99:
				XP[:, i+n_features] = exp_x
				XP_fresh[i+n_features] = True
			else:
				XP_use[i+n_features] = 0

		if isinstance(X, pandas.DataFrame):
			result = pandas.DataFrame(
				data=XP,
				columns=list(X.columns) + [f'{c} ~ {self._interaction_name}' for c in X.columns],
				index=X.index,
			)
			return result.iloc[:, XP_use]

		return XP[:,XP_use]


