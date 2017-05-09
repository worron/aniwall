from gi.repository import Gtk, GdkPixbuf


def hex_from_rgba(rgba):
	"""Translate color from Gdk.RGBA to html hex format"""
	return "#%02X%02X%02X" % tuple([int(getattr(rgba, name) * 255) for name in ("red", "green", "blue")])


def pixbuf_from_hex(value, width=128, height=16):
	"""Create GDK pixbuf from color"""
	pixbuf = GdkPixbuf.Pixbuf.new(GdkPixbuf.Colorspace.RGB, False, 8, width, height)
	pixbuf.fill(int(value[1:] + "FF", 16))
	return pixbuf


class GuiBase:
	"""Base for Gtk widget set created with builder"""
	def __init__(self, *files, elements=(), path=None):
		self.resource_path = path
		self.builder = Gtk.Builder()
		for file_ in files:
			self.builder.add_from_resource(self.resource_path + file_)
		self.gui = {element: self.builder.get_object(element) for element in elements}


class AttributeDict(dict):
	"""Dictionary with keys as attributes. Does nothing but easy reading"""
	def __getattr__(self, attr):
		return self[attr]

	def __setattr__(self, attr, value):
		self[attr] = value


class TreeViewData:
	"""Gtk treeview data handler"""
	def __init__(self, data):
		self.column = AttributeDict()
		self.visible = []
		self.types = []
		self.titles = []
		self.visible = []
		self.maintain = []

		for i, item in enumerate(data):
			self.column[item["literal"]] = i
			self.types.append(item["type"])
			self.titles.append(item["title"])
			self.visible.append(item["visible"])
			if "maintain" in item and item["maintain"]:
				self.maintain.append(i)
