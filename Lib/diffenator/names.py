def dump_nametable(font):
    """Dump a font's nametable

    Parameters
    ----------
    font: InputFont

    Returns
    -------
    dump_table: list
        Each row in the table is represented as a dict.
        [
            {'id': (1, 3, 1, 1033), 'string': 'Noto Sans'},
            {'id': (2, 3, 1, 1033), 'string': 'Regular'},
            ...
        ]
    """
    table = []
    name_table = font['name']

    for name in name_table.names:
        table.append({
            'string': name.toUnicode(),
            'id': (name.nameID, name.platformID, name.platEncID, name.langID)
        })
    return table
