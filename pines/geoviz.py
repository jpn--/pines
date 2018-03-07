import geopandas as gpd
import pandas
import numpy
import matplotlib
import matplotlib.pyplot as plt

class Map:
	def __init__(self,
				 center=(None,None), extent=(None,None),
				 xlim=None, ylim=None,
				 xticks=None, yticks=None,
				 title=None, bgcolor=None):
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

		ax.set_xticks([] if xticks is None else xticks)
		ax.set_yticks([] if yticks is None else yticks)

		if title is not None:
			ax.set_title(title)
		if bgcolor is not None:
			fig.patch.set_facecolor(bgcolor)

		self.ax = ax
		self.fig = fig

	def choropleth(self, gdf, column, cmap=None, legend=True, vmin=None, vmax=None):
		gdf.plot(
			ax=self.ax,
			column=column,
			cmap=cmap,
			legend=legend,
			vmin=vmin,
			vmax=vmax,
		)

	def invalid_area(self, gdf, color='#000000AA'):
		gdf.plot(
			ax=self.ax,
			color=color,
		)

	def borderlines(self, gdf, edgecolor="#000000FF", weight=1):
		gdf.plot(
			ax=self.ax,
			color="#FFFFFF00", # transparent fill color
			edgecolor=edgecolor,
			linewidth=weight,
		)

	def labels(self, gdf, column, **kwargs):
		if column not in gdf.columns:
			raise KeyError(f'column "{column}" not in gdf.columns')
		gdf.apply(
			lambda x: self.ax.annotate(
				s=str(x[column]), xy=x.geometry.centroid.coords[0],
				ha='center', va='center', clip_on=True,
				**kwargs
			),
			axis=1
		)



#
# def map_showing(
# 		column,
# 		title=None,
# 		invalid=None,
# 		vmin=None,
# 		vmax=None,
# 		invalid_color='#000000AA',
# 		gdf=None,
# 		cmap='OrRd',
# 		gdf_labels=None,
# 		gdf_label_col=None,
# 		gdf_heavy=None
# ):
# 	if gdf is None:
# 		gdf = geo
# 	j = 5000
# 	k = 20000
# 	fig, ax = plt.subplots()
# 	ax.set_aspect('equal')
# 	ax.set_xlim(435000+j,530000-j)
# 	ax.set_ylim(4935000+k,5025000-k)
# 	ax.set_xticks([])
# 	ax.set_yticks([])
# 	gdf.plot(ax=ax, column=column, cmap=cmap, legend=True, vmin=vmin, vmax=vmax)
# 	if invalid:
# 		blackout = matplotlib.colors.LinearSegmentedColormap.from_list('BlackOut', ['#00000000',invalid_color,])
# 		gdf.plot(ax=ax, column=invalid, cmap=blackout)
# 	districts.plot(ax=ax, color="#FFFFFF00", edgecolor="#00000044")
# 	if title is not None:
# 		ax.set_title(title)
# 	if gdf_labels is not None:
# 		gdf_labels.apply(
# 			lambda x: ax.annotate(s=str(x[gdf_label_col]),
# 								  xy=x.geometry.centroid.coords[0],
# 								  ha='center', clip_on=True),
# 			axis=1
# 		)
# 	if gdf_heavy is not None:
# 		gdf_heavy.plot(ax=ax, color="#FFFFFF00", edgecolor="#000000FF", linewidth=2)
# 	fig.patch.set_facecolor('white')
