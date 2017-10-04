import matplotlib.pyplot as plt
import numpy

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
	quads = ax.pcolormesh(binsX_, binsY_, heatmap_, cmap=cmap, vmin=zmin, vmax=zmax, **kwargs)

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
