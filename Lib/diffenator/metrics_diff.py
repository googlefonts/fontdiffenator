"""Compare advance width and sidebearing differences"""
__all__ = ['MetricsDiffFinder']


class MetricsDiffFinder(object):
    """Provides methods to compare two font's metrics"""
    def __init__(self, font_a, font_b, error_bound=20):
        self._font_a = font_a
        self._font_b = font_b
        self.error_bound = error_bound

        self._shared_glyphs = self._shared_glyphs(self._font_a, self._font_b)

        self._modified_adv_width = []
        self._modified_sidebearings = []

    def _shared_glyphs(self, font_a, font_b):
        return set(font_a.getGlyphSet().keys()) & \
               set(font_b.getGlyphSet().keys())

    @property
    def modified_adv_widths(self):
        """Find differences in glyph advanced widths"""
        if not self._modified_adv_width:
            self._modified_adv_width = self._find_modified_adv_widths()
        return self._modified_adv_width

    @property
    def modified_sidebearings(self):
        """Find differences between sidebearings"""
        if not self._modified_sidebearings:
            self._modified_sidebearings = self._find_modified_sidebearings()
        return self._modified_sidebearings

    def _find_modified_adv_widths(self):
        differences = []
        for glyph_name in self._shared_glyphs:
            glyph_a_width = self._glyph_adv_width(self._font_a, glyph_name)
            glyph_b_width = self._glyph_adv_width(self._font_b, glyph_name)

            difference = glyph_a_width - glyph_b_width
            if abs(difference) > self.error_bound:
                differences.append((glyph_name, difference))
        differences.sort(key=lambda tup: tup[1], reverse=True)
        return [{'glyph': d[0], 'width_diff': d[1]} for d in differences]

    def _find_modified_sidebearings(self):
        differences = []
        for glyph_name in self._shared_glyphs:

            glyph_a_lsb = self._glyph_lsb(self._font_a, glyph_name)
            glyph_b_lsb = self._glyph_lsb(self._font_b, glyph_name)

            glyph_a_rsb = self._glyph_rsb(self._font_a, glyph_name)
            glyph_b_rsb = self._glyph_rsb(self._font_b, glyph_name)

            difference_lsb = glyph_a_lsb - glyph_b_lsb
            difference_rsb = glyph_a_rsb - glyph_b_rsb

            if abs(difference_lsb) > self.error_bound or \
               abs(difference_rsb) > self.error_bound:
                differences.append((glyph_name, difference_lsb, difference_rsb))
        differences.sort(key=lambda tup: abs(tup[1]) + abs(tup[2]), reverse=True)
        return [{'glyph': d[0], 'lsb_diff': d[1], 'rsb_diff': d[2]} for d in differences]

    def _glyph_adv_width(self, font, char):
        return font['hmtx'].metrics[char][0]

    def _glyph_lsb(self, font, char):
        """Get the left side bearing for a glyph.
        If the Xmin attribute does not exist, the font is zero width so
        return 0"""
        try:
            return font['glyf'][char].xMin
        except AttributeError:
            return 0

    def _glyph_rsb(self, font, char):
        """Get the right side bearing for a glyph.
        If the Xmax attribute does not exist, the font is zero width so
        return 0"""
        glyph_width = font['hmtx'].metrics[char][0]
        try:
            return glyph_width - font['glyf'][char].xMax
        except AttributeError:
            return 0
