import datetime
import logging


logging.basicConfig(level=logging.WARN)
logger = logging.getLogger(__name__)


def _panose(panose):
    return '{}-{}-{}-{}-{}-{}-{}-{}-{}-{}'.format(
        panose.bFamilyType,
        panose.bSerifStyle,
        panose.bWeight,
        panose.bProportion,
        panose.bContrast,
        panose.bStrokeVariation,
        panose.bArmStyle,
        panose.bLetterForm,
        panose.bMidline,
        panose.bXHeight
        )


def _timestamp(epoch):
    """fontTool's epoch origin is 1904, not 1970.

    days between datetime(1970,1,1,1) - datetime(1904,1,1,1) = 24107

    https://github.com/fonttools/fonttools/issues/99"""
    d = datetime.datetime.fromtimestamp(epoch) - datetime.timedelta(days=24107)
    return d.strftime('%Y/%m/%d %H:%M:%S')


OS2 = [
    # 'fsFirstCharIndex',
    # 'fsLastCharIndex',
    ('fsSelection', int),
    ('fsType', int),
    ('panose', _panose),
    ('sCapHeight', int),
    ('sFamilyClass', int),
    ('sTypoAscender', int),
    ('sTypoDescender', int),
    ('sTypoLineGap', int),
    ('sxHeight', int),
    ('ulCodePageRange1', int),
    ('ulCodePageRange2', int),
    ('ulUnicodeRange1', int),
    ('ulUnicodeRange2', int),
    ('ulUnicodeRange3', int),
    ('ulUnicodeRange4', int),
    ('usBreakChar', int),
    ('usDefaultChar', int),
    ('usFirstCharIndex', int),
    ('usLastCharIndex', int),
    ('usMaxContex', int),
    ('usMaxContext', int),
    ('usWeightClass', int),
    ('usWidthClass', int),
    ('usWinAscent', int),
    ('usWinDescent', int),
    ('version', int),
    # 'xAvgCharWidth', int),
    ('yStrikeoutPosition', int),
    ('yStrikeoutSize', int),
    ('ySubscriptXOffset', int),
    ('ySubscriptXSize', int),
    ('ySubscriptYOffset', int),
    ('ySubscriptYSize', int),
    ('ySuperscriptXOffset', int),
    ('ySuperscriptXSize', int),
    ('ySuperscriptYOffset', int),
    ('ySuperscriptYSize', int)
]

HHEA = [
    # ('advanceWidthMax', int),
    ('ascent', int),
    ('caretOffset', int),
    ('caretSlopeRise', int),
    ('caretSlopeRun', int),
    ('descent', int),
    ('lineGap', int),
    # ('metricDataFormat', int),
    # ('minLeftSideBearing', int),
    # ('minRightSideBearing', int),
    # ('numberOfHMetrics', int),
    ('reserved0', int),
    ('reserved1', int),
    ('reserved2', int),
    ('reserved3', int),
    # ('tableTag', int),
    ('tableVersion', int),
]

GASP = [
    ('gaspRange', dict),
    ('version', int),
]

HEAD = [
    # ('checkSumAdjustment', int),
    ('fontRevision', float),
    # ('glyphDataFormat', int),
    ('macStyle', int),
    # ('magicNumber', int),
    ('modified', _timestamp),
    # ('tableTag', int),
    ('tableVersion', int),
    ('unitsPerEm', int),
    ('xMax', int),
    ('xMin', int),
    ('yMax', int),
    ('yMin', int),
]


def dump_attribs(font):
    """""Dump a font's attribs

    Parameters
    ----------
    font: InputFont

    Returns
    -------
    dump_table: list
        Each row in the table is represented as a dict.
        [
            {'table': 'OS/2', 'attrib': 'fsSelection': 'value': 128},
            {'table': 'hhea', 'attrib': 'ascender', 'value': 1100}
            ...
        ]
    """
    attribs = []
    for table_tag, font_table in zip(['OS/2', 'hhea', 'gasp', 'head'],
                                     [OS2, HHEA, GASP, HEAD]):
        if table_tag in font:
            for attr, converter in font_table:
                try:
                    row = {
                        'attrib': attr,
                        'value': converter(getattr(font[table_tag], attr)),
                        'table': table_tag
                    }
                    attribs.append(row)
                except AttributeError:
                    logger.info("{} Missing attrib {}".format(table_tag, attr))
    return attribs
