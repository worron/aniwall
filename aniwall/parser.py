import os
import re
import tempfile
import shutil

from itertools import count
from lxml import etree
from aniwall.logger import logger


class ImageData:
	"""Structure to store image parameters"""
	def __init__(self, file_, tree):
		self.file = file_
		self.tree = tree

		self.bg = None
		self.colors = []
		self.tags = {}
		self.shift = [0, 0]
		self.scale = "1.00"

	def get_palette(self):
		"""Build full list of colors"""
		palette = [(0, "Background", self.bg)]
		for i, color in enumerate(self.colors, start=1):
			palette.append((i, "Color" + str(i), color))
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


class ImageParser:
	"""
	Image manager.
	Read and edit SVG images.
	"""
	def __init__(self, mainapp):
		self._mainapp = mainapp
		self.parser = etree.XMLParser(remove_blank_text=True)
		self.current = None
		self.temporary = tempfile.NamedTemporaryFile()
		self.test_image = os.path.join(self._mainapp.path.data, "test.svg")

		self.image_list = sorted(self.load_svg(self._mainapp.path.images))

	def load_svg(self, *directories):
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
			imagepack.append(self.test_image)
		return imagepack

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

	def set_image(self, file_):
		"""Select currently active image"""
		shutil.copy2(file_, self.temporary.name)  # create temporary copy
		self.current = self._load_image_data(file_, self.temporary.name)  # parse SVG data

	def apply_changes(self):
		"""Preview image changes"""
		self.current.rebuild(self.temporary.name)
