"""
客語模組 (Hakka Module)

提供客語斷詞、發音查詢、G2P 轉換功能。
"""

from .g2p import (
    MARKERS as PUNCTUATIONS,
    G2PResult,
    apply_variant_map,
    clear_tokenizer_cache,
    g2p,
    get_cached_tokenizers,
    get_pronunciation,
    init_tokenizer,
    normalize_text as normalize,
    run_jieba,
    segment_with_pronunciation,
    text_to_pronunciation,
)

__all__ = [
    "PUNCTUATIONS",
    "G2PResult",
    "g2p",
    "normalize",
    "apply_variant_map",
    "run_jieba",
    "get_pronunciation",
    "segment_with_pronunciation",
    "text_to_pronunciation",
    "clear_tokenizer_cache",
    "get_cached_tokenizers",
    "init_tokenizer",
]
