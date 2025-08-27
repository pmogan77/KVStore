# KVStore

A simple in-memory key-value store with **nested transactions**, **MVCC (snapshot isolation)**, and **SQLite persistence**, exposed via a **Flask API**. Dockerized for easy setup.

---

## Features

- **In-memory key-value store** with:
  - Nested transactions
  - Snapshot isolation (MVCC)
  - Rollback/commit support
- **Persistence** to SQLite
- **Flask API** for CRUD operations
- Fully **Dockerized**
- Unit tests included

---

## Requirements

- Docker
- (Optional) Python 3.11+ if running without Docker
- Make (if using Makefile)

---

## Quick Start (Docker + Makefile)

### 1. Build the Docker image

```bash
make build
```

### 2. Run the Flask API

```bash
make run
```

- API is exposed on `http://localhost:5000`
- SQLite database persists to the container’s filesystem (`store.sqlite` inside container). Use Docker volumes for persistence outside the container.

### 3. Run unit tests

```bash
make test
```

- Uses the same Docker image and environment as the app
- Ensures consistency between app and test runs

### 4. Stop and remove the running container

```bash
make stop
```

### 5. Run a shell inside the container (for debugging)

```bash
make shell
```

---

## Flask API Endpoints

| Method | Endpoint         | Description                        | Payload Example                     |
|--------|------------------|------------------------------------|-------------------------------------|
| GET    | `/get/<key>`     | Get value for a key                | N/A                                  |
| POST   | `/set`           | Set value for a key                | `{ "key": "foo", "value": "bar" }` |
| POST   | `/delete/<key>`  | Delete a key                       | N/A                                  |
| POST   | `/begin`         | Start a new transaction            | N/A                                  |
| POST   | `/commit`        | Commit the current transaction     | N/A                                  |
| POST   | `/rollback`      | Rollback the current transaction   | N/A                                  |
| GET    | `/snapshot`      | Get resolved view of current state | N/A                                  |

---

## Example Requests

> All examples assume the API is running locally at `http://localhost:5000`.

### 1) Quick sanity check

```bash
curl -s http://localhost:5000/snapshot | jq
```

**Sample response**
```json
{}
```

### 2) Basic CRUD

**Set a key**
```bash
curl -s -X POST http://localhost:5000/set   -H 'Content-Type: application/json'   -d '{"key":"foo","value":"bar"}' | jq
```

**Get a key**
```bash
curl -s http://localhost:5000/get/foo | jq
```

**Sample response**
```json
{"key": "foo", "value": "bar"}
```

**Delete a key**
```bash
curl -s -X POST http://localhost:5000/delete/foo | jq
```

**Get after delete (404)**
```bash
curl -i http://localhost:5000/get/foo
```

### 3) Transactions

**Start a transaction**
```bash
curl -s -X POST http://localhost:5000/begin | jq
```

**Set values inside the transaction**
```bash
curl -s -X POST http://localhost:5000/set   -H 'Content-Type: application/json'   -d '{"key":"a","value":"1"}' | jq

curl -s -X POST http://localhost:5000/set   -H 'Content-Type: application/json'   -d '{"key":"b","value":"2"}' | jq
```

**See the transaction-local state**
```bash
curl -s http://localhost:5000/snapshot | jq
```

**Sample response**
```json
{"a": "1", "b": "2"}
```

**Commit**
```bash
curl -s -X POST http://localhost:5000/commit | jq
```

**Verify committed state**
```bash
curl -s http://localhost:5000/snapshot | jq
```

### 4) Rollback

```bash
curl -s -X POST http://localhost:5000/begin | jq
curl -s -X POST http://localhost:5000/set   -H 'Content-Type: application/json'   -d '{"key":"temp","value":"42"}' | jq
curl -s http://localhost:5000/snapshot | jq    # shows temp
curl -s -X POST http://localhost:5000/rollback | jq
curl -s http://localhost:5000/snapshot | jq    # temp is gone
```

### 5) Nested transactions

```bash
# Outer begin
curl -s -X POST http://localhost:5000/begin | jq

# Set x in outer txn
curl -s -X POST http://localhost:5000/set   -H 'Content-Type: application/json'   -d '{"key":"x","value":"outer"}' | jq

# Inner begin
curl -s -X POST http://localhost:5000/begin | jq

# Override x in inner txn
curl -s -X POST http://localhost:5000/set   -H 'Content-Type: application/json'   -d '{"key":"x","value":"inner"}' | jq

# Snapshot inside inner shows "inner"
curl -s http://localhost:5000/snapshot | jq

# Rollback inner; x should revert to "outer"
curl -s -X POST http://localhost:5000/rollback | jq
curl -s http://localhost:5000/snapshot | jq

# Commit outer
curl -s -X POST http://localhost:5000/commit | jq
```

### 6) Python requests examples

```python
import requests
base = "http://localhost:5000"

# Set
requests.post(f"{base}/set", json={"key": "lang", "value": "python"}).json()

# Get
requests.get(f"{base}/get/lang").json()

# Transaction
requests.post(f"{base}/begin")
requests.post(f"{base}/set", json={"key": "n", "value": 1})
requests.get(f"{base}/snapshot").json()  # {"lang":"python", "n":1}
requests.post(f"{base}/commit")
```

### 7) Common error cases

**Getting a missing key**
```bash
curl -i http://localhost:5000/get/does-not-exist
```

Expected: `404 Not Found`.

**Commit without a transaction**
```bash
curl -i -X POST http://localhost:5000/commit
```

Expected: `400 Bad Request` with a helpful error message.

---

## SQLite Persistence

- Data is saved in `store.sqlite` inside the container.
- To persist across container restarts, mount a volume:

```bash
docker run -d -p 5000:5000 -v $(pwd)/data:/app kvstore-app
```

- Your SQLite file will then persist in `./data/store.sqlite`.

---

## Project Structure

```
.
├── store.py           # Core KV store implementation with MVCC
├── api.py             # Flask API exposing the store
├── test_store.py      # Unit tests for KV store
├── Dockerfile
├── Makefile           # Build/run/test automation
└── README.md
```

---

## Development Notes

- Transactions are **atomic** and provide **snapshot isolation**.
- `flush_to_sqlite()` is used internally to persist the store.
- The store is **thread-safe** for single-threaded Flask deployment. For multi-threaded servers, consider separate SQLite connections per thread.

---

## License

MIT License
