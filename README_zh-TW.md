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
result = g2p("天公落水", "hak_sx", "ipa")
print(result.pronunciations)
# ['tʰ-ien_24 k-uŋ_24', 'l-ok_5 s-ui_31']

# 檢查是否有未知詞彙
if result.has_unknown:
    print(f"未知詞彙: {result.unknown_words}")
```

## 使用方式

### G2P 轉換（發音字串）
```python
# 若需要純字串輸出，可使用 G2PResult.pronunciations 
# 或使用 text_to_pronunciation
from formog2p.hakka import text_to_pronunciation

pron_str = text_to_pronunciation("天公落水", "hak_sx", "ipa")
# 'tʰ-ien_24 k-uŋ_24 l-ok_5 s-ui_31'
```

### G2P 參數說明

```python
result = g2p(
    text,                          # 輸入文字
    lang_group="hak_sx",           # 腔調名稱
    pronunciation_type="ipa",      # 發音格式: "ipa" 或 "pinyin"
    unknown_token=None,            # 未知詞彙的替代符號
    keep_unknown=True,             # 是否保留未知詞彙
    use_variant_map=True,          # 是否套用異體字轉換
    include_eng=False,             # 是否包含英文發音
)
```

### 中英混合 G2P

```python
from formog2p.hakka import g2p

# 啟用英文發音（僅支援 IPA）
result = g2p("天公落水Hello World", "hak_sx", "ipa", include_eng=True)
print(result.pronunciations)
# ['tʰ-ien_24 k-uŋ_24', 'l-ok_5 s-ui_31', 'h ə l oʊ', 'w ɝ l d']

# 不啟用英文（英文會被視為未知詞彙）
result = g2p("天公落水Hello", "hak_sx", "ipa", include_eng=False)
print(result.unknown_words)
# ['Hello']
```

### 文本正規化

```python
from formog2p.hakka import normalize, apply_variant_map

# 完整正規化（包含異體字轉換）
normalize("天公落水!")           # '天公落水！'（半形轉全形）
normalize("台灣真好")            # '臺灣真好'（異體字轉換）
normalize("Hello", use_variant_map=True)  # 'HELLO' (轉大寫)

# 單獨套用異體字轉換
apply_variant_map("台灣")        # '臺灣'
apply_variant_map("温泉")        # '溫泉'
```

正規化處理項目：
1. Unicode NFKC 正規化（全形轉半形）
2. 半形標點轉全形（`, ? ! .` → `，？！。`）
3. 移除不需要的標點（保留 `，。？！`）
4. 異體字轉換（可選）
5. 英文轉大寫

### 標點符號處理

標點符號 `，。？！` 會被視為 known token，直接輸出：

```python
result = g2p("天公落水，好靚！", "hak_sx", "ipa")
print(result.pronunciations)
# ['tʰ-ien_24 k-uŋ_24', 'l-ok_5 s-ui_31', '，', '好靚', '！']
```

### 基本斷詞

```python
from formog2p.hakka import run_jieba

# 使用指定腔調斷詞
words, oovs = run_jieba("天公落水", "hak_sx")
# words: ['天公', '落水']

# 包含英文詞典
words, oovs = run_jieba("天公落水ABC", "hak_sx", include_eng=True)
# words: ['天公', '落水', 'ABC']
```

### 發音查詢

```python
from formog2p.hakka import get_pronunciation

# 查詢單一詞彙發音
pron = get_pronunciation("天公", "hak_sx", "ipa")
# ['tʰ-ien_24 k-uŋ_24']
```

### Tokenizer 快取管理

Tokenizer 會在第一次呼叫時載入並快取，之後的呼叫不會重複載入：

```python
from formog2p.hakka import get_cached_tokenizers, clear_tokenizer_cache

# 查看已快取的 Tokenizer
get_cached_tokenizers()
# ['hak_sx', ...]

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
| `g2p(text, lang_group, pronunciation_type, ...)` | 完整 G2P 轉換，回傳 G2PResult |
| `text_to_pronunciation(text, lang_group, pronunciation_type, ...)` | 回傳合併的發音字串 |
| `normalize(text, use_variant_map)` | 文本正規化 |
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
| `run_jieba(text, lang_group, include_eng)` | 使用指定腔調斷詞，回傳 (words, oovs) |

### 發音查詢

| 函數 | 說明 |
|------|------|
| `get_pronunciation(word, lang_group, pronunciation_type)` | 查詢單一詞彙發音 |
| `segment_with_pronunciation(text, lang_group, include_eng)` | 斷詞並附帶發音 |

### 統計與快取

| 函數 | 說明 |
|------|------|
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
├── lexicon/           # 發音詞典
│   ├── ipa/
│   └── pinyin/
├── share/             # 共享資源（如異體字對照表）
├── formog2p/               # 套件原始碼
│   ├── __init__.py
│   └── hakka/
│       ├── __init__.py
│       └── g2p.py     # 客語 G2P 主要邏輯
└── tests/             # 測試
```

## 授權

MIT License
