import matplotlib.pyplot as plt
import numpy

def percentilize(x):
	return numpy.argsort(numpy.argsort(x)) / len(x) * 100.0

def homogeneous_size_bins(nbins, arr, robustness=0):
	"""
	Find bins with homogeneous size

	Parameters
	----------
	nbins : int
		number of bins to create
	arr : array-like
		the data to get binned
	robustness : int
		chop this many percentiles off the top and bottom of the range

	Returns
	-------
	ndarray
		the bin edges (length nbins+1)

	"""
	if robustness:
		bottom = numpy.nanpercentile(arr, robustness)
		top = numpy.nanpercentile(arr, 100-robustness)
	else:
		bottom = numpy.nanmin(arr)
		top = numpy.nanmax(arr)
	return numpy.linspace(bottom, top, nbins+1)

def homogeneous_mass_bins(nbins, arr, robustness=0):
	"""
	Find bins with homogeneous mass

	Parameters
	----------
	nbins : int
		number of bins to create
	arr : array-like
		the data to get binned
	robustness : int
		chop this many percentiles off the top and bottom of the range

	Returns
	-------
	ndarray
		the bin edges (length nbins+1)

	"""
	bottom = robustness
	top = 100-robustness
	return numpy.nanpercentile(arr, numpy.linspace(bottom, top, nbins+1))

def n_uniques(arr, stop_at=10):
	u = set()
	for i in arr:
		u.add(i)
		if len(u)>=stop_at:
			return stop_at, u
	return len(u), sorted(u)

def punique(arr, uniq):
	digitizer = list(uniq)
	digitizer.append(numpy.inf)
	bins = numpy.arange(len(uniq) + 1)
	ticks = bins[:-1] + 0.5, uniq
	a = numpy.digitize(arr, digitizer, right=False)
	return a, bins, ticks

def psize(arr, nbins, robustness=0):
	n_uniq, uniq = n_uniques(arr, nbins+1)
	if n_uniq <= nbins:
		return punique(arr, uniq)
	else:
		bins = homogeneous_size_bins(nbins, arr, robustness=robustness)
		a = numpy.digitize(arr, bins, right=True)
		ticks = None
	return a, bins, ticks

def pmass(arr, nbins, robustness=0):
	n_uniq, uniq = n_uniques(arr, nbins+1)
	if n_uniq <= nbins:
		return punique(arr, uniq)
	else:
		bins = homogeneous_mass_bins(nbins, arr, robustness=robustness)
		a = numpy.digitize(arr, bins, right=True)
		ticks = None
	return a, bins, ticks

def pmass_even(arr, nbins, robustness=0):
	a, _, ticks = pmass(arr, nbins, robustness)
	bins = numpy.linspace(robustness, 100-robustness, nbins+1)
	return a, bins, ticks

def _generate_heatmap(
		x_digitized,
		x_bins,
		x_ticks,
		y_digitized,
		y_bins,
		y_ticks,
		normalize_dim='',
		cmap='jet',
		z_robustness=2,
		z_min=None,
		z_max=None,
		clf=True,
		subplot=(1,1,1),
		x_label=None,
		y_label=None,
		title=None,
		**kwargs
):
	bins = (numpy.arange(1,len(x_bins)+1)-0.5, numpy.arange(1,len(y_bins)+1)-0.5)

	# print("bins", bins)
	# print("x_bins", x_bins)
	# print("y_bins", y_bins)
	# print("x_", numpy.unique(x_digitized, return_counts=True))
	# print("y_", numpy.unique(y_digitized, return_counts=True))

	h,h1,h2 = numpy.histogram2d(
		x_digitized, y_digitized,
		bins=bins,
	)

	if normalize_dim.lower()=='y':
		h /= h.sum(0)[None,:]
	elif normalize_dim.lower()=='x':
		h /= h.sum(1)[:,None]

	if z_min is None:
		z_min = numpy.percentile(h,z_robustness)
	if z_max is None:
		z_max = numpy.percentile(h,100-z_robustness)

	if clf:
		plt.clf()
	ax = plt.subplot(*subplot)

	heatmap_ = numpy.zeros([h.shape[0]+1, h.shape[1]+1], dtype=h.dtype)
	heatmap_[:-1,:-1] = h

	quads = ax.pcolormesh(x_bins, y_bins, heatmap_.T, cmap=cmap, vmin=z_min, vmax=z_max, **kwargs)

	cbar = plt.colorbar(quads, ax=ax)
	if x_label:
		plt.xlabel(f'{x_label}')
	if y_label:
		plt.ylabel(f'{y_label}')
	if title:
		plt.title(title)
	if x_ticks:
		plt.xticks(*x_ticks, rotation='vertical')
	if y_ticks:
		plt.yticks(*y_ticks)


def heatmap_dataframe(
		x_digitized,
		x_bins,
		x_ticks,
		y_digitized,
		y_bins,
		y_ticks,
		normalize_dim='',
		tick_fmt='.2f',
		**kwargs
):
	bins = (numpy.arange(1,len(x_bins)+1)-0.5, numpy.arange(1,len(y_bins)+1)-0.5)

	# print("bins", bins)
	# print("x_bins", x_bins)
	# print("y_bins", y_bins)
	# print("x_", numpy.unique(x_digitized, return_counts=True))
	# print("y_", numpy.unique(y_digitized, return_counts=True))

	h,h1,h2 = numpy.histogram2d(
		x_digitized, y_digitized,
		bins=bins,
	)

	if normalize_dim.lower()=='y':
		h /= h.sum(0)[None,:]
	elif normalize_dim.lower()=='x':
		h /= h.sum(1)[:,None]

	if x_ticks is not None:
		cols = x_ticks[1]
	else:
		cols = [f"{i:{tick_fmt}} to {j:{tick_fmt}}" for i,j in zip(x_bins[:-1],x_bins[1:])]
	if y_ticks is not None:
		rows = y_ticks[1]
	else:
		rows = [f"{i:{tick_fmt}} to {j:{tick_fmt}}" for i,j in zip(y_bins[:-1],y_bins[1:])]

	import pandas
	return pandas.DataFrame(
		data=h.T,
		columns=cols,
		index=rows,
	).iloc[::-1]

def heatmapper( x, y, x_robustness=0, y_robustness=0, **kwargs ):
	"""
	Create a heatmap

	Parameters
	----------
	x, y : array or tuple
		Either an array or a tuple generated from psize, pmass, or pmass_even
	x_robustness, y_robustness : numeric
		if x or y is an array, use this robustness value to trim the extremes
	kwargs
		passed to _generate_heatmap

	"""
	if isinstance(x, numpy.ndarray):
		x = psize(x,10,x_robustness)
	if isinstance(y, numpy.ndarray):
		y = psize(y,10,y_robustness)
	return _generate_heatmap( *x, *y, **kwargs)

def heatmap_sns(x, y, x_robustness=0, y_robustness=0, max_dim=20, **kwargs):
	"""
	Create a heatmap using seaborn

	Parameters
	----------
	x, y : array or tuple
		Either an array or a tuple generated from psize, pmass, or pmass_even
	x_robustness, y_robustness : numeric
		if x or y is an array, use this robustness value to trim the extremes
	kwargs
		passed to _generate_heatmap

	"""
	if isinstance(x, numpy.ndarray):
		x = psize(x,max_dim,x_robustness)
	if isinstance(y, numpy.ndarray):
		y = psize(y,max_dim,y_robustness)
	frame = heatmap_dataframe( *x, *y )
	import seaborn
	return seaborn.heatmap(frame, **kwargs)








def heatmap(x,y, xlabel=None, ylabel=None, title=None, bins=(100,100),
			pctile=(True, False), rpctile=(False,False), cmap='jet', # 'viridis',
			robustness=2, trim_y=1, docx_writer=None,
			zmin=None, zmax=None,
			y_normalize=True, **kwargs):
	"""Plot a heatmap figure

	Parameters
	----------
	x
	y
	xlabel, ylabel : str, optional
		Axis labels
	title : str, optional
		Figure title
	bins
	pctile
	rpctile : 2-tuple
		For (x,y), should the values be rescaled into percentiles instead of the original values.
		This will cause the output to be plotted on a 0-100 scale instead of the original scale
		of the given values.
	cmap : str
		Name of a colormap to pass to `pcolormesh`
	robustness : numeric
		Amount to trim from the z-scale range, in percentile amounts
	trim_y : numeric
		Amount to trim from the y axis range, in percentile amounts
	docx_writer
	zmin
	zmax
	y_normalize
	kwargs

	Returns
	-------

	"""


	plt.clf()
	# ax = plt.subplot(2,1,1)
	ax = plt.subplot(1,1,1)
	if rpctile[0] or pctile[0]:
		binsX = numpy.percentile(x, numpy.linspace(0,100,bins[0]))
		for i in range(1,len(binsX)):
			if binsX[i] <= binsX[i-1]:
				binsX[i] = binsX[i - 1] + numpy.abs(binsX[i - 1])*1e-4 + 1e-7
	else:
		binsX = bins[0]
	if rpctile[0]:
		x = numpy.argsort(numpy.argsort(x)) / len(x) * 100.0
		binsX_ = numpy.linspace(0,100,bins[0])
	else:
		binsX_ = binsX

	if isinstance(binsX_, int):
		binsX_ = numpy.linspace(numpy.nanmin(x), numpy.nanmax(x), binsX_)

	if pctile[1] or pctile[1]:
		binsY = numpy.percentile(y, numpy.linspace(0,100,bins[1]))
		for i in range(1,len(binsY)):
			if binsY[i] <= binsY[i-1]:
				binsY[i] = binsY[i - 1] + numpy.abs(binsY[i - 1])*1e-4 + 1e-7
	else:
		binsY = bins[1]
	if rpctile[1]:
		y = numpy.argsort(numpy.argsort(y)) / len(y) * 100.0
		binsY_ = numpy.linspace(0,100,bins[1])
		trim_y = 0
	else:
		binsY_ = binsY

	if isinstance(binsY_, int):
		binsY_ = numpy.linspace(numpy.nanmin(y), numpy.nanmax(y), binsY_)

	try:
		heatmap, yedges, xedges = numpy.histogram2d(y, x, bins=(binsY_,binsX_))
	except ValueError:
		print('binsY')
		print(binsY)
		print('binsX')
		print(binsX)
		raise

	if y_normalize:
		heatmap /= heatmap.sum(0)[None,:]

	if zmin is None:
		zmin = numpy.percentile(heatmap,robustness)
	if zmax is None:
		zmax = numpy.percentile(heatmap,100-robustness)

	heatmap_ = numpy.zeros([heatmap.shape[0]+1, heatmap.shape[1]+1], dtype=heatmap.dtype)
	heatmap_[:-1,:-1] = heatmap
	try:
		quads = ax.pcolormesh(binsX_, binsY_, heatmap_, cmap=cmap, vmin=zmin, vmax=zmax, **kwargs)
	except:
		print(binsX_)
		print(binsY_)
		print(heatmap_)
		raise

	ymin, ymax = numpy.percentile(y, [trim_y, 100-trim_y])

	ax.set_ylim(ymin, ymax)
	cbar = plt.colorbar(quads, ax=ax)
	if xlabel:
		if rpctile[0]:
			plt.xlabel(f'Percentile {xlabel}')
		else:
			plt.xlabel(f'{xlabel}')
	if ylabel:
		if rpctile[1]:
			plt.ylabel(f'Percentile {ylabel}')
		else:
			plt.xlabel(f'{ylabel}')
	if title:
		plt.title(title)

	if docx_writer is not None:
		docx_writer.write_plt()
	plt.show()
