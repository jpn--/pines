import os
import xml.etree.ElementTree
from xml.etree.ElementTree import Element, SubElement, TreeBuilder
from contextlib import contextmanager
from .uid import uid as _uid
import base64
from . import styles

xml.etree.ElementTree.register_namespace("", "http://www.w3.org/2000/svg")
xml.etree.ElementTree.register_namespace("xlink", "http://www.w3.org/1999/xlink")

# @import url(https://fonts.googleapis.com/css?family=Roboto+Mono:400,700,700italic,400italic,100,100italic);






_default_css = """

@import url(https://fonts.googleapis.com/css?family=Roboto:400,700,500italic,100italic|Roboto+Mono:300,400,700);

.error_report {color:red; font-family:monospace;}

body {""" + styles.body_font + """}

table {border-collapse:collapse;}

table, th, td {
	border: 1px solid #999999;
	font-family:"Roboto Mono", monospace;
	font-size:90%;
	font-weight:400;
	}

th, td { padding:2px; }

td.parameter_category {
	font-family:"Roboto", monospace;
	font-weight:500;
	background-color: #f4f4f4; 
	font-style: italic;
	}

th {
	font-family:"Roboto", monospace;
	font-weight:700;
	}

.larch_signature {""" + styles.signature_font + """}
.larch_name_signature {""" + styles.signature_name_font + """}

a.parameter_reference {font-style: italic; text-decoration: none}

.strut2 {min-width:1in}

.histogram_cell { padding-top:1; padding-bottom:1; vertical-align:center; }

.raw_log pre {
	font-family:"Roboto Mono", monospace;
	font-weight:300;
	font-size:70%;
	}

caption {
    caption-side: bottom;
	text-align: left;
	font-family: Roboto;
	font-style: italic;
	font-weight: 100;
	font-size: 80%;
}

table.dictionary { border:0px hidden !important; border-collapse: collapse !important; }
div.blurb {
	margin-top: 15px;
	max-width: 6.5in;
}

div.note {
	font-size:90%;
	padding-left:1em;
	padding-right:1em;
	border: 1px solid #999999;
	border-radius: 4px;
}

p.admonition-title {
	font-weight: 700;
}

"""


class Elem(Element):
	"""Extends :class:`xml.etree.ElementTree.Element`"""

	def __init__(self, tag, attrib=None, text=None, tail=None, **extra):
		if attrib is None:
			attrib = {}
		if isinstance(text, Element):
			Element.__init__(self, tag, attrib, **extra)
			for k, v in text.attrib.items():
				if k not in attrib and k not in extra:
					self.set(k, v)
			self.text = text.text
			if tail:
				self.tail = text.tail + tail
			else:
				self.tail = text.tail
		else:
			Element.__init__(self, tag, attrib, **extra)
			if text: self.text = str(text)
			if tail: self.tail = str(tail)

	def put(self, tag, attrib=None, text=None, tail=None, **extra):
		if attrib is None:
			attrib = {}
		attrib = attrib.copy()
		attrib.update(extra)
		element = Elem(tag, attrib)
		if text: element.text = str(text)
		if tail: element.tail = str(tail)
		self.append(element)
		return element

	def __call__(self, *arg, **attrib):
		for a in arg:
			if isinstance(a, dict):
				for key, value in a.items():
					self.set(str(key), str(value))
			if isinstance(a, str):
				if self.text is None:
					self.text = a
				else:
					self.text += a
		for key, value in attrib.items():
			self.set(str(key), str(value))
		return self

	def append(self, arg):
		try:
			super().append(arg)
		except TypeError:
			if callable(arg):
				super().append(arg())
			else:
				raise

	def __lshift__(self, other):
		if other is not None:
			self.append(other)
		return self

	def tobytes(self):
		return xml.etree.ElementTree.tostring(self, encoding="utf8", method="html")

	def tostring(self):
		return self.tobytes().decode()

	def _repr_html_(self):
		return self.tostring().decode()

	def pprint(self, indent=0, hush=False):
		dent = "  " * indent
		if hush and self.tag in ('div', 'tfoot', 'a') and not self.text and len(self) == 0:
			if self.tail:
				return dent + self.tail
			else:
				return ""
		s = "{}<{}>".format(dent, self.tag)
		if self.text:
			s += self.text
		any_subs = False
		for i in self():
			if isinstance(i, Elem):
				sub = i.pprint(indent=indent + 1, hush=True)
				if sub:
					s += "\n{}".format(sub)
					any_subs = True
			else:
				s += "\n{}{}".format(dent, i)
				any_subs = True
		if any_subs:
			s += "\n{}".format(dent)
		s += "</{}>".format(self.tag)
		if self.tail:
			s += self.tail
		return s

	def __repr__(self):
		return "<larch.util.xhtml.Elem '{}' at {}>".format(self.tag, hex(id(self)))  # +self.pprint()

	def save(self, filename, overwrite=True):
		if os.path.exists(filename) and not overwrite:
			raise IOError("file {0} already exists".format(filename))
		with _XHTML(filename, overwrite=overwrite, view_on_exit=False) as f:
			f << self

	def anchor(self, ref, reftxt, cls, toclevel):
		self.put("a", {'name': ref, 'reftxt': reftxt, 'class': cls, 'toclevel': toclevel})

	def hn(self, n, content, attrib=None, anchor=None, **extra):
		if attrib is None:
			attrib = {}
		if anchor:
			h_elem = self.put("h{}".format(n), attrib, **extra)
			h_elem.put("a", {'name': _uid(), 'reftxt': anchor if isinstance(anchor, str) else content, 'class': 'toc',
			                 'toclevel': '{}'.format(n)}, tail=content)
		else:
			self.put("h{}".format(n), attrib, text=content, **extra)


class _XHTML():
	"""A class used to conveniently build xhtml documents."""

	def __init__(self, filename=None, *, overwrite=False, spool=True, quickhead=None, css=None, extra_css=None,
	             view_on_exit=True, jquery=True, jqueryui=True, floating_tablehead=True, embed_model=None, toc=True):
		self.view_on_exit = view_on_exit
		self.root = Elem(tag="html", xmlns="http://www.w3.org/1999/xhtml")
		self.head = Elem(tag="head")
		self.body = Elem(tag="body")
		self.root << self.head
		self.root << self.body
		if filename is None or filename is False:
			import io
			filemaker = lambda: io.BytesIO()
		elif filename.lower() == "temp":
			from .temporary import TemporaryHtml
			filemaker = lambda: TemporaryHtml(nohead=True)
		else:
			if os.path.exists(filename) and not overwrite and not spool:
				raise IOError("file {0} already exists".format(filename))
			if os.path.exists(filename) and not overwrite and spool:
				from .file_util import next_filename
				filename = next_filename(filename)
			filename, filename_ext = os.path.splitext(filename)
			if filename_ext == "":
				filename_ext = ".html"
			filename = filename + filename_ext
			filemaker = lambda: open(filename, 'wb')
		self._filename = filename
		self._f = filemaker()
		self.title = Elem(tag="title")
		self.style = Elem(tag="style")
		from .img import favicon
		self.favicon = Elem(tag="link",
		                    attrib={'href': "data:image/png;base64,{}".format(favicon), 'rel': "shortcut icon",
		                            'type': "image/png"})

		if jquery:
			self.jquery = Elem(tag="script", attrib={
				'src': "https://code.jquery.com/jquery-3.0.0.min.js",
				'integrity': "sha256-JmvOoLtYsmqlsWxa7mDSLMwa6dZ9rrIdtrrVYRnDRH0=",
				'crossorigin': "anonymous",
			})
			self.head << self.jquery

		if jqueryui:
			self.jqueryui = Elem(tag="script", attrib={
				'src': "https://code.jquery.com/ui/1.11.4/jquery-ui.min.js",
				'integrity': "sha256-xNjb53/rY+WmG+4L6tTl9m6PpqknWZvRt0rO1SRnJzw=",
				'crossorigin': "anonymous",
			})
			self.head << self.jqueryui

		if floating_tablehead:
			self.floatThead = Elem(tag="script", attrib={
				'src': "https://cdnjs.cloudflare.com/ajax/libs/floatthead/1.4.0/jquery.floatThead.min.js",
			})
			self.floatTheadA = Elem(tag="script")
			self.floatTheadA.text = """
			$( document ).ready(function() {
				var $table = $('table.floatinghead');
				$table.floatThead({ position: 'absolute' });
				var $tabledf = $('table.dataframe');
				$tabledf.floatThead({ position: 'absolute' });
			});
			$(window).on("hashchange", function () {
				window.scrollTo(window.scrollX, window.scrollY - 50);
			});
			"""
			self.head << self.floatThead
			self.head << self.floatTheadA

		self.head << self.favicon
		self.head << self.title
		self.head << self.style

		self.toc_color = 'lime'

		if toc:
			self.with_toc = True
			toc_width = 200
			default_css = _default_css + """

			body { margin-left: """ + str(toc_width) + """px; }
			.table_of_contents_frame { width: """ + str(
				toc_width - 13) + """px; position: fixed; margin-left: -""" + str(toc_width) + """px; top:0; padding-top:10px; z-index:2000;}
			.table_of_contents { width: """ + str(toc_width - 13) + """px; position: fixed; margin-left: -""" + str(
				toc_width) + """px; font-size:85%;}
			.table_of_contents_head { font-weight:700; padding-left:25px;  }
			.table_of_contents ul { padding-left:25px;  }
			.table_of_contents ul ul { font-size:75%; padding-left:15px; }
			.larch_signature {""" + styles.signature_font + """ width: """ + str(toc_width - 30) + """px; position: fixed; left: 0px; bottom: 0px; padding-left:20px; padding-bottom:2px; background-color:rgba(255,255,255,0.9);}
			.larch_name_signature {""" + styles.signature_name_font + """}
			a.parameter_reference {font-style: italic; text-decoration: none}
			.strut2 {min-width:2in}
			.histogram_cell { padding-top:1; padding-bottom:1; vertical-align:center; }
			table.floatinghead thead {background-color:#FFF;}
			table.dataframe thead {background-color:#FFF;}
			@media print {
			   body { color: #000; background: #fff; width: 100%; margin: 0; padding: 0;}
			   /*.table_of_contents { display: none; }*/
			   @page {
				  margin: 1in;
			   }
			   h1, h2, h3 { page-break-after: avoid; }
			   img { max-width: 100% !important; }
			   ul, img, table { page-break-inside: avoid; }
			   .larch_signature {""" + styles.signature_font + """ padding:0; background-color:#fff; position: fixed; bottom: 0;}
			   .larch_name_signature {""" + styles.signature_name_font + """}
			   .larch_signature img {display:none;}
			   .larch_signature .noprint {display:none;}
			}
			"""
		else:
			self.with_toc = False
			default_css = _default_css + """

		   .larch_signature {""" + styles.signature_font + """ padding:0; background-color:#fff; }
			.larch_name_signature {""" + styles.signature_name_font + """}
			a.parameter_reference {font-style: italic; text-decoration: none}
			.strut2 {min-width:2in}
			.histogram_cell { padding-top:1; padding-bottom:1; vertical-align:center; }
			table.floatinghead thead {background-color:#FFF;}
			table.dataframe thead {background-color:#FFF;}
			@media print {
			   body { color: #000; background: #fff; width: 100%; margin: 0; padding: 0;}
			   /*.table_of_contents { display: none; }*/
			   @page {
				  margin: 1in;
			   }
			   h1, h2, h3 { page-break-after: avoid; }
			   img { max-width: 100% !important; }
			   ul, img, table { page-break-inside: avoid; }
			   .larch_signature {""" + styles.signature_font + """ padding:0; background-color:#fff; position: fixed; bottom: 0;}
			   .larch_name_signature {""" + styles.signature_name_font + """}
			   .larch_signature img {display:none;}
			   .larch_signature .noprint {display:none;}
			}
			"""

		css = styles.load_css(css)

		if quickhead is not None:
			try:
				title = quickhead.title
			except AttributeError:
				title = "Untitled"
			if title != '': self.title.text = str(title)
			if css is None:
				css = default_css
			if extra_css is not None:
				css += extra_css
			try:
				css += quickhead.css
			except AttributeError:
				pass
			self.style.text = css.replace('\n', ' ').replace('\t', ' ')
		else:
			if css is None:
				css = default_css
			if extra_css is not None:
				css += extra_css
			self.style.text = css.replace('\n', ' ').replace('\t', ' ')
		if embed_model is not None:
			self.head << Elem(tag="meta", name='pymodel',
			                  content=base64.standard_b64encode(embed_model.__getstate__()).decode('ascii'))

	def __enter__(self):
		return self

	def __exit__(self, type, value, traceback):
		if type or value or traceback:
			# traceback.print_exception(type, value, traceback)
			return False
		else:
			self.dump(toc=self.with_toc)
			if self.view_on_exit:
				self.view()
			self._f.close()
			if self.view_on_exit and self._filename is not None and self._filename.lower() != 'temp':
				# import webbrowser
				# webbrowser.open('f ile://'+os.path.realpath(self._filename))
				from .temporary import _open_in_chrome_or_something
				_open_in_chrome_or_something('file://' + os.path.realpath(self._filename))

	def toc(self, insert=False):
		xtoc = Elem("div", {'class': 'table_of_contents'})
		from .img import local_logo
		logo = local_logo()
		if logo is not None:
			if isinstance(logo, bytes):
				logo = logo.decode()
			xtoc << Elem('img', attrib={'width': '150', 'src': "data:image/png;base64,{}".format(logo),
			                          'style': 'display: block; margin-left: auto; margin-right: auto'})
		xtoc << Elem('p', text="Table of Contents", attrib={'class': 'table_of_contents_head'})
		toclvl = 0
		xtoc_tree = []
		for anchor in self.root.findall('.//a[@toclevel]'):
			anchor_ref = anchor.get('name')
			anchor_text = anchor.get('reftxt')
			anchor_lvl = int(anchor.get('toclevel'))
			if anchor_lvl > toclvl:
				xtoc_tree.append(xtoc)
				xtoc = Elem('ul')
				toclvl = anchor_lvl
			while anchor_lvl < toclvl:
				xtoc_tree[-1] << xtoc
				xtoc = xtoc_tree[-1]
				toclvl -= 1
			xtoc << (Elem('li') << Elem('a', text=anchor_text, attrib={'href': '#{}'.format(anchor_ref)}))
		if insert:
			self.body.insert(0, xtoc)
		return xtoc

	def toc_iframe(self, insert=False):
		css = """
		.table_of_contents { font-size:85%; """ + styles.body_font + """ }
		.table_of_contents a:link { text-decoration: none; }
		.table_of_contents a:visited { text-decoration: none; }
		.table_of_contents a:hover { text-decoration: underline; }
		.table_of_contents a:active { text-decoration: underline; }
		.table_of_contents_head { font-weight:700; padding-left:20px }
		.table_of_contents ul { padding-left:20px; }
		.table_of_contents ul ul { font-size:75%; padding-left:15px; }
		::-webkit-scrollbar {
			-webkit-appearance: none;
			width: 7px;
		}
		::-webkit-scrollbar-thumb {
			border-radius: 4px;
			background-color: rgba(0,0,0,.5);
			-webkit-box-shadow: 0 0 1px rgba(255,255,255,.5);
		"""
		xtoc_html = _XHTML(css=css)
		xtoc_html.head << Elem(tag='base', target="_parent")
		xtoc_html.body << self.toc()

		BLAH = xml.etree.ElementTree.tostring(xtoc_html.root, method="html", encoding="unicode")

		from .colors import strcolor_rgb256
		toc_elem = Elem(tag='iframe', attrib={
			'class': 'table_of_contents_frame',
			'style': '''height:calc(100% - 100px); border:none; /*background-color:rgba(128,189,1, 0.95);*/
			  background: -webkit-linear-gradient(rgba({0}, 0.95), rgba(255, 255, 255, 0.95)); /* For Safari 5.1 to 6.0 */
			  background: -o-linear-gradient(rgba({0}, 0.95), rgba(255, 255, 255, 0.95)); /* For Opera 11.1 to 12.0 */
			  background: -moz-linear-gradient(rgba({0}, 0.95), rgba(255, 255, 255, 0.95)); /* For Firefox 3.6 to 15 */
			  background: linear-gradient(rgba({0}, 0.95), rgba(255, 255, 255, 0.95)); /* Standard syntax */
			'''.format(strcolor_rgb256(self.toc_color)),
			'srcdoc': BLAH,
		})

		if insert:
			self.body.insert(0, toc_elem)
		return toc_elem

	def sign(self, insert=False):
		xsign = Elem("div", {'class': 'larch_signature'})
		from . import __version__
		from .img import favicon
		import time

		p = Elem('p')
		p << Elem('img', {'width': "14", 'height': "14", 'src': "data:image/png;base64,{}".format(favicon),
		                    'style': 'position:relative;top:2px;'})
		p << Elem('span', attrib={'class': 'larch_name_signature'}, text=" Pines {}".format(__version__))
		p << Elem('br', tail="Report generated on ")
		p << Elem('br', attrib={'class': 'noprint'}, tail=time.strftime("%A %d %B %Y "))
		p << Elem('br', attrib={'class': 'noprint'}, tail=time.strftime("%I:%M:%S %p"))
		xsign << p
		if insert:
			self.body.append(xsign)
		return xsign

	def finalize(self, toc=True, sign=True):
		if sign:
			self.sign(True)
		if toc:
			self.toc_iframe(True)

		c = self.root.copy()

		if sign:
			s = self.root.find(".//div[@class='larch_signature']/..")
			if s is not None:
				s.remove(s.find(".//div[@class='larch_signature']"))
		if toc:
			s = self.root.find(".//div[@class='table_of_contents']/..")
			if s is not None:
				s.remove(s.find(".//div[@class='table_of_contents']"))
		return c

	def dump(self, toc=True, sign=True):
		if sign:
			self.sign(True)
		if toc:
			self.toc_iframe(True)
		self._f.write(
			b'<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">')
		xml.etree.ElementTree.ElementTree(self.root).write(self._f, xml_declaration=False, method="html")
		self._f.flush()
		if sign:
			s = self.root.find(".//div[@class='larch_signature']/..")
			if s is not None:
				s.remove(s.find(".//div[@class='larch_signature']"))
		if toc:
			s = self.root.find(".//div[@class='table_of_contents']/..")
			if s is not None:
				s.remove(s.find(".//div[@class='table_of_contents']"))
		try:
			return self._f.getvalue()  # for BytesIO
		except AttributeError:
			return

	def dump_seg(self):
		xml.etree.ElementTree.ElementTree(self.root).write(self._f, xml_declaration=False, method="html")
		self._f.flush()
		try:
			return self._f.getvalue()  # for BytesIO
		except AttributeError:
			return

	def view(self):
		try:
			self._f.view()
		except AttributeError:
			pass

	def append(self, node):
		if isinstance(node, Element):
			self.body.append(node)
		elif hasattr(node, '__xml__'):
			self.body.append(node.__xml__())
		elif node is None:
			pass
		else:
			raise TypeError(
				"must be xml.etree.ElementTree.Element or XML_Builder or TreeBuilder or something with __xml__ defined, not {!s}".format(
					type(node)))

	def __lshift__(self, other):
		self.append(other)
		return self

	def anchor(self, ref, reftxt, cls, toclevel):
		self.append(Elem(tag="a", attrib={'name': ref, 'reftxt': reftxt, 'class': cls, 'toclevel': toclevel}))

	def hn(self, n, content, attrib=None, anchor=None):
		if attrib is None:
			attrib = {}
		if anchor:
			h_elem = Elem(tag="h{}".format(n), attrib=attrib)
			h_elem.put("a", {'name': _uid(), 'reftxt': anchor if isinstance(anchor, str) else content, 'class': 'toc',
			                 'toclevel': '{}'.format(n)}, tail=content)
		else:
			h_elem = Elem(tag="h{}".format(n), attrib=attrib, text=content)
		self.append(h_elem)
