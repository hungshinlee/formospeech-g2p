"""
客語 G2P (Grapheme-to-Phoneme) 模組

將客語文字轉換為發音序列。

使用方式:
    from formog2p import g2p

    # 基本用法
    result = g2p("天公落水", "客語_四縣", "ipa")
    print(result)  # ['tʰ-ien_24 k-uŋ_24', 'l-ok_5 s-ui_31']
"""

import json
import re
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path

from .word_segment import (
    DIALECTS,
    DialectType,
    PronunciationType,
    _get_lexicon,
    _load_english_lexicon,
    run_jieba,
)

# 模組路徑
MODULE_DIR = Path(__file__).parent
DATA_DIR = MODULE_DIR / "data"
SHARE_DIR = DATA_DIR / "hakka" / "share"

# 標點符號（視為 known token）
PUNCTUATIONS = {"，", "。", "？", "！"}

# 半形轉全形標點對照表
PUNCT_HALF_TO_FULL = {
    ",": "，",
    "?": "？",
    "!": "！",
    ".": "。",
}

# 異體字對照表（延遲載入）
_variant_map: dict[str, str] | None = None


def _load_variant_map() -> dict[str, str]:
    """載入異體字對照表。"""
    global _variant_map
    if _variant_map is None:
        variant_map_path = SHARE_DIR / "variant_map.json"
        if variant_map_path.exists():
            with open(variant_map_path, "r", encoding="utf-8") as f:
                _variant_map = json.load(f)
        else:
            _variant_map = {}
    return _variant_map


def apply_variant_map(text: str) -> str:
    """
    套用異體字對照表，將異體字轉換為標準字。

    Args:
        text: 輸入文字

    Returns:
        轉換後的文字

    Example:
        >>> apply_variant_map("台灣")
        '臺灣'
        >>> apply_variant_map("温泉")
        '溫泉'
    """
    variant_map = _load_variant_map()
    if not variant_map:
        return text

    # 逐字替換
    result = []
    for char in text:
        result.append(variant_map.get(char, char))
    return "".join(result)


def normalize(
    text: str, use_variant_map: bool = True, include_english: bool = False
) -> str:
    """
    正規化文字。

    處理項目:
        1. Unicode NFKC 正規化（全形轉半形等）
        2. 半形標點轉全形標點（, ? ! . → ，？！。）
        3. 移除不需要的標點符號（保留 ，。？！）
        4. 移除多餘空白
        5. 套用異體字對照表（可選）
        6. 如果包含英文，將文本轉為大寫
        7. 保留中文字、數字、英文字母、指定標點

    Args:
        text: 原始文字
        use_variant_map: 是否套用異體字對照表，預設為 True
        include_english: 是否包含英文（會將文本轉為大寫），預設為 False

    Returns:
        正規化後的文字

    Example:
        >>> normalize("天公落水！！")
        '天公落水！！'
        >>> normalize("天公落水!!")
        '天公落水！！'
        >>> normalize("台灣")
        '臺灣'
        >>> normalize("Hello World", include_english=True)
        'HELLO WORLD'
    """
    # 1. Unicode NFKC 正規化（全形轉半形、相容字元轉換）
    text = unicodedata.normalize("NFKC", text)

    # 2. 半形標點轉全形標點
    for half, full in PUNCT_HALF_TO_FULL.items():
        text = text.replace(half, full)

    # 3. 移除不需要的標點和特殊字元
    # 保留: 中文字、數字、英文字母、空格、指定標點（，。？！）
    # Unicode 範圍說明:
    #   - \u2e80-\u9fff   : CJK 部首、基本漢字
    #   - \uf900-\ufaff   : CJK 相容漢字
    #   - \U00020000-\U000323af : CJK 擴展 B ~ H（臺客語常用外字）
    #   - \ue000-\uf8ff   : 私用區 (PUA)
    #   - \U000f0000-\U0010fffd : 私用區補充 A & B（臺客語造字）
    pattern = (
        r"[^"
        r"\u2e80-\u9fff"
        r"\uf900-\ufaff"
        r"\U00020000-\U000323af"
        r"\ue000-\uf8ff"
        r"\U000f0000-\U0010fffd"
        r"a-zA-Z0-9\s，。？！]"
    )
    text = re.sub(pattern, "", text)

    # 4. 移除多餘空白（多個空白合併為一個）
    text = re.sub(r"\s+", " ", text)

    # 5. 去除頭尾空白
    text = text.strip()

    # 6. 套用異體字對照表
    if use_variant_map:
        text = apply_variant_map(text)

    # 7. 如果包含英文，將文本轉為大寫（英文詞典的 key 是大寫）
    if include_english:
        text = text.upper()

    return text


@dataclass
class G2PResult:
    """
    G2P 轉換結果。

    Attributes:
        pronunciations: 發音序列
        unknown_words: 未知詞彙列表
        details: 詳細的詞彙與發音對應
    """

    pronunciations: list[str] = field(default_factory=list)
    unknown_words: list[str] = field(default_factory=list)
    details: list[dict[str, str | None]] = field(default_factory=list)

    @property
    def has_unknown(self) -> bool:
        """是否有未知詞彙"""
        return len(self.unknown_words) > 0

    def __str__(self) -> str:
        return " ".join(self.pronunciations)


def g2p(
    text: str,
    dialect: DialectType = "客語_四縣",
    pronunciation_type: PronunciationType = "ipa",
    unknown_token: str | None = None,
    keep_unknown: bool = True,
    use_variant_map: bool = True,
    include_english: bool = False,
) -> G2PResult:
    """
    將文字轉換為發音序列 (Grapheme-to-Phoneme)。

    流程:
        1. 正規化文字 (normalize)，包含異體字轉換
        2. 如果包含英文，將文本轉為大寫
        3. 使用 Jieba 斷詞
        4. 查詢每個詞的發音（取列表中的第一個）
        5. 標點符號（，。？！）視為 known token，直接作為發音
        6. 如果是英文詞彙且 pronunciation_type 為 ipa，查詢英文詞典
        7. 回傳 G2PResult（包含發音序列與未知詞彙）

    Args:
        text: 輸入文字
        dialect: 腔調名稱，預設為「客語_四縣」
        pronunciation_type: 發音格式 ("ipa" 或 "pinyin")
        unknown_token: 未知詞彙的替代符號，若為 None 則使用原詞
        keep_unknown: 是否保留未知詞彙，若為 False 則跳過
        use_variant_map: 是否套用異體字對照表，預設為 True
        include_english: 是否包含英文發音（僅支援 ipa），預設為 False

    Returns:
        G2PResult 物件，包含:
            - pronunciations: 發音序列
            - unknown_words: 未知詞彙列表
            - details: 詳細的詞彙與發音對應
            - has_unknown: 是否有未知詞彙

    Example:
        >>> result = g2p("天公落水", "客語_四縣", "ipa")
        >>> result.pronunciations
        ['tʰ-ien_24 k-uŋ_24', 'l-ok_5 s-ui_31']

        >>> result = g2p("天公落水HELLO", "客語_四縣", "ipa", include_english=True)
        >>> result.pronunciations
        ['tʰ-ien_24 k-uŋ_24', 'l-ok_5 s-ui_31', 'h ə l oʊ']
    """
    # 1. 正規化（包含異體字轉換，以及英文大寫轉換）
    normalized_text = normalize(
        text, use_variant_map=use_variant_map, include_english=include_english
    )

    if not normalized_text:
        return G2PResult()

    # 2. 斷詞
    words = run_jieba(normalized_text, dialect, include_english=include_english)

    # 3. 載入詞典
    lexicon = _get_lexicon(dialect, pronunciation_type)

    # 如果包含英文且發音類型是 ipa，載入英文詞典
    english_lexicon = None
    if include_english and pronunciation_type == "ipa":
        english_lexicon = _load_english_lexicon()

    # 4. 查詢發音
    pronunciations: list[str] = []
    unknown_words: list[str] = []
    details: list[dict[str, str | None]] = []

    for word in words:
        # 跳過空白
        if not word.strip():
            continue

        # 標點符號視為 known token
        if word in PUNCTUATIONS:
            pronunciations.append(word)
            details.append({"word": word, "pronunciation": word})
            continue

        # 先查客語詞典
        pron_list = lexicon.get(word)

        if pron_list:
            # 取第一個發音
            pron = pron_list[0]
            pronunciations.append(pron)
            details.append({"word": word, "pronunciation": pron})
        elif english_lexicon and word in english_lexicon:
            # 查英文詞典（key 已經是大寫）
            pron = english_lexicon[word][0]
            pronunciations.append(pron)
            details.append({"word": word, "pronunciation": pron})
        else:
            # 記錄未知詞彙
            unknown_words.append(word)
            details.append({"word": word, "pronunciation": None})

            # 處理未知詞彙的輸出
            if keep_unknown:
                if unknown_token is not None:
                    pronunciations.append(unknown_token)
                else:
                    pronunciations.append(word)

    return G2PResult(
        pronunciations=pronunciations,
        unknown_words=unknown_words,
        details=details,
    )


def g2p_simple(
    text: str,
    dialect: DialectType = "客語_四縣",
    pronunciation_type: PronunciationType = "ipa",
    unknown_token: str | None = None,
    keep_unknown: bool = True,
    use_variant_map: bool = True,
    include_english: bool = False,
) -> list[str]:
    """
    簡化版 G2P，只回傳發音序列。

    Args:
        text: 輸入文字
        dialect: 腔調名稱
        pronunciation_type: 發音格式
        unknown_token: 未知詞彙的替代符號
        keep_unknown: 是否保留未知詞彙
        use_variant_map: 是否套用異體字對照表
        include_english: 是否包含英文發音

    Returns:
        發音序列列表

    Example:
        >>> g2p_simple("天公落水", "客語_四縣", "ipa")
        ['tʰ-ien_24 k-uŋ_24', 'l-ok_5 s-ui_31']
    """
    result = g2p(
        text,
        dialect,
        pronunciation_type,
        unknown_token,
        keep_unknown,
        use_variant_map,
        include_english,
    )
    return result.pronunciations


def g2p_string(
    text: str,
    dialect: DialectType = "客語_四縣",
    pronunciation_type: PronunciationType = "ipa",
    separator: str = " ",
    unknown_token: str = "?",
    keep_unknown: bool = True,
    use_variant_map: bool = True,
    include_english: bool = False,
) -> str:
    """
    將文字轉換為發音字串。

    與 g2p() 類似，但回傳合併後的字串而非 G2PResult。

    Args:
        text: 輸入文字
        dialect: 腔調名稱
        pronunciation_type: 發音格式
        separator: 詞彙間的分隔符
        unknown_token: 未知詞彙的替代符號
        keep_unknown: 是否保留未知詞彙
        use_variant_map: 是否套用異體字對照表
        include_english: 是否包含英文發音

    Returns:
        發音字串

    Example:
        >>> g2p_string("天公落水", "客語_四縣", "ipa")
        'tʰ-ien_24 k-uŋ_24 l-ok_5 s-ui_31'
    """
    result = g2p(
        text,
        dialect,
        pronunciation_type,
        unknown_token=unknown_token,
        keep_unknown=keep_unknown,
        use_variant_map=use_variant_map,
        include_english=include_english,
    )
    return separator.join(result.pronunciations)


def batch_g2p(
    texts: list[str],
    dialect: DialectType = "客語_四縣",
    pronunciation_type: PronunciationType = "ipa",
    unknown_token: str | None = None,
    keep_unknown: bool = True,
    use_variant_map: bool = True,
    include_english: bool = False,
) -> list[G2PResult]:
    """
    批次處理多個文字。

    Args:
        texts: 文字列表
        dialect: 腔調名稱
        pronunciation_type: 發音格式
        unknown_token: 未知詞彙的替代符號
        keep_unknown: 是否保留未知詞彙
        use_variant_map: 是否套用異體字對照表
        include_english: 是否包含英文發音

    Returns:
        G2PResult 列表

    Example:
        >>> results = batch_g2p(["天公落水", "日頭落山"], "客語_四縣", "ipa")
        >>> for r in results:
        ...     print(r.pronunciations)
    """
    return [
        g2p(
            text,
            dialect,
            pronunciation_type,
            unknown_token,
            keep_unknown,
            use_variant_map,
            include_english,
        )
        for text in texts
    ]


# =============================================================================
# 主程式（測試用）
# =============================================================================


if __name__ == "__main__":
    print("=" * 60)
    print("G2P 測試")
    print("=" * 60)

    # 測試異體字轉換
    print("\n【異體字轉換測試】")
    variant_tests = [
        ("台灣", "臺灣"),
        ("温泉", "溫泉"),
        ("强大", "強大"),
        ("靓女", "靚女"),
        ("您好", "你好"),
    ]
    for original, expected in variant_tests:
        result = apply_variant_map(original)
        status = "✓" if result == expected else "✗"
        print(f"  {status} {original} → {result} (預期: {expected})")

    # 測試正規化（含英文大寫）
    print("\n【正規化測試（含英文大寫轉換）】")
    test_cases = [
        ("Hello World", False, "Hello World"),
        ("Hello World", True, "HELLO WORLD"),
        ("天公落水abc", False, "天公落水abc"),
        ("天公落水abc", True, "天公落水ABC"),
    ]
    for text, include_en, expected in test_cases:
        normalized = normalize(text, include_english=include_en)
        status = "✓" if normalized == expected else "✗"
        print(f"  {status} {repr(text)} (en={include_en}) → {repr(normalized)}")

    # 測試 G2P
    print("\n【G2P 測試（不含英文）】")
    test_text = "天公落水，好靚！"
    result = g2p(test_text, "客語_四縣", "ipa")

    print(f"  原始文字: {test_text}")
    print(f"  發音序列: {result.pronunciations}")
    print(f"  未知詞彙: {result.unknown_words}")

    # 測試中英混合 G2P
    print("\n【中英混合 G2P 測試】")
    test_text = "天公落水Hello World"

    print(f"  原始文字: {test_text}")

    # 不含英文
    result = g2p(test_text, "客語_四縣", "ipa", include_english=False)
    print(f"  不含英文: {result.pronunciations}")
    print(f"  未知詞彙: {result.unknown_words}")

    # 包含英文
    result = g2p(test_text, "客語_四縣", "ipa", include_english=True)
    print(f"  包含英文: {result.pronunciations}")
    print(f"  未知詞彙: {result.unknown_words}")

    # 測試純英文
    print("\n【純英文 G2P 測試】")
    test_text = "Hello World ABC"
    result = g2p(test_text, "客語_四縣", "ipa", include_english=True)
    print(f"  原始文字: {test_text}")
    print(f"  正規化後: {normalize(test_text, include_english=True)}")
    print(f"  發音序列: {result.pronunciations}")
    print(f"  未知詞彙: {result.unknown_words}")

    # 各腔調測試
    print("\n" + "=" * 60)
    print("各腔調 G2P 結果")
    print("=" * 60)

    test_text = "天公落水！"
    for dialect in DIALECTS:
        result = g2p(test_text, dialect, "ipa")
        unknown_info = f" (未知: {result.unknown_words})" if result.has_unknown else ""
        print(f"{dialect}: {result}{unknown_info}")
