"""Compare character set differences"""


__all__ = ['CharsetDiffFinder']


class CharsetDiffFinder(object):
    """Provides methods to compare two fonts metrics"""
    def __init__(self, font_a, font_b, error_bound=0):
        self._font_a = font_a
        self._font_b = font_b

        self._font_a_chars = self._font_a.getGlyphSet().keys()
        self._font_b_chars = self._font_b.getGlyphSet().keys()

        self._new_glyphs = []
        self._missing_glyphs = []

    @property
    def new_glyphs(self):
        if not self._new_glyphs:
            self._new_glyphs = self._subtract_chars(
                self._font_b_chars, self._font_a_chars
            )
        return self._new_glyphs

    @property
    def missing_glyphs(self):
        if not self._missing_glyphs:
            self._missing_glyphs = self._subtract_chars(
                self._font_a_chars, self._font_b_chars
            )
        return self._missing_glyphs

    def _subtract_chars(self, char1, char2):
        chars_leftover = list(set(char1) - set(char2))
        chars = [{'glyph': g} for g in chars_leftover]
        chars.sort(key=lambda t: t['glyph'])
        return chars