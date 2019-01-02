import unittest
from mockfont import mock_font, test_glyph


class TestGposKerningDump(unittest.TestCase):

    def test_pair_on_pair_kerns(self):
        font = mock_font()
        fea="""
            feature kern {
            pos A V -140;
            pos V A -140;} kern;
        """
        font.builder.addOpenTypeFeatures(fea)
        font.recalc_tables()
        self.assertEqual(len(font.kerns), 2)

    def test_class_on_class_kerns(self):
        """dump_gpos_kerning will flatten class kerns into pairs kerns.
        This implementation may change in the future"""
        font = mock_font()
        fea="""
            @A_l = [ A Aacute ];
            @A_r = [ A Aacute ];
            @V_l = [ V ];
            @V_r = [ V ];

            feature kern {
            pos @A_l @V_r -140;
            pos @V_l @A_r -140;} kern;
        """
        font.builder.addOpenTypeFeatures(fea)
        font.recalc_tables()
        self.assertEqual(len(font.kerns), 4)

    def test_class_on_class_kerns2(self):
        """TODO (M Foley) Simple groups e.g

            [A Aacute] [V] - 120} -140;

        Are not yet supported. Fortunately most font editors do not
        generate kerns in this manner (citation/proof needed).
        """
        pass


class TestGposMarkDump(unittest.TestCase):

    def test_mark(self):
        font = mock_font()
        fea="""
        markClass [acutecomb] <anchor 150 0> @top;

        feature mark {
            pos base [A Aacute]
             <anchor 100 300> mark @top;
        } mark;
        """
        font.builder.addOpenTypeFeatures(fea)
        font.recalc_tables()
        self.assertEqual(len(font.marks), 2)

    def test_mkmk(self):
        font = mock_font()
        fea="""
        markClass [acutecomb gravecomb] <anchor 150 0> @top;

        feature mkmk {
            pos mark @top
             <anchor 100 300> mark @top;
        } mkmk;
        """
        font.builder.addOpenTypeFeatures(fea)
        font.recalc_tables()
        self.assertEqual(len(font.mkmks), 4)


if __name__ == '__main__':
    unittest.main()
