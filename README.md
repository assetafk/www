Flash-Sale Reservations

Run

1) Create .env
cp .env.example .env

2) Start services
docker compose up -d --build

3) Check
curl -s http://localhost:8000/health

Migrations

Migrations are applied automatically on api container start.
If you need to run them manually:
docker compose run --rm api alembic upgrade head

Examples (curl)

Create product
curl -s -X POST "http://localhost:8000/products" -H "content-type: application/json" -d '{"name":"TV","stock":2}'

List products
curl -s "http://localhost:8000/products?limit=50&offset=0"

Create reservation
curl -s -X POST "http://localhost:8000/reservations" -H "content-type: application/json" -d '{"user_id":"u1","product_id":"<PRODUCT_ID>"}'

Confirm reservation
curl -s -X POST "http://localhost:8000/reservations/<RESERVATION_ID>/confirm"

Cancel reservation
curl -s -X POST "http://localhost:8000/reservations/<RESERVATION_ID>/cancel"

Sync expired reservations
curl -s -X POST "http://localhost:8000/admin/expired-reservations/sync?limit=500"

Metrics
curl -s "http://localhost:8000/admin/metrics"

Train dataset export
curl -s "http://localhost:8000/admin/train-dataset?mode=full&fmt=csv"
