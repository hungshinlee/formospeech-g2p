# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [0.1.0] - 2024-12-31

### Added

- **G2P Conversion**: Convert Hakka text to IPA or Pinyin pronunciation
- **Smart Tokenization**: Jieba-based segmentation with dialect-specific dictionaries
- **Variant Character Normalization**: Automatic conversion of variant characters (台→臺)
- **Mixed Chinese-English Support**: Optional English pronunciation integration
- **Extended CJK Support**: Full support for CJK Extension B–H and Private Use Area
- **Unknown Word Detection**: Automatic identification of out-of-vocabulary words

### Supported Dialects

- 客語_四縣 (Sixian)
- 客語_南四縣 (Nan-Sixian)
- 客語_海陸 (Hailu)
- 客語_大埔 (Dapu)
- 客語_饒平 (Raoping)
- 客語_詔安 (Zhaoan)

### Package Structure

- Package name: `formog2p`
- Dynamic versioning with `hatch-vcs`
- PEP 561 type hints support (`py.typed`)
- Data files centralized under `formog2p/data/`

[0.1.0]: https://github.com/hungshinlee/formospeech-g2p/releases/tag/v0.1.0
