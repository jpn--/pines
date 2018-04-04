
from sklearn.linear_model import LinearRegression
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn import preprocessing
from sklearn.base import TransformerMixin
from sklearn.gaussian_process.kernels import RBF, ConstantKernel as C, RationalQuadratic as RQ
from sklearn.base import RegressorMixin, BaseEstimator
from sklearn.model_selection import cross_val_score, cross_val_predict
import numpy, pandas

from .attribute_dict import dicta

class LinearAndGaussianProcessRegression(
		BaseEstimator,
		RegressorMixin,
):

	def __init__(self):
		self.lr = LinearRegression()
		self.gpr = GaussianProcessRegressor()
		self.y_residual = None
		self.kernel_generator = lambda dims: C() * RBF([1.0] * dims)


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
		self.lr.fit(X, y)
		self.y_residual = y - self.lr.predict(X)
		dims = X.shape[1]
		self.gpr.kernel = self.kernel_generator(dims)
		self.gpr.fit(X, self.y_residual)
		return self


	def predict(self, X):
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
		y_hat_lr = self.lr.predict(X=X)
		y_hat_gpr = self.gpr.predict(X)
		return y_hat_lr + y_hat_gpr

	def cross_val_scores(self, X, y, cv=3):
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



def cross_val_scores(pipe, X, y, cv=3):
	# For pipelines

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