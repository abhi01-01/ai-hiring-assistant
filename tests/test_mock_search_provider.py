import asyncio

from api.services import search as search_module
from api.services.search import MockSearchProvider


def _search(**kwargs):
    provider = MockSearchProvider()
    defaults = dict(
        client=None,
        job_description="Backend engineer with Java and Spring Boot",
        job_role="Backend Engineer",
        company=None,
        per_page=10,
    )
    defaults.update(kwargs)
    return asyncio.run(provider.search_candidates(**defaults))


class TestMockCandidatePhoneNumbers:
    def test_every_candidate_has_a_distinct_phone_by_default(self, monkeypatch):
        monkeypatch.setattr(search_module.settings, "MOCK_CANDIDATE_PHONE", None)

        results = _search(per_page=100)

        phone_numbers = [candidate.phone_number for candidate in results]
        assert len(phone_numbers) == len(set(phone_numbers)), (
            "mock candidates must not share a phone number - HiringService "
            "upserts by phone_number, so a collision silently overwrites one "
            "candidate's identity with another's"
        )

    def test_mock_candidate_phone_only_overrides_top_ranked_result(self, monkeypatch):
        monkeypatch.setattr(search_module.settings, "MOCK_CANDIDATE_PHONE", "+911234500000")

        results = _search(per_page=100)

        assert results[0].phone_number == "+911234500000"
        other_numbers = [candidate.phone_number for candidate in results[1:]]
        assert "+911234500000" not in other_numbers
        assert len(other_numbers) == len(set(other_numbers))
