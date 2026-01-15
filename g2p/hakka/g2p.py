"""
Author: Hung-Shin Lee & Li-Wei Chen
Apache 2.0
"""

import json
import re
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal, get_args

import jieba

jieba.re_han_default = re.compile(
    r"(["
    r"\u2e80-\u9fff"  # CJK 基本區域
    r"\uf900-\ufaff"  # CJK 相容漢字
    r"\U00020000-\U000323af"  # CJK 擴展 B ~ H
    r"\ue000-\uf8ff"  # 私用區
    r"\U000f0000-\U0010fffd"  # 私用區補充 A & B
    r"a-zA-Z0-9"  # 英文字母、數字
    r"+#&\.\_%\-'"  # 常見符號
    r"]+)",
    re.U,
)

# 模組路徑
MODULE_DIR = Path(__file__).parent
LEXICON_DIR = MODULE_DIR.parent / "lexicon"
SHARE_DIR = MODULE_DIR.parent / "share"

# 語言類型
LangGroupType = Literal[
    "hak_sx",
    "hak_nsx",
    "hak_hl",
    "hak_dp",
    "hak_rp",
    "hak_za",
]

# 支援的語言列表
LANG_GROUPS = list(get_args(LangGroupType))

# 發音格式類型
PronunciationType = Literal["ipa", "pinyin"]

# 支援的發音格式
PRONUNCIATIONS = list(get_args(PronunciationType))

# 標點符號列表
MARKERS = {"，", "。", "？", "！"}

# 半型轉全型標點對照表
MARKER_HALF_TO_FULL = {",": "，", "?": "？", "!": "！", ".": "。"}


_tokenizers: dict[str, jieba.Tokenizer] = {}
_lexicons: dict[str, dict[str, list[str]]] = {}
_variant_map: dict[str, str] | None = None

# 正規化使用的 Regex Pattern
_NORMALIZE_PATTERN = (
    r"[^"
    r"\u2e80-\u9fff"  # CJK 部首、基本漢字
    r"\uf900-\ufaff"  # CJK 相容漢字
    r"\U00020000-\U000323af"  # CJK 擴展 B ~ H（臺客語常用外字）
    r"\ue000-\uf8ff"  # 私用區 (PUA)
    r"\U000f0000-\U0010fffd"  # 私用區補充 A & B（臺客語造字）
    r"a-zA-Z0-9\s，。？！]"
)
RE_NORMALIZE = re.compile(_NORMALIZE_PATTERN)
RE_WHITESPACE = re.compile(r"\s+|\t+")


# =============================================================================
# 斷詞
# =============================================================================


def _load_lexicon(
    lang_group: LangGroupType, include_eng: bool = False
) -> dict[str, list[str]]:
    lexicon = {}
    for pronunciation_type in PRONUNCIATIONS:
        lexicon_path = LEXICON_DIR / pronunciation_type / f"{lang_group}.json"

        if not lexicon_path.exists():
            raise FileNotFoundError(f"找不到語言字典檔案: {lexicon_path}")

        with lexicon_path.open() as file:
            lexicon[pronunciation_type] = json.load(file)

        if include_eng:
            for eng_lexicon_path in (LEXICON_DIR / pronunciation_type).glob(
                "eng_*.json"
            ):
                with eng_lexicon_path.open() as file:
                    eng_lexicon = json.load(file)

                for word in eng_lexicon:
                    if word not in lexicon[pronunciation_type]:
                        lexicon[pronunciation_type][word] = eng_lexicon[word]
                    else:
                        for pron in eng_lexicon[word]:
                            if pron not in lexicon[pronunciation_type][word]:
                                lexicon[pronunciation_type][word].append(pron)

    return lexicon


def _get_lexicon(
    lang_group: str,
    include_eng: bool = False,
) -> dict[str, list[str]]:
    if lang_group in _lexicons:
        return _lexicons[lang_group]

    _lexicons[lang_group] = _load_lexicon(lang_group, include_eng)

    return _lexicons[lang_group]


def _get_tokenizer(
    lang_group: str,
    pronunciation_type: PronunciationType = "ipa",
    include_eng: bool = False,
) -> jieba.Tokenizer:
    if lang_group not in LANG_GROUPS:
        raise ValueError(
            f"不支援的語言: {lang_group}\n支援的語言: {', '.join(LANG_GROUPS)}"
        )

    if lang_group not in _tokenizers:
        tokenizer = jieba.Tokenizer()

        lexicon = _get_lexicon(lang_group, include_eng)
        for word in lexicon[pronunciation_type].keys():
            freq = len(word) * 10000
            tokenizer.add_word(word, freq=freq)

        _tokenizers[lang_group] = tokenizer

    return _tokenizers[lang_group]


def init_tokenizer(
    pronunciation_type: PronunciationType = "ipa", include_eng: bool = False
) -> None:
    for lang_group in LANG_GROUPS:
        _get_tokenizer(
            lang_group, pronunciation_type=pronunciation_type, include_eng=include_eng
        )


def clear_tokenizer_cache() -> None:
    global _tokenizers
    _tokenizers = {}


def get_cached_tokenizers() -> list[str]:
    return list(_tokenizers.keys())


def run_jieba(
    text: str,
    lang_group: LangGroupType = "hak_sx",
    pronunciation_type: PronunciationType = "ipa",
    return_oovs: bool = True,
) -> tuple[list[str], list[str]]:
    if lang_group not in _tokenizers:
        raise ValueError(
            f"Tokenizer for '{lang_group}' not initialized. "
            f"Call init_tokenizer('{lang_group}') first."
        )

    tokenizer = _get_tokenizer(lang_group)
    result = list(tokenizer.cut(text, HMM=False))
    result = [x for x in result if x.strip()]
    oovs = []

    if return_oovs:
        lexicon = _lexicons[lang_group][pronunciation_type]

        for word in result:
            if word in MARKERS:
                continue

            if word not in lexicon:
                oovs.append(word)

    return result, oovs


# =============================================================================
# 發音
# =============================================================================


def get_pronunciation(
    word: str,
    lang_group: LangGroupType = "hak_sx",
    pronunciation_type: PronunciationType = "ipa",
) -> list[str] | None:
    return _lexicons[lang_group][pronunciation_type].get(word, None)


def segment_with_pronunciation(
    text: str, lang_group: LangGroupType = "hak_sx"
) -> list[dict[str, str | list[str] | None]]:
    words, oovs = run_jieba(text, lang_group, return_oovs=True)
    results = []
    for word in words:
        pron = get_pronunciation(word, lang_group)
        results.append({"word": word, "pronunciation": pron})
    return results


def text_to_pronunciation(
    text: str,
    lang_group: LangGroupType = "hak_sx",
    separator: str = " ",
    unknown_marker: str = "?",
) -> str:
    words, oovs = run_jieba(text, lang_group)
    pronunciations = []

    for word in words:
        pron = get_pronunciation(word, lang_group)
        if pron:
            pronunciations.append(pron[0])
        else:
            pronunciations.append(unknown_marker)

    return separator.join(pronunciations)

    words, oovs = run_jieba(text, lang_group)
    pronunciations = []

    for word in words:
        pron = get_pronunciation(word, lang_group)
        if pron:
            # 取第一個發音（若有多個）
            pronunciations.append(pron[0])
        else:
            pronunciations.append(unknown_marker)

    return separator.join(pronunciations)


# =============================================================================
# G2P
# =============================================================================


@dataclass
class G2PResult:
    pronunciations: list[str] = field(default_factory=list)
    unknown_words: list[str] = field(default_factory=list)
    details: list[dict[str, str | None]] = field(default_factory=list)

    @property
    def has_unknown(self) -> bool:
        return len(self.unknown_words) > 0

    def __str__(self) -> str:
        return " ".join(self.pronunciations)


def _load_variant_map() -> dict[str, str]:
    global _variant_map
    if _variant_map is None:
        variant_map_path = SHARE_DIR / "variant_map.json"
        if variant_map_path.exists():
            with variant_map_path.open() as file:
                _variant_map = json.load(file)
        else:
            _variant_map = {}
    return _variant_map


def apply_variant_map(text: str) -> str:
    variant_map = _load_variant_map()
    if not variant_map:
        return text

    result = []
    for char in text:
        result.append(variant_map.get(char, char))
    return "".join(result)


def normalize_text(text: str, use_variant_map: bool = True) -> str:
    # 1. Unicode NFKC 正規化（全形轉半形、相容字元轉換）
    text = text.upper()
    text = unicodedata.normalize("NFKC", text)

    # 2. 半形標點轉全形標點
    for half, full in MARKER_HALF_TO_FULL.items():
        text = text.replace(half, full)

    # 3. 移除不需要的標點和特殊字元
    # 保留: 中文字、數字、英文字母、空格、指定標點（，。？！）
    text = RE_NORMALIZE.sub("", text)

    # 4. 移除多餘空白與 Tab（多個空白合併為一個）
    text = RE_WHITESPACE.sub(" ", text)

    # 5. 去除頭尾空白
    text = text.strip()

    # 6. 套用異體字對照表
    if use_variant_map:
        text = apply_variant_map(text)

    return text


def g2p(
    text: str,
    lang_group: LangGroupType = "hak_sx",
    pronunciation_type: PronunciationType = "ipa",
    unknown_token: str | None = None,
    keep_unknown: bool = True,
    use_variant_map: bool = True,
    include_eng: bool = False,
) -> G2PResult:
    # 1. 正規化文字
    normalized_text = normalize_text(text, use_variant_map=use_variant_map)

    if not normalized_text:
        return G2PResult()

    # 2. 斷詞
    words, oovs = run_jieba(
        normalized_text, lang_group, pronunciation_type, return_oovs=True
    )

    # 3. 載入詞典
    lexicon = _get_lexicon(lang_group, include_eng=include_eng)

    # 4. 查詢發音
    pronunciations: list[str] = []
    details: list[dict[str, str | None]] = []

    for word in words:
        if word in MARKERS:
            pronunciations.append(word)
            details.append({"word": word, "pronunciation": word})
            continue

        pron_list = lexicon[pronunciation_type].get(word)

        if pron_list:
            # 取第一個發音
            pron = pron_list[0]
            pronunciations.append(pron)
            details.append({"word": word, "pronunciation": pron})
        else:
            # 記錄未知詞彙
            details.append({"word": word, "pronunciation": None})

            # 處理未知詞彙的輸出
            if keep_unknown:
                if unknown_token is not None:
                    pronunciations.append(unknown_token)
                else:
                    pronunciations.append(word)

    return G2PResult(
        pronunciations=pronunciations,
        unknown_words=oovs,
        details=details,
    )


if __name__ == "__main__":
    text = (
        "雲林縣崙背鄉今年个鄉長盃卡拉 OK 比賽，參加比賽个長青組假假都係唱學老歌，"
        "唱个老人家假假都係會講詔安客話，嗄無唱詔安客家歌，參加比賽个選手就講，"
        "佢乜蓋想愛唱啊，蓋無結煞受著比賽硬體設備个限制無客家歌好唱。"
    )

    lang_group = "hak_sx"

    init_tokenizer()
    result = g2p(text, lang_group)
    print(result)
