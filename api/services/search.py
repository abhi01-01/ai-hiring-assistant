import logging
import re
from abc import ABC, abstractmethod
from urllib.parse import urlencode

import httpx
from fastapi import HTTPException

from api.core.config import settings
from api.schemas import SearchCandidateResponse

logger = logging.getLogger(__name__)


TECH_TERMS = {
    "java",
    "python",
    "go",
    "golang",
    "rust",
    "javascript",
    "typescript",
    "kotlin",
    "scala",
    "spring",
    "spring boot",
    "fastapi",
    "django",
    "node",
    "node.js",
    "react",
    "next.js",
    "postgresql",
    "postgres",
    "mysql",
    "mongodb",
    "redis",
    "kafka",
    "rabbitmq",
    "aws",
    "azure",
    "gcp",
    "docker",
    "kubernetes",
    "microservices",
    "rest",
    "graphql",
    "system design",
}


def extract_keywords(job_description: str) -> list[str]:
    text = job_description.lower()

    found = [
        term
        for term in TECH_TERMS
        if term in text
    ]

    return found[:8]


def extract_titles(
        job_role: str | None,
        job_description: str,
) -> list[str]:
    if job_role and job_role.strip():
        return [job_role.strip()]

    candidates = re.findall(
        r"(?:senior|sr\.?|lead|staff|principal|junior|jr\.?)?\s*"
        r"(?:software|backend|frontend|full[- ]stack|data|devops|machine learning|ml|platform)\s+"
        r"(?:engineer|developer|scientist|architect)",
        job_description,
        flags=re.IGNORECASE,
    )

    unique: list[str] = []

    for title in candidates:
        cleaned = " ".join(title.split())

        if cleaned.lower() not in {
            item.lower() for item in unique
        }:
            unique.append(cleaned)

    return unique[:5] or ["Software Engineer"]


class CandidateSearchProvider(ABC):
    @abstractmethod
    async def search_candidates(
            self,
            client: httpx.AsyncClient,
            *,
            job_description: str,
            job_role: str | None,
            company: str | None,
            per_page: int,
    ) -> list[SearchCandidateResponse]:
        raise NotImplementedError


# ============================================================
# MOCK PROVIDER


class MockSearchProvider(CandidateSearchProvider):
    CANDIDATES = [
        {
            "name": "Rahul Sharma",
            "email": "rahul.sharma@example.com",
            "phone_number": settings.MOCK_CANDIDATE_PHONE,
            "linkedin_url": "https://linkedin.com/in/rahul-sharma",
            "title": "Senior Java Backend Engineer",
            "company": "FinTech Labs",
            "skills": [
                "Java",
                "Spring Boot",
                "Kafka",
                "PostgreSQL",
                "Docker",
                "AWS",
                "Microservices",
            ],
        },
        {
            "name": "Priya Verma",
            "email": "priya.verma@example.com",
            "phone_number": settings.MOCK_CANDIDATE_PHONE,
            "linkedin_url": "https://linkedin.com/in/priya-verma",
            "title": "Backend Software Engineer",
            "company": "Cloud Systems",
            "skills": [
                "Java",
                "Spring Boot",
                "PostgreSQL",
                "Redis",
                "Docker",
                "Kubernetes",
            ],
        },
        {
            "name": "Arjun Mehta",
            "email": "arjun.mehta@example.com",
            "phone_number": settings.MOCK_CANDIDATE_PHONE,
            "linkedin_url": "https://linkedin.com/in/arjun-mehta",
            "title": "Software Engineer",
            "company": "ScaleTech",
            "skills": [
                "Java",
                "Spring",
                "Kafka",
                "AWS",
                "MySQL",
                "Microservices",
            ],
        },
        {
            "name": "Sneha Patel",
            "email": "sneha.patel@example.com",
            "phone_number": settings.MOCK_CANDIDATE_PHONE,
            "linkedin_url": "https://linkedin.com/in/sneha-patel",
            "title": "Full Stack Engineer",
            "company": "Product Labs",
            "skills": [
                "Java",
                "Spring Boot",
                "React",
                "TypeScript",
                "PostgreSQL",
                "Docker",
            ],
        },
        {
            "name": "Vikram Singh",
            "email": "vikram.singh@example.com",
            "phone_number": settings.MOCK_CANDIDATE_PHONE,
            "linkedin_url": "https://linkedin.com/in/vikram-singh",
            "title": "Lead Backend Engineer",
            "company": "Digital Payments Inc",
            "skills": [
                "Java",
                "Spring Boot",
                "Kafka",
                "PostgreSQL",
                "Kubernetes",
                "AWS",
                "System Design",
            ],
        },
        {
            "name": "Ananya Gupta",
            "email": "ananya.gupta@example.com",
            "phone_number": settings.MOCK_CANDIDATE_PHONE,
            "linkedin_url": "https://linkedin.com/in/ananya-gupta",
            "title": "Java Developer",
            "company": "Enterprise Software",
            "skills": [
                "Java",
                "Spring Boot",
                "MySQL",
                "REST",
                "Docker",
            ],
        },
        {
            "name": "Karan Malhotra",
            "email": "karan.malhotra@example.com",
            "phone_number": settings.MOCK_CANDIDATE_PHONE,
            "linkedin_url": "https://linkedin.com/in/karan-malhotra",
            "title": "Platform Engineer",
            "company": "CloudScale",
            "skills": [
                "Java",
                "Kubernetes",
                "Docker",
                "AWS",
                "Kafka",
                "Microservices",
            ],
        },
        {
            "name": "Neha Kapoor",
            "email": "neha.kapoor@example.com",
            "phone_number": settings.MOCK_CANDIDATE_PHONE,
            "linkedin_url": "https://linkedin.com/in/neha-kapoor",
            "title": "Senior Software Engineer",
            "company": "Tech Ventures",
            "skills": [
                "Java",
                "Spring Boot",
                "PostgreSQL",
                "Redis",
                "Kafka",
                "AWS",
            ],
        },
    ]

    async def search_candidates(
            self,
            client: httpx.AsyncClient,
            *,
            job_description: str,
            job_role: str | None,
            company: str | None,
            per_page: int,
    ) -> list[SearchCandidateResponse]:
        keywords = extract_keywords(job_description)

        # Score candidates by overlap between JD keywords
        # and candidate skills.
        scored_candidates = []

        for candidate in self.CANDIDATES:
            candidate_skills = {
                skill.lower()
                for skill in candidate["skills"]
            }

            matched_keywords = [
                keyword
                for keyword in keywords
                if keyword.lower() in candidate_skills
            ]

            score = len(matched_keywords)

            scored_candidates.append(
                (
                    score,
                    matched_keywords,
                    candidate,
                )
            )

        scored_candidates.sort(
            key=lambda item: item[0],
            reverse=True,
        )

        results: list[SearchCandidateResponse] = []

        for _, matched_keywords, candidate in scored_candidates[:per_page]:
            results.append(
                SearchCandidateResponse(
                    apollo_id=None,
                    name=candidate["name"],
                    email=candidate["email"],
                    phone_number=candidate["phone_number"],
                    linkedin_url=candidate["linkedin_url"],
                    title=candidate["title"],
                    company=candidate["company"],
                    skills=candidate["skills"],
                    metadata={
                        "provider": "mock",
                        "matched_keywords": matched_keywords,
                    },
                )
            )

        return results


# ============================================================
# APOLLO PROVIDER
# ============================================================

class ApolloSearchProvider(CandidateSearchProvider):
    BASE_URL = settings.APOLLO_BASE_URL.rstrip("/")

    @classmethod
    def _headers(cls) -> dict[str, str]:
        if not settings.APOLLO_API_KEY:
            raise HTTPException(
                status_code=503,
                detail="APOLLO_API_KEY is not configured",
            )

        return {
            "x-api-key": settings.APOLLO_API_KEY,
            "accept": "application/json",
            "content-type": "application/json",
            "cache-control": "no-cache",
        }

    async def search_candidates(
            self,
            client: httpx.AsyncClient,
            *,
            job_description: str,
            job_role: str | None,
            company: str | None,
            per_page: int,
    ) -> list[SearchCandidateResponse]:

        titles = extract_titles(
            job_role,
            job_description,
        )

        keywords = extract_keywords(
            job_description
        )

        params: list[tuple[str, str]] = [
            (
                "per_page",
                str(
                    min(
                        per_page,
                        settings.APOLLO_PER_PAGE,
                    )
                ),
            )
        ]

        for title in titles:
            params.append(
                ("person_titles[]", title)
            )

        if keywords:
            params.append(
                (
                    "q_keywords",
                    " ".join(keywords),
                )
            )

        if company and "." in company:
            params.append(
                (
                    "q_organization_domains_list[]",
                    company.strip(),
                )
            )

        url = (
            f"{self.BASE_URL}"
            f"/mixed_people/api_search?"
            f"{urlencode(params)}"
        )

        try:
            response = await client.post(
                url,
                headers=self._headers(),
                timeout=settings.APOLLO_HTTP_TIMEOUT,
            )
        except httpx.TimeoutException as exc:
            raise HTTPException(
                status_code=504,
                detail="Apollo API request timed out",
            ) from exc

        except httpx.RequestError as exc:
            logger.exception(
                "Apollo network error"
            )
            raise HTTPException(
                status_code=502,
                detail="Unable to reach Apollo API",
            ) from exc

        if response.is_error:
            detail = response.text[:3000]

            raise HTTPException(
                status_code=502,
                detail={
                    "message": "Apollo API rejected the request",
                    "upstream_status": response.status_code,
                    "upstream_response": detail,
                },
            )

        try:
            data = response.json()
        except ValueError as exc:
            raise HTTPException(
                status_code=502,
                detail="Apollo returned invalid JSON",
            ) from exc

        people = (
            data.get("people", [])
            if isinstance(data, dict)
            else []
        )

        if not isinstance(people, list):
            return []

        enriched = {}

        if settings.APOLLO_ENRICH_RESULTS:
            enriched = await self._enrich_people(
                client,
                people[:per_page],
            )

        results: list[SearchCandidateResponse] = []

        for person in people[:per_page]:
            pid = person.get("id")

            enrichment = enriched.get(
                pid,
                {},
            )

            full = {
                **person,
                **enrichment,
            }

            organization = (
                    full.get("organization")
                    or {}
            )

            name = (
                    full.get("name")
                    or " ".join(
                value
                for value in (
                    full.get("first_name"),
                    full.get("last_name"),
                )
                if value
            ).strip()
            )

            results.append(
                SearchCandidateResponse(
                    apollo_id=pid,
                    name=name or "Unknown Candidate",
                    email=full.get("email"),
                    phone_number=(
                            full.get("phone")
                            or full.get("direct_phone")
                    ),
                    linkedin_url=full.get(
                        "linkedin_url"
                    ),
                    title=full.get("title"),
                    company=(
                        organization.get("name")
                        if isinstance(
                            organization,
                            dict,
                        )
                        else None
                    ),
                    skills=keywords,
                    metadata={
                        "provider": "apollo",
                        "apollo": {
                            "person_id": pid,
                        },
                    },
                )
            )

        return results

    @classmethod
    async def _enrich_people(
            cls,
            client: httpx.AsyncClient,
            people: list[dict],
    ) -> dict:

        ids = [
            person.get("id")
            for person in people
            if person.get("id")
        ]

        if not ids:
            return {}

        url = (
            f"{cls.BASE_URL}"
            "/people/bulk_match"
        )

        params = {
            "reveal_personal_emails": "false",
            "reveal_phone_number": "false",
        }

        payload = {
            "details": [
                {"id": person_id}
                for person_id in ids
            ]
        }

        try:
            response = await client.post(
                url,
                params=params,
                headers=cls._headers(),
                json=payload,
                timeout=settings.APOLLO_HTTP_TIMEOUT,
            )
        except httpx.RequestError:
            logger.exception(
                "Apollo enrichment request failed"
            )
            return {}

        if response.is_error:
            logger.warning(
                "Apollo enrichment failed: "
                "status=%s body=%s",
                response.status_code,
                response.text[:1000],
            )
            return {}

        try:
            data = response.json()
        except ValueError:
            return {}

        matches = (
            data.get("matches", [])
            if isinstance(data, dict)
            else []
        )

        return {
            match.get("id"): match
            for match in matches
            if (
                    isinstance(match, dict)
                    and match.get("id")
            )
        }


# ============================================================
# PROVIDER FACTORY
# ============================================================

def get_search_provider() -> CandidateSearchProvider:
    provider = (
            getattr(
                settings,
                "CANDIDATE_SEARCH_PROVIDER",
                "mock",
            )
            or "mock"
    ).strip().lower()

    if provider == "apollo":
        return ApolloSearchProvider()

    if provider == "mock":
        return MockSearchProvider()

    raise ValueError(
        f"Unsupported candidate search provider: {provider}"
    )