# WHOOP MCP Server

A Model Context Protocol (MCP) server for accessing WHOOP wearable health data.

## Features

- **User Profile**: Get user profile and body measurements
- **Cycles**: Physiological cycles with strain, recovery, and sleep data
- **Sleep**: Sleep sessions with stage summaries and performance metrics
- **Recovery**: Daily recovery scores with HRV, RHR, SpO2, and skin temperature
- **Workouts**: Activity data with strain, heart rate zones, and distance

## Setup

### 1. Create a WHOOP Developer App

1. Go to [WHOOP Developer Dashboard](https://developer-dashboard.whoop.com)
2. Create a new application
3. Add redirect URI: `http://localhost:8888/callback`
4. Note your **Client ID** and **Client Secret**

### 2. Configure Credentials

```bash
cp config/.env.example config/.env
```

Add your client credentials to `config/.env`:

```bash
WHOOP_CLIENT_ID=<client_id>
WHOOP_CLIENT_SECRET=<client_secret>
```

### 3. Get Your Tokens

```bash
uv run python scripts/get_token.py
```

The script reads credentials from `config/.env` and opens your browser for WHOOP authorization. After authorization, copy the output tokens to `config/.env`:

```bash
WHOOP_ACCESS_TOKEN=<access_token>
WHOOP_REFRESH_TOKEN=<refresh_token>
```

With all values configured, tokens will automatically refresh when expired.

## Usage

### Docker Compose

```bash
docker compose up -d
```

The `docker-compose.yml` file automatically loads environment variables from `config/.env`.

### Local

```bash
uv sync
uv run python -m app.main
```

The server runs on `http://localhost:8000/mcp`.

### Pushing to Docker Hub

Build and push the image:

```bash
docker compose build
docker push healthkowshik/whoop-mcp-server:latest
```

Make sure you're logged in to Docker Hub first:

```bash
docker login
```

### MCP Client Configuration

Add to your MCP client config (e.g., Claude Desktop or Cursor):

```json
{
  "mcpServers": {
    "whoop": {
      "url": "http://localhost:8000/mcp"
    }
  }
}
```

## Available Tools

| Tool | Description |
|------|-------------|
| `get_user()` | Get user profile and body measurements |
| `get_cycles(start, end, limit)` | Get physiological cycles |
| `get_cycle(cycle_id)` | Get single cycle with sleep and recovery |
| `get_sleeps(start, end, limit)` | Get sleep sessions |
| `get_sleep(sleep_id)` | Get single sleep session |
| `get_recoveries(start, end, limit)` | Get recovery records |
| `get_recovery(cycle_id)` | Get recovery for specific cycle |
| `get_workouts(start, end, limit)` | Get workout records |
| `get_workout(workout_id)` | Get single workout |

## Data Units

- **Durations**: Milliseconds
- **Timestamps**: ISO 8601 with timezone
- **Heart Rates**: BPM
- **Strain**: 0-21 scale
- **Percentages**: 0-100 scale
- **Distances**: Meters
- **Energy**: Kilojoules
- **Temperature**: Celsius

## License

MIT
