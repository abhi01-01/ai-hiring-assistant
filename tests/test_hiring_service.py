from api.services.hiring import HiringService


class TestNormalizeStatus:
    def test_known_alias_maps_to_canonical_value(self):
        assert HiringService._normalize_status("queued") == "CREATED"
        assert HiringService._normalize_status("Complete") == "COMPLETED"
        assert HiringService._normalize_status("error") == "FAILED"

    def test_already_canonical_value_passes_through(self):
        assert HiringService._normalize_status("IN_PROGRESS") == "IN_PROGRESS"

    def test_unrecognized_value_is_upper_snake_cased_and_truncated(self):
        assert HiringService._normalize_status("some weird status") == "SOME_WEIRD_STATUS"
        long_value = "x" * 50
        assert len(HiringService._normalize_status(long_value)) == 40

    def test_missing_value_uses_default(self):
        assert HiringService._normalize_status(None, default="RECEIVED") == "RECEIVED"
        assert HiringService._normalize_status(None) == "UNKNOWN"


class TestSanitizeJobDescription:
    def test_strips_disallowed_characters(self):
        result = HiringService._sanitize_job_description("Need C++ dev 😀 asap!!", None)
        assert "😀" not in result
        assert "!!" not in result

    def test_falls_back_to_role_when_description_missing(self):
        result = HiringService._sanitize_job_description(None, "Backend Engineer")
        assert "Backend Engineer" in result

    def test_truncates_to_1000_characters(self):
        result = HiringService._sanitize_job_description("a" * 5000, None)
        assert len(result) == 1000


class TestExtractExternalCallId:
    def test_reads_top_level_call_id(self):
        assert HiringService._extract_external_call_id({"call_id": "abc123"}) == "abc123"

    def test_reads_nested_call_object(self):
        assert HiringService._extract_external_call_id({"call": {"id": "nested-1"}}) == "nested-1"

    def test_returns_none_when_nothing_matches(self):
        assert HiringService._extract_external_call_id({"unrelated": "value"}) is None
