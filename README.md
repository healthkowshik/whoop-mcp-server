# WHOOP MCP Server

A Model Context Protocol (MCP) server for accessing WHOOP wearable health data.

## Features

- **User Profile**: Get user profile and body measurements
- **Cycles**: Physiological cycles with strain, recovery, and sleep data
- **Sleep**: Sleep sessions with stage summaries and performance metrics
- **Recovery**: Daily recovery scores with HRV, RHR, SpO2, and skin temperature
- **Workouts**: Activity data with strain, heart rate zones, and distance

## Installation

```bash
# Clone and install
git clone https://github.com/healthkowshik/whoop-mcp-server.git
cd whoop-mcp-server
uv sync
```

## Setup

### 1. Create a WHOOP Developer App

1. Go to [WHOOP Developer Dashboard](https://developer-dashboard.whoop.com)
2. Create a new application
3. Add redirect URI: `http://localhost:8888/callback`
4. Note your **Client ID** and **Client Secret**

### 2. Get Your Access Token

```bash
uv run python scripts/get_token.py
```

This opens your browser for WHOOP authorization and outputs the access token.

### 3. Configure

```bash
cp config/.env.example config/.env
```

Paste your access token in `config/.env`.

> **Note:** WHOOP tokens expire. Re-run `scripts/get_token.py` when you get 401 errors.

## Usage

### Run the server

```bash
uv run python -m app.main
```

### Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "whoop": {
      "command": "uv",
      "args": ["run", "python", "-m", "app.main"],
      "cwd": "/path/to/whoop-mcp-server"
    }
  }
}
```

## Available Tools

| Tool | Description |
|------|-------------|
| `get_user()` | Get user profile and body measurements |
| `get_cycles(start, end, limit)` | Get physiological cycles |
| `get_cycle(cycle_id, include_sleep, include_recovery)` | Get single cycle with optional related data |
| `get_sleeps(start, end, limit)` | Get sleep sessions |
| `get_sleep(sleep_id)` | Get single sleep session |
| `get_recoveries(start, end, limit)` | Get recovery records |
| `get_recovery(cycle_id)` | Get recovery for specific cycle |
| `get_workouts(start, end, limit)` | Get workout records |
| `get_workout(workout_id)` | Get single workout |

## Data Units

- **Durations**: Milliseconds (convert to hours: `ms / 3,600,000`)
- **Timestamps**: ISO 8601 with timezone
- **Heart Rates**: BPM
- **Strain**: 0-21 scale
- **Percentages**: 0-100 scale
- **Distances**: Meters
- **Energy**: Kilojoules (kJ)
- **Temperature**: Celsius

## License

MIT
