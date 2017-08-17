
import scipy.stats
import numpy

def beta_pert( x_min, x_mode, x_max,  lamb= 4 ):
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

	Returns
	-------
	rv_frozen
	"""

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


