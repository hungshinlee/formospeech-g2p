"""
客語斷詞模組 (Hakka Word Segmentation Module)

使用 Jieba 搭配各腔調專屬的自定義字典進行斷詞。
每個腔調使用獨立的 Jieba Tokenizer 實例，確保字典不會混用。

支援的腔調 (Supported Dialects):
    - 客語_四縣
    - 客語_南四縣
    - 客語_海陸
    - 客語_大埔
    - 客語_饒平
    - 客語_詔安
"""

import json
import re
from pathlib import Path
from typing import Literal, Optional

import jieba

# =============================================================================
# 修改 Jieba 的漢字正則表達式，使其支援：
#   1. 中英文混合斷詞
#   2. 臺灣本土語言常用的擴展漢字（擴展 B ~ H）
#   3. 私用區字元（臺語、客語外字）
#
# Unicode 範圍說明：
#   - \u2e80-\u9fff   : CJK 部首、基本漢字
#   - \uf900-\ufaff   : CJK 相容漢字
#   - \U00020000-\U000323af : CJK 擴展 B ~ H（臺客語常用外字）
#   - \ue000-\uf8ff   : 私用區 (PUA)
#   - \U000f0000-\U0010fffd : 私用區補充 A & B（臺客語造字）
#   - a-zA-Z0-9       : 英文字母、數字
#   - +#&._%'-        : 常見符號
# =============================================================================
jieba.re_han_default = re.compile(
    r"(["
    r"\u2e80-\u9fff"           # CJK 基本區域
    r"\uf900-\ufaff"           # CJK 相容漢字
    r"\U00020000-\U000323af"   # CJK 擴展 B ~ H
    r"\ue000-\uf8ff"           # 私用區
    r"\U000f0000-\U0010fffd"   # 私用區補充 A & B
    r"a-zA-Z0-9"               # 英文字母、數字
    r"+#&\.\_%\-'"             # 常見符號
    r"]+)",
    re.U
)

# 模組路徑
MODULE_DIR = Path(__file__).parent
LEXICON_DIR = MODULE_DIR / "lexicon"
ENGLISH_DIR = MODULE_DIR.parent / "english"

# 支援的腔調列表
DIALECTS = [
    "客語_四縣",
    "客語_南四縣",
    "客語_海陸",
    "客語_大埔",
    "客語_饒平",
    "客語_詔安",
]

# 腔調類型
DialectType = Literal[
    "客語_四縣", "客語_南四縣", "客語_海陸", "客語_大埔", "客語_饒平", "客語_詔安"
]

# 發音格式類型
PronunciationType = Literal["ipa", "pinyin"]

# =============================================================================
# Tokenizer 快取機制
#
# 每個腔調的 Tokenizer 會在「第一次呼叫」時載入並快取。
# 之後的呼叫會直接從快取取得，不會重複載入。
#
# 快取 key 格式:
#   - "{dialect}"      : 不含英文的 tokenizer
#   - "{dialect}_en"   : 含英文的 tokenizer
#
# 例如: "客語_四縣" 和 "客語_四縣_en" 是兩個不同的快取項目
# =============================================================================
_tokenizers: dict[str, jieba.Tokenizer] = {}

# 儲存各腔調的詞典資料（用於查詢發音）
_lexicons: dict[str, dict[str, dict[str, list[str]]]] = {}

# 儲存英文詞典資料（延遲載入，只載入一次）
_english_lexicon: dict[str, list[str]] | None = None


def _load_lexicon(
    dialect: str, pronunciation_type: PronunciationType = "ipa"
) -> dict[str, list[str]]:
    """
    載入指定腔調的詞典。

    Args:
        dialect: 腔調名稱
        pronunciation_type: 發音格式 ("ipa" 或 "pinyin")

    Returns:
        詞典 (key: 詞彙, value: 發音列表)
    """
    lexicon_path = LEXICON_DIR / pronunciation_type / f"{dialect}.json"

    if not lexicon_path.exists():
        raise FileNotFoundError(f"找不到腔調字典檔案: {lexicon_path}")

    with open(lexicon_path, "r", encoding="utf-8") as f:
        return json.load(f)


def _load_english_lexicon() -> dict[str, list[str]]:
    """
    載入並合併所有英文詞典。

    此函數使用延遲載入機制，只會在第一次呼叫時載入。
    之後的呼叫會直接回傳快取的結果。

    Returns:
        合併後的英文詞典 (key: 詞彙, value: 發音列表)
    """
    global _english_lexicon
    if _english_lexicon is not None:
        return _english_lexicon

    _english_lexicon = {}

    if not ENGLISH_DIR.exists():
        return _english_lexicon

    # 載入所有英文詞典 JSON 檔
    for json_path in ENGLISH_DIR.glob("*.json"):
        with open(json_path, "r", encoding="utf-8") as f:
            lexicon = json.load(f)
            # 合併詞典（後載入的會覆蓋先前的）
            for word, pronunciations in lexicon.items():
                if word not in _english_lexicon:
                    _english_lexicon[word] = pronunciations
                else:
                    # 合併發音列表（避免重複）
                    existing = set(_english_lexicon[word])
                    for pron in pronunciations:
                        if pron not in existing:
                            _english_lexicon[word].append(pron)

    return _english_lexicon


def _get_lexicon(
    dialect: str, pronunciation_type: PronunciationType = "ipa"
) -> dict[str, list[str]]:
    """
    取得或載入指定腔調的詞典（有快取機制）。

    Args:
        dialect: 腔調名稱
        pronunciation_type: 發音格式

    Returns:
        詞典
    """
    if dialect not in _lexicons:
        _lexicons[dialect] = {}

    if pronunciation_type not in _lexicons[dialect]:
        _lexicons[dialect][pronunciation_type] = _load_lexicon(
            dialect, pronunciation_type
        )

    return _lexicons[dialect][pronunciation_type]


def _get_tokenizer(dialect: str, include_english: bool = False) -> jieba.Tokenizer:
    """
    取得或建立指定腔調的 Jieba Tokenizer。

    每個腔調使用獨立的 Tokenizer 實例，確保字典不會混用。
    Tokenizer 會在第一次呼叫時建立並快取，之後的呼叫直接從快取取得。

    Args:
        dialect: 腔調名稱
        include_english: 是否包含英文詞典

    Returns:
        該腔調專用的 Jieba Tokenizer 實例（從快取取得或新建）
    """
    if dialect not in DIALECTS:
        raise ValueError(
            f"不支援的腔調: {dialect}\n支援的腔調: {', '.join(DIALECTS)}"
        )

    # 使用不同的 key 來區分是否包含英文
    # 這樣 "客語_四縣" 和 "客語_四縣_en" 會分別快取
    cache_key = f"{dialect}_en" if include_english else dialect

    if cache_key not in _tokenizers:
        # 建立新的 Tokenizer 實例（只在第一次呼叫時執行）
        tokenizer = jieba.Tokenizer()

        # 載入該腔調的詞彙
        lexicon = _get_lexicon(dialect, "ipa")

        # 將詞彙加入自定義字典
        # 給予較高的詞頻以確保這些詞優先被識別
        for word in lexicon.keys():
            # 詞頻設為詞長的 10000 倍，讓較長的詞優先匹配
            freq = len(word) * 10000
            tokenizer.add_word(word, freq=freq)

        # 如果需要包含英文詞典
        if include_english:
            english_lexicon = _load_english_lexicon()
            for word in english_lexicon.keys():
                freq = len(word) * 10000
                tokenizer.add_word(word, freq=freq)

        # 存入快取
        _tokenizers[cache_key] = tokenizer

    return _tokenizers[cache_key]


# =============================================================================
# 核心斷詞功能
# =============================================================================


def run_jieba(
    text: str, dialect: DialectType = "客語_四縣", include_english: bool = False
) -> list[str]:
    """
    使用指定腔調的字典進行斷詞。

    Tokenizer 會在第一次呼叫時載入並快取，之後的呼叫不會重複載入。

    Args:
        text: 要斷詞的文本
        dialect: 腔調名稱，預設為「客語_四縣」
        include_english: 是否包含英文詞典，預設為 False

    Returns:
        斷詞後的詞彙列表

    Example:
        >>> words = run_jieba("天公落水", "客語_四縣")
        >>> print(words)
        ['天公', '落水']

        >>> words = run_jieba("天公落水ABC", "客語_四縣", include_english=True)
        >>> print(words)
        ['天公', '落水', 'ABC']
    """
    tokenizer = _get_tokenizer(dialect, include_english)
    return list(tokenizer.cut(text))


def run_jieba_all_dialects(
    text: str, include_english: bool = False
) -> dict[str, list[str]]:
    """
    使用所有腔調的字典分別進行斷詞。

    Args:
        text: 要斷詞的文本
        include_english: 是否包含英文詞典

    Returns:
        各腔調斷詞結果的字典

    Example:
        >>> results = run_jieba_all_dialects("天公落水")
        >>> for dialect, words in results.items():
        ...     print(f"{dialect}: {words}")
    """
    results = {}
    for dialect in DIALECTS:
        results[dialect] = run_jieba(text, dialect, include_english)
    return results


# =============================================================================
# 英文詞典功能
# =============================================================================


def get_english_pronunciation(word: str) -> list[str] | None:
    """
    查詢英文詞彙的發音。

    Args:
        word: 英文詞彙（會自動轉大寫）

    Returns:
        發音列表，若詞彙不存在則回傳 None

    Example:
        >>> get_english_pronunciation("hello")
        ['h ə l oʊ', 'h ɛ l oʊ']
    """
    english_lexicon = _load_english_lexicon()
    return english_lexicon.get(word.upper())


def english_word_exists(word: str) -> bool:
    """
    檢查英文詞彙是否存在於字典中。

    Args:
        word: 英文詞彙（會自動轉大寫）

    Returns:
        是否存在
    """
    english_lexicon = _load_english_lexicon()
    return word.upper() in english_lexicon


def get_english_lexicon_stats() -> dict[str, int]:
    """
    取得英文字典的統計資訊。

    Returns:
        統計資訊字典
    """
    english_lexicon = _load_english_lexicon()

    if not english_lexicon:
        return {"total_words": 0}

    return {
        "total_words": len(english_lexicon),
        "max_word_length": max(len(w) for w in english_lexicon.keys()),
    }


# =============================================================================
# 發音查詢功能
# =============================================================================


def get_pronunciation(
    word: str,
    dialect: DialectType = "客語_四縣",
    pronunciation_type: PronunciationType = "ipa",
) -> list[str] | None:
    """
    查詢單一詞彙的發音。

    Args:
        word: 詞彙
        dialect: 腔調名稱
        pronunciation_type: 發音格式 ("ipa" 或 "pinyin")

    Returns:
        發音列表，若詞彙不存在則回傳 None

    Example:
        >>> get_pronunciation("天公", "客語_四縣", "ipa")
        ['tʰ-ien_55 k-uŋ_55']
    """
    lexicon = _get_lexicon(dialect, pronunciation_type)
    return lexicon.get(word)


def get_pronunciation_all_dialects(
    word: str, pronunciation_type: PronunciationType = "ipa"
) -> dict[str, list[str] | None]:
    """
    查詢詞彙在所有腔調中的發音。

    Args:
        word: 詞彙
        pronunciation_type: 發音格式

    Returns:
        各腔調的發音字典

    Example:
        >>> results = get_pronunciation_all_dialects("天公")
        >>> for dialect, pron in results.items():
        ...     print(f"{dialect}: {pron}")
    """
    results = {}
    for dialect in DIALECTS:
        results[dialect] = get_pronunciation(word, dialect, pronunciation_type)
    return results


# =============================================================================
# 斷詞 + 發音功能
# =============================================================================


def segment_with_pronunciation(
    text: str,
    dialect: DialectType = "客語_四縣",
    pronunciation_type: PronunciationType = "ipa",
    include_english: bool = False,
) -> list[dict[str, str | list[str] | None]]:
    """
    斷詞並附帶發音資訊。

    Args:
        text: 要斷詞的文本
        dialect: 腔調名稱
        pronunciation_type: 發音格式
        include_english: 是否包含英文詞典

    Returns:
        包含詞彙和發音的字典列表

    Example:
        >>> results = segment_with_pronunciation("天公落水", "客語_四縣")
        >>> for item in results:
        ...     print(f"{item['word']}: {item['pronunciation']}")
    """
    words = run_jieba(text, dialect, include_english)
    results = []
    for word in words:
        pron = get_pronunciation(word, dialect, pronunciation_type)
        results.append({"word": word, "pronunciation": pron})
    return results


def text_to_pronunciation(
    text: str,
    dialect: DialectType = "客語_四縣",
    pronunciation_type: PronunciationType = "ipa",
    separator: str = " ",
    unknown_marker: str = "?",
    include_english: bool = False,
) -> str:
    """
    將文本轉換為發音字串。

    Args:
        text: 要轉換的文本
        dialect: 腔調名稱
        pronunciation_type: 發音格式
        separator: 詞彙間的分隔符
        unknown_marker: 未知詞彙的標記
        include_english: 是否包含英文詞典

    Returns:
        發音字串

    Example:
        >>> text_to_pronunciation("天公落水", "客語_四縣")
        'tʰ-ien_55 k-uŋ_55 l-ok_5 s-ui_31'
    """
    words = run_jieba(text, dialect, include_english)
    pronunciations = []

    for word in words:
        pron = get_pronunciation(word, dialect, pronunciation_type)
        if pron:
            # 取第一個發音（若有多個）
            pronunciations.append(pron[0])
        else:
            pronunciations.append(unknown_marker)

    return separator.join(pronunciations)


# =============================================================================
# 詞彙檢查功能
# =============================================================================


def word_exists(word: str, dialect: DialectType = "客語_四縣") -> bool:
    """
    檢查詞彙是否存在於指定腔調的字典中。

    Args:
        word: 詞彙
        dialect: 腔調名稱

    Returns:
        是否存在
    """
    lexicon = _get_lexicon(dialect, "ipa")
    return word in lexicon


def word_exists_in_dialects(word: str) -> dict[str, bool]:
    """
    檢查詞彙在各腔調中是否存在。

    Args:
        word: 詞彙

    Returns:
        各腔調的存在狀態

    Example:
        >>> word_exists_in_dialects("天公")
        {'客語_四縣': True, '客語_南四縣': True, ...}
    """
    results = {}
    for dialect in DIALECTS:
        results[dialect] = word_exists(word, dialect)
    return results


def find_unknown_words(
    text: str, dialect: DialectType = "客語_四縣", include_english: bool = False
) -> list[str]:
    """
    找出斷詞後不在字典中的詞彙。

    Args:
        text: 文本
        dialect: 腔調名稱
        include_english: 是否包含英文詞典

    Returns:
        未知詞彙列表
    """
    words = run_jieba(text, dialect, include_english)
    unknown = []
    for w in words:
        if not word_exists(w, dialect):
            # 如果包含英文，也檢查英文詞典
            if include_english and english_word_exists(w):
                continue
            unknown.append(w)
    return unknown


# =============================================================================
# 字典統計功能
# =============================================================================


def get_lexicon_stats(dialect: DialectType = "客語_四縣") -> dict[str, int]:
    """
    取得指定腔調字典的統計資訊。

    Args:
        dialect: 腔調名稱

    Returns:
        統計資訊字典

    Example:
        >>> stats = get_lexicon_stats("客語_四縣")
        >>> print(f"總詞數: {stats['total_words']}")
    """
    lexicon = _get_lexicon(dialect, "ipa")

    # 統計各詞長的數量
    length_counts: dict[int, int] = {}
    for word in lexicon.keys():
        length = len(word)
        length_counts[length] = length_counts.get(length, 0) + 1

    return {
        "total_words": len(lexicon),
        "max_word_length": max(len(w) for w in lexicon.keys()) if lexicon else 0,
        "single_char_words": length_counts.get(1, 0),
        "two_char_words": length_counts.get(2, 0),
        "three_char_words": length_counts.get(3, 0),
        "four_plus_char_words": sum(
            count for length, count in length_counts.items() if length >= 4
        ),
    }


def get_all_lexicon_stats() -> dict[str, dict[str, int]]:
    """
    取得所有腔調字典的統計資訊。

    Returns:
        各腔調的統計資訊
    """
    return {dialect: get_lexicon_stats(dialect) for dialect in DIALECTS}


# =============================================================================
# 腔調比較功能
# =============================================================================


def compare_dialects(word: str) -> dict[str, dict[str, list[str] | None]]:
    """
    比較同一詞彙在不同腔調中的發音差異。

    Args:
        word: 詞彙

    Returns:
        各腔調的 IPA 和拼音發音

    Example:
        >>> compare_dialects("天公")
    """
    results = {}
    for dialect in DIALECTS:
        results[dialect] = {
            "ipa": get_pronunciation(word, dialect, "ipa"),
            "pinyin": get_pronunciation(word, dialect, "pinyin"),
        }
    return results


def find_common_words(*dialects: str) -> set[str]:
    """
    找出多個腔調共有的詞彙。

    Args:
        *dialects: 腔調名稱（至少 2 個）

    Returns:
        共有詞彙集合

    Example:
        >>> common = find_common_words("客語_四縣", "客語_海陸")
        >>> print(f"共有詞彙數: {len(common)}")
    """
    if len(dialects) < 2:
        raise ValueError("至少需要指定 2 個腔調")

    # 取得第一個腔調的詞彙集合
    common = set(_get_lexicon(dialects[0], "ipa").keys())

    # 與其他腔調取交集
    for dialect in dialects[1:]:
        common &= set(_get_lexicon(dialect, "ipa").keys())

    return common


def find_unique_words(dialect: DialectType) -> set[str]:
    """
    找出某腔調獨有的詞彙（其他腔調都沒有的）。

    Args:
        dialect: 腔調名稱

    Returns:
        獨有詞彙集合
    """
    target_words = set(_get_lexicon(dialect, "ipa").keys())

    # 收集其他腔調的所有詞彙
    other_words: set[str] = set()
    for d in DIALECTS:
        if d != dialect:
            other_words |= set(_get_lexicon(d, "ipa").keys())

    return target_words - other_words


# =============================================================================
# 快取管理
# =============================================================================


def clear_tokenizer_cache() -> None:
    """
    清除所有 Tokenizer 快取。

    這會強制下次呼叫時重新建立 Tokenizer。
    通常只在需要重新載入詞典時使用。
    """
    global _tokenizers
    _tokenizers = {}


def get_cached_tokenizers() -> list[str]:
    """
    取得目前已快取的 Tokenizer 列表。

    Returns:
        快取 key 列表

    Example:
        >>> get_cached_tokenizers()
        ['客語_四縣', '客語_四縣_en', '客語_海陸']
    """
    return list(_tokenizers.keys())


# =============================================================================
# 主程式（測試用）
# =============================================================================


if __name__ == "__main__":
    test_text = "天公落水"

    print(f"測試文本: {test_text}")
    print("=" * 50)

    # 1. 基本斷詞
    print("\n【基本斷詞】")
    for dialect in DIALECTS:
        words = run_jieba(test_text, dialect)
        print(f"  {dialect}: {words}")

    # 2. 斷詞 + 發音
    print("\n【斷詞 + IPA 發音】(客語_四縣)")
    results = segment_with_pronunciation(test_text, "客語_四縣", "ipa")
    for item in results:
        print(f"  {item['word']}: {item['pronunciation']}")

    # 3. 文本轉發音
    print("\n【文本轉發音】")
    pron = text_to_pronunciation(test_text, "客語_四縣", "ipa")
    print(f"  IPA: {pron}")
    pron = text_to_pronunciation(test_text, "客語_四縣", "pinyin")
    print(f"  拼音: {pron}")

    # 4. 字典統計
    print("\n【字典統計】")
    for dialect in DIALECTS:
        stats = get_lexicon_stats(dialect)
        print(f"  {dialect}: {stats['total_words']} 詞")

    # 5. 腔調比較
    print("\n【「天公」各腔調發音比較】")
    comparison = compare_dialects("天公")
    for dialect, prons in comparison.items():
        if prons["ipa"]:
            print(f"  {dialect}: {prons['ipa'][0]}")

    # 6. 英文詞典測試
    print("\n【英文詞典測試】")
    en_stats = get_english_lexicon_stats()
    print(f"  英文詞典總詞數: {en_stats.get('total_words', 0)}")

    test_en_words = ["HELLO", "WORLD", "ABC"]
    for word in test_en_words:
        pron = get_english_pronunciation(word)
        print(f"  {word}: {pron}")

    # 7. 中英混合斷詞測試
    print("\n【中英混合斷詞測試】")
    mixed_text = "天公落水ABC"
    words_no_en = run_jieba(mixed_text, "客語_四縣", include_english=False)
    words_with_en = run_jieba(mixed_text, "客語_四縣", include_english=True)
    print(f"  文本: {mixed_text}")
    print(f"  不含英文: {words_no_en}")
    print(f"  包含英文: {words_with_en}")

    # 8. Tokenizer 快取測試
    print("\n【Tokenizer 快取測試】")
    print(f"  已快取的 Tokenizer: {get_cached_tokenizers()}")

    # 9. 擴展漢字測試
    print("\n【擴展漢字測試】")
    ext_chars = ["𦤦", "𱱿", "󿕅", "𫠛"]
    for char in ext_chars:
        code = f"U+{ord(char):05X}"
        words = run_jieba(f"測試{char}字", "客語_四縣")
        print(f"  {char} ({code}): {words}")
