import geopandas as gpd
import pandas
import numpy
import os
import matplotlib
import matplotlib.pyplot as plt
import seaborn as sns

local_palattes = {
	'radar': ['deep purple', 'deep green', 'green', 'green', 'yellow', 'orange',]
}



def color_palette_alpha(palatte='Reds', low_alpha=0.0, high_alpha=1.0):

	if palatte in local_palattes:
		return color_list_alpha(local_palattes[palatte], low_alpha=low_alpha, high_alpha=high_alpha, name=palatte)
	c = sns.color_palette(palatte)
	from matplotlib.colors import LinearSegmentedColormap
	return LinearSegmentedColormap.from_list(
		name=palatte+"_gen",
		colors=[
			(*i, j)
			for i,j in zip(
				c, numpy.linspace(low_alpha, high_alpha, len(c))
			)
		]
	)


def color_list_alpha(colorlist=(), low_alpha=0.0, high_alpha=1.0, name="_gen"):
	if colorlist==():
		colorlist = ['deep purple', 'deep green', 'green', 'green', 'yellow', 'orange',]
	c = [sns.colors.xkcd_rgb[i] for i in colorlist]
	from matplotlib.colors import LinearSegmentedColormap
	return LinearSegmentedColormap.from_list(
		name=name,
		colors=[
			(int(i[1:3],16)/256, int(i[3:5],16)/256, int(i[5:7],16)/256, j)
			for i,j in zip(
				c, numpy.linspace(low_alpha, high_alpha, len(c))
			)
		]
	)

local_cmaps = {
	k: color_list_alpha(local_palattes[k], 0.0,1.0,k)
	for k in local_palattes
}


from geopandas import read_file # convenience

class Map:
	def __init__(self,
				 center=(None,None), extent=(None,None),
				 xlim=None, ylim=None,
				 xticks=None, yticks=None,
				 title=None, bgcolor=None,
				 height=None, width=None,
				 frame=None):
		fig, ax = plt.subplots()
		ax.set_aspect('equal')

		if center[0] and extent[0]:
			ax.set_xlim(center[0]-extent[0], center[0]+extent[0])
		elif xlim is not None:
			ax.set_xlim(*xlim)

		if center[1] and extent[1]:
			ax.set_ylim(center[1]-extent[1], center[1]+extent[1])
		elif ylim is not None:
			ax.set_ylim(*ylim)

		if xticks is None or xticks is False:
			ax.set_xticks([])
		elif xticks is not True:
			ax.set_xticks(xticks)

		if yticks is None or yticks is False:
			ax.set_yticks([])
		elif yticks is not True:
			ax.set_yticks(yticks)

		if bgcolor is not None:
			fig.patch.set_facecolor(bgcolor)

		self.ax = ax
		self.fig = fig

		self.set_title(title)

		if height is not None:
			self.fig.set_figheight(height)
		if width is not None:
			self.fig.set_figwidth(width)

		if frame is not None:
			self.ax.set_frame_on(frame)

	def set_title(self, title):
		self._title = title
		if title is not None:
			self.ax.set_title(title)
		return self

	def __repr__(self):
		if self._title:
			return f"<pines.geoviz.Map: {self._title}>"
		else:
			return f"<pines.geoviz.Map: Untitled>"

	def get_png(self, *args, **kwargs):
		import io
		buf = io.BytesIO()
		kwargs.pop('format', None)
		bbox_inches = kwargs.pop('bbox_inches', 'tight')
		self.fig.savefig(buf, format='png', bbox_inches=bbox_inches, *args, **kwargs)
		return buf.getvalue()

	def choropleth(
			self,
			gdf:gpd.GeoDataFrame,
			column,
			cmap=None,
			legend=True,
			vmin=None,
			vmax=None,
			labels=None,
			colorbar_fraction = 0.046,
			colorbar_pad = 0.04,
			colorbar_shrink = 0.75,
			**kwargs,
	):
		if legend == 'manual':
			manual_legend = True
			legend = False
		else:
			manual_legend = False

		y = gdf.plot(
			ax=self.ax,
			column=column,
			cmap=cmap,
			legend=legend,
			vmin=vmin,
			vmax=vmax,
			**kwargs
		)

		if manual_legend:
			mn = gdf[column].min() if vmin is None else vmin
			mx = gdf[column].max() if vmax is None else vmax
			from matplotlib.colors import Normalize
			from matplotlib import cm
			norm = Normalize(vmin=mn, vmax=mx)
			n_cmap = cm.ScalarMappable(norm=norm, cmap=cmap)
			n_cmap.set_array([])
			self.fig.colorbar(n_cmap, fraction=colorbar_fraction, pad=colorbar_pad, shrink=colorbar_shrink)

		if labels is not None:
			from seaborn.utils import relative_luminance
			areacolors = y.collections[0].get_facecolors()
			label_col = labels.pop('column')
			formatter = labels.pop('formatter', lambda x: x)
			for r in range(len(gdf)):
				self.ax.annotate(
					s=str(formatter(gdf.iloc[r][label_col])),
					xy=gdf.iloc[r].geometry.representative_point().coords[0],
					ha='center', va='center', clip_on=True,
					color=".15" if relative_luminance(areacolors[r]) > .408 else "w",
					**labels
				)
		return self

	def invalid_area(self, gdf, color='#000000AA', **kwargs):
		gdf.plot(
			ax=self.ax,
			color=color,
			**kwargs
		)
		return self

	def borderlines(self, gdf, edgecolor="#000000FF", weight=1, **kwargs):
		gdf.plot(
			ax=self.ax,
			color="#FFFFFF00", # transparent fill color
			edgecolor=edgecolor,
			linewidth=weight,
			**kwargs
		)
		return self

	def labels(self, gdf, column, formatter=lambda x:x, **kwargs):
		if column not in gdf.columns:
			raise KeyError(f'column "{column}" not in gdf.columns')
		gdf.apply(
			lambda x: self.ax.annotate(
				s=str(formatter(x[column])), xy=x.geometry.centroid.coords[0],
				ha='center', va='center', clip_on=True,
				**kwargs
			),
			axis=1
		)
		return self

	def kdeplot(self, lat, lon, gridsize=100, bw=.01, legend=False, cmap=None, palatte="Reds", clist=None, **kwargs):

		if cmap is None:
			if clist is None:
				cmap = color_palette_alpha(palatte)
			else:
				cmap = color_list_alpha(clist)

		import seaborn as sns
		sns.kdeplot(
			lon,
			lat,
			clip=(
				self.ax.get_xlim(),
				self.ax.get_ylim(),
			),
			ax=self.ax,
			shade=True,
			gridsize=gridsize,
			bw=bw,
			shade_lowest=False,
			cmap=cmap,
			# LinearSegmentedColormap.from_list('name', [(1, 0, 0, 0), (1, 0, 0, 1/3), (1, 0, 0, 2/3), (0, 1, 0, 1)]),
			legend=legend,
			**kwargs
		)
		return self

	def wkdeplot(self, lat, lon, wgt, gridsize=100, bw=.01, legend=False, palatte="Reds", cmap=None, clist=None, **kwargs):

		from sklearn.neighbors import KernelDensity
		if cmap is None:
			if clist is None:
				cmap = color_palette_alpha(palatte)
			else:
				cmap = color_list_alpha(clist)


		Xtrain = numpy.vstack([
			lat,
			lon]
		).T

		X, Y = numpy.meshgrid(
			numpy.linspace(*self.ax.get_xlim(), gridsize),
			numpy.linspace(*self.ax.get_ylim(), gridsize),
		)
		xy = numpy.vstack([Y.ravel(), X.ravel()]).T

		kde = KernelDensity(bandwidth=bw,
							#metric='haversine',
							kernel='gaussian',
							algorithm='ball_tree')
		kde.fit(Xtrain, sample_weight=wgt)
		Z = kde.score_samples(xy)
		Z = Z.reshape(X.shape)
		levels = numpy.linspace(0, Z.max(), 25)

		if cmap is None:
			cmap= color_palette_alpha(palatte)

		self.ax.contourf(
			X, Y, Z,
			levels=levels,
			cmap=cmap,
		)
		return self

	def points(self, gdf, color='#BB0000', plotnumber=0, **kwargs):

		# if self.grid_width == 1 and self.grid_height == 1:
		# 	ax = self.axes
		# else:
		# 	ax = self.axes.ravel()[plotnumber]

		gdf.plot(
			ax=self.ax,
			color=color,
			**kwargs
		)

		return self


	def colored_points(self, gdf, column, cmap='vidiris', plotnumber=0, **kwargs):

		# if self.grid_width == 1 and self.grid_height == 1:
		# 	ax = self.axes
		# else:
		# 	ax = self.axes.ravel()[plotnumber]

		gdf.plot(
			ax=self.ax,
			column=column,
			cmap=cmap,
			**kwargs
		)

		return self





class MapMaker:
	def __init__(self, *args, **kwargs):
		self._args = args
		self._kwargs = kwargs

	def __call__(self, **kwargs):
		return Map(*self._args, **self._kwargs, **kwargs)




def reduce_coordinate_precision_of_shapefile(in_filename, *out_filename, **kwargs):
	from shapely.geometry import shape, mapping

	gdf = gpd.read_file(in_filename)

	for xx in gdf.index:
		geojson = mapping(gdf.geometry[xx])
		geojson['coordinates'] = numpy.round(numpy.array(geojson['coordinates']), 6)
		gdf.loc[xx, 'geometry'] = shape(geojson)

	gdf.to_file(*out_filename, **kwargs)


def get_distance_matrix(gdf, id_col, filename=None):
	if filename is not None and os.path.exists(filename):
		return pandas.read_pickle(filename)
	distance_matrix = pandas.DataFrame(
		data=0,
		index=gdf[id_col],
		columns=gdf[id_col],
		dtype=numpy.float64,
	)
	for i in range(len(gdf)):
		distance_matrix.values[:,i] = gdf.centroid.distance(gdf.centroid[i])
	distance_matrix = distance_matrix.sort_index(0).sort_index(1)
	if filename is not None and not os.path.exists(filename):
		os.makedirs(os.path.dirname(filename), exist_ok=True)
		distance_matrix.to_pickle(filename)
	return distance_matrix

