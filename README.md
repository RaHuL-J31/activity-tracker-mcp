# 🏃‍♂️ Strava Activity Tracker MCP

A powerful Model Context Protocol (MCP) server that connects your Strava training data to Claude. This server allows Claude to act as your personal running coach, performance analyst, and training partner.

## 🌟 Features

- **Personal Running Coach**: Generate custom 5k, 10k, HM, or Marathon plans based on your actual fitness levels.
- **Deep Performance Analysis**: Per-kilometer breakdown of pace, heart rate efficiency, and cardiac drift.
- **Personal Records (PRs)**: Instant access to your all-time best efforts (1k, 5k, 10k, etc.) and lifetime totals.
- **Smart Activity Filtering**: Automatically finds the right activity type (Run, Ride, Walk) even if you've done other workouts since.

---

## 🚀 Quick Start

### 1. Prerequisites
- **Python 3.11+**
- **uv** (Fast Python package manager)
  - [Install uv](https://github.com/astral-sh/uv) if you haven't already.
- **Strava API Credentials**: [Click here to see the setup guide](#-detailed-strava-api-setup-guide).

### 2. Setup
Clone the repository and run the sync:
```bash
uv sync
```

### 3. Configuration
1. Copy `.env.example` to `.env`.
2. Fill in your `STRAVA_CLIENT_ID` and `STRAVA_CLIENT_SECRET`.
3. Your `.env` should initially look like this:
   ```env
   STRAVA_CLIENT_ID=12345
   STRAVA_CLIENT_SECRET=abc123yoursecret
   STRAVA_ACCESS_TOKEN=''
   STRAVA_REFRESH_TOKEN=''
   STRAVA_TOKEN_EXPIRES_AT=0
   ```
   > **Note**: Even if the Strava dashboard shows you an "Access Token," it usually lacks the necessary permissions (scopes) to read your activity data. Running the script in the next step ensures you have the correct `activity:read_all` access.

### 4. Authentication
Run the helper script to authorize the app and get your tokens:
```bash
uv run scripts/get_token.py
```
- A browser window will open. Click **Authorize**.
- You will be redirected to a localhost URL. **Copy the complete URL** from the browser.
- Paste it back into your terminal. Your tokens are now saved in `.env`.

---

## 🛠️ Testing & Verification

Always run commands from the **project root**.

| Command | Purpose |
| :--- | :--- |
| `uv run scripts/health.py` | Basic check for `.env` and API connectivity. |
| `uv run scripts/mcp-integration-test.py` | Full test of all 5 MCP tools with real data. |
| `uv run scripts/get_token.py` | Do not Run this command if you haven't faced "Unauthorized" errors while running above commands. Run this if you face "Unauthorized" errors to refresh tokens. No need to provide client id and secret every time as it is stored in .env file. This is a one time process. |
---

## 🤖 Claude Desktop Integration

Add this to your `claude_desktop_config.json`:

### Windows
```json
"mcpServers": {
  "strava": {
    "command": "uv",
    "args": [
      "run",
      "--directory",
      "C:\\Path\\To\\activity-tracker-mcp",
      "src\\main.py"
    ]
  }
}
```

### macOS / Linux
```json
"mcpServers": {
  "strava": {
    "command": "uv",
    "args": [
      "run",
      "--directory",
      "/path/to/activity-tracker-mcp",
      "src/main.py"
    ]
  }
}
```

---

## 🔍 Available Tools & Example Queries

| Tool | Description | Example Questions |
| :--- | :--- | :--- |
| **`check_strava_connection`** | Verifies if Claude can talk to Strava. | "Is my Strava connection working?" |
| **`get_recent_activities`** | Lists your latest workouts. | "Show me my last 5 activities." |
| **`analyze_workout`** | Detailed per-km split & HR analysis. | "Analyze my last run and check for heart rate drift." |
| **`get_personal_records`** | Shows lifetime totals and PRs. | "What are my PRs for 5k and 10k?" |
| **`generate_training_plan`** | AI Coach creates a week-by-week plan. | "I want to run a sub-50min 10k in 10 weeks. Build me a plan." |

---

## ⚠️ Notes
- **Metric by Default**: This server prioritizes metric units (km, meters) for precision in analysis.
- **Safety**: The Coach tool will deny unrealistic goals (e.g., Marathon in 1 week) to prevent injury.
- **Privacy**: Your `.env` file contains sensitive tokens. Never commit it to version control.

---

## 🔑 Detailed Strava API Setup Guide

Follow these steps to get your credentials if you don't have them yet:

1.  **Login to Strava**: Visit the [Strava API Settings](https://www.strava.com/settings/api).
2.  **Create Application**: You will be taken to the "My API Application" page.
    *   **Application Name**: Give it any name (e.g., "My Activity Tracker"). *Note: Do not use "Strava" in the name.*
    *   **Category**: Select `Performance Analysis`.
    *   **Club**: Select `None`.
    *   **Website**: Use `www.website.com` for now.
    *   **Application Description**: You can leave this empty.
    *   **Authorization Callback Domain**: Set this to `localhost` (**Crucial step!**).
3.  **Upload Logo**: Strava requires a logo to create the app. You can find a [logo.png](logo.png) in this repository that you can use, or upload your own.
4.  **Get Credentials**: Once the application is created, you will see your **Client ID** and **Client Secret**.
5.  **Update .env**: Copy these two values into your `.env` file and save it. You can ignore the "Access Token" shown on that page for now, as the `get_token.py` script will handle authentication for you.
