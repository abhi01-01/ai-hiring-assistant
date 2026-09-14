from api.services.search import _extract_domain


class TestExtractDomain:
    def test_bare_domain_is_returned_as_is(self):
        assert _extract_domain("hunar.ai") == "hunar.ai"

    def test_full_url_is_normalized_to_bare_domain(self):
        assert _extract_domain("https://www.hunar.ai/careers") == "hunar.ai"

    def test_uppercase_is_lowercased(self):
        assert _extract_domain("WWW.HUNAR.AI") == "hunar.ai"

    def test_plain_company_name_returns_none(self):
        assert _extract_domain("Hunar AI") is None

    def test_blank_input_returns_none(self):
        assert _extract_domain("   ") is None
