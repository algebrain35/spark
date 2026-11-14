# 7. Chat

Chat delivers messages between matched users in real time over a WebSocket, saves every message in PostgreSQL, and uses Redis pub/sub to reach users connected to a different worker process. The chat module owns the `messages` table and every WebSocket connection. It learns whether a chat is allowed only by calling `swipes.get_active_partner(match_id, user_id)`.

## Connecting

Each phone opens one WebSocket when the app opens: `/ws?token=<JWT>`. The server checks the token through the auth module **before** accepting. An invalid token rejects the handshake (close code 1008) (D20).

Each worker keeps a map from user to the sockets it holds. A user can have more than one socket: two devices, or an old socket that hasn't been cleaned up yet when the phone reconnects. Each socket removes only itself when it closes, so the order connections open and close in never matters.

## Frames

Every frame is a JSON object with a `type`.

| Type | Direction | Fields | Purpose |
|---|---|---|---|
| `send` | phone → server | `match_id`, `body`, `client_msg_id` | Send a message |
| `read` | phone → server | `match_id`, `up_to` | "I have seen everything up to this message" |
| `ack` | server → sender | `client_msg_id`, `id` | The message is saved; here is its ID |
| `message` | server → both users | `id`, `match_id`, `sender_id`, `body` | A new message |
| `read` | server → both users | `match_id`, `reader_id`, `up_to` | Read receipt |
| `chat_closed` | server → both users | `match_id` | The match was unmatched or blocked |
| `error` | server → sender | `reason`, `client_msg_id` | The frame was rejected; the connection stays open |

A malformed frame (bad JSON, missing field, body outside 1 to 2,000 characters) gets an `error` frame back and never closes the connection.

## Sending a message

1. **Check the frame.** `match_id` is a UUID and `body` is 1 to 2,000 characters.
2. **Check the match.** `swipes.get_active_partner` returns the other user, or nothing if the sender isn't in the match or it was unmatched. Blocking also unmatches (D19), so this one check covers blocks.
3. **Save.** Insert into `messages`, returning the new UUIDv7 `id`.
4. **Deliver.** Publish the `message` frame to the partner's channel and to the sender's own channel (for their other devices).
5. **Acknowledge.** Send `ack` to the sending socket.

**Why save before acknowledging (D18).** The ack promises the message is stored, and its `id` only exists once the database creates it. If the insert were queued instead, a failed job would leave the sender seeing "sent" for a message that disappears on reload.

The outgoing `message` frame is built from values the server trusts. The client's frame is never forwarded, so a client can't fake `sender_id`.

## Delivery across workers

Every socket lives in the worker process that accepted it. Workers never deliver directly. They publish to Redis, and every worker listens.

- Each worker runs **one** listener, started at startup. It subscribes to the pattern `chat:user:*` and to the `match.unmatched` event (D23).
- The listener delivers only to sockets **this worker** holds. It never re-publishes; if it did, a user would get one copy per worker.
- If Redis drops, the listener logs the error and reconnects after one second instead of stopping silently.
- The listener must run in the web process, next to the sockets. It cannot move to the background-worker process.

## Catching up

Redis pub/sub stores nothing, so anything sent while a phone is offline or reconnecting is missed live. PostgreSQL is the source of truth (D24).

`GET /matches/{match_id}/messages?after=<id>` returns up to 100 messages newer than `after`, ordered by `id`. It uses the `(match_id, id)` index. Without `after`, it loads the start of a chat.

**Reconnect order (D21):**

1. Remember the newest message ID the phone already has.
2. Open the WebSocket. Live messages start arriving.
3. Fetch messages after the ID from step 1.
4. Merge both, drop duplicates by `id`, and sort by `id`. UUIDv7 is time-ordered, so this is chronological.

Connecting first means no message can slip through the gap between the fetch and the connection. The cost is that a message may arrive twice, which step 4 handles. The phone must not move its "newest ID" forward from a live message before the fetch returns, or it would skip what it missed.

## Read receipts

When a user views a chat, the phone sends `read` with `up_to`, the newest message it has displayed (D22). The server sets `read_at = now()` on the other person's messages in that match with `id <= up_to` that are not yet read. If no rows change, nothing is published. Otherwise a `read` frame goes to the partner (their "read" ticks) and to the reader's other devices (to clear unread badges).

`up_to` is used instead of "mark everything" so that a message arriving while the chat screen loads isn't marked read before it is seen.

## Unmatch and block while a chat is open

Swipes owns `matches`. After an unmatch (or a block, which calls it) commits, swipes publishes `match.unmatched` with `match_id`, `user_a` and `user_b`. The channel name lives in the shared `app/events.py`. Every chat listener receives the event and sends `chat_closed` to both users' local sockets. The phone leaves the chat and removes the match from the list.

If the event is lost, the next `send` returns `invalid_match`, which the phone treats the same as `chat_closed`.

## Known gaps

- **Lost live delivery.** If publishing to Redis fails, the message is still saved and appears on the recipient's next fetch. Publish errors are logged rather than raised, so the sender doesn't see a failure, retry, and create a duplicate.
- **Message during unmatch.** A message checked just before an unmatch commits can be saved after it. It is never shown, because history also requires an active match.
- **Token in the URL.** The JWT can appear in server logs.
- **Push notifications** for offline recipients are not built yet. They will go through the worker queue (design rule 3).

**At scale.** Chat is the first module to split into its own service (D3), because long-lived connections scale with memory and connection count, not CPU. Before that:

- Each worker subscribes to `chat:user:{id}` when a user's first socket connects and unsubscribes when the last one closes, so it no longer receives every message.
- `match.unmatched` moves to the transactional outbox described for `match.created`.
- Socket auth switches to a short-lived, single-use ticket instead of the JWT in the URL.
- `messages` is partitioned by `match_id`, as section 4 describes; every chat query already filters on it.

---

## Decision log additions (section 13)

| ID | Decision | Choice | Status | Reason |
|---|---|---|---|---|
| D17 | Real-time transport | One WebSocket per device; Redis pub/sub between workers | Decided | Server pushes instantly; polling trades latency for wasted requests. Follows design rule 1 |
| D18 | Order of save and ack | Insert the message, publish, then ack | Proposed | The ack promises the message is stored and carries its database ID |
| D19 | Blocking and matches | Blocking also unmatches, in the same transaction | Proposed | One check (`get_active_partner`) covers both; safety must call swipes to unmatch |
| D20 | WebSocket auth | JWT in the query string, checked before accepting | Proposed | Simple at demo scale; replaced by a short-lived ticket at scale |
| D21 | Reconnect order | Connect, then fetch missed messages, dedupe by ID | Proposed | Fetching first leaves a gap where messages are lost |
| D22 | Read receipts | `read` frame with an `up_to` message ID | Proposed | Ordered IDs mean one ID covers the whole chat; never marks unseen messages read |
| D23 | Redis subscription | One pattern subscription per worker; per-user deferred | Proposed | Simplest correct option at demo scale |
| D24 | Missed live messages | Accepted; PostgreSQL is the source of truth and phones catch up | Proposed | Pub/sub stores nothing; history fetch covers every gap |
