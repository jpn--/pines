
import numpy, pandas

def uniques(input, counts=True):
	len_action = len(input)
	try:
		input = input[~numpy.isnan(input)]
	except TypeError:
		num_nan = 0
	else:
		num_nan = len_action - len(input)
	if counts:
		x = numpy.unique(input, return_counts=counts)
		y = pandas.Series(x[1], x[0])
		if num_nan:
			y[numpy.nan] = num_nan
		return y
	if num_nan:
		numpy.append(input, numpy.nan)
	return numpy.unique(input)