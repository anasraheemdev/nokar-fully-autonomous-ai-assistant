# NOKAR Configuration Guide

This guide covers all configuration options, environment variables, audio settings, and integration parameters for **NOKAR – Fully Autonomous AI Assistant**.

---

## 1. Quick Configuration Methods

You can configure NOKAR using two primary methods:

1. **Graphical Setup**: On first launch, if `config/api_keys.json` does not exist, NOKAR displays an onboarding setup modal. You can also modify settings at any time via the **⚙ SETUP** and **🎛 CONTROLS** drawers in the top navigation bar.
2. **Configuration File**: Copy `config/api_keys.example.json` to `config/api_keys.json` and edit your parameters directly.
3. **Environment Variables**: Copy `.env.example` to `.env` to override configuration settings.

---

## 2. Configuration Schema (`config/api_keys.json`)

```json
{
  "gemini_api_key": "YOUR_GEMINI_API_KEY",
  "os_system": "windows",
  "assistant_name": "Nokar",
  "user_name": "Commander",
  "news_api_key": "OPTIONAL_NEWS_API_KEY",
  "weather_api_key": "OPTIONAL_OPENWEATHER_KEY",
  "default_city": "London",
  "autostart_enabled": false,
  "morning_brief_enabled": true,
  "ui_color": "#a855f7",
  "email": {
    "address": "user@example.com",
    "password": "YOUR_EMAIL_APP_PASSWORD",
    "smtp_host": "smtp.hostinger.com",
    "smtp_port": 465,
    "smtp_ssl": true,
    "imap_host": "imap.hostinger.com",
    "imap_port": 993,
    "imap_ssl": true,
    "pop_host": "pop.hostinger.com",
    "pop_port": 995,
    "pop_ssl": true,
    "protocol": "imap"
  },
  "voice_name": "Puck"
}
```

### Parameter Reference

| Parameter | Type | Required | Description |
|---|:---:|:---:|---|
| `gemini_api_key` | string | **Yes** | Primary Google Gemini API key ([Get a key](https://aistudio.google.com/app/apikey)) |
| `os_system` | string | No | Operating system identifier (`windows`, `darwin`, `linux`) |
| `assistant_name` | string | No | The name your assistant responds to (default: `Nokar`) |
| `user_name` | string | No | Your preferred salutation (e.g. `Commander` or your name) |
| `news_api_key` | string | No | Optional API key for NewsAPI headlines |
| `weather_api_key` | string | No | Optional OpenWeatherMap API key |
| `default_city` | string | No | City for morning weather forecasts |
| `autostart_enabled`| boolean| No | Register assistant with OS startup |
| `morning_brief_enabled`| boolean| No | Deliver briefing on first boot of the day |
| `ui_color` | string | No | Primary accent color in hex (e.g. `#a855f7` purple, `#00e5ff` cyan) |
| `voice_name` | string | No | Gemini voice: `Puck`, `Charon`, `Kore`, `Fenrir`, `Aoede` |

---

## 3. Email Suite Configuration

NOKAR's Proactive Executive Watchdog connects directly to your IMAP/SMTP provider:

```json
"email": {
  "address": "anasraheem@obrixlabs.com",
  "password": "YOUR_APP_PASSWORD",
  "smtp_host": "smtp.hostinger.com",
  "smtp_port": 465,
  "smtp_ssl": true,
  "imap_host": "imap.hostinger.com",
  "imap_port": 993,
  "imap_ssl": true
}
```

- **Hostinger Users**: Use `smtp.hostinger.com:465` (SSL) and `imap.hostinger.com:993` (SSL).
- **Gmail Users**: Use `smtp.gmail.com:465` and `imap.gmail.com:993` with a Google **App Password**.

---

## 4. Hotkeys & Global Shortcuts

| Shortcut | Function | Scope |
|---|---|---|
| **`F8` / `Alt+Space`** | Summon / dismiss floating Spotlight Search Bar | Global |
| **`F9`** | Trigger instant active-window Screen Vision query | Global |
| **`F11`** | Toggle Fullscreen HUD mode | Application |
| **`Ctrl+Space`** | Push-to-Talk (hold to speak, release to send) | Global (Windows) / App |
| **`Escape`** | Dismiss popovers, dialogs, and PiP cards | Application |

---

## 5. Audio Device Configuration

If your microphone or speakers are not detected:
1. Open **⚙ SETUP → 🎧 AUDIO DEVICES** in the application.
2. NOKAR automatically filters out redundant host API duplicate listings (MME vs DirectSound vs WASAPI).
3. Select your preferred device by name. NOKAR saves device selections by hardware name rather than volatile device indices.
