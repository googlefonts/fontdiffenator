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
    f = TTFont('/Users/marc/Desktop/tajawal/AmaticSC-Regular.ttf')
    print dump_nametable(f)