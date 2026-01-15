# FormoSpeech G2P

臺灣本土語言文字轉音素 (Grapheme-to-Phoneme) 工具

[English](README.md)

## 功能特色

- **G2P 轉換**：將文字轉換為 IPA 或拼音發音序列
- **智慧斷詞**：使用 Jieba 搭配各腔調專屬詞典
- **異體字正規化**：自動將異體字轉換為標準字
- **中英混合支援**：可選擇性加入英文發音
- **擴展漢字支援**：完整支援臺灣客語常用的 CJK 擴展字集與私用區造字
- **未知詞彙回報**：自動識別並回報不在詞典中的詞彙

### 支援的客語腔調

- 客語_四縣（hak_sx）
- 客語_南四縣（hak_nsx）
- 客語_海陸（hak_hl）
- 客語_大埔（hak_dp）
- 客語_饒平（hak_rp）
- 客語_詔安（hak_za）

## 安裝

### 從 PyPI 安裝

```bash
pip install formog2p
```

### 從 Github 安裝

```bash
pip install git+https://github.com/hungshinlee/formospeech-g2p.git
```

### 開發環境安裝

```bash
git clone https://github.com/hungshinlee/formospeech-g2p.git
cd formospeech-g2p

# 使用 uv（推薦）
uv sync --all-extras

# 或使用 pip
pip install -e ".[dev]"

# 安裝 pre-commit hooks（選用）
pre-commit install
```

## 快速開始

```python
from formog2p.hakka import g2p

# 基本 G2P 轉換
result = g2p("天公落水", "客語_四縣", "ipa")
print(result.pronunciations)
# ['tʰ-ien_24 k-uŋ_24', 'l-ok_5 s-ui_31']

# 檢查是否有未知詞彙
if result.has_unknown:
    print(f"未知詞彙: {result.unknown_words}")
```

## 使用方式

### G2P 轉換

```python
from formog2p.hakka import g2p, g2p_simple, g2p_string, batch_g2p

# 完整 G2P（回傳 G2PResult 物件）
result = g2p("天公落水，好靚！", "客語_四縣", "ipa")
result.pronunciations  # 發音序列
result.unknown_words   # 未知詞彙列表
result.details         # 詳細的詞彙與發音對應
result.has_unknown     # 是否有未知詞彙

# 簡化版（只回傳發音列表）
prons = g2p_simple("天公落水", "客語_四縣", "ipa")
# ['tʰ-ien_24 k-uŋ_24', 'l-ok_5 s-ui_31']

# 字串版（回傳合併的發音字串）
pron_str = g2p_string("天公落水", "客語_四縣", "ipa")
# 'tʰ-ien_24 k-uŋ_24 l-ok_5 s-ui_31'

# 批次處理
results = batch_g2p(["天公落水", "日頭落山"], "客語_四縣", "ipa")
```

### G2P 參數說明

```python
result = g2p(
    text,                          # 輸入文字
    dialect="客語_四縣",            # 腔調名稱
    pronunciation_type="ipa",      # 發音格式: "ipa" 或 "pinyin"
    unknown_token=None,            # 未知詞彙的替代符號
    keep_unknown=True,             # 是否保留未知詞彙
    use_variant_map=True,          # 是否套用異體字轉換
    include_english=False,         # 是否包含英文發音
)
```

### 中英混合 G2P

```python
from formog2p.hakka import g2p

# 啟用英文發音（僅支援 IPA）
result = g2p("天公落水Hello World", "客語_四縣", "ipa", include_english=True)
print(result.pronunciations)
# ['tʰ-ien_24 k-uŋ_24', 'l-ok_5 s-ui_31', 'h ə l oʊ', 'w ɝ l d']

# 不啟用英文（英文會被視為未知詞彙）
result = g2p("天公落水Hello", "客語_四縣", "ipa", include_english=False)
print(result.unknown_words)
# ['Hello']
```

### 文本正規化

```python
from formog2p.hakka import normalize, apply_variant_map

# 完整正規化（包含異體字轉換）
normalize("天公落水!")           # '天公落水！'（半形轉全形）
normalize("台灣真好")            # '臺灣真好'（異體字轉換）
normalize("Hello", include_english=True)  # 'HELLO'（轉大寫）

# 單獨套用異體字轉換
apply_variant_map("台灣")        # '臺灣'
apply_variant_map("温泉")        # '溫泉'
```

正規化處理項目：
1. Unicode NFKC 正規化（全形轉半形）
2. 半形標點轉全形（`, ? ! .` → `，？！。`）
3. 移除不需要的標點（保留 `，。？！`）
4. 異體字轉換（可選）
5. 英文轉大寫（可選）

### 標點符號處理

標點符號 `，。？！` 會被視為 known token，直接輸出：

```python
result = g2p("天公落水，好靚！", "客語_四縣", "ipa")
print(result.pronunciations)
# ['tʰ-ien_24 k-uŋ_24', 'l-ok_5 s-ui_31', '，', '好靚', '！']
```

### 基本斷詞

```python
from formog2p.hakka import run_jieba, run_jieba_all_dialects

# 使用指定腔調斷詞
words = run_jieba("天公落水", "客語_四縣")
# ['天公', '落水']

# 包含英文詞典
words = run_jieba("天公落水ABC", "客語_四縣", include_english=True)
# ['天公', '落水', 'ABC']

# 使用所有腔調斷詞
results = run_jieba_all_dialects("天公落水")
```

### 發音查詢

```python
from formog2p.hakka import get_pronunciation, get_pronunciation_all_dialects

# 查詢單一詞彙發音
pron = get_pronunciation("天公", "客語_四縣", "ipa")
# ['tʰ-ien_24 k-uŋ_24']

# 查詢所有腔調發音
all_prons = get_pronunciation_all_dialects("天公", "ipa")
```

### 英文發音查詢

```python
from formog2p.hakka import get_english_pronunciation, english_word_exists, get_english_lexicon_stats

# 查詢英文發音（會自動轉大寫）
get_english_pronunciation("hello")
# ['h ə l oʊ', 'h ɛ l oʊ']

# 檢查英文詞彙是否存在
english_word_exists("hello")  # True

# 英文詞典統計
get_english_lexicon_stats()
# {'total_words': 126282, 'max_word_length': ...}
```

### 詞彙檢查

```python
from formog2p.hakka import word_exists, find_unknown_words

# 檢查詞彙是否存在
word_exists("天公", "客語_四縣")  # True

# 找出未知詞彙
unknown = find_unknown_words("天公落水ABC", "客語_四縣")
# ['ABC']

# 包含英文詞典檢查
unknown = find_unknown_words("天公落水ABC", "客語_四縣", include_english=True)
# []（ABC 在英文詞典中）
```

### 腔調比較

```python
from formog2p.hakka import compare_dialects, find_common_words, find_unique_words

# 比較同一詞彙在不同腔調的發音
comparison = compare_dialects("天公")
# {'客語_四縣': {'ipa': [...], 'pinyin': [...]}, ...}

# 找出多個腔調共有的詞彙
common = find_common_words("客語_四縣", "客語_海陸")

# 找出某腔調獨有的詞彙
unique = find_unique_words("客語_四縣")
```

### 字典統計

```python
from formog2p.hakka import get_lexicon_stats, get_all_lexicon_stats

# 單一腔調統計
stats = get_lexicon_stats("客語_四縣")
# {'total_words': 91281, 'max_word_length': ..., ...}

# 所有腔調統計
all_stats = get_all_lexicon_stats()
```

### Tokenizer 快取管理

Tokenizer 會在第一次呼叫時載入並快取，之後的呼叫不會重複載入：

```python
from formog2p.hakka import get_cached_tokenizers, clear_tokenizer_cache

# 查看已快取的 Tokenizer
get_cached_tokenizers()
# ['客語_四縣', '客語_四縣_en', '客語_海陸', ...]

# 清除快取（如需重新載入詞典）
clear_tokenizer_cache()
```

## Unicode 支援範圍

完整支援臺客語常用的擴展字集：

| 範圍 | 說明 |
|------|------|
| `U+2E80-U+9FFF` | CJK 部首、基本漢字 |
| `U+F900-U+FAFF` | CJK 相容漢字 |
| `U+20000-U+323AF` | CJK 擴展 B ~ H（臺灣客語常用外字） |
| `U+E000-U+F8FF` | 私用區 (PUA) |
| `U+F0000-U+10FFFD` | 私用區補充 A & B（臺灣客語造字） |

## API 參考

### G2P 功能

| 函數 | 說明 |
|------|------|
| `g2p(text, dialect, type, ...)` | 完整 G2P 轉換，回傳 G2PResult |
| `g2p_simple(text, dialect, type, ...)` | 簡化版，只回傳發音列表 |
| `g2p_string(text, dialect, type, ...)` | 回傳合併的發音字串 |
| `batch_g2p(texts, dialect, type, ...)` | 批次處理多個文字 |
| `normalize(text, use_variant_map, include_english)` | 文本正規化 |
| `apply_variant_map(text)` | 套用異體字轉換 |

### G2PResult 物件

| 屬性 | 類型 | 說明 |
|------|------|------|
| `pronunciations` | `list[str]` | 發音序列 |
| `unknown_words` | `list[str]` | 未知詞彙列表 |
| `details` | `list[dict]` | 詳細的詞彙與發音對應 |
| `has_unknown` | `bool` | 是否有未知詞彙 |

### 斷詞功能

| 函數 | 說明 |
|------|------|
| `run_jieba(text, dialect, include_english)` | 使用指定腔調斷詞 |
| `run_jieba_all_dialects(text, include_english)` | 使用所有腔調斷詞 |

### 發音查詢

| 函數 | 說明 |
|------|------|
| `get_pronunciation(word, dialect, type)` | 查詢單一詞彙發音 |
| `get_pronunciation_all_dialects(word, type)` | 查詢所有腔調發音 |
| `segment_with_pronunciation(text, dialect, type, include_english)` | 斷詞並附帶發音 |
| `text_to_pronunciation(text, dialect, type, ...)` | 文本轉發音字串 |

### 英文功能

| 函數 | 說明 |
|------|------|
| `get_english_pronunciation(word)` | 查詢英文發音 |
| `english_word_exists(word)` | 檢查英文詞彙是否存在 |
| `get_english_lexicon_stats()` | 英文詞典統計 |

### 詞彙檢查

| 函數 | 說明 |
|------|------|
| `word_exists(word, dialect)` | 檢查詞彙是否存在 |
| `word_exists_in_dialects(word)` | 檢查詞彙在各腔調是否存在 |
| `find_unknown_words(text, dialect, include_english)` | 找出未知詞彙 |

### 腔調比較

| 函數 | 說明 |
|------|------|
| `compare_dialects(word)` | 比較詞彙在各腔調的發音 |
| `find_common_words(*dialects)` | 找出多個腔調共有詞彙 |
| `find_unique_words(dialect)` | 找出某腔調獨有詞彙 |

### 統計與快取

| 函數 | 說明 |
|------|------|
| `get_lexicon_stats(dialect)` | 取得字典統計 |
| `get_all_lexicon_stats()` | 取得所有腔調統計 |
| `get_cached_tokenizers()` | 取得已快取的 Tokenizer 列表 |
| `clear_tokenizer_cache()` | 清除 Tokenizer 快取 |

## 專案結構

```
formospeech-g2p/
├── pyproject.toml
├── README.md
├── README_zh-TW.md
├── LICENSE
├── CHANGELOG.md
├── formog2p/
│   ├── __init__.py
│   ├── word_segment.py    # 斷詞模組
│   ├── g2p.py             # G2P 模組
│   ├── py.typed           # 型別提示標記
│   └── data/
│       ├── hakka/
│       │   ├── lexicon/   # 客語發音詞典
│       │   └── share/     # 異體字對照表
│       └── english/       # 英文發音詞典
└── tests/                 # 測試
```

## 授權

MIT License
