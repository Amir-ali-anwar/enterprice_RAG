# Enterprise RAG Analysis and Next-Feature Roadmap

## 1. What Is Implemented Today

### 1.1 Application and API
- FastAPI backend service with:
  - `GET /` health-style endpoint
  - `GET /graph` workflow image generation from LangGraph
  - `POST /query` main RAG execution endpoint
- Request schema includes `query` and `thread_id`.
- Basic startup hook initializes guardrails.

### 1.2 Agentic RAG Workflow (LangGraph)
- LangGraph state machine with 3 nodes:
  - Planner node
  - Retriever node
  - Responder node
- Conditional route:
  - Conversational requests can skip retrieval.
  - Technical requests go through retrieve + generate.
- In-memory checkpointer (`MemorySaver`) is enabled.

### 1.3 Retrieval Stack
- Embeddings via Vertex AI (`text-embedding-005`).
- Vector search via Qdrant.
- Reranking via FlashRank cross-encoder.
- Top context chunks are formatted and passed to generation.

### 1.4 Response Generation
- Groq chat model integration for planner and responder.
- Context-window trimming logic before LLM call.
- Separate prompt behavior for:
  - Conversational memory mode
  - Technical context mode

### 1.5 Guardrails
- NeMo Guardrails initialized at startup.
- Colang rules include:
  - Off-topic refusal
  - Jailbreak resistance
  - Greeting/capabilities/farewell flows
- Guardrail gate runs before LangGraph invocation.

### 1.6 Ingestion Pipeline (Batch/CLI Style)
- Universal ingestion function scans folders and processes files.
- Loader coverage:
  - PDF (Document AI)
  - HTML
  - TXT
  - Office files (`docx`, `pptx`)
- Chunking, embedding, and upsert into Qdrant implemented.
- Raw and processed artifacts upload to GCS.

### 1.7 UI
- Streamlit chat app with session ID threading.
- Displays thought process and expandable source chunks.
- Logfire instrumentation is integrated in UI and backend.

### 1.8 Infrastructure and Delivery
- Terraform for:
  - Cloud Run services (backend, UI, ingestion)
  - Cloud SQL (Postgres)
  - Memorystore (Redis)
  - GCS buckets
  - Artifact Registry
  - Eventarc trigger
- Cloud Build config builds and pushes 3 Docker images.

## 2. High-Impact Risks Found (Current Gaps)

### Critical
1. Secret exposure risk:
   - Real-looking API keys and passwords are present in `terraform/terraform.tfvars`.
   - This is a major production blocker and key-management risk.

2. Ingestion service deployment mismatch:
   - Ingestion container starts `uvicorn app.ingestion.processor:app`, but `app` is not defined in `app/ingestion/processor.py`.
   - Cloud Run ingestion service likely cannot boot as configured.

3. Event-driven ingestion design mismatch:
   - Terraform/Eventarc implies GCS event webhook ingestion.
   - Current processor is implemented like local file-system batch ingestion, not a Cloud Run event handler.

### High
4. Conversation state key inconsistency:
   - Agent state uses `message`, but responder returns `messages` on success.
   - This can break or degrade memory continuity across turns.

5. No automated test suite found:
   - No unit/integration/e2e tests discovered.

6. Public unauthenticated backend and UI:
   - Cloud Run IAM allows `allUsers` invoker on both services.
   - No application-layer auth/RBAC in API.

### Medium
7. Guardrail config drift possibility:
   - Colang YAML references OpenAI model config while runtime injects Groq LLM object.
   - Can cause confusion and fragile behavior over time.

8. Weak failure-recovery patterns:
   - Limited retry/backoff/circuit-breaker handling across external dependencies.

9. Limited retrieval metadata and citations:
   - Returned source is mostly chunk text, without strong citation primitives (doc id/page/chunk id/url).

## 3. Prioritized Next Features to Build (Learning + Production)

## Phase 1: Security and Correctness First
1. Secrets management hardening
   - Move all secrets to Secret Manager.
   - Use Terraform variables without committing values.
   - Rotate all exposed credentials.
   - Learning: secure delivery pipelines, cloud secret lifecycle.

2. Fix ingestion runtime architecture
   - Decide one mode:
     - Batch worker job (Cloud Run Job) OR
     - Event-driven webhook service (Cloud Run service + Eventarc payload parser).
   - Update Docker command and entrypoint accordingly.
   - Learning: event-driven ingestion and stateless cloud execution.

3. Fix agent state schema consistency
   - Standardize on one key (`message` or `messages`) across all nodes.
   - Validate state updates with strict typing/tests.
   - Learning: robust state-machine design.

4. Add baseline tests
   - Unit tests: planner routing, reranker fallback, chunking.
   - Integration tests: `/query` happy path and guardrail path.
   - Learning: confidence-driven development for AI systems.

## Phase 2: Retrieval Quality and Explainability
5. Add structured metadata to every chunk
   - `doc_id`, `chunk_id`, `source_uri`, `page`, `section`, `ingested_at`, `version`.
   - Return citations in response payload.
   - Learning: explainable RAG and traceable answers.

6. Hybrid retrieval
   - Combine dense vector search + keyword/BM25 signals.
   - Reciprocal rank fusion or weighted merge.
   - Learning: practical retrieval engineering.

7. Query rewriting and decomposition
   - Add planner improvements for multi-hop questions.
   - Optional sub-queries + answer synthesis.
   - Learning: advanced agent planning patterns.

8. Grounded answer controls
   - Add confidence thresholds and abstain policy.
   - If retrieval confidence is low, ask clarifying questions.
   - Learning: hallucination reduction in production.

## Phase 3: Reliability, Scale, and Ops
9. Persistent memory/checkpoint backend
   - Replace in-memory checkpointer with Postgres saver in production path.
   - Add conversation retention policy.
   - Learning: durable multi-user conversational systems.

10. Caching strategy
   - Implement semantic cache with Redis (already provisioned in infra).
   - Add TTL and invalidation strategy per corpus version.
   - Learning: latency/cost optimization trade-offs.

11. Observability with SLOs
   - Track p95 latency, retrieval hit rate, groundedness score, guardrail hit rate.
   - Add dashboards and error budget alerts.
   - Learning: operating LLM systems with measurable reliability.

12. Resilience patterns
   - Retries with backoff and jitter for Groq, Qdrant, Vertex APIs.
   - Timeout budgets per stage and graceful degradation.
   - Learning: fault-tolerant distributed AI services.

## Phase 4: Governance and Product Maturity
13. AuthN/AuthZ and multi-tenancy
   - Protect API with identity layer (IAP/JWT/OAuth).
   - Namespace data by tenant and enforce row/vector isolation.
   - Learning: enterprise security architecture.

14. Evaluation pipeline (CI + offline)
   - Curate golden dataset from your domain docs.
   - Run RAGAS/DeepEval in CI for regression checks.
   - Learning: quality gates for LLM releases.

15. Data lifecycle and reindex strategy
   - Version embeddings and track corpus snapshots.
   - Incremental re-ingestion and deletion propagation.
   - Learning: large-scale corpus management.

16. API and contract hardening
   - Add schema versioning and strict response contracts.
   - Add idempotency keys and request tracing IDs.
   - Learning: production API evolution discipline.

## 4. Suggested 30-Day Implementation Path
1. Week 1:
   - Secrets cleanup and rotation.
   - Fix ingestion deployment model.
   - Fix state schema mismatch.

2. Week 2:
   - Add tests and CI checks.
   - Add structured citations and metadata.

3. Week 3:
   - Add Redis semantic caching.
   - Add Postgres checkpointer and retention rules.

4. Week 4:
   - Build evaluation harness (RAGAS/DeepEval).
   - Add SLO dashboards and alerting.

## 5. Quick Win Backlog (If You Want Fast Progress)
- Add health/readiness endpoints for backend and ingestion.
- Add request/response Pydantic models for all node outputs.
- Add fallback model routing when Groq fails.
- Add chunk deduplication and near-duplicate filtering during ingestion.
- Add citation rendering in UI with source file + chunk identifiers.

---

This file is an implementation-grounded snapshot of your current architecture and the most valuable next steps to make the system robust and production-ready while maximizing learning.