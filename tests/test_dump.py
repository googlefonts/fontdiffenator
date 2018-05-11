import unittest
from mockfont import mock_font
from diffenator.kerning import dump_gpos_kerning
from diffenator.marks import DumpMarks

class TestGposKerningDump(unittest.TestCase):

    def test_pair_on_pair_kerns(self):
        font = mock_font(
            glyphs=[('A', 50, 50), ('V', 10, 10)],
            fea="""
                feature kern {
                pos A V -140;
                pos V A -140;} kern;
            """
        )
        kerns = dump_gpos_kerning(font)
        self.assertEqual(len(kerns), 2)

    def test_class_on_class_kerns(self):
        """dump_gpos_kerning will flatten class kerns into pairs kerns.
        This implementation may change in the future"""
        font = mock_font(
            glyphs=[('A', 50, 50), ('Aacute', 50, 50), ('V', 10, 10)],
            fea="""
                @A_l = [ A Aacute ];
                @A_r = [ A Aacute ];
                @V_l = [ V ];
                @V_r = [ V ];

                feature kern {
                pos @A_l @V_r -140;
                pos @V_l @A_r -140;} kern;
            """
        )
        kerns = dump_gpos_kerning(font)
        self.assertEqual(len(kerns), 4)

    def test_class_on_class_kerns2(self):
        """TODO (M Foley) Simple groups e.g

            [A Aacute] [V] - 120} -140;

        Are not yet supported. Fortunately most font editors do not
        generate kerns in this manner (citation/prood needed).
        """
        pass


class TestGposMarkDump(unittest.TestCase):

    def test_mark(self):
        font = mock_font(
            attrs=[('head', 'unitsPerEm', 1000)],
            glyphs=[('A', 100, 100), ('Aacute', 100, 100), ('acutecomb', 0, 0)],
            fea="""
            markClass [acutecomb] <anchor 150 0> @top;

            feature mark {
                pos base [A Aacute]
                 <anchor 100 300> mark @top;
            } mark;
            """
        )
        marks = DumpMarks(font)
        self.assertEqual(len(marks.mark_table), 2)

    def test_mkmk(self):
        font = mock_font(
            attrs=[('head', 'unitsPerEm', 1000)],
            glyphs=[('gravecomb', 0, 0), ('acutecomb', 0, 0)],
            fea="""
            markClass [acutecomb gravecomb] <anchor 150 0> @top;

            feature mkmk {
                pos mark @top
                 <anchor 100 300> mark @top;
            } mkmk;
            """
        )
        marks = DumpMarks(font)
        self.assertEqual(len(marks.mkmk_table), 4)


if __name__ == '__main__':
    unittest.main()