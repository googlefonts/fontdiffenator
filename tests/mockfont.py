from fontTools.agl import AGL2UV
from fontTools.feaLib.builder import addOpenTypeFeaturesFromString

from diffenator.font import DFont
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen 
import tempfile


def drawTestGlyph(pen):
    pen.moveTo((100, 100))
    pen.lineTo((100, 1000))
    pen.qCurveTo((200, 900), (400, 900), (500, 1000))
    pen.lineTo((500, 100))
    pen.closePath()


def test_glyph():
    pen = TTGlyphPen(None)
    drawTestGlyph(pen)
    glyph = pen.glyph()
    return glyph

def minimalTTF():
    fb = FontBuilder(1024, isTTF=True)
    fb.updateHead(unitsPerEm=1000, created=0, modified=0)
    fb.setupGlyphOrder([".notdef", ".null", "A", "Aacute", "V", "acutecomb", "gravecomb", "A.alt"])
    fb.setupCharacterMap({65: "A", 192: "Aacute", 86: "V", 769: "acutecomb", 768: "gravecomb"})
    advanceWidths = {".notdef": 600, "A": 600, "Aacute": 600, "V": 600, ".null": 600, "acutecomb": 0, "gravecomb": 0, "A.alt": 600}
    familyName = "HelloTestFont"
    styleName = "TotallyNormal"
    nameStrings = dict(familyName=dict(en="HelloTestFont", nl="HalloTestFont"),
                       styleName=dict(en="TotallyNormal", nl="TotaalNormaal"))
    nameStrings['psName'] = familyName + "-" + styleName
    glyphs = {
        ".notdef": test_glyph(), 
        ".null": test_glyph(),
        "A": test_glyph(),
        "Aacute": test_glyph(),
        "V": test_glyph(),
        "acutecomb": test_glyph(),
        "gravecomb": test_glyph(),
        "A.alt": test_glyph()
    }
    fb.setupGlyf(glyphs)
    metrics = {}
    glyphTable = fb.font["glyf"]
    for gn, advanceWidth in advanceWidths.items():
        metrics[gn] = (advanceWidth, glyphTable[gn].xMin)
    fb.setupHorizontalMetrics(metrics)
    fb.setupHorizontalHeader()
    fb.setupNameTable(nameStrings)
    fb.setupOS2()
    fb.setupPost()
    return fb


def mock_font():
    f_path = tempfile.NamedTemporaryFile()
    ttf = minimalTTF()
    ttf.font.save(f_path.name)
    dfont = DFont(f_path.name)
    dfont.builder = FontBuilder(font=dfont.ttfont)
    f_path.close()
    return dfont

