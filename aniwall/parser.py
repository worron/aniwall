import os
import tempfile
import shutil

from itertools import count
from lxml import etree


def get_svg(*directories):
	"""Find all SVG icon in directories"""
	file_list = []
	for path in directories:
		for root, _, files in os.walk(path):
			file_list.extend([os.path.join(root, name) for name in files if name.endswith('.svg')])
	return file_list


class ImageData:
	"""Structure to store image parameters"""
	def __init__(self, file_, tree):
		self.file = file_
		self.tree = tree

		self.bg = None
		self.colors = []
		self.tags = {}

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

	def change_color(self, color, index):
		"""Change color in palette by index"""
		if index == 0:
			self.bg = color
		else:
			self.colors[index] = color

	def rebuild(self, file_=None):
		"""Apply image changes"""
		if file_ is None:
			file_ = self.file

		self.tags["background"].set("fill", self.bg)
		for i, color in enumerate(self.colors, start=1):
			self.tags["color" + str(i)].set("fill", color)

		self.tree.write(file_, pretty_print=True)


class ImageParser:
	"""
	Image manager.
	Read and edit SVG images.
	"""
	def __init__(self):
		dl = (os.path.join(os.path.dirname(os.path.abspath(__file__)), "images"),)
		self.image_list = sorted(get_svg(*dl))

		self.parser = etree.XMLParser(remove_blank_text=True)
		self.current = None
		self.temporary = tempfile.NamedTemporaryFile()

	def set_image(self, file_):
		"""Select currently active image"""
		# create temporary copy
		shutil.copy2(file_, self.temporary.name)

		# parse SVG data
		tree = etree.parse(self.temporary.name, self.parser)
		root = tree.getroot()
		xhtml = "{%s}" % root.nsmap[None]

		self.current = ImageData(file_, tree)

		background_tag = root.find(".//%s*[@id='background']" % xhtml)
		self.current.set_background(background_tag)

		counter = count(1)
		while True:
			index = next(counter)
			id_ = "color" + str(index)
			tag = root.find(".//%s*[@id='%s']" % (xhtml, id_))
			if tag is None:
				break
			self.current.set_color(tag, id_)

	def apply_changes(self):
		"""Preview image changes"""
		self.current.rebuild(self.temporary.name)
