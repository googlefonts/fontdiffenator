import os
import unittest
from diffenator.constants import FTHintMode
from diffenator.font import (
    DFont,
    find_token,
    WIDTH_NAME_TO_FVAR,
    WEIGHT_NAME_TO_FVAR
)


class TestFont(unittest.TestCase):
 
    def test_find_token(self):
        string = "MavenProExtraExpanded-ExtraBold.ttf"
        self.assertEqual(
            find_token(string, list(WIDTH_NAME_TO_FVAR.keys())),
            "ExtraExpanded"
        )

        self.assertEqual(
            find_token(string, list(WEIGHT_NAME_TO_FVAR.keys())),
            "ExtraBold"
        )

    def test_ft_hint_mode(self):
        self._path = os.path.dirname(__file__)
        font_path = os.path.join(self._path, 'data', 'Play-Regular.ttf')

        unhinted_font = DFont(font_path, ft_load_glyph_flags=FTHintMode.UNHINTED)
        # gid 4 = A
        unhinted_font.ftfont.load_glyph(4, flags=unhinted_font.ft_load_glyph_flags)
        unhinted_bitmap = unhinted_font.ftslot.bitmap

        hinted_font = DFont(font_path, ft_load_glyph_flags=FTHintMode.NORMAL)
        hinted_font.ftfont.load_glyph(4, flags=hinted_font.ft_load_glyph_flags)
        hinted_bitmap = hinted_font.ftslot.bitmap

        self.assertNotEqual(unhinted_bitmap.buffer, hinted_bitmap.buffer)


if __name__ == "__main__":
    unittest.main()

