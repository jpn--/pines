

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
from sklearn.linear_model import LinearRegression

from . import LinearAndGaussianProcessRegression, GaussianProcessRegressor_, ignore_warnings

import numpy, pandas
import scipy.stats
import warnings
import contextlib




from sklearn.multioutput import MultiOutputRegressor as MultiOutputRegressor_

class MultiOutputRegressor(MultiOutputRegressor_):

	def cross_val_scores(self, X, Y, cv=3):
		p = self.cross_val_predicts(X, Y, cv=cv)
		return pandas.Series(
			r2_score(Y, p, sample_weight=None, multioutput='raw_values'),
			index=Y.columns
		)

	def cross_val_predicts(self, X, Y, cv=3, alt_y=None):
		if not isinstance(X, pandas.DataFrame):
			raise TypeError('must use pandas.DataFrame for X')
		if not isinstance(Y, pandas.DataFrame):
			raise TypeError('must use pandas.DataFrame for Y')
		with ignore_warnings(DataConversionWarning):
			p = cross_val_predict(self, X, Y, cv=cv)
		return pandas.DataFrame(p, columns=Y.columns, index=Y.index)




class SingleTargetRegression(
		BaseEstimator,
		RegressorMixin,
):

	def __init__(self, core_features=None, keep_other_features=3, detrend=True):
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
		self.use_linear = detrend


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
			#raise TypeError('must use pandas.DataFrame for X')
			X = pandas.DataFrame(X)

		if self.core_features is None:
			return X

		X_core = X.loc[:,self.core_features]
		X_other = X.loc[:, X.columns.difference(self.core_features)]
		if X_other.shape[1] <= self.keep_other_features:
			return X

		# If self.keep_other_features is zero, there is no feature selecting to do and we return only the core.
		if self.keep_other_features == 0:
			return X_core

		if y is not None:
			self.feature_selector = SelectKBest(mutual_info_regression, k=self.keep_other_features).fit(X_other, y)

		X_other = pandas.DataFrame(
			self.feature_selector.transform(X_other),
			columns=X_other.columns[self.feature_selector.get_support()],
			index=X_other.index,
		)

		return pandas.concat([X_core, X_other], axis=1)


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

		if not isinstance(X, pandas.DataFrame):
			#raise TypeError('must use pandas.DataFrame for X')
			X = pandas.DataFrame(X)

		with ignore_warnings(DataConversionWarning):

			if isinstance(y, pandas.DataFrame):
				self.Y_columns = y.columns
			elif isinstance(y, pandas.Series):
				self.Y_columns = [y.name]
			else:
				self.Y_columns = None

			X_core_plus = self._feature_selection(X, y)

			if self.use_linear:
				self.lr.fit(X_core_plus, y)
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
			#raise TypeError('must use pandas.DataFrame for X')
			X = pandas.DataFrame(X)

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

	def cross_val_predict(self, X, y, cv=3):

		with ignore_warnings(DataConversionWarning):

			X_core_plus = self._feature_selection(X, y)

			total = cross_val_predict(self, X_core_plus, y, cv=cv)
			return pandas.DataFrame(
				total,
				index=y.index,
				columns=y.columns,
			)



def SingleTargetRegressions(*args, **kwargs):
	return MultiOutputRegressor(SingleTargetRegression(*args, **kwargs))








class ChainedTargetRegression(
		BaseEstimator,
		RegressorMixin,
):

	def __init__(self, keep_other_features=3, replication=100):
		"""

		Parameters
		----------
		core_features
			feature columns to definitely keep for both LR and GPR

		"""

		self.core_features = None
		self.keep_other_features = keep_other_features
		self.step1 = LinearAndGaussianProcessRegression()
		self.gpr = GaussianProcessRegressor_(n_restarts_optimizer=9)
		self.y_residual = None
		self.kernel_generator = lambda dims: C() * RBF([1.0] * dims)

	def fit(self, X, Y):
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
		if not isinstance(X, pandas.DataFrame):
			raise TypeError('must use pandas.DataFrame for X')

		if not isinstance(Y, pandas.DataFrame):
			raise TypeError('must use pandas.DataFrame for Y')

		with ignore_warnings(DataConversionWarning):

			self.Y_columns = Y.columns

			Yhat = pandas.DataFrame(
				index=X.index,
				columns=self.Y_columns,
			)

			self.steps = []

			for n, col in enumerate(Y.columns):
				self.steps.append(
					LinearAndGaussianProcessRegression(
						core_features=X.columns,
						keep_other_features=self.keep_other_features,
					).fit(
						pandas.concat([X, Yhat.iloc[:,:n]], axis=1),
						Y[col]
					)
				)
				Yhat.iloc[:, n] = self.steps[-1].cross_val_predict(pandas.concat([X, Yhat.iloc[:,:n]], axis=1), Y[col])

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

		Yhat = pandas.DataFrame(
			index=X.index,
			columns=self.Y_columns,
		)

		if return_std:
			Ystd = pandas.DataFrame(
				index=X.index,
				columns=self.Y_columns,
			)
			for n, col in enumerate(self.Y_columns):
				y1, y2 = self.steps[n].predict(
					pandas.concat([X, Yhat.iloc[:, :n]], axis=1),
					return_std=True
				)
				Yhat.iloc[:, n] = y1
				Ystd.iloc[:, n] = y2
			return Yhat, Ystd

		else:
			for n, col in enumerate(self.Y_columns):
				y1 = self.steps[n].predict(
					pandas.concat([X, Yhat.iloc[:, :n]], axis=1),
				)
				Yhat.iloc[:, n] = y1
			return Yhat


	def cross_val_scores(self, X, Y, cv=3):
		p = self.cross_val_predicts(X, Y, cv=cv)
		return pandas.Series(
			r2_score(Y, p, sample_weight=None, multioutput='raw_values'),
			index=Y.columns
		)

	def cross_val_predicts(self, X, Y, cv=3, alt_y=None):
		if not isinstance(X, pandas.DataFrame):
			raise TypeError('must use pandas.DataFrame for X')
		if not isinstance(Y, pandas.DataFrame):
			raise TypeError('must use pandas.DataFrame for Y')
		with ignore_warnings(DataConversionWarning):
			p = cross_val_predict(self, X, Y, cv=cv)
		return pandas.DataFrame(p, columns=Y.columns, index=Y.index)


	def score(self, X, y, sample_weight=None):
		"""Returns the coefficient of determination R^2 of the prediction.

		The coefficient R^2 is defined as (1 - u/v), where u is the residual
		sum of squares ((y_true - y_pred) ** 2).sum() and v is the total
		sum of squares ((y_true - y_true.mean()) ** 2).sum().
		The best possible score is 1.0 and it can be negative (because the
		model can be arbitrarily worse). A constant model that always
		predicts the expected value of y, disregarding the input features,
		would get a R^2 score of 0.0.

		Parameters
		----------
		X : array-like, shape = (n_samples, n_features)
			Test samples.

		y : array-like, shape = (n_samples) or (n_samples, n_outputs)
			True values for X.

		sample_weight : array-like, shape = [n_samples], optional
			Sample weights.

		Returns
		-------
		score : float
			R^2 of self.predict(X) wrt. y.
		"""

		return r2_score(y, self.predict(X), sample_weight=sample_weight,
						multioutput='raw_values').mean()




class StackedSingleTargetRegression(
		BaseEstimator,
		RegressorMixin,
):

	def __init__(
			self,
			keep_other_features=3,
			keep_core_features=False,
			replication=100,
			step1_detrend=True,
	):
		"""

		Parameters
		----------
		core_features
			feature columns to definitely keep for both LR and GPR

		"""

		self.core_features = None
		self.keep_other_features = keep_other_features
		self.keep_core_features = keep_core_features
		self.step1_detrend = step1_detrend
		self.step2_cv_folds = 5

		# self.gpr = GaussianProcessRegressor_(n_restarts_optimizer=9)
		# self.y_residual = None
		# self.kernel_generator = lambda dims: C() * RBF([1.0] * dims)

	def fit(self, X, Y):
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
		if not isinstance(X, pandas.DataFrame):
			raise TypeError('must use pandas.DataFrame for X')

		if not isinstance(Y, pandas.DataFrame):
			raise TypeError('must use pandas.DataFrame for Y')

		with ignore_warnings(DataConversionWarning):

			self.step1 = SingleTargetRegressions(
				core_features=X.columns,
				keep_other_features=0,
				detrend = self.step1_detrend,
			).fit(X, Y)

			Y_cv = self.step1.cross_val_predict(X, Y, cv=self.step2_cv_folds)

			self.step2 = [
				SingleTargetRegression(
					core_features=X.columns if self.keep_core_features else (),
					keep_other_features=self.keep_other_features,
					detrend=False,
				).fit(
					pandas.concat([X, Y_cv], axis=1),
					Y[col]
				)
				for n,col in enumerate(Y.columns)
			]

			self.Y_columns = Y.columns

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

		Yhat2 = pandas.DataFrame(
			index=X.index,
			columns=self.Y_columns,
		)

		Yhat1 = self.step1.predict(X)

		for n, col in enumerate(self.Y_columns):
			temp = self.step2[n].predict(
				pandas.concat([X, Yhat1], axis=1),
			)
			Yhat2.iloc[:, n] = temp

		return Yhat2


	def cross_val_scores(self, X, Y, cv=3):
		p = self.cross_val_predicts(X, Y, cv=cv)
		return pandas.Series(
			r2_score(Y, p, sample_weight=None, multioutput='raw_values'),
			index=Y.columns
		)

	def cross_val_predicts(self, X, Y, cv=3, alt_y=None):
		if not isinstance(X, pandas.DataFrame):
			raise TypeError('must use pandas.DataFrame for X')
		if not isinstance(Y, pandas.DataFrame):
			raise TypeError('must use pandas.DataFrame for Y')
		with ignore_warnings(DataConversionWarning):
			p = cross_val_predict(self, X, Y, cv=cv)
		return pandas.DataFrame(p, columns=Y.columns, index=Y.index)


	def score(self, X, y, sample_weight=None):
		"""Returns the coefficient of determination R^2 of the prediction.

		The coefficient R^2 is defined as (1 - u/v), where u is the residual
		sum of squares ((y_true - y_pred) ** 2).sum() and v is the total
		sum of squares ((y_true - y_true.mean()) ** 2).sum().
		The best possible score is 1.0 and it can be negative (because the
		model can be arbitrarily worse). A constant model that always
		predicts the expected value of y, disregarding the input features,
		would get a R^2 score of 0.0.

		Parameters
		----------
		X : array-like, shape = (n_samples, n_features)
			Test samples.

		y : array-like, shape = (n_samples) or (n_samples, n_outputs)
			True values for X.

		sample_weight : array-like, shape = [n_samples], optional
			Sample weights.

		Returns
		-------
		score : float
			R^2 of self.predict(X) wrt. y.
		"""

		return r2_score(y, self.predict(X), sample_weight=sample_weight,
						multioutput='raw_values').mean()

