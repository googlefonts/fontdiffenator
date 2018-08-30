import unittest
from diffenator.utils import stylename_from_name


class TestUtils(unittest.TestCase):

    def test_stylename_from_name(self):
        fullname = 'Roboto UltraLight'
        self.assertEqual('UltraLight',
                         stylename_from_name(fullname))

        fullname = 'Roboto Ultra Light'
        self.assertEqual('Ultra Light',
                         stylename_from_name(fullname))

        fullname = 'Roboto Condensed SemiBold'
        self.assertEqual('Condensed SemiBold',
                         stylename_from_name(fullname))

        fullname = 'Roboto SemiCondensed ExtraLight Italic'
        self.assertEqual('SemiCondensed ExtraLight Italic',
                         stylename_from_name(fullname))

        fullname = 'Roboto Semi Condensed Extra Light Italic'
        self.assertEqual('Semi Condensed Extra Light Italic',
                         stylename_from_name(fullname))


if __name__ == '__main__':
    unittest.main()