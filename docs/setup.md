# Synapse — End-to-End Setup

A step-by-step runbook: prerequisites → start the stack → hit the API → tear
down. Fully containerized — you don't need Python or any DB client on your
host.

---

## 1. Prerequisites

You need exactly one thing:

- **Docker Desktop** (macOS/Windows) or **Docker Engine + Docker Compose v2**
  (Linux). Verify:

  ```bash
  docker info | head -5
  docker compose version
  ```

  You should see `Server: … Server Version: …` (not `Cannot connect to the
  Docker daemon`) and `Docker Compose version v2.x`.

Optional but useful:
- `curl` (macOS ships with it) — for hitting the API from the terminal
- A web browser — for Swagger and Adminer

You do **not** need Python, `pip`, `psql`, or Node on your host. Everything
runs in containers.

---

## 2. Clone and configure

Clone the repo, `cd` into it, then:

```bash
cp .env.example .env
```

That's it — the defaults in `.env` work out of the box. Only change them if
you want different credentials or ports.

---

## 3. Start the stack

```bash
docker compose -f local.yml up -d --build
```

**What this does:**
1. Builds the `synapse-api` image (first run: ~1–2 min for base image + pip install; subsequent runs are cached).
2. Starts three containers on a private compose network:
   - `synapse-postgres` — PostgreSQL 16, port 5432 → host 5432
   - `synapse-adminer` — DB UI, port 8080 → host 8080
   - `synapse-api` — FastAPI (uvicorn), port 8000 → host 8000
3. The `api` container's entrypoint automatically runs `alembic upgrade head`
   before starting uvicorn — schema is applied on first boot.

**Verify:**

```bash
docker compose -f local.yml ps
```

You should see three rows, all `Up`, and `synapse-postgres` marked `(healthy)`.

---

## 4. Confirm the API is serving

```bash
curl -sS http://localhost:8000/health
```

Expected: `{"status":"ok"}`

If it takes a couple of seconds to respond, that's the api container finishing
alembic + starting uvicorn. Retry after 5s.

---

## 5. Open the docs UIs

- **Swagger UI (interactive):** http://localhost:8000/docs
- **ReDoc (read-only):** http://localhost:8000/redoc
- **OpenAPI spec (JSON):** http://localhost:8000/openapi.json
- **Adminer (DB inspector):** http://localhost:8080
  - System: **PostgreSQL**
  - Server: **postgres** (the container name — **not** `localhost`)
  - Username: **synapse**
  - Password: **change-me**
  - Database: **synapse**

---

## 6. Create your first project

### Via Swagger

1. Open http://localhost:8000/docs
2. Expand **`POST /api/v1/projects`** → click **Try it out**
3. Paste this body (or edit the pre-filled one):

   ```json
   {
     "name": "My First Project",
     "project_type": "NEW",
     "source": "PPM",
     "created_by": "pradip",
     "description": "Kicking the tires",
     "source_reference_id": "TRY-1",
     "configuration": {
       "context": "Exploring Synapse",
       "goals": "Learn the API",
       "scope": "MVP",
       "constraints": "none",
       "tech_stack": {"backend": ["Python"], "frontend": ["React"]},
       "coding_standards": "PEP 8"
     }
   }
   ```

4. Click **Execute** → you get **`201 Created`** with the full project JSON.
5. **Copy the `id`** from the response — you'll use it for GET/PATCH/DELETE.

### Via curl

```bash
curl -sS -X POST http://localhost:8000/api/v1/projects \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My First Project",
    "project_type": "NEW",
    "source": "PPM",
    "created_by": "pradip",
    "configuration": {
      "context": "c", "goals": "g", "scope": "s", "constraints": "n",
      "tech_stack": {"backend": ["Python"]}, "coding_standards": "PEP 8"
    }
  }'
```

Pipe to `python3 -m json.tool` or `jq` to prettify.

---

## 7. Fetch / update / delete

Replace `<ID>` with the id you got from POST.

```bash
# Fetch
curl -sS http://localhost:8000/api/v1/projects/<ID>

# Partial update — change status and one config field
curl -sS -X PATCH http://localhost:8000/api/v1/projects/<ID> \
  -H "Content-Type: application/json" \
  -d '{"status": "ACTIVE", "configuration": {"goals": "Updated goals"}}'

# Delete (cascades to configuration)
curl -sS -X DELETE http://localhost:8000/api/v1/projects/<ID> -w "%{http_code}\n"
```

Allowed enum values:
- `project_type`: `NEW`, `EXISTING`
- `source`: `PPM`, `OTHER`
- `status`: `DRAFT` (auto on create), `ACTIVE`, `ARCHIVED`

Response codes:

| Status | Meaning |
|---|---|
| 201 | Created |
| 200 | GET / PATCH success |
| 204 | Delete success (empty body) |
| 404 | `project_not_found` |
| 422 | Validation failure (Pydantic or domain) |
| 500 | Persistence failure |

---

## 8. Inspect data in Adminer

1. Open http://localhost:8080
2. Log in with the credentials from step 5
3. Click the `projects` or `project_configurations` table on the left
4. Click **Select data** to see rows

The two tables have a 1:1 relationship enforced by `UNIQUE(project_id)` and
`FK ... ON DELETE CASCADE` — deleting a project row also removes its
configuration.

---

## 9. Watch logs

```bash
# tail all services
docker compose -f local.yml logs -f

# just the api
docker compose -f local.yml logs -f api
```

You'll see structured log lines like:

```
synapse-api  | 2026-08-25 04:26:07 INFO [app.services.project_service] create_project succeeded id=8402b804-...
```

---

## 10. Common commands

```bash
docker compose -f local.yml ps                 # what's running
docker compose -f local.yml logs -f api        # tail API logs
docker compose -f local.yml restart api        # after code change (no rebuild)
docker compose -f local.yml up -d --build      # after code / deps change (rebuild)
docker compose -f local.yml down               # stop, keep DB data
docker compose -f local.yml down -v            # stop + wipe DB volume (full reset)
```

To run alembic manually inside the api container (rare — it auto-runs on
start):

```bash
docker compose -f local.yml exec api alembic current
docker compose -f local.yml exec api alembic history
docker compose -f local.yml exec api alembic downgrade -1
```

---

## 11. Troubleshooting

### "Cannot connect to the Docker daemon"

Docker Desktop isn't running. Start it and wait ~15s.

### `synapse-api` keeps restarting

Check its logs:

```bash
docker compose -f local.yml logs api | tail -40
```

Most likely causes:
- Postgres not yet healthy when api started (rare with the `depends_on: condition: service_healthy` gate — should self-recover).
- `.env` missing or malformed — the container reads `DATABASE_*` values from
  its environment. Rebuild after editing `.env`:
  `docker compose -f local.yml up -d --build`.

### `curl: (7) Failed to connect to localhost port 8000`

The api container isn't up. Check `docker compose ps` — if it's not listed
or shows `Restarting`, see previous item.

### 404 `project_not_found` for a UUID that "should exist"

You probably fetched the **Swagger example placeholder**
`3fa85f64-5717-4562-b3fc-2c963f66afa6` instead of the real id returned by
POST. Copy the id from the POST response body and use that.

### Adminer says "Connection refused" or "unknown server"

In Adminer, the **Server** field must be `postgres` (the container name on
the compose network), not `localhost`.

### Port already in use (5432 / 8000 / 8080)

Something else on your host is using that port. Either stop it, or change the
host-side mapping in `.env` (`DATABASE_PORT`, `APP_PORT`) and Adminer's
mapping in `local.yml`.

### Schema seems out of date after a code change

The api container auto-runs `alembic upgrade head` on start. If you added a
new migration, restart or rebuild the api service:

```bash
docker compose -f local.yml restart api          # migration only ran, no image rebuild needed
docker compose -f local.yml up -d --build        # if you also changed code / requirements
```

### Full reset — start from a truly empty state

```bash
docker compose -f local.yml down -v              # drops DB volume
docker compose -f local.yml up -d --build
```

---

## 12. Running the test suite (optional, needs Python on host)

The included test suite runs on the host, not in the api container.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
pytest -q
```

The integration tests hit the running Docker Postgres and use FastAPI's
`TestClient` (they do **not** need the api container — only Postgres).

---

## 13. Tearing down

```bash
docker compose -f local.yml down
```

This stops all three containers but keeps the DB volume, so restarting later
picks up where you left off. To wipe the DB too:

```bash
docker compose -f local.yml down -v
```

That's it. You're set up end to end.
