# signalr_group_chat

SignalR-based group chat sample with negotiate, room join, and room-scoped broadcast endpoints.

## Prerequisites

- Python 3.10+
- Azure Functions Core Tools v4
- Azure SignalR Service in serverless mode

## Run Locally

```bash
cd examples/realtime/signalr_group_chat
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp local.settings.json.example local.settings.json
func start
```

## Expected Output

- `POST /api/chat/negotiate` returns SignalR connection metadata.
- `POST /api/chat/join` adds a user to a room.
- `POST /api/chat/message` emits a `newMessage` event to that room.
