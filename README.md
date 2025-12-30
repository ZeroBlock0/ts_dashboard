# TS Dashboard

A comprehensive dashboard for TeamSpeak 5, featuring event monitoring, chat logging, and server administration tools.

## Features

- **Dashboard**: Real-time monitoring of TeamSpeak events (Client Moved, Text Message, etc.).
- **Chat Monitor**: View chat logs from the server.
- **Server Admin**: 
  - View Server Info, Channel List, Client List, Ban List.
  - Execute administrative actions: Kick, Poke, Global Message.
  - Send custom ServerQuery commands.
- **Settings**: 
  - Configure connection details for both Remote Apps (WebSocket) and ServerQuery (Telnet).
  - **Auto Connect**: Toggle automatic connection on startup.
  - **Manual Control**: Connect/Disconnect buttons with status indicators.
  - **API Key**: Manage your TeamSpeak Remote Apps API Key directly.

> **Note**: Configuration is saved in `ts_config.json`. If the application fails to start, try deleting this file to reset settings.

## Setup

1. **Enable Remote Apps in TeamSpeak**:
   - Go to TeamSpeak Options -> Remote Apps.
   - Ensure the WebSocket server is running (default port 5899).

2. **Run the Application**:
   - Run `TS_Dashboard.exe` (Windows) or `TS Dashboard.app` (macOS).
   - On first run, TeamSpeak will ask you to authorize the application. Click "Allow".

3. **ServerQuery Connection (Optional)**:
   - To use Server Admin features, go to the **Settings** tab.
   - Enter your ServerQuery credentials (IP, Port, Username, Password).
   - Click "Save & Reconnect" or use the individual Connect buttons.

## Development & Building

This project uses `uv` for dependency management and `Nuitka` for compilation.

### Prerequisites

- [uv](https://github.com/astral-sh/uv) installed.
- **Windows**: Visual Studio Build Tools (C++ Desktop Development workload).
- **macOS**: Xcode Command Line Tools.

### Build Instructions

The project includes one-click build scripts that handle environment setup and compilation.

**Windows:**
```powershell
.\build_nuitka.bat
```
The executable will be generated at `dist_nuitka\TS_Dashboard.exe`.

**macOS:**
```bash
chmod +x build_nuitka.sh
./build_nuitka.sh
```
The application bundle will be generated at `dist_nuitka/TS Dashboard.app`.

### Running from Source

```bash
uv sync
uv run main.py
```

### Release Process

To release a new version:

1.  Update the version number in `_version.py`.
2.  Run the release script:

    **Windows:**
    ```powershell
    .\release.bat
    ```

    **macOS / Linux:**
    ```bash
    ./release.sh
    ```

This script will:
- Sync the version to `pyproject.toml`.
- Commit all changes.
- Push to the `main` branch.
- Create and push a git tag (e.g., `v1.0.0`), which triggers the CI/CD workflow.

