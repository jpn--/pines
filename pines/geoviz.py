import geopandas as gpd
import pandas
import numpy
import matplotlib
import matplotlib.pyplot as plt

from geopandas import read_file # convenience

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


	def set_title(self, title):
		self._title = title
		if title is not None:
			self.ax.set_title(title)

	def __repr__(self):
		if self._title:
			return f"<pines.geoviz.Map: {self._title}>"
		else:
			return f"<pines.geoviz.Map: Untitled>"

	def choropleth(self, gdf, column, cmap=None, legend=True, vmin=None, vmax=None, labels=None, **kwargs):
		y = gdf.plot(
			ax=self.ax,
			column=column,
			cmap=cmap,
			legend=legend,
			vmin=vmin,
			vmax=vmax,
			**kwargs
		)
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


class MapMaker:
	def __init__(self, *args, **kwargs):
		self._args = args
		self._kwargs = kwargs

	def __call__(self, **kwargs):
		return Map(*self._args, **self._kwargs, **kwargs)

