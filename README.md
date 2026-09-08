# AI Hiring Assistant

An AI-assisted technical recruitment platform that combines candidate discovery, recruiter-controlled outreach, Voice AI calls, persistent call telemetry, and webhook-driven call updates in a single workflow.

The application is implemented as a Next.js frontend and FastAPI backend backed by PostgreSQL, with Hunar Voice Agents used for outbound voice outreach and Apollo.io available as an external candidate-search provider. The repository also contains a mock candidate-search provider so the search workflow can be exercised without an Apollo API key.

Repository: https://github.com/abhi01-01/ai-hiring-assistant

## 1. What problem does it solve?

Technical recruiting is usually split across several disconnected activities:

1. A recruiter receives a job description.
2. The recruiter looks for people whose profile appears relevant.
3. Candidate information is copied into a separate system.
4. A recruiter or calling tool initiates outreach.
5. The outcome of the call is captured somewhere else.
6. Recruiters manually revisit records to understand campaign progress.

AI Hiring Assistant turns those steps into one application-level workflow.

A recruiter can provide a job description, search for matching candidates, select a candidate, trigger an outbound Voice AI call, and monitor the resulting call status, transcript, summary, duration, result, and recording metadata from the dashboard.

The system is intentionally designed around a persistent candidate and call history rather than treating the Voice AI provider as the system of record.

## 2. Core capabilities

### Candidate management

- Stores candidate name, phone number, email, LinkedIn URL, skills, and creation timestamp.
- Uses phone number as the unique candidate identity constraint.
- Reuses an existing candidate record for repeat outreach instead of creating duplicates.
- Stores multiple call records per candidate.

### Candidate discovery

The search API supports a provider abstraction with two implementations:

- `mock`: an in-memory demo dataset with deterministic keyword-overlap scoring.
- `apollo`: Apollo.io-based people search using titles, extracted technical keywords, and optional organization-domain filtering.

The provider is selected by configuration, so the UI does not need to know which external source is active.

### AI Voice outreach

When a recruiter triggers outreach, the backend:

1. Validates the candidate payload.
2. Finds or creates the candidate.
3. Creates a local call log in `INITIATING` state.
4. Builds sanitized job/context metadata.
5. Calls the Hunar Voice Agents API.
6. Persists the returned external call ID and initial status.
7. Returns the candidate and call record to the frontend.

The local database therefore records the outreach attempt independently of Hunar.

### Webhook processing

Hunar sends call lifecycle/result information back to the backend through:

`POST /api/webhooks/hunar`

The webhook handler:

- Accepts flexible field naming such as `call_id` / `callId`, `conversation_id` / `conversationId`, etc.
- Attempts to match the event to a local `CallLog` using the external call ID.
- Falls back to candidate phone matching where available.
- Normalizes phone numbers to E.164-style storage.
- Updates status, transcript, summary, result, recording URL, duration, and raw payload metadata.
- Supports HMAC-SHA256 signature validation when `HUNAR_WEBHOOK_SECRET` is configured.
- Safely ignores unmatched events with `No matching call log` rather than creating orphan call records.

## 3. Business workflow

```mermaid
flowchart TD
    A[Recruiter] --> B[Open Hiring Assistant]
    B --> C[Enter Company / Job Role / Job Description]
    C --> D[Search Candidates]
    D --> E{Search Provider}
    E -->|mock| F[Demo Candidate Dataset]
    E -->|apollo| G[Apollo.io People Search]
    F --> H[Rank / Return Candidates]
    G --> H
    H --> I[Recruiter Reviews Candidate]
    I --> J[Enter / Confirm E.164 Phone]
    J --> K[Trigger Voice AI]
    K --> L[Create / Update Candidate]
    L --> M[Create CallLog: INITIATING]
    M --> N[Hunar Voice API]
    N --> O[Outbound AI Call]
    O --> P[Hunar Callback / Webhook]
    P --> Q[Match CallLog]
    Q --> R[Persist Status / Transcript / Summary / Result]
    R --> S[Dashboard Polls API]
    S --> T[Recruiter Sees Campaign Telemetry]
```

## 4. High-level architecture

```mermaid
flowchart LR
    subgraph Client[Client / Browser]
        UI[Next.js UI]
    end

    subgraph Frontend[Frontend Service]
        NEXT[Next.js App Router]
        REWRITE[Next.js API Rewrite]
    end

    subgraph Backend[Backend Service]
        API[FastAPI]
        HIRING[HiringService]
        SEARCH[Search Provider Abstraction]
        HUNAR[HunarVoiceService]
        WEBHOOK[Webhook Router]
        REPO[Repository Layer]
    end

    subgraph Data[Persistence]
        PG[(PostgreSQL)]
    end

    subgraph External[External Services]
        APOLLO[Apollo.io]
        HUNAR_API[Hunar Voice Agents API]
    end

    UI --> NEXT
    NEXT --> REWRITE
    REWRITE --> API
    API --> HIRING
    API --> SEARCH
    API --> WEBHOOK
    HIRING --> HUNAR
    HIRING --> REPO
    WEBHOOK --> REPO
    REPO --> PG
    SEARCH --> APOLLO
    HUNAR --> HUNAR_API
    HUNAR_API -->|callbacks| WEBHOOK
```

## 5. Component responsibilities

| Component | Responsibility |
|---|---|
| Next.js App Router | Serves the recruiter UI and server-side API rewrites |
| `DashboardClient` | Shows persisted candidates and campaign telemetry; polls for updates |
| `ReachoutClient` | Collects JD/search inputs, displays discovered candidates, triggers outreach |
| FastAPI | HTTP API, validation, CORS, lifecycle/startup, routing |
| `HiringService` | Orchestrates candidate creation/reuse, call-log creation, and Hunar dispatch |
| `HunarVoiceService` | Encapsulates Hunar API authentication, request construction, and error handling |
| Search provider abstraction | Separates candidate-search behavior from API consumers |
| `MockSearchProvider` | Deterministic local/demo search dataset |
| `ApolloSearchProvider` | External candidate discovery through Apollo.io |
| Webhook router | Receives and normalizes Hunar callbacks |
| Repository layer | Encapsulates database access |
| PostgreSQL | System-of-record for candidates and call logs |

## 6. Repository structure

```text
ai-hiring-assistant/
├── api/
│   ├── core/
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── migrations.py
│   │   └── run_migrations.py
│   ├── repositories/
│   │   ├── base.py
│   │   ├── call_log.py
│   │   ├── candidate.py
│   │   └── models.py
│   ├── routers/
│   │   ├── candidates.py
│   │   ├── search.py
│   │   └── webhooks.py
│   ├── services/
│   │   ├── hiring.py
│   │   ├── hunar.py
│   │   └── search.py
│   ├── index.py
│   ├── schemas.py
│   ├── requirements.txt
│   └── Dockerfile
├── app/
│   ├── components/
│   │   ├── DashboardClient.tsx
│   │   └── ReachoutClient.tsx
│   ├── globals.css
│   ├── layout.tsx
│   └── page.tsx
├── components/
│   └── ui/
├── lib/
├── public/
├── types/
├── .github/workflows/ci.yml
├── .env.example
├── Dockerfile.frontend
├── docker-compose.yml
├── docker-compose.prod.yml
├── next.config.ts
├── package.json
└── README.md
```

The current repository is a single Git repository containing both frontend and backend code. It can be developed locally as a Docker Compose stack or as separate frontend/backend processes.

## 7. Data model

There are two primary database entities.

### Candidate

A candidate is the persistent person/profile record.

Key fields:

- `id`: UUID string primary key.
- `name`: required candidate name.
- `phone_number`: required E.164-style number and unique across candidates.
- `email`: optional.
- `linkedin_url`: optional.
- `skills`: JSON array.
- `created_at`: timestamp.

### CallLog

A call log represents one outreach attempt / Voice AI interaction.

Key fields:

- `id`: UUID string primary key.
- `external_call_id`: provider-side call identifier, unique when present.
- `candidate_id`: foreign key to `candidates`.
- `status`: call lifecycle status.
- `transcript`: optional transcript.
- `summary`: optional summary.
- `duration_seconds`: optional duration.
- `result`: optional outcome/disposition.
- `recording_url`: optional recording location.
- `custom_data`: raw/structured metadata from the workflow.
- `created_at` / `updated_at`: audit timestamps.

Relationship:

```mermaid
erDiagram
    CANDIDATE ||--o{ CALL_LOG : has

    CANDIDATE {
        string id PK
        string name
        string phone_number UK
        string email
        string linkedin_url
        json skills
        datetime created_at
    }

    CALL_LOG {
        string id PK
        string external_call_id UK
        string candidate_id FK
        string status
        text transcript
        text summary
        int duration_seconds
        string result
        string recording_url
        json custom_data
        datetime created_at
        datetime updated_at
    }
```

## 8. API surface

The backend exposes the following routes under `/api`.

### Health

`GET /api/health`

Checks application/database health by opening a database connection and executing `SELECT 1`.

Example response:

```json
{
  "status": "ok",
  "environment": "development"
}
```

### List candidates

`GET /api/candidates?skip=0&limit=100`

Returns candidates ordered by newest creation time and includes their call history.

### Create candidate / initiate outreach

`POST /api/candidates`

Request example:

```json
{
  "name": "Jane Doe",
  "phone_number": "+919876543210",
  "email": "jane@example.com",
  "linkedin_url": "https://linkedin.com/in/jane-doe",
  "skills": ["Java", "Spring Boot", "PostgreSQL"],
  "job_description": "Backend Engineer responsible for Java microservices...",
  "company": "Example Corp",
  "job_role": "Backend Engineer"
}
```

The endpoint validates candidate data, persists/reuses the candidate, creates a call log, and dispatches the voice call through Hunar.

### Dashboard data

`GET /api/candidates/dashboard`

Returns flattened candidate/call information for dashboard-style presentation.

### Candidate search

`POST /api/search`

Request example:

```json
{
  "job_description": "We need a backend engineer with Java, Spring Boot, Kafka and PostgreSQL.",
  "company": "example.com",
  "job_role": "Backend Engineer",
  "per_page": 10
}
```

The configured search provider returns normalized `SearchCandidateResponse` objects.

### Hunar webhook

`POST /api/webhooks/hunar`

Receives Hunar callback payloads and updates the corresponding local `CallLog`.

### API interaction sequence

```mermaid
sequenceDiagram
    actor Recruiter
    participant Browser
    participant Next as Next.js
    participant API as FastAPI
    participant DB as PostgreSQL
    participant Hunar as Hunar API

    Recruiter->>Browser: Search JD
    Browser->>Next: POST /api/search
    Next->>API: POST /api/search
    API-->>Next: Candidate list
    Next-->>Browser: Candidate list

    Recruiter->>Browser: Trigger Voice AI
    Browser->>Next: POST /api/candidates
    Next->>API: POST /api/candidates
    API->>DB: Find/create Candidate
    API->>DB: Insert CallLog(INITIATING)
    API->>Hunar: POST /calls/
    Hunar-->>API: External call ID + status
    API->>DB: Update CallLog
    API-->>Next: Candidate + CallLog
    Next-->>Browser: Outreach result

    Hunar->>API: POST /api/webhooks/hunar
    API->>DB: Match CallLog by external ID
    API->>DB: Update status/transcript/summary/result
    API-->>Hunar: 200 OK

    loop Every 10 seconds
        Browser->>Next: GET /api/candidates?limit=100
        Next->>API: GET /api/candidates?limit=100
        API->>DB: Query candidates + calls
        API-->>Next: Latest telemetry
        Next-->>Browser: Updated dashboard
    end
```

## 9. Frontend behavior

The homepage currently combines two primary UI sections.

### Initiate Outreach

The dashboard contains a simple form for directly calling a known candidate:

- Candidate name
- E.164 phone number
- Optional email
- `Call Candidate` action

### Campaign Telemetry

The dashboard displays:

- Candidate name
- Contact number
- Latest call status
- Duration
- Result

The client refreshes candidate data every 10 seconds and keeps the last known UI state when the API is temporarily unavailable.

### People Search & AI Reachout

The recruiter can enter:

- Company
- Job role
- Job description

After searching, the UI displays candidate identity/profile data, LinkedIn profile, and a phone input. A recruiter can then trigger Voice AI outreach against an individual result.

## 10. Candidate search design

Search is implemented using a provider interface:

```text
CandidateSearchProvider
        │
        ├── MockSearchProvider
        │
        └── ApolloSearchProvider
```

### Mock provider

The mock provider is useful for:

- local development
- UI development
- demos without third-party credentials
- CI/build environments

It extracts a bounded set of known technical terms from the job description and scores each demo candidate by skill overlap.

### Apollo provider

The Apollo provider:

1. Extracts likely job titles.
2. Extracts known technical keywords.
3. Builds Apollo `mixed_people/api_search` parameters.
4. Applies optional organization-domain filtering.
5. Normalizes returned data into the application's `SearchCandidateResponse` model.

The abstraction allows the API contract to stay stable while the search backend changes.

## 11. Voice outreach design

The `HiringService` is the main orchestration boundary.

```mermaid
flowchart TD
    A[POST /api/candidates] --> B[Validate CandidateCreate]
    B --> C{Candidate exists by phone?}
    C -->|No| D[Create Candidate]
    C -->|Yes| E[Update existing profile]
    D --> F[Create CallLog]
    E --> F
    F --> G[Commit local INITIATING state]
    G --> H[Sanitize JD / Build custom_data]
    H --> I[HunarVoiceService.initiate_call]
    I --> J{Hunar response}
    J -->|Success| K[Persist external_call_id + status]
    J -->|Failure| L[Mark CallLog FAILED]
    K --> M[Return candidate + call]
    L --> N[Propagate HTTP error]
```

A useful property of this design is that the local call log is created before the third-party call is dispatched. That gives the system a durable record of the attempted outreach even when the provider call fails.

## 12. Webhook lifecycle

```mermaid
flowchart TD
    A[Hunar callback] --> B[Read raw request body]
    B --> C{Webhook secret configured?}
    C -->|No| D[Skip signature validation]
    C -->|Yes| E[Verify HMAC-SHA256 signature]
    E --> F{Signature valid?}
    F -->|No| G[401]
    F -->|Yes| H[Parse JSON]
    D --> H
    H --> I[Extract external call ID]
    I --> J[Lookup CallLog]
    J --> K{Match found?}
    K -->|No| L[Log warning + return ignored]
    K -->|Yes| M[Normalize status]
    M --> N[Extract transcript / summary / result / recording / duration]
    N --> O[Persist raw payload + fields]
    O --> P[200 success]
```

The webhook endpoint is intentionally tolerant of callback schema variations because the provider payload may expose semantically equivalent fields under different names.

## 13. Local development

There are two supported approaches.

### Option A: Docker Compose (recommended)

Prerequisites:

- Docker Desktop / Docker Engine
- Docker Compose
- Git

Clone the repository:

```bash
git clone https://github.com/abhi01-01/ai-hiring-assistant.git
cd ai-hiring-assistant
```

Create the local environment file:

```bash
cp .env.example .env
```

Minimum local configuration for the mock search workflow:

```env
ENVIRONMENT=development
DATABASE_URL=
CORS_ORIGINS=http://localhost:3000
PUBLIC_BASE_URL=http://localhost:8000
HUNAR_API_KEY=
DEFAULT_AGENT_ID=
HUNAR_WEBHOOK_URL=http://localhost:8000/api/webhooks/hunar
HUNAR_WEBHOOK_SECRET=
CANDIDATE_SEARCH_PROVIDER=mock
```

Start the entire stack:

```bash
docker compose up --build
```

The services are:

```text
Frontend  http://localhost:3000
Backend   http://localhost:8000
Postgres  localhost:5432
```

The Compose file injects a Docker-network database URL into the backend and waits for PostgreSQL to become healthy before starting the backend.

Open:

```text
http://localhost:3000
```

Check backend health:

```bash
curl http://localhost:8000/api/health
```

Expected:

```json
{
  "status": "ok",
  "environment": "development"
}
```

Stop the stack:

```bash
docker compose down
```

Stop and delete the PostgreSQL volume as well:

```bash
docker compose down -v
```

### Option B: Run backend and frontend directly

#### Backend

Prerequisites:

- Python 3.11
- PostgreSQL 15 or compatible PostgreSQL instance

Create a virtual environment:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
```

Install backend dependencies:

```bash
pip install -r api/requirements.txt
```

Create `.env` from `.env.example` and provide a valid PostgreSQL `DATABASE_URL`, for example:

```env
DATABASE_URL=postgresql://postgres:password@localhost:5432/hunar_db
```

For development, schema creation can be enabled through environment variables used by the Compose setup:

```env
DB_AUTO_CREATE=true
DB_AUTO_MIGRATE=true
```

Start FastAPI:

```bash
uvicorn api.index:app --host 0.0.0.0 --port 8000 --reload
```

#### Frontend

Prerequisites:

- Node.js 22
- npm

Install dependencies:

```bash
npm ci
```

Start the Next.js development server:

```bash
npm run dev
```

The application will normally be available at:

```text
http://localhost:3000
```

## 14. Environment variables

The canonical development template is `.env.example`.

| Variable | Purpose | Typical local value |
|---|---|---|
| `ENVIRONMENT` | Runtime environment label | `development` |
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://...` |
| `DB_AUTO_CREATE` | Create SQLAlchemy tables automatically in development | `true` |
| `DB_AUTO_MIGRATE` | Run compatible startup migrations | `true` |
| `CORS_ORIGINS` | Comma-separated browser origins allowed by FastAPI | `http://localhost:3000` |
| `PUBLIC_BASE_URL` | Public/application base URL used by integration configuration | `http://localhost:8000` |
| `HUNAR_API_KEY` | Hunar API authentication key | secret |
| `DEFAULT_AGENT_ID` | Hunar agent identifier used for calls | provider value |
| `HUNAR_WEBHOOK_URL` | URL Hunar calls for callbacks | local/prod webhook URL |
| `HUNAR_WEBHOOK_SECRET` | Optional HMAC webhook verification secret | empty locally unless configured |
| `CANDIDATE_SEARCH_PROVIDER` | Search implementation | `mock` or `apollo` |
| `MOCK_CANDIDATE_PHONE` | Shared phone number for mock search results | optional |
| `APOLLO_API_KEY` | Apollo API authentication | secret |
| `APOLLO_BASE_URL` | Apollo API base URL | `https://api.apollo.io/api/v1` |
| `APOLLO_PER_PAGE` | Maximum Apollo result page size | `10` |
| `APOLLO_ENRICH_RESULTS` | Apollo enrichment toggle | `true`/`false` |
| `APOLLO_HTTP_TIMEOUT` | Apollo request timeout in seconds | `20` |

Do not commit real API keys, webhook secrets, or production database credentials.

## 15. Important configuration behavior

### Hunar webhook secret

The backend supports optional webhook HMAC verification. When `HUNAR_WEBHOOK_SECRET` is empty, the verifier intentionally skips signature validation. When configured, the endpoint requires the `X-Hunar-Signature` header and validates the raw request body with SHA-256 HMAC.

For a production deployment, configuring and rotating a real webhook secret is preferable.

### CORS

`CORS_ORIGINS` is parsed as a comma-separated list. In production it should contain the deployed frontend origin, for example:

```env
CORS_ORIGINS=https://your-frontend-domain.example
```

Do not use a trailing slash in an origin value.

## 16. Docker architecture

The development Compose stack contains three services:

```mermaid
flowchart TB
    subgraph Compose[Docker Compose Network]
        DB[(PostgreSQL)]
        BE[backend:8000]
        FE[frontend:3000]
        FE -->|HTTP| BE
        BE -->|PostgreSQL| DB
    end

    Browser[Browser] --> FE
```

The backend container is built with `api/Dockerfile` and starts Uvicorn on `0.0.0.0:${PORT:-8000}`.

The frontend image is built with `Dockerfile.frontend`, performs `npm ci`, runs `npm run build`, exposes port `3000`, and starts with `npm start`.

## 17. Production deployment model

The repository can be deployed as two Railway services plus a managed PostgreSQL service:

```mermaid
flowchart LR
    USER[Internet User] --> FE[Railway Frontend]
    FE -->|Private Railway network| BE[Railway Backend]
    BE --> DB[(Railway PostgreSQL)]
    BE --> H[Hunar Voice API]
    BE --> A[Apollo.io]
    H -->|Webhook| BE
```

The frontend should expose a public HTTPS domain. The backend can expose a public endpoint for external webhooks, while frontend-to-backend traffic can use Railway private networking where appropriate.

A public backend domain is required when Hunar needs to send callbacks from outside the Railway private network.

### Typical Railway environment variables

Backend:

```env
ENVIRONMENT=production
DATABASE_URL=<Railway PostgreSQL connection string>
DB_AUTO_CREATE=false
DB_AUTO_MIGRATE=false
CORS_ORIGINS=https://<frontend-domain>
PUBLIC_BASE_URL=https://<frontend-domain-or-application-base-url>
HUNAR_API_KEY=<secret>
DEFAULT_AGENT_ID=<agent-id>
HUNAR_WEBHOOK_URL=https://<backend-public-domain>/api/webhooks/hunar
HUNAR_WEBHOOK_SECRET=<optional-secret>
CANDIDATE_SEARCH_PROVIDER=mock
```

Frontend:

If the Next.js rewrite targets the backend through Railway's private network, the runtime/build configuration must point the rewrite to the backend's private hostname and listening port, rather than Docker Compose's local `backend` hostname.

The public frontend URL itself is not the backend URL.

## 18. CI/CD

GitHub Actions currently validates three areas:

```mermaid
flowchart TD
    PUSH[Push / Pull Request] --> BACK[Backend Job]
    PUSH --> FRONT[Frontend Job]
    BACK --> DOCKER[Docker Build Job]
    FRONT --> DOCKER

    BACK --> B1[Python 3.11]
    B1 --> B2[pip install]
    B2 --> B3[compileall]

    FRONT --> F1[Node 22]
    F1 --> F2[npm ci]
    F2 --> F3[npm run build]

    DOCKER --> D1[Build Backend Image]
    DOCKER --> D2[Build Frontend Image]
```

Current workflow behavior:

- Runs on pushes to `main`, `master`, and `development`.
- Runs for pull requests targeting those branches.
- Backend job installs dependencies and compiles Python modules.
- Frontend job installs npm dependencies and performs a production Next.js build.
- Docker job builds both application images after backend/frontend jobs pass.

## 19. Testing and validation checklist

### Local infrastructure

```bash
docker compose up --build
curl -i http://localhost:8000/api/health
```

### Candidate read path

```bash
curl -i "http://localhost:8000/api/candidates?limit=100"
```

### Candidate write / outreach path

Use a valid E.164 number:

```bash
curl -i -X POST http://localhost:8000/api/candidates \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Candidate",
    "phone_number": "+919876543210",
    "email": "test@example.com",
    "skills": ["Java", "Spring Boot"],
    "job_description": "Backend Engineer with Java and Spring Boot",
    "company": "Example Corp",
    "job_role": "Backend Engineer"
  }'
```

This path requires `HUNAR_API_KEY` and `DEFAULT_AGENT_ID` to be configured if the request is expected to reach Hunar successfully.

### Webhook smoke test

With a fake call ID that is not present in the database:

```bash
curl -i -X POST http://localhost:8000/api/webhooks/hunar \
  -H "Content-Type: application/json" \
  -d '{"call_id":"test-123","status":"COMPLETED"}'
```

Expected behavior is an ignored event rather than creation of an orphan call log:

```json
{
  "status": "ignored",
  "reason": "No matching call log"
}
```

## 20. Error handling strategy

The integration clients translate common upstream failures into HTTP-level application errors:

- Hunar timeout → `504`
- Hunar network failure → `502`
- Hunar rejected request → `502`
- Hunar invalid JSON → `502`
- Missing Hunar API key → `503`
- Apollo missing API key → `503`
- Apollo timeout → `504`
- Apollo network failure → `502`
- Apollo rejected request → `502`
- Invalid webhook JSON → `400`
- Invalid configured webhook signature → `401`

The UI currently displays the most relevant error detail returned by the API and uses alert-based feedback for several interactive actions.

## 21. Design decisions

### PostgreSQL is the system of record

The application stores candidate profiles and call telemetry locally instead of relying on the external voice provider for historical state.

### Phone-number uniqueness

A candidate is uniquely identified by phone number. This prevents repeat submissions from creating multiple candidate records for the same outreach target.

### Call log before provider dispatch

The call log is created before contacting Hunar. This gives the system a durable local state even when the external dispatch fails.

### Provider abstraction for candidate search

The frontend consumes one normalized API contract while search implementations can change independently.

### Raw webhook payload preservation

`custom_data` stores the callback payload, allowing future fields to be inspected without immediately requiring a database schema change for every new provider attribute.

### Flexible webhook parsing

The callback parser accepts several naming variants so the application is resilient to provider payload changes.

## 22. Security considerations

The current application is a functional prototype / production-style foundation, not a finished enterprise IAM platform.

Recommended hardening before exposing it broadly:

1. Add recruiter authentication and authorization.
2. Add rate limiting on public API routes and webhooks.
3. Always configure `HUNAR_WEBHOOK_SECRET` when Hunar supports it for the production integration.
4. Restrict `CORS_ORIGINS` to known frontend origins.
5. Store API credentials only in a secret manager / platform secret store.
6. Add request IDs and structured audit logging.
7. Consider webhook idempotency / replay protection if the provider can retry callbacks.
8. Add stricter authorization around candidate and call records.
9. Protect recording URLs if they expose sensitive data.
10. Add database backups and restore procedures before production use.

## 23. Current limitations

The repository intentionally keeps the scope focused on the recruitment/outreach workflow. The current implementation does not yet provide a complete enterprise recruitment suite.

Known gaps include:

- No user/login/role-management layer.
- No recruiter-to-organization tenancy model.
- No full audit trail for every user action.
- No sophisticated ranking/ML model; the mock provider uses technical-keyword overlap and the Apollo provider delegates discovery to Apollo.
- No background job queue for long-running integrations.
- No dedicated observability stack included in the repository.
- No production-grade webhook replay/idempotency store beyond external-call uniqueness.
- No automated end-to-end integration suite against real Hunar/Apollo accounts.

These are architectural extension points rather than blockers for the current workflow.

## 24. Future evolution

A natural evolution path is:

```mermaid
flowchart LR
    A[Current Prototype] --> B[Authenticated Recruiter Accounts]
    B --> C[Organization / Tenant Isolation]
    C --> D[Background Job Queue]
    D --> E[Event-driven Call Processing]
    E --> F[Advanced Candidate Ranking]
    F --> G[Interview Scheduling]
    G --> H[Analytics / Hiring Funnel]
```

Potential next-stage engineering improvements include:

- Redis-backed rate limiting and job coordination.
- Celery/RQ/Arq or another worker model for provider operations.
- Event-driven call-status processing.
- Strong webhook idempotency keys and retry handling.
- Full-text/vector candidate matching.
- Human review stages and recruiter assignment.
- Interview scheduling and calendar integration.
- Metrics, traces, structured logs, and alerting.
- Fine-grained RBAC and tenant isolation.


## 25. Development commands

Frontend:

```bash
npm ci
npm run dev
npm run build
npm start
npm run lint
```

Backend:

```bash
python -m compileall api
uvicorn api.index:app --host 0.0.0.0 --port 8000 --reload
```

Docker:

```bash
docker compose up --build
docker compose down
docker compose down -v
docker build -f api/Dockerfile -t ai-hiring-backend .
docker build -f Dockerfile.frontend -t ai-hiring-frontend .
```

## 26. Technology stack

### Frontend

- Next.js 16
- React 19
- TypeScript
- Tailwind CSS 4
- shadcn-style UI components
- React Hook Form
- Zod

### Backend

- Python 3.11
- FastAPI
- Uvicorn
- Pydantic v2
- Pydantic Settings
- SQLAlchemy 2
- psycopg2-binary
- HTTPX

### Infrastructure

- PostgreSQL 15 in the supplied Docker Compose setup
- Docker / Docker Compose
- Railway-compatible deployment model
- GitHub Actions CI

### External integrations

- Hunar Voice Agents API
- Apollo.io People Search API

---

## Quick Start

```bash
git clone https://github.com/abhi01-01/ai-hiring-assistant.git
cd ai-hiring-assistant
cp .env.example .env
docker compose up --build
```

Then open:

`http://localhost:3000`

Backend health:

`http://localhost:8000/api/health`

The fastest zero-credential demo path is to use `CANDIDATE_SEARCH_PROVIDER=mock`. Voice outreach requires valid Hunar configuration.
