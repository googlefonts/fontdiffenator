"""Dump font's nametable"""
from fontTools.ttLib import TTFont


def dump_nametable(ttfont):
    table = []
    name_table = ttfont['name']

    for name in name_table.names:
        table.append({
            'string': name.toUnicode(),
            'id': (name.nameID, name.platformID, name.platEncID, name.langID)
        })
    return table

if __name__ == '__main__':
    from fontTools.ttLib import TTFont

    f = TTFont('/Users/marc/Documents/googlefonts/manual_font_cleaning/opensans/tests/original/OpenSans-Regular.ttf')
    names = dump_nametable(f)
    k = []
    for r in names:
        k.append(r['string'])

    print '\n'.join(k)