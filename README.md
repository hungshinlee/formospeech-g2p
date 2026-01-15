# FormoSpeech G2P

Grapheme-to-Phoneme (G2P) Toolkit for Taiwanese Languages

[繁體中文](README_zh-TW.md)

## Features

- **G2P Conversion**: Convert text to IPA or Pinyin pronunciation sequences
- **Smart Tokenization**: Jieba-based segmentation with dialect-specific dictionaries
- **Variant Character Normalization**: Automatic conversion of variant characters to standard forms
- **Mixed Chinese-English Support**: Optional English pronunciation integration
- **Extended CJK Support**: Full support for CJK Extension B–H and Private Use Area characters commonly used in Taiwanese languages
- **Unknown Word Detection**: Automatic identification and reporting of out-of-vocabulary words

### Supported Hakka Dialects

- 客語_四縣（hak_sx）
- 客語_南四縣（hak_nsx）
- 客語_海陸（hak_hl）
- 客語_大埔（hak_dp）
- 客語_饒平（hak_rp）
- 客語_詔安（hak_za）

## Installation

### From PyPI

```bash
pip install formog2p
```

### From Github

```bash
pip install git+https://github.com/hungshinlee/formospeech-g2p.git
```

### Development Installation

```bash
git clone https://github.com/hungshinlee/formospeech-g2p.git
cd formospeech-g2p

# Using uv (recommended)
uv sync --all-extras

# Or using pip
pip install -e ".[dev]"

# Install pre-commit hooks (optional)
pre-commit install
```

## Quick Start

```python
from formog2p.hakka import g2p

# Basic G2P conversion
result = g2p("天公落水", "hak_sx", "ipa")
print(result.pronunciations)
# ['tʰ-ien_24 k-uŋ_24', 'l-ok_5 s-ui_31']

# Check for unknown words
if result.has_unknown:
    print(f"Unknown words: {result.unknown_words}")
```

## Usage

### G2P conversion (Concatenated String)
```python
# To get a simple string output, you can use the result object
# or use text_to_pronunciation
from formog2p.hakka import text_to_pronunciation

pron_str = text_to_pronunciation("天公落水", "hak_sx", "ipa")
# 'tʰ-ien_24 k-uŋ_24 l-ok_5 s-ui_31'
```

### G2P Parameters

```python
result = g2p(
    text,                          # Input text
    lang_group="hak_sx",           # Dialect name
    pronunciation_type="ipa",      # Pronunciation format: "ipa" or "pinyin"
    unknown_token=None,            # Replacement token for unknown words
    keep_unknown=True,             # Whether to keep unknown words in output
    use_variant_map=True,          # Whether to apply variant character conversion
    include_eng=False,             # Whether to include English pronunciations
)
```

### Mixed Chinese-English G2P

```python
from formog2p.hakka import g2p

# Enable English pronunciation (IPA only)
result = g2p("天公落水Hello World", "hak_sx", "ipa", include_eng=True)
print(result.pronunciations)
# ['tʰ-ien_24 k-uŋ_24', 'l-ok_5 s-ui_31', 'h ə l oʊ', 'w ɝ l d']

# Without English (English words treated as unknown)
result = g2p("天公落水Hello", "hak_sx", "ipa", include_eng=False)
print(result.unknown_words)
# ['Hello']
```

### Text Normalization

```python
from formog2p.hakka import normalize, apply_variant_map

# Full normalization (including variant character conversion)
normalize("天公落水!")           # '天公落水！' (half-width to full-width)
normalize("台灣真好")            # '臺灣真好' (variant character conversion)
normalize("Hello", use_variant_map=True)  # 'HELLO' (uppercase conversion)

# Apply variant character conversion only
apply_variant_map("台灣")        # '臺灣'
apply_variant_map("温泉")        # '溫泉'
```

Normalization processing steps:
1. Unicode NFKC normalization (full-width to half-width)
2. Half-width punctuation to full-width (`, ? ! .` → `，？！。`)
3. Remove unnecessary punctuation (keep `，。？！`)
4. Variant character conversion (optional)
5. Uppercase conversion

### Punctuation Handling

Punctuation marks `，。？！` are treated as known tokens and output directly:

```python
result = g2p("天公落水，好靚！", "hak_sx", "ipa")
print(result.pronunciations)
# ['tʰ-ien_24 k-uŋ_24', 'l-ok_5 s-ui_31', '，', '好靚', '！']
```

### Basic Tokenization

```python
from formog2p.hakka import run_jieba

# Tokenize with specific dialect
words, oovs = run_jieba("天公落水", "hak_sx")
# words: ['天公', '落水']

# Include English dictionary
words, oovs = run_jieba("天公落水ABC", "hak_sx", include_eng=True)
# words: ['天公', '落水', 'ABC']
```

### Pronunciation Lookup

```python
from formog2p.hakka import get_pronunciation

# Query pronunciation for a single word
pron = get_pronunciation("天公", "hak_sx", "ipa")
# ['tʰ-ien_24 k-uŋ_24']
```

### Tokenizer Cache Management

Tokenizers are loaded and cached on first invocation; subsequent calls retrieve from cache:

```python
from formog2p.hakka import get_cached_tokenizers, clear_tokenizer_cache

# View cached tokenizers
get_cached_tokenizers()
# ['hak_sx', ...]

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
| `g2p(text, lang_group, pronunciation_type, ...)` | Full G2P conversion, returns G2PResult |
| `text_to_pronunciation(text, lang_group, pronunciation_type, ...)` | Returns concatenated pronunciation string |
| `normalize(text, use_variant_map)` | Text normalization |
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
| `run_jieba(text, lang_group, include_eng)` | Tokenize and return (words, unknown_words) |

### Pronunciation Lookup

| Function | Description |
|----------|-------------|
| `get_pronunciation(word, lang_group, pronunciation_type)` | Query single word pronunciation |
| `segment_with_pronunciation(text, lang_group, include_eng)` | Tokenize with pronunciation |

### Statistics and Cache

| Function | Description |
|----------|-------------|
| `get_cached_tokenizers()` | Get list of cached tokenizers |
| `clear_tokenizer_cache()` | Clear tokenizer cache |

## Project Structure

```
formospeech-g2p/
├── pyproject.toml
├── README.md
├── README_zh-TW.md
├── lexicon/           # Pronunciation dictionaries
│   ├── ipa/
│   └── pinyin/
├── share/             # Shared resources (e.g. variant map)
├── formog2p/               # Source code
│   ├── __init__.py
│   └── hakka/
│       ├── __init__.py
│       └── g2p.py     # Main G2P logic
```

## License

MIT License
