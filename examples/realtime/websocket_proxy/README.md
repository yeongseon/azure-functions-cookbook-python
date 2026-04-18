# websocket_proxy

Azure Functions front door for Azure Web PubSub that negotiates client tokens and forwards publish requests.

## Prerequisites

- Python 3.10+
- Azure Functions Core Tools v4
- Azure Web PubSub service

## Run Locally

```bash
cd examples/realtime/websocket_proxy
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp local.settings.json.example local.settings.json
func start
```

## Expected Output

- `POST /api/websocket/negotiate` returns Web PubSub access metadata.
- `POST /api/websocket/publish` forwards a message to a Web PubSub group.
- `POST /api/websocket/events` handles upstream callbacks from Web PubSub.
