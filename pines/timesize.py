def timesize(t):
	if t<60:
		return f"{t:.2f}s"
	elif t<3600:
		return f"{t/60:.2f}m"
	elif t<86400:
		return f"{t/3600:.2f}h"
	else:
		return f"{t/86400:.2f}d"
