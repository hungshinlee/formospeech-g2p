# FormoSpeech G2P

Grapheme-to-Phoneme (G2P) Toolkit for Formosan Languages

[繁體中文](README_zh-TW.md)

## Features

- **G2P Conversion**: Convert text to IPA or Pinyin pronunciation sequences
- **Smart Tokenization**: Jieba-based segmentation with dialect-specific dictionaries
- **Variant Character Normalization**: Automatic conversion of variant characters to standard forms
- **Mixed Chinese-English Support**: Optional English pronunciation integration
- **Extended CJK Support**: Full support for CJK Extension B–H and Private Use Area characters commonly used in Taiwanese languages
- **Unknown Word Detection**: Automatic identification and reporting of out-of-vocabulary words

### Supported Hakka Dialects

- 客語_四縣 (Sixian)
- 客語_南四縣 (Nan-Sixian)
- 客語_海陸 (Hailu)
- 客語_大埔 (Dapu)
- 客語_饒平 (Raoping)
- 客語_詔安 (Zhaoan)

## Installation

```bash
# Using uv
uv sync

# Or using pip
pip install -e .
```

## Quick Start

```python
from hakka import g2p

# Basic G2P conversion
result = g2p("天公落水", "客語_四縣", "ipa")
print(result.pronunciations)
# ['tʰ-ien_24 k-uŋ_24', 'l-ok_5 s-ui_31']

# Check for unknown words
if result.has_unknown:
    print(f"Unknown words: {result.unknown_words}")
```

## Usage

### G2P Conversion

```python
from hakka import g2p, g2p_simple, g2p_string, batch_g2p

# Full G2P (returns G2PResult object)
result = g2p("天公落水，好靚！", "客語_四縣", "ipa")
result.pronunciations  # Pronunciation sequence
result.unknown_words   # List of unknown words
result.details         # Detailed word-pronunciation mapping
result.has_unknown     # Whether unknown words exist

# Simplified version (returns pronunciation list only)
prons = g2p_simple("天公落水", "客語_四縣", "ipa")
# ['tʰ-ien_24 k-uŋ_24', 'l-ok_5 s-ui_31']

# String version (returns concatenated pronunciation string)
pron_str = g2p_string("天公落水", "客語_四縣", "ipa")
# 'tʰ-ien_24 k-uŋ_24 l-ok_5 s-ui_31'

# Batch processing
results = batch_g2p(["天公落水", "日頭落山"], "客語_四縣", "ipa")
```

### G2P Parameters

```python
result = g2p(
    text,                          # Input text
    dialect="客語_四縣",            # Dialect name
    pronunciation_type="ipa",      # Pronunciation format: "ipa" or "pinyin"
    unknown_token=None,            # Replacement token for unknown words
    keep_unknown=True,             # Whether to keep unknown words in output
    use_variant_map=True,          # Whether to apply variant character conversion
    include_english=False,         # Whether to include English pronunciations
)
```

### Mixed Chinese-English G2P

```python
from hakka import g2p

# Enable English pronunciation (IPA only)
result = g2p("天公落水Hello World", "客語_四縣", "ipa", include_english=True)
print(result.pronunciations)
# ['tʰ-ien_24 k-uŋ_24', 'l-ok_5 s-ui_31', 'h ə l oʊ', 'w ɝ l d']

# Without English (English words treated as unknown)
result = g2p("天公落水Hello", "客語_四縣", "ipa", include_english=False)
print(result.unknown_words)
# ['Hello']
```

### Text Normalization

```python
from hakka import normalize, apply_variant_map

# Full normalization (including variant character conversion)
normalize("天公落水!")           # '天公落水！' (half-width to full-width)
normalize("台灣真好")            # '臺灣真好' (variant character conversion)
normalize("Hello", include_english=True)  # 'HELLO' (uppercase conversion)

# Apply variant character conversion only
apply_variant_map("台灣")        # '臺灣'
apply_variant_map("温泉")        # '溫泉'
```

Normalization processing steps:
1. Unicode NFKC normalization (full-width to half-width)
2. Half-width punctuation to full-width (`, ? ! .` → `，？！。`)
3. Remove unnecessary punctuation (keep `，。？！`)
4. Variant character conversion (optional)
5. Uppercase conversion for English (optional)

### Punctuation Handling

Punctuation marks `，。？！` are treated as known tokens and output directly:

```python
result = g2p("天公落水，好靚！", "客語_四縣", "ipa")
print(result.pronunciations)
# ['tʰ-ien_24 k-uŋ_24', 'l-ok_5 s-ui_31', '，', '好靚', '！']
```

### Basic Tokenization

```python
from hakka import run_jieba, run_jieba_all_dialects

# Tokenize with specific dialect
words = run_jieba("天公落水", "客語_四縣")
# ['天公', '落水']

# Include English dictionary
words = run_jieba("天公落水ABC", "客語_四縣", include_english=True)
# ['天公', '落水', 'ABC']

# Tokenize with all dialects
results = run_jieba_all_dialects("天公落水")
```

### Pronunciation Lookup

```python
from hakka import get_pronunciation, get_pronunciation_all_dialects

# Query pronunciation for a single word
pron = get_pronunciation("天公", "客語_四縣", "ipa")
# ['tʰ-ien_24 k-uŋ_24']

# Query pronunciation across all dialects
all_prons = get_pronunciation_all_dialects("天公", "ipa")
```

### English Pronunciation Lookup

```python
from hakka import get_english_pronunciation, english_word_exists, get_english_lexicon_stats

# Query English pronunciation (auto-converts to uppercase)
get_english_pronunciation("hello")
# ['h ə l oʊ', 'h ɛ l oʊ']

# Check if English word exists
english_word_exists("hello")  # True

# English dictionary statistics
get_english_lexicon_stats()
# {'total_words': 126282, 'max_word_length': ...}
```

### Vocabulary Check

```python
from hakka import word_exists, find_unknown_words

# Check if word exists
word_exists("天公", "客語_四縣")  # True

# Find unknown words
unknown = find_unknown_words("天公落水ABC", "客語_四縣")
# ['ABC']

# Include English dictionary check
unknown = find_unknown_words("天公落水ABC", "客語_四縣", include_english=True)
# [] (ABC exists in English dictionary)
```

### Dialect Comparison

```python
from hakka import compare_dialects, find_common_words, find_unique_words

# Compare pronunciation of the same word across dialects
comparison = compare_dialects("天公")
# {'客語_四縣': {'ipa': [...], 'pinyin': [...]}, ...}

# Find words common to multiple dialects
common = find_common_words("客語_四縣", "客語_海陸")

# Find words unique to a specific dialect
unique = find_unique_words("客語_四縣")
```

### Dictionary Statistics

```python
from hakka import get_lexicon_stats, get_all_lexicon_stats

# Single dialect statistics
stats = get_lexicon_stats("客語_四縣")
# {'total_words': 91281, 'max_word_length': ..., ...}

# All dialects statistics
all_stats = get_all_lexicon_stats()
```

### Tokenizer Cache Management

Tokenizers are loaded and cached on first invocation; subsequent calls retrieve from cache:

```python
from hakka import get_cached_tokenizers, clear_tokenizer_cache

# View cached tokenizers
get_cached_tokenizers()
# ['客語_四縣', '客語_四縣_en', '客語_海陸', ...]

# Clear cache (if dictionary reload is needed)
clear_tokenizer_cache()
```

## Unicode Support

Full support for extended character sets commonly used in Taiwanese languages:

| Range | Description |
|-------|-------------|
| `U+2E80-U+9FFF` | CJK Radicals, Basic CJK |
| `U+F900-U+FAFF` | CJK Compatibility Ideographs |
| `U+20000-U+323AF` | CJK Extension B–H (Taiwanese language characters) |
| `U+E000-U+F8FF` | Private Use Area (PUA) |
| `U+F0000-U+10FFFD` | Supplementary Private Use Areas A & B (custom characters) |

## API Reference

### G2P Functions

| Function | Description |
|----------|-------------|
| `g2p(text, dialect, type, ...)` | Full G2P conversion, returns G2PResult |
| `g2p_simple(text, dialect, type, ...)` | Simplified version, returns pronunciation list only |
| `g2p_string(text, dialect, type, ...)` | Returns concatenated pronunciation string |
| `batch_g2p(texts, dialect, type, ...)` | Batch process multiple texts |
| `normalize(text, use_variant_map, include_english)` | Text normalization |
| `apply_variant_map(text)` | Apply variant character conversion |

### G2PResult Object

| Attribute | Type | Description |
|-----------|------|-------------|
| `pronunciations` | `list[str]` | Pronunciation sequence |
| `unknown_words` | `list[str]` | List of unknown words |
| `details` | `list[dict]` | Detailed word-pronunciation mapping |
| `has_unknown` | `bool` | Whether unknown words exist |

### Tokenization Functions

| Function | Description |
|----------|-------------|
| `run_jieba(text, dialect, include_english)` | Tokenize with specific dialect |
| `run_jieba_all_dialects(text, include_english)` | Tokenize with all dialects |

### Pronunciation Lookup

| Function | Description |
|----------|-------------|
| `get_pronunciation(word, dialect, type)` | Query single word pronunciation |
| `get_pronunciation_all_dialects(word, type)` | Query pronunciation across all dialects |
| `segment_with_pronunciation(text, dialect, type, include_english)` | Tokenize with pronunciation |
| `text_to_pronunciation(text, dialect, type, ...)` | Convert text to pronunciation string |

### English Functions

| Function | Description |
|----------|-------------|
| `get_english_pronunciation(word)` | Query English pronunciation |
| `english_word_exists(word)` | Check if English word exists |
| `get_english_lexicon_stats()` | English dictionary statistics |

### Vocabulary Check

| Function | Description |
|----------|-------------|
| `word_exists(word, dialect)` | Check if word exists |
| `word_exists_in_dialects(word)` | Check word existence across all dialects |
| `find_unknown_words(text, dialect, include_english)` | Find unknown words |

### Dialect Comparison

| Function | Description |
|----------|-------------|
| `compare_dialects(word)` | Compare word pronunciation across dialects |
| `find_common_words(*dialects)` | Find words common to multiple dialects |
| `find_unique_words(dialect)` | Find words unique to a dialect |

### Statistics and Cache

| Function | Description |
|----------|-------------|
| `get_lexicon_stats(dialect)` | Get dictionary statistics |
| `get_all_lexicon_stats()` | Get all dialect statistics |
| `get_cached_tokenizers()` | Get list of cached tokenizers |
| `clear_tokenizer_cache()` | Clear tokenizer cache |

## Project Structure

```
formospeech-g2p/
├── pyproject.toml
├── README.md
├── README_zh-TW.md
├── hakka/
│   ├── __init__.py
│   ├── word_segment.py    # Tokenization module
│   ├── g2p.py             # G2P module
│   ├── lexicon/
│   │   ├── ipa/           # IPA pronunciation dictionaries
│   │   └── pinyin/        # Pinyin dictionaries
│   └── share/
│       └── variant_map.json  # Variant character mapping
└── english/
    ├── lexicon_cmu.json      # CMU English pronunciation dictionary
    └── lexicon_sinica.json   # Academia Sinica English pronunciation dictionary
```

## License

MIT License
