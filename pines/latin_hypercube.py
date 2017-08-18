
import numpy
from scipy.optimize import minimize_scalar


def lhs( n_factors, n_samples, genepool=10000, random_in_cell=True ):
	"""

	Parameters
	----------
	n_factors : int
		The number of columns to sample
	n_samples : int
		The number of Latin hypercube samples (rows)
	genepool : int
		The nubmer of random permutation from which to find good (uncorrelated) columns
	random_in_cell : bool, default True
		If true, a uniform random point in each hypercube cell is chosen, otherwise the
		center point in each cell is chosen.

	Returns
	-------
	ndarray
	"""
	candidates = numpy.empty([genepool, n_samples], dtype=numpy.float64)
	for i in range(genepool):
		candidates[i,:] = numpy.random.permutation(n_samples)
	corr = numpy.fabs(numpy.corrcoef(candidates))
	keepers = [0]
	keeper_gross_corr = 0
	for j in range(n_factors-1):
		keeper_gross_corr += corr[keepers[-1], :]
		k = numpy.argmin(keeper_gross_corr)
		keepers.append(k)

	lhs = candidates[keepers, :].copy()
	if random_in_cell:
		lhs += numpy.random.rand(*(lhs.shape))
	else:
		lhs += 0.5
	lhs /= n_samples
	return lhs


def induce_correlation(h, corr, rows=None, inplace=False):
	h_full = h
	if rows:
		h = h[rows,:]
	h1 = numpy.zeros_like(h)
	nfact = h.shape[0]
	def _avg_off_diag(a):
		upper = numpy.triu_indices(a.shape[0], 1)
		lower = numpy.tril_indices(a.shape[0], -1)
		return (a[upper].mean() + a[lower].mean())/2
	def _calc_corr(m):
		nonlocal h1
		j = (1-m)/nfact
		for i in range(nfact):
			h1[i,:] = h[i]*m + (h[:i].sum(0)+h[i+1:].sum(0))*j
		return _avg_off_diag(numpy.corrcoef(h1))
	_target_corr = lambda j: (_calc_corr(j)-corr)**2
	result = minimize_scalar(_target_corr, bounds=(0,1), method='Bounded')
	if inplace:
		if rows:
			h_full[rows,:] = h1[:]
		else:
			h[:] = h1[:]
	else:
		return h1

