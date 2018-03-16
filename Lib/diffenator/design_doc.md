Design doc:

For v1, we plan to add diff tests for the following:

- Glyphs
    - New
    - Missing
    - Modified (Based on shape_diff)
- Kerning (Based on gpos_diff)
    - New
    - Missing
    - Modified
- Marks (Based on gpos_diff)
    - New
    - Missing
    - Modified
- Glyph Metrics
    - Modified sidebearings
    - Modified Advance Widths


In v2, we plan to add further diffs:

- Browser rendering (Use Browserstack screenshot api with GFRegression)
- Importers/fixers for font editors


## Api



### Initialization

The `diff_fonts` function is used to compare two fonts. It has two compulsory parameters, font_a, font_b which are the filepaths for the two fonts to compare.

```
>>> comparison = diff_fonts('./font_a.ttf', './font_b.ttf')
```

### Endpoints:

Each comparison category, glyphs, kerning etc may have several attributes, new, missing...

```
>>> comparison.glyphs.new
[{'glyph': 'A.sc',}, {'glyph': 'B.sc'}]

>>> comparison.marks.modified
[{'glyph': 'AE', 'x_diff': 10, 'y_diff': 0}]

```

