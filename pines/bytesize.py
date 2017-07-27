
def bytes_scaled(b):
	labels = ['B' ,'KB' ,'MB' ,'GB' ,'TB']
	scale = 0
	while scale < 4 and b > 1024:
		b /= 1024
		scale += 1
	return "{:.2f} {}".format(b ,labels[scale])
