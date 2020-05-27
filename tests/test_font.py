import unittest
from diffenator.font import find_token, WIDTH_NAME_TO_FVAR, WEIGHT_NAME_TO_FVAR


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

if __name__ == "__main__":
    unittest.main()

