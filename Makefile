.PHONY: up down logs ingest seed web

# Start Postgres + the agent service.
up:
	docker compose up --build -d

down:
	docker compose down

logs:
	docker compose logs -f agent

# Embed the sample corpus into the knowledge base (runs inside the agent container).
ingest:
	docker compose exec agent python -m app.ingest /srv/corpus

# Seed a demo backlog of untriaged stories (idempotent; runs inside the agent container).
seed:
	docker compose exec agent python -m app.seed_stories

# Run the Next.js frontend locally (hot reload), pointed at the agent service.
web:
	cd web && npm install && npm run dev
