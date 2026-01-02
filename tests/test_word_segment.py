"""斷詞功能測試"""

from formog2p.hakka import (
    DIALECTS,
    english_word_exists,
    find_unknown_words,
    get_english_pronunciation,
    get_lexicon_stats,
    get_pronunciation,
    run_jieba,
    word_exists,
)


class TestRunJieba:
    """Jieba 斷詞測試"""

    def test_basic_segmentation(self):
        """測試基本斷詞"""
        words = run_jieba("天公落水", "客語_四縣")
        assert isinstance(words, list)
        assert len(words) > 0

    def test_all_dialects(self):
        """測試所有腔調斷詞"""
        for dialect in DIALECTS:
            words = run_jieba("天公", dialect)
            assert isinstance(words, list)


class TestGetPronunciation:
    """發音查詢測試"""

    def test_known_word(self):
        """測試已知詞彙"""
        pron = get_pronunciation("天公", "客語_四縣", "ipa")
        assert pron is not None
        assert isinstance(pron, list)
        assert len(pron) > 0

    def test_unknown_word(self):
        """測試未知詞彙"""
        pron = get_pronunciation("XYZABC", "客語_四縣", "ipa")
        assert pron is None


class TestWordExists:
    """詞彙檢查測試"""

    def test_exists(self):
        """測試存在的詞彙"""
        assert word_exists("天公", "客語_四縣") is True

    def test_not_exists(self):
        """測試不存在的詞彙"""
        assert word_exists("XYZABC", "客語_四縣") is False


class TestEnglish:
    """英文相關功能測試"""

    def test_english_word_exists(self):
        """測試英文詞彙存在檢查"""
        assert english_word_exists("HELLO") is True
        assert english_word_exists("hello") is True  # 應自動轉大寫

    def test_english_pronunciation(self):
        """測試英文發音查詢"""
        pron = get_english_pronunciation("hello")
        assert pron is not None
        assert isinstance(pron, list)


class TestLexiconStats:
    """詞典統計測試"""

    def test_stats_structure(self):
        """測試統計結構"""
        stats = get_lexicon_stats("客語_四縣")
        assert "total_words" in stats
        assert stats["total_words"] > 0


class TestFindUnknownWords:
    """未知詞彙查找測試"""

    def test_find_unknown(self):
        """測試找出未知詞彙"""
        unknown = find_unknown_words("天公XYZ", "客語_四縣")
        assert isinstance(unknown, list)
