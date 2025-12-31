"""
FormoG2P - 台灣本土語言 G2P 模組

提供客語斷詞、發音查詢、G2P 轉換功能。
"""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("formog2p")
except PackageNotFoundError:
    __version__ = "0.0.0.dev"

from .g2p import (
    PUNCTUATIONS,
    G2PResult,
    apply_variant_map,
    batch_g2p,
    g2p,
    g2p_simple,
    g2p_string,
    normalize,
)
from .word_segment import (
    DIALECTS,
    clear_tokenizer_cache,
    compare_dialects,
    english_word_exists,
    find_common_words,
    find_unique_words,
    find_unknown_words,
    get_all_lexicon_stats,
    get_cached_tokenizers,
    get_english_lexicon_stats,
    get_english_pronunciation,
    get_lexicon_stats,
    get_pronunciation,
    get_pronunciation_all_dialects,
    run_jieba,
    run_jieba_all_dialects,
    segment_with_pronunciation,
    text_to_pronunciation,
    word_exists,
    word_exists_in_dialects,
)

__all__ = [
    # 版本
    "__version__",
    # 常數
    "DIALECTS",
    "PUNCTUATIONS",
    # G2P 功能
    "G2PResult",
    "g2p",
    "g2p_simple",
    "g2p_string",
    "batch_g2p",
    "normalize",
    "apply_variant_map",
    # 斷詞功能
    "run_jieba",
    "run_jieba_all_dialects",
    # 發音查詢
    "get_pronunciation",
    "get_pronunciation_all_dialects",
    "segment_with_pronunciation",
    "text_to_pronunciation",
    # 英文功能
    "get_english_pronunciation",
    "english_word_exists",
    "get_english_lexicon_stats",
    # 詞彙檢查
    "word_exists",
    "word_exists_in_dialects",
    "find_unknown_words",
    # 統計
    "get_lexicon_stats",
    "get_all_lexicon_stats",
    # 腔調比較
    "compare_dialects",
    "find_common_words",
    "find_unique_words",
    # 快取管理
    "clear_tokenizer_cache",
    "get_cached_tokenizers",
]
