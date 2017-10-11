# Diffenator

Compare two fonts against each other.

Still extreme wip.


## Limitations

- gsub_diff: Cannot parse gsub rules LookupTypes 5, 6, 8
- Vertical metrics tests missing
- Browser rendering tests missing


## Future work

### Comparing OpenType features

The developers of fontTools are working on [otlLib](https://github.com/fonttools/fonttools/issues/468) which will make working with OpenType data much easier. Our current solution uses the approach implemented in nototools. We ttxn the gpos and gsub font tables then use regular expressions to parse the data. We should refactor once otlLib can unbuild OpenType features.


## Installation
```
$ virtualenv venv
$ source venv/bin/activate
$ pip install -r requirements.txt
$ pip install . # -e . for dev installation
```

Diffenator relies on Harfbuzz. Install it using homebrew.

```
brew install --with-cairo harfbuzz cairo
```


### CLI usage (Google fonts):

```
$ diffenator ./path/to/font_a.ttf ./path/to/font_b.ttf
```

### Python (Google fonts):

```
>>> from diffenator import diff_fonts
>>> font_a_path = './path/to/font_a.ttf'
>>> font_b_path = './path/to/font_b.ttf'
>>> diff_fonts(font_a_path, font_b_path)
...
```

## Running tests
```
nosetests
```