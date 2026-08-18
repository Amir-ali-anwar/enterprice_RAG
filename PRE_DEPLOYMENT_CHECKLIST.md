# Pre-Deployment Checklist

Status as of 2026-08-18, based on live testing of the running app plus the
static audit in [RAG_PRODUCTION_ANALYSIS.md](RAG_PRODUCTION_ANALYSIS.md)
(score 27/100 at the time it was written). Checkboxes reflect verified
current state, not intent — re-verify after each session rather than
trusting this file blindly once time has passed.

## Tier 0 — Nothing works at all until these are done

- [x] **Retired Groq model replaced.** `llama-3.3-70b-versatile` was pulled
      from Groq's catalog (404 on every call). [app/config.py](app/config.py)
      now defaults `GROQ_MODEL` to `openai/gpt-oss-120b`, confirmed live
      against the real API key.
- [ ] **Provision a working Qdrant cluster.** The endpoint in `.env`
      (`QDRANT_CLUSTER_ENDPOINT`) returns `404 page not found` on every
      call — the cluster no longer exists. Create a new one at
      cloud.qdrant.io and update `.env` with the new URL + API key.
- [ ] **Set up GCP credentials for Vertex AI.** `GOOGLE_APPLICATION_CREDENTIALS`
      is empty and no Application Default Credentials file exists locally.
      Run `gcloud auth application-default login` (or attach a service
      account key) so embeddings can authenticate.
- [ ] **Re-ingest `DATA/`** into the new Qdrant collection once the two
      items above are done. Until this happens, every technical query is
      either an accidental-luck answer from the model's own training data
      or a correct "I don't know" — never an actual grounded answer.

## Tier 1 — Required before a public/safe deployment

- [x] **Secrets moved to Secret Manager** instead of plaintext env vars —
      [terraform/secrets.tf](terraform/secrets.tf). *Written, not applied.*
- [x] **Backend Cloud Run invoker restricted** to the UI's service account
      instead of `allUsers` — [terraform/cloud_run.tf](terraform/cloud_run.tf).
      *Written, not applied.*
- [x] **Cloud SQL `0.0.0.0/0` authorized network removed** —
      [terraform/database.tf](terraform/database.tf). *Written, not applied.*
- [x] **UI attaches a Google-signed ID token** to backend calls, matching
      the IAM-only backend access — [ui/app.py](ui/app.py). *Written, not
      tested against a real deployment.*
- [ ] **Rotate every exposed key** (Groq, Qdrant, Hugging Face, Logfire,
      LangSmith). The old `.env` sat in plaintext while open in the editor;
      treat those values as compromised regardless of whether the cluster
      they pointed to still exists.
- [ ] **Rebuild container images** with the fixed code:
      `gcloud builds submit --config cloudbuild.yaml .`
- [ ] **Run Terraform.** No `terraform.tfstate` exists yet — nothing above
      has actually been deployed, it only exists as code:
      `cd terraform && terraform init && terraform plan && terraform apply`
- [ ] **Push rotated secret values into Secret Manager** (only after
      `terraform apply` has created the secret containers):
      `gcloud secrets versions add <groq-api-key|qdrant-api-key|logfire-token|langsmith-api-key> --data-file=-`
- [ ] **Verify the deployed backend actually rejects unauthenticated
      calls**, and that the UI can still reach it through the new IAM
      binding.

## Tier 2 — Should fix before calling this "production quality"

Not started. Lower urgency than Tier 0/1, but real:

- [ ] **Non-idempotent ingestion** — every chunk gets `uuid.uuid4()`;
      re-running ingestion duplicates vectors instead of replacing them.
      [app/ingestion/processor.py](app/ingestion/processor.py)
- [ ] **In-memory LangGraph checkpointing** — `MemorySaver()` loses all
      conversation state on restart or when Cloud Run scales to a new
      instance. [app/agents/graph.py](app/agents/graph.py)
- [ ] **Responder error path drops `final_answer`** — a genuine LLM
      failure returns `answer: null` instead of a graceful message.
      [app/agents/nodes/responder.py](app/agents/nodes/responder.py)
- [ ] **No retrieval score threshold / abstention policy** — confirmed
      live: with retrieval broken, the model answered one question
      confidently from general knowledge and correctly declined another,
      with no signal to the user either way about whether an answer is
      actually grounded in your documents.
- [ ] **Guardrails rely on brittle phrase matching** — confirmed live: a
      jailbreak-style prompt was not caught by the NeMo rails; the refusal
      that came back was the underlying LLM's own alignment, not the
      app's guardrail layer.
- [ ] **Windows console `UnicodeEncodeError`** when Logfire logs emoji
      characters under cp1252 — cosmetic but noisy in local logs.

## Runbook (run in this order)

1. Rotate keys: console.groq.com, cloud.qdrant.io, huggingface.co/settings/tokens,
   logfire.pydantic.dev, smith.langchain.com
2. Create a new Qdrant Cloud cluster; update `.env`
3. `gcloud auth login && gcloud auth application-default login`
4. Re-ingest `DATA/`; verify `/query` returns grounded answers with real `sources`
5. `gcloud builds submit --config cloudbuild.yaml .`
6. `cd terraform && terraform init && terraform plan -var="project_id=enterprice-rag-497712" -var="qdrant_url=<new-url>" -var="doc_ai_processor_id=e9f45a52c2a78e4e"`
   then the equivalent `terraform apply`
7. `gcloud secrets versions add <name> --project=enterprice-rag-497712 --data-file=-` for each of the four provider secrets
8. Verify: unauthenticated `curl` against the deployed backend is rejected; the deployed UI still answers correctly end to end
