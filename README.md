# Palworld Discord Bot

A lightweight, production-ready Discord bot split into focused modules to manage a local Palworld server's state via its native REST API. This bot is designed to run completely headlessly in the Windows background, tracking player counts, managing dynamic status indicators, and executing graceful automated shutdowns.

## 🛠️ Architecture Overview

The system is decoupled across three specialized Python modules to keep the codebase maintainable:

*   **`main.py`**: The central supervisor. Handles bot initialization, Discord event tracking, and the asynchronous background loop for auto-shutdown checks.
*   **`commands.py`**: The interface layer. Holds all player-facing slash or text commands (`!start`, `!stop`, `!settings`).
*   **`api_client.py`**: The data layer. Manages the direct REST API handshake with the local Palworld server engine.

---

## 🌐 Network & Port Forwarding Setup

To allow players outside your local network to connect to your Palworld server, and to ensure the bot can securely talk to the server's backend, you must open the correct ports on your router.

### 1. Identify Your Ports
Palworld relies on two distinct network pathways. Log into your router's administration panel and forward the following ports to your server hosting machine's local static IP address:

| Protocol | Default Port | Purpose | Destination |
| :--- | :--- | :--- | :--- |
| **UDP** | `8211` | Game Traffic | Exposed to your players |
| **TCP** | `8212` | REST API | Kept local / Used by the Bot |

> ⚠️ **Security Warning:** Only expose port **`8211` (UDP)** to the internet. Keep port **`8212` (TCP)** bound to your local loopback (`127.0.0.1`) or local network. Never expose the REST API port publicly to the open internet, as it allows administrative controls over your server machine.

---

## ⚙️ Core Server Mechanics & Settings Configuration

To ensure your server communicates properly with the bot and protects player data against unexpected power losses, modify your native configuration file.

### 1. Locate the Configuration File
Navigate to your server's installation directory and locate the configuration file:
`.../Pal/Saved/Config/WindowsServer/PalWorldSettings.ini`

### 2. Apply Required Variables
Open the file in a text editor and update or append the following values inside the `[/Script/Pal.PalGameSetting]` options string:

```ini
; Enable the REST API so the bot can track player metrics and send commands
RESTAPIEnabled=True
RESTAPIPort=8212

; Set your secure administrative credentials
AdminPassword="your_secure_admin_password_here"

```

### 3. Smart Idle Auto-Shutdown
The background loop in `main.py` monitors player presence. If the player count drops to **0** and remains completely empty for **10 consecutive minutes**, the bot automatically communicates with the game API to gracefully save the world and shut down the server process to free up system RAM.

### 4. Explicit Manual Shutdown (`!stop`)
When an administrator calls the manual `!stop` command via Discord, the bot executes a safe two-step handshake while the system is fully stable:
1. Triggers `call_palworld_api("save")` to flush the absolute latest state to disk.
2. Triggers `call_palworld_api("shutdown")` only after the save handle closes cleanly.

---

## 🔧 Configuration Setup (`.env`)

The application handles credentials locally using an environment file. Create a file named `.env` in your working root directory:

```env
# Discord Settings
DISCORD_TOKEN=your_discord_bot_token_here
DISCORD_CHANNEL_ID=123456789012345678

# Palworld Server API Settings
PALWORLD_API_URL=http://127.0.0.1:8212
PALWORLD_ADMIN_PASSWORD=your_server_admin_password
```

> ⚠️ **Security Warning:** The `.env` file contains sensitive administrative credentials. It is explicitly blacklisted in `.gitignore` and must never be committed to source control.

---

## 📦 Production Deployment (Windows Executable)

To deploy the bot as a completely hidden, native background process that starts up automatically when your PC turns on, compile it into a single binary file.

### 1. Compile the Executable
Run PyInstaller with the headless configuration flags. 

*If your `.env` settings are fixed, embed them directly inside the binary:*
```bash
pyinstaller --onefile --noconsole --add-data ".env;." -n "PalworldDiscordBot" main.py
```

*If you prefer to keep your `.env` file external and editable next to the app:*
```bash
pyinstaller --onefile --noconsole -n "PalworldDiscordBot" main.py
```

### 2. Install to System
1. Move the finalized `PalworldDiscordBot.exe` out of your workspace `dist/` folder and into a dedicated deployment directory (e.g., `C:\Program Files\PalworldDiscordBot\` or `C:\Users\YourUsername\Documents\PalworldBot_Release`).
2. *(If using external config)* Move your active `.env` file into that exact same folder.
3. Right-click `PalworldDiscordBot.exe` ➔ Create Shortcut.
4. Press `Win + R`, type `shell:startup`, and hit Enter. Drop the shortcut inside this folder to enable **Auto-Run on boot**.

---

## 🛑 Managing the Background Process

Because the executable runs with the `--noconsole` flag, it will have no visible desktop window. 

*   **To verify it is running:** Check your Discord server—the bot will appear online displaying dynamic player counts (e.g., `Playing: Palworld (0/32 Players)`).
*   **To manually terminate:** Open **Task Manager** (`Ctrl + Shift + Esc`), scroll down to *Background Processes*, locate `PalworldDiscordBot`, right-click it, and select **End task**.
