# Deployment Checklist

This checklist is for deploying the project in a clean, portfolio-safe way with:
- Backend on Render
- Frontend on Vercel or a Render-hosted UI

Use this checklist on the `deploy/render-vercel` branch.

---

## 1. Pre-deployment readiness

### Code and branch
- [ ] Confirm you are on the deployment branch: `deploy/render-vercel`
- [ ] Ensure the repo is pushed to GitHub
- [ ] Make sure `.env` is not committed
- [ ] Confirm no secrets are stored in source files, Terraform state, or logs

### Security review
- [ ] Remove or rotate any exposed API keys
- [ ] Ensure all secrets are stored in Render/Vercel secret managers
- [ ] Verify no private credentials are in repo history or local config files
- [ ] Confirm no `.env` file is included in the deployment build context

### Runtime assumptions
- [ ] Confirm the backend can start with `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- [ ] Confirm the app has valid Qdrant credentials
- [ ] Confirm the app has a valid Groq API key
- [ ] Confirm the app has valid Google Cloud / Vertex AI credentials if embedding or GCS is used
- [ ] Confirm the app has a valid Logfire token if tracing is enabled
- [ ] Confirm the app has a valid LangSmith key if tracing is enabled

---

## 2. Backend deployment on Render

### Render settings
- [ ] Create a new Render Web Service
- [ ] Connect the GitHub repo
- [ ] Select the `deploy/render-vercel` branch
- [ ] Set runtime to Python 3.11
- [ ] Build command:
  ```bash
  pip install -r requirements-backend.txt
  ```
- [ ] Start command:
  ```bash
  uvicorn app.main:app --host 0.0.0.0 --port $PORT
  ```

### Backend env vars
Add these as Render environment variables or secrets:

- [ ] `GROQ_API_KEY`
- [ ] `QDRANT_CLUSTER_ENDPOINT`
- [ ] `QDRANT_API_KEY`
- [ ] `PROJECT_ID`
- [ ] `LOCATION`
- [ ] `LOGFIRE_TOKEN`
- [ ] `LANGSMITH_API_KEY`
- [ ] `LANGSMITH_PROJECT`
- [ ] `LANGSMITH_ENDPOINT`
- [ ] `GOOGLE_APPLICATION_CREDENTIALS` if required for local service account flow

### Backend validation
- [ ] Deploy the service
- [ ] Open the Render URL
- [ ] Confirm `GET /` returns HTTP 200
- [ ] Confirm backend starts without crash loop
- [ ] Confirm `/query` accepts a POST request
- [ ] Test a basic request with a known short prompt
- [ ] Check whether the response includes `answer` and `status`

### Backend security hardening
- [ ] Restrict `/query` access using auth if it is not meant to be public
- [ ] Do not expose raw API keys in logs or output
- [ ] Make sure startup fails gracefully when required env vars are missing
- [ ] Add endpoint-level or service-level auth before public release

---

## 3. Qdrant and retrieval validation

- [ ] Confirm the Qdrant cluster is reachable from Render
- [ ] Confirm the configured collection exists: `enterprise_rag`
- [ ] Ingest or load documents to Qdrant
- [ ] Confirm vector search returns non-empty results
- [ ] Confirm the backend returns sources in the response payload
- [ ] Validate a query that should yield actual context

If this fails, the app will reply with degraded or empty results and should fail gracefully instead of pretending to work.

---

## 4. Frontend deployment decisions

### Option A: Keep Streamlit UI on Render
- [ ] Create another Render Web Service
- [ ] Use Python runtime
- [ ] Build command:
  ```bash
  pip install -r requirements-ui.txt
  ```
- [ ] Start command:
  ```bash
  streamlit run ui/app.py --server.port $PORT --server.address 0.0.0.0
  ```
- [ ] Set `BACKEND_URL` to the Render backend URL
- [ ] Confirm the UI loads successfully
- [ ] Confirm chat requests reach the backend

### Option B: Deploy frontend on Vercel
This requires converting the current Streamlit UI into a Vercel-compatible app.

- [ ] Create a new frontend app in Vercel
- [ ] Use a React/Next.js app instead of Streamlit
- [ ] Set `NEXT_PUBLIC_API_URL` or equivalent to the Render backend URL
- [ ] Replace the current UI logic in `ui/app.py` with a web app that calls the backend
- [ ] Confirm the API integration works end-to-end
- [ ] Confirm the frontend renders sources and answers correctly

> Recommended: For this current repo, Render for the UI is the simplest and most compatible path.

---

## 5. Deployment checklist for production safety

- [ ] No secrets committed into Git
- [ ] No `.env` file included in production image or deployment
- [ ] Qdrant access keys are in secrets manager
- [ ] Groq keys are in secrets manager
- [ ] Logging tokens are in secrets manager
- [ ] Auth is enabled for protected endpoints
- [ ] Backend health endpoints are checked
- [ ] Startup validation is implemented
- [ ] Empty retrieval results handle gracefully
- [ ] Retrieval failure does not produce fake confidence
- [ ] App keeps a proper error message for downstream failures

---

## 6. Final launch checklist

### Backend
- [ ] Render service is live
- [ ] `GET /` works
- [ ] `/query` works with a test question
- [ ] Qdrant returns context
- [ ] Response includes `answer`, `status`, and `sources`

### Frontend
- [ ] UI loads on deployed URL
- [ ] User can submit a question
- [ ] Chat request reaches backend
- [ ] Response renders correctly
- [ ] Sources are visible if available

### Security and posture
- [ ] No secrets in repo or logs
- [ ] Auth is enabled for sensitive endpoints
- [ ] Only required services are public

---

## 7. Recommended portfolio deployment posture

For a portfolio project, the most realistic setup is:
- Backend: Render
- Frontend: Render (Streamlit) OR Vercel after frontend rewrite

Do not publicly expose the backend until:
- auth is enforced,
- secrets are moved to secrets manager,
- and retrieval is validated end-to-end.

---

## 8. Deployment sign-off

Only mark deployment complete when all boxes below are checked:

- [ ] Backend successfully deployed
- [ ] Frontend successfully deployed
- [ ] API works end-to-end
- [ ] Qdrant is live and returns actual context
- [ ] Secrets are not exposed
- [ ] App is behind appropriate auth or access control
- [ ] Demo is stable and repeatable

---

## 9. Useful deployment commands

Backend local run:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Streamlit local run:
```bash
streamlit run ui/app.py --server.port 8501 --server.address 0.0.0.0
```

Health check:
```bash
curl https://<your-render-backend>/
```

Test query:
```bash
curl -X POST https://<your-render-backend>/query \
  -H "Content-Type: application/json" \
  -d '{"query":"What does the parallelism field do in a Kubernetes Job?","thread_id":"demo"}'
```
