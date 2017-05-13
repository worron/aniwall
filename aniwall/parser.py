import os
import re
import tempfile
import shutil

from configparser import ConfigParser
from itertools import count
from lxml import etree
from gi.repository import GdkPixbuf
from aniwall.logger import logger, debuginfo


class ImageData:
	"""Structure to store image parameters"""
	def __init__(self, file_, tree):
		self.file = file_
		self.tree = tree
		if file_ is not None:
			self.name = os.path.splitext((os.path.split(file_)[1]))[0]

		self.bg = None
		self.colors = []
		self.tags = {}
		self.shift = [0, 0]
		self.scale = "1.00"

	def __repr__(self):
		return "<%s> %s" % (
			self.__module__ + "." + self.__class__.__name__,
			str({k: v for k, v in self.__dict__.items() if k not in ("tags", "tree")})
		)

	@debuginfo(input_log=False)
	def get_palette(self):
		"""Build full list of colors"""
		palette = [dict(index=0, name="Background", hex=self.bg)]
		for i, color in enumerate(self.colors, start=1):
			palette.append(dict(index=i, name="Color" + str(i), hex=color))
		return palette

	def set_background(self, tag):
		"""Save background properties"""
		self.bg = tag.get("fill")
		self.tags["background"] = tag

	def set_color(self, tag, id_):
		"""Save color properties"""
		self.colors.append(tag.get("fill"))
		self.tags[id_] = tag

	def set_transform(self, tag):
		"""Save transform properties"""
		attribute = tag.get("transform")
		shift = re.search("translate\((.+?),(.+?)\)", attribute)
		scale = re.search("scale\((.+?)\)", attribute)
		self.shift = [shift.group(1), shift.group(2)]
		self.scale = scale.group(1)
		self.tags["transform"] = tag

	def change_color(self, color, index):
		"""Change color in palette by index"""
		if index == 0:
			self.bg = color
		else:
			self.colors[index - 1] = color

	def change_shift(self, value, index):
		"""Change image main figure offset"""
		self.shift[index] = value

	def change_scale(self, value):
		"""Change image main figure scale"""
		self.scale = value

	def rebuild(self, file_=None):
		"""Apply image changes"""
		if file_ is None:
			file_ = self.file

		transform_data = (self.shift[0], self.shift[1], self.scale)
		self.tags["transform"].set("transform", "translate(%s,%s) scale(%s)" % transform_data)
		self.tags["background"].set("fill", self.bg)
		for i, color in enumerate(self.colors, start=1):
			self.tags["color" + str(i)].set("fill", color)

		self.tree.write(file_, pretty_print=True)

		if logger.is_debug:
			tag_info = "Current image parameters "
			for name, tag in self.tags.items():
				attr = "transform" if name == "transform" else "fill"
				tag_info += "[%s: %s], " % (name, tag.get(attr))
			logger.debug(tag_info)

	def export_colors(self, file_):
		"""Export colors to ini file"""
		bg = dict(background=self.bg)
		colors = {"color" + str(i): c for i, c in enumerate(self.colors)}
		palette = {**bg, **colors}
		logger.debug("Exporting colors: %s", str(palette))

		config = ConfigParser()
		config["colors"] = palette
		with open(file_, "w") as configfile:
			config.write(configfile)

	def import_colors(self, file_):
		"""Import colors from ini file"""
		try:
			config = ConfigParser()
			config.read(file_)
			self.bg = config["colors"]["background"]
			for i, color in enumerate(self.colors):
				tag = "color" + str(i)
				if tag in config["colors"]:
					self.colors[i] = config["colors"][tag]
			logger.debug("Updated color scheme: %s, %s", self.bg, str(self.colors))
		except Exception:
			logger.exception("Fail to load palette from file: %s", file_)


class ImageParser:
	"""
	Image manager.
	Read and edit SVG images.
	"""
	def __init__(self, mainapp, image_sample):
		self._mainapp = mainapp
		self._testimage = image_sample
		self.temporary = tempfile.NamedTemporaryFile()
		self.parser = etree.XMLParser(remove_blank_text=True)
		self.current = None
		self.image_list = []

	def _load_image_data(self, file_, source):
		"""Read image settings from SVG tags"""
		tree = etree.parse(source, self.parser)
		root = tree.getroot()
		xhtml = "{%s}" % root.nsmap[None]

		imagedata = ImageData(file_, tree)

		transform_tag = root.find(".//%s*[@id='transform']" % xhtml)
		imagedata.set_transform(transform_tag)

		background_tag = root.find(".//%s*[@id='background']" % xhtml)
		imagedata.set_background(background_tag)

		counter = count(1)
		while True:
			index = next(counter)
			id_ = "color" + str(index)
			tag = root.find(".//%s*[@id='%s']" % (xhtml, id_))
			if tag is None:
				break
			imagedata.set_color(tag, id_)

		return imagedata

	@debuginfo(output_log=False)
	def load_images(self, *directories):
		"""Find all formatted SVG images in directories"""
		imagepack = []
		for path in directories:
			for root, _, files in os.walk(path):
				svg_files = [os.path.join(root, name) for name in files if name.endswith('.svg')]
				# check if images formatted correctly
				for file_ in svg_files:
					try:
						temp_data = self._load_image_data(None, file_)
						if (
							temp_data.bg is None
							or any([item is None for item in temp_data.colors])
							or any([item is None for item in temp_data.shift])
						):
							raise Exception("Missed tag parameter")
						imagepack.append(file_)
					except Exception:
						logger.exception("Broken image file:\n%s" % file_)

		logger.debug("%s image files was found." % len(imagepack))
		if not imagepack:
			logger.warning("No image was found.\nLoad test sample.")
			imagepack.append(self._testimage)

		self.image_list = sorted(imagepack)

	@debuginfo()
	def load_image_data(self, file_, source):
		"""Read image settings from SVG tags"""
		return self._load_image_data(file_, source)

	@debuginfo(output_log=False)
	def set_image(self, file_):
		"""Select currently active image"""
		shutil.copy2(file_, self.temporary.name)  # create temporary copy
		self.current = self.load_image_data(file_, self.temporary.name)  # parse SVG data

	@debuginfo(False, False)
	def apply_changes(self):
		"""Preview image changes"""
		self.current.rebuild(self.temporary.name)

	@debuginfo(False, False)
	def export_image(self):
		"""GUI handler"""
		type_ = self._mainapp.settings.get_string("export-type")
		file_ = os.path.join(self._mainapp.settings.get_string("export-path"), self.current.name + "." + type_)
		width = self._mainapp.settings.get_string("export-width")
		height = self._mainapp.settings.get_string("export-height")
		logger.debug("Exporting image: %s at size %sx%s", file_, width, height)

		pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(self.temporary.name, int(width), int(height), False)
		pixbuf.savev(file_, type_, [], [])
