# Spark backend: chat module

```
app/
├── main.py              FastAPI app, shared lifespan, routers
├── events.py            Redis channel names shared between modules
├── redis_client.py      the one Redis client
├── chat/
│   ├── __init__.py      exposes router + lifespan
│   ├── connections.py   ConnectionManager (sockets held by this worker)
│   ├── protocol.py      frame formats, SendFrame / ReadFrame, send_error
│   ├── pubsub.py        publish_to_user, the per-worker Redis listener, lifespan
│   ├── handlers.py      handle_frame, handle_send, handle_read
│   └── routes.py        WebSocket /ws and GET /matches/{id}/messages
└── swipes/              PARTIAL: only what chat depends on
    ├── __init__.py
    └── service.py       get_active_partner (stub), publish_match_unmatched
```

## Not included (other modules provide these)

| Import | Expected |
| --- | --- |
| `app.settings.REDIS_URL` | e.g. `"redis://localhost:6379"` |
| `app.db.db` | an asyncpg pool |
| `app.auth.user_id_from_token(token)` | `UUID` or `None` |
| `app.auth.current_user_id` | FastAPI dependency returning the caller's `UUID` |
| `app.swipes.get_active_partner` | stubbed in `swipes/service.py`, to be written |

Requires Python 3.10+, `fastapi[standard]`, `redis>=5.0.1`, `asyncpg`.

## Run

```
fastapi dev app/main.py              # one worker
fastapi run app/main.py --workers 2  # test cross-worker delivery through Redis
```
