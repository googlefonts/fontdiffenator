# Diffenator

Compare two fonts against each other.

## Features

**Glyph matching**

Most differs will only compare glyphs if they have matching names. Diffenator matches glyphs by creating a key consisting of the unicodes and OT features used to produce the glyph. This allows us to make comparisons where font A uses AGl names whilst font B uses uniXXXX names.

**Mark positioning**

Marks coordinates are related to the glyph's outlines; not the metrics.

A single matching glyph is chosen from each mark class; thus keeping the output compact.

**Kerning**

Pair and class to class kerning are supported. The class kerns get flattened into pairs. Unfortunately this approach is very slow and needs improving.


**Upm aware**

Values by default are scaled in relation to the font's upm. This means we can easily compare fonts with differing upms. e.g

font_a @1000upm

- kern = pos A V -100;


font_b @2000upm

- kern = pos A V -200

This example won't produce a match, visually they will appear the same.


## Limitations

- gsub_diff: Cannot parse gsub rules LookupTypes 5, 6, 8
- mkmk still needs implementing


## Future work

### Comparing OpenType features

The developers of fontTools are working on [otlLib](https://github.com/fonttools/fonttools/issues/468) which will make working with GPOS and GSUB tables much easier.


## Installation
```
$ virtualenv venv
$ source venv/bin/activate
$ pip install -r requirements.txt
$ pip install . # -e . for dev installation
```

## Usage:

```
$ diffenator ./path/to/font_a.ttf ./path/to/font_b.ttf
```

## Python (Google fonts):

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