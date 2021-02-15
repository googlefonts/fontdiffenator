[![Build Status](https://travis-ci.org/googlefonts/fontdiffenator.svg?branch=main)](https://travis-ci.org/googlefonts/fontdiffenator)

# Diffenator

Python 3 library/tool to compare two **TTF** fonts against each other. It's capable of producing diff images using Harfbuzz, Cairo and FreeType. It can also produce Markdown reports for Github.

## Features

Currenly only supports TrueType flavoured fonts - **CFF/OTF flavour fonts are not supported!**

**Glyph matching**

Most differs will only compare glyphs if they have matching names. Diffenator matches glyphs by creating a key consisting of the unicodes and OT features used to produce the glyph. This allows us to make comparisons where font A uses AGl names whilst font B uses uniXXXX names.

**Mark positioning**

Marks coordinates are relative to the glyph's outlines, not the glyph metrics.


**Kerning**

Pair and class to class kerning are supported. The class kerns get flattened into pairs. Unfortunately this approach is very slow and needs improving.


**Upm aware**

Values by default are scaled in relation to the font's upm. This means we can easily compare fonts with differing upms. e.g

font_before @1000upm

- kern = pos A V -100;


font_after @2000upm

- kern = pos A V -200

This example won't produce a match, visually they will appear the same.


## Limitations

- gsub_diff: Cannot parse gsub rules LookupTypes 5, 6, 8


## Future work

### Comparing OpenType features

The developers of fontTools are working on [otlLib](https://github.com/fonttools/fonttools/issues/468) which will make working with GPOS and GSUB tables much easier.


## Installation

```
pip install fontdiffenator
```

To generate images, you will need to install Cairo, FreeType and Harfbuzz. Easiest way to do this is by using a package manager. For OS X we can use brew.

```
brew install cairo
brew install freetype
brew install harfbuzz
```


### Dev install 
```
$ git clone https://github.com/googlefonts/fontdiffenator
$ cd fontdiffenator
$ virtualenv venv
$ source venv/bin/activate
$ pip install . # -e . for dev installation
```

## Usage:

```
$ diffenator ./path/to/font_before.ttf ./path/to/font_after.ttf

# Generate before and after gifs

$ diffenator ./path/to/font_before.ttf ./path/to/font_after.ttf -r ./path/to/out_gifs
```

## Python (Google fonts):

```
>>> from diffenator import DiffFonts
>>> from diffenator.font import DFont
>>> font_before = DFont('./path/to/font_before.ttf')
>>> font_after = DFont('./path/to/font_after.ttf')
>>> diff = DiffFonts(font_before, font_after)
...
```

## Running tests

Tests are located in the /tests dir. Tests are based on the standard unittest framework.

```
sh ./tests/run.sh
```
