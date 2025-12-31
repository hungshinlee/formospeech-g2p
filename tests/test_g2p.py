"""G2P 功能測試"""

from formog2p import (
    G2PResult,
    apply_variant_map,
    g2p,
    g2p_simple,
    g2p_string,
    normalize,
)


class TestNormalize:
    """正規化功能測試"""

    def test_half_to_full_punctuation(self):
        """測試半形標點轉全形"""
        assert "，" in normalize("Hello,")
        assert "？" in normalize("Hello?")
        assert "！" in normalize("Hello!")

    def test_variant_map(self):
        """測試異體字轉換"""
        result = normalize("台灣")
        assert result == "臺灣"

    def test_english_uppercase(self):
        """測試英文大寫轉換"""
        result = normalize("Hello World", include_english=True)
        assert result == "HELLO WORLD"


class TestApplyVariantMap:
    """異體字轉換測試"""

    def test_common_variants(self):
        """測試常見異體字"""
        assert apply_variant_map("台") == "臺"
        assert apply_variant_map("台灣") == "臺灣"


class TestG2P:
    """G2P 轉換測試"""

    def test_basic_g2p(self):
        """測試基本 G2P 轉換"""
        result = g2p("天公", "客語_四縣", "ipa")
        assert isinstance(result, G2PResult)
        assert len(result.pronunciations) > 0

    def test_g2p_with_punctuation(self):
        """測試含標點的 G2P"""
        result = g2p("天公！", "客語_四縣", "ipa")
        assert "！" in result.pronunciations

    def test_g2p_unknown_word(self):
        """測試未知詞彙處理"""
        result = g2p("XYZ未知詞", "客語_四縣", "ipa")
        assert result.has_unknown
        assert len(result.unknown_words) > 0

    def test_g2p_all_dialects(self):
        """測試所有腔調"""
        from formog2p import DIALECTS

        for dialect in DIALECTS:
            result = g2p("天公", dialect, "ipa")
            assert isinstance(result, G2PResult)


class TestG2PSimple:
    """簡化版 G2P 測試"""

    def test_returns_list(self):
        """測試回傳列表"""
        result = g2p_simple("天公", "客語_四縣", "ipa")
        assert isinstance(result, list)


class TestG2PString:
    """G2P 字串版測試"""

    def test_returns_string(self):
        """測試回傳字串"""
        result = g2p_string("天公", "客語_四縣", "ipa")
        assert isinstance(result, str)
