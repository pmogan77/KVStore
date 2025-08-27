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

| Method | Endpoint         | Description                        | Payload Example                    |
|--------|------------------|------------------------------------|-----------------------------------|
| GET    | `/get/<key>`     | Get value for a key                 | N/A                               |
| POST   | `/set`           | Set value for a key                 | `{"key": "foo", "value": "bar"}` |
| POST   | `/delete/<key>`  | Delete a key                        | N/A                               |
| POST   | `/begin`         | Start a new transaction             | N/A                               |
| POST   | `/commit`        | Commit the current transaction      | N/A                               |
| POST   | `/rollback`      | Rollback the current transaction    | N/A                               |
| GET    | `/snapshot`      | Get resolved view of current state  | N/A                               |

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
