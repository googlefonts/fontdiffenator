"""Module for DFont"""
from fontTools.misc.py23 import unichr
from fontTools.ttLib import TTFont
from fontTools.varLib.mutator import instantiateVariableFont
from diffenator.hbinput import HbInputGenerator
from diffenator.dump import (
        DumpAnchors,
        dump_kerning,
        dump_glyphs,
        dump_glyph_metrics,
        dump_attribs,
        dump_nametable
)
from copy import copy
import uharfbuzz as hb
import freetype
from freetype.raw import *
from freetype import (
        FT_PIXEL_MODE_MONO,
        FT_PIXEL_MODE_GRAY,
        FT_Pointer,
        FT_Bitmap,
        FT_Fixed,
        FT_Set_Var_Design_Coordinates
)
import sys
import logging
try:
    # try and import unicodedata2 backport for py2.7.
    import unicodedata2 as uni
except ImportError:
    # on py2.7, this module only goes up to unicode 5.2.0 so it won't support
    # recently added glyphs.
    import unicodedata as uni
if sys.version_info.major == 3:
    unicode = str


logger = logging.getLogger('fontdiffenator')

class DFont(TTFont):
    """Container font for ttfont, freetype and hb fonts"""
    def __init__(self, path=None, lazy=False, size=1500):
        self.path = path
        self.ttfont = TTFont(self.path)
        self._src_ttfont = TTFont(self.path)
        self.glyphset = None
        self.recalc_glyphset()
        self.axis_order = None
        self.instance_coordinates = self._get_dflt_instance_coordinates()
        self.instances_coordinates = self._get_instances_coordinates()
        self.glyphs = self.marks = self.mkmks = self.kerns = \
            self.glyph_metrics = self.names = self.attribs = None

        self.ftfont = freetype.Face(self.path)
        self.ftslot = self.ftfont.glyph

        self.size = size
        self.ftfont.set_char_size(self.size)

        with open(self.path, 'rb') as fontfile:
            self._fontdata = fontfile.read()
        self.hbface = hb.Face.create(self._fontdata)
        self.hbfont = hb.Font.create(self.hbface)

        self.hbfont.scale = (self.size, self.size)

        if not lazy:
            self.recalc_tables()

    def _get_instances_coordinates(self):
        if self.is_variable:
            return [i.coordinates for i in self._src_ttfont["fvar"].instances]
        return None

    def _get_dflt_instance_coordinates(self):
        if self.is_variable:
            return {i.axisTag: i.defaultValue for i in self._src_ttfont['fvar'].axes}
        return None

    def glyph(self, name):
        return self.glyphset[name]

    def recalc_glyphset(self):
        if not 'cmap' in self.ttfont.keys():
            self.glyphset = []
        inputs = InputGenerator(self).all_inputs()
        self.glyphset = {g.name: g for g in inputs}

    @property
    def is_variable(self):
        if 'fvar' in self._src_ttfont:
            return True
        return False

    def set_variations(self, axes):
        """Instantiate a ttfont VF with axes vals"""
        if self.is_variable:
            font = instantiateVariableFont(self._src_ttfont, axes, inplace=False)
            self.ttfont = copy(font)
            self.axis_order = [a.axisTag for a in self._src_ttfont['fvar'].axes]
            self.instance_coordinates = {a.axisTag: a.defaultValue for a in
                                    self._src_ttfont['fvar'].axes}
            for axis in axes:
                if axis in self.instance_coordinates:
                    self.instance_coordinates[axis] = axes[axis]
                else:
                    logger.info("font has no axis called {}".format(axis))
            self.recalc_tables()

            coords = []
            for name in self.axis_order:
                coord = FT_Fixed(int(self.instance_coordinates[name]) << 16)
                coords.append(coord)
            ft_coords = (FT_Fixed * len(coords))(*coords)
            FT_Set_Var_Design_Coordinates(self.ftfont._FT_Face, len(ft_coords), ft_coords)
            self.hbface = hb.Face.create(self._fontdata)
            self.hbfont = hb.Font.create(self.hbface)
            self.hbfont.set_variations(self.instance_coordinates)
            self.hbfont.scale = (self.size, self.size)
        else:
            logger.info("Not vf")

    def set_variations_from_static(self, dfont):
        """Set the variations of a variable font using the vals from a
        static font"""
        variations = {}
        if self.is_variable:
            variations["wght"] = dfont.ttfont["OS/2"].usWeightClass
            # TODO (M Foley) add wdth, slnt axes
            self.set_variations(variations)

    def recalc_tables(self):
        """Recalculate DFont tables"""
        self.recalc_glyphset()
        anchors = DumpAnchors(self)
        self.glyphs = dump_glyphs(self)
        self.marks = anchors.marks_table
        self.mkmks = anchors.mkmks_table
        self.glyph_metrics = dump_glyph_metrics(self)
        self.attribs = dump_attribs(self)
        self.names = dump_nametable(self)
        self.kerns = dump_kerning(self)
        self.metrics = dump_glyph_metrics(self)


class InputGenerator(HbInputGenerator):
    """Taken from Nototool's HbIntputGenerator"""

    def all_inputs(self, warn=False):
        """Generate harfbuzz inputs for all glyphs in a given font."""

        inputs = []
        glyph_set = self.font.ttfont.getGlyphSet()
        for name in self.font.ttfont.getGlyphOrder():
            is_zero_width = glyph_set[name].width == 0
            cur_input = self.input_from_name(name, pad=is_zero_width)
            if cur_input is not None:
                features, characters = cur_input
                characters = characters.replace(' ', '')
                inputs.append(
                    Glyph(name, features, unicode(characters), self.font)
                )
            else:
                features = ('',)
                inputs.append(Glyph(name, features, '', self.font))
        return inputs

    def input_from_name(self, name, seen=None, pad=False):
        """Given glyph name, return input to harbuzz to render this glyph.

        Returns input in the form of a (features, text) tuple, where `features`
        is a list of feature tags to activate and `text` is an input string.

        Argument `seen` is used by the method to avoid following cycles when
        recursively looking for possible input. `pad` can be used to add
        whitespace to text output, for non-spacing glyphs.

        Can return None in two situations: if no possible input is found (no
        simple unicode mapping or substitution rule exists to generate the
        glyph), or if the requested glyph already exists in `seen` (in which
        case this path of generating input should not be followed further).
        """

        if name in self.memo:
            return self.memo[name]

        inputs = []

        # avoid following cyclic paths through features
        if seen is None:
            seen = set()
        if name in seen:
            return None
        seen.add(name)

        # see if this glyph has a simple unicode mapping
        if name in self.reverse_cmap:
            text = unichr(self.reverse_cmap[name])
            if text != unichr(0):
                inputs.append(((), text))

        # check the substitution features
        inputs.extend(self._inputs_from_gsub(name, seen))
        # seen.remove(name)

        # since this method sometimes returns None to avoid cycles, the
        # recursive calls that it makes might have themselves returned None,
        # but we should avoid returning None here if there are other options
        inputs = [i for i in inputs if i is not None]
        if not inputs:
            return None

        features, text = min(inputs)
        # can't pad if we don't support space
        if pad and self.space_width > 0:
            width, space = self.widths[name], self.space_width
            padding = ' ' * (width // space + (1 if width % space else 0))
            text = padding + text
        self.memo[name] = features, text
        return self.memo[name]


class Glyph:
    def __init__(self, name, features, characters, font):
        self.name = name
        self.features = features
        self.characters = characters
        self.combining = True if characters and uni.combining(characters[0]) else False
        self.key = self.characters + ''.join(features)
        self.font = font

    def __repr__(self):
        return self.name

    def __str__(self):
        return self.name

