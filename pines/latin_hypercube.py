
import numpy

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