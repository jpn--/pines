
import scipy.stats
import numpy

def beta_pert( x_min, x_mode, x_max,  lamb= 4, mode_as_fraction=None ):
	"""
	Beta-PERT

	To transform a [0,1] random uniform `x` to a beta-PERT random,
	use beta_pert(*arg).ppf(x)

	Parameters
	----------
	x_min, x_mode, x_max : float
		The min, mode, and max for the beta-pert distribution
	lamb : float
		The pert shape modifier
	mode_as_fraction : float, optional
		The mode is replaced with the fraction of the distance from the min to the max.

	Returns
	-------
	rv_frozen
	"""

	if mode_as_fraction is not None:
		x_mode = x_min + mode_as_fraction*(x_max-x_min)

	if ( x_min > x_max or x_mode > x_max or x_mode < x_min ):
		raise ValueError( "invalid parameters" )

	x_range = x_max - x_min
	if ( x_range == 0 ):
		return numpy.full_like(q, fill_value=x_min)

	mu = ( x_min + x_max + lamb * x_mode ) / ( lamb + 2 )

	# special case if mu == mode
	if ( mu == x_mode ):
		v = ( lamb / 2 ) + 1
	else:
		v = (( mu - x_min ) * ( 2 * x_mode - x_min - x_max )) / (( x_mode - mu ) * ( x_max - x_min ))

	w = ( v * ( x_max - mu )) / ( mu - x_min )

	return scipy.stats.beta( v, w, loc=x_min, scale=x_range )


def triangular( x_min, x_mode, x_max, mode_as_fraction=None ):
	if mode_as_fraction is not None:
		x_mode = x_min + mode_as_fraction*(x_max-x_min)
	if ( x_min > x_max or x_mode > x_max or x_mode < x_min ):
		raise ValueError( "invalid parameters" )
	scale = x_max - x_min
	if scale==0:
		peak = x_mode
	else:
		peak = (x_mode-x_min)/scale
	return scipy.stats.triang( peak, loc=x_min, scale=scale )


def uniform( x_min, x_max ):
	if ( x_min > x_max ):
		raise ValueError( "invalid parameters" )
	scale = x_max - x_min
	return scipy.stats.uniform( loc=x_min, scale=scale )

def binary( p ):
	if (p < 0) or (p > 1):
		raise ValueError( "invalid parameters" )
	return scipy.stats.binom( n=1, p=p )


def _mod_linspace(start, stop, num=50, dtype=None):
	y, step = numpy.linspace(start, stop, num=num, endpoint=False, retstep=True, dtype=dtype)
	y += step/2
	return y

def prod_two_dists_ppf_approx(dist1, dist2, q, draws=500):
	x = _mod_linspace(0,1,draws)
	x1 = dist1.ppf(x)
	x2 = dist2.ppf(x)
	x1x2 = numpy.outer(x1,x2).flatten()
	return numpy.percentile(x1x2,q*100)

def sum_two_dists_ppf_approx(dist1, dist2, q, draws=500):
	x = _mod_linspace(0,1,draws)
	x1 = dist1.ppf(x)
	x2 = dist2.ppf(x)
	x1x2 = numpy.zeros([draws,draws])
	x1x2 += x1[:,None]
	x1x2 += x2[None,:]
	return numpy.percentile(x1x2,q*100)


def prod_two_triangular_ppf_approx(q, x1_min, x1_mode, x1_max, x2_min, x2_mode, x2_max):
	x = numpy.linspace(0,1,500)
	x1 = triangular( x1_min, x1_mode, x1_max ).ppf(x)
	x2 = triangular( x2_min, x2_mode, x2_max ).ppf(x)
	x1x2 = numpy.outer(x1,x2).flatten()
	return numpy.percentile(x1x2,q*100)


def quick_linear_regression(X, y, log=None):
	import statsmodels.api as sm
	import pandas
	Xc = sm.add_constant(X)
	m = sm.OLS(y, Xc, hasconst=True)
	statsmodel_results = m.fit()
	if log is not None:
		log(statsmodel_results.summary())

	sm_df = pandas.concat((statsmodel_results.params,
						   statsmodel_results.bse,
						   statsmodel_results.tvalues,
						   statsmodel_results.pvalues,
						   statsmodel_results.conf_int()), axis=1)
	sm_df.columns = ['coef', 'std err', 't', 'P>|t|', '[0.025', '0.975]']
	return sm_df