# SpencerBot & Korean Language Learning Bot

A unified Discord bot with two distinct feature sets:
- **SpencerBot**: GPT chat, voice TTS, message summarization, fact-checking
- **Korean Bot**: 8 language learning modes powered by GPT-4o and Anki integration (restricted to one guild)

---

## 🧠 Features

### SpencerBot
* **🔊 TTS in Voice Channels** – Converts text to speech and plays in voice channels
* **🤖 ChatGPT Interface** – Chat with GPT, ask questions, generate ideas
* **✍️ Summarize Messages** – Summarize message threads in channels
* **📚 Fact-Check Claims** – Verify facts in messages with context
* **🍕 Domino's Tracker™** – Records when you last ordered Domino's
* **😭 Relapse Tracking** – Track and react to relapse events

### Korean Language Learning Bot (Guild-Restricted)
* **📚 8 Learning Modes** – Vocabulary, Translation, Audio, Dictation, Cloze, Reading, Writing, Building
* **🎯 Anki Integration** – Direct integration with Anki SQLite database for vocabulary management
* **🤖 AI-Powered Exercises** – GPT-4o generates contextual exercises and intelligent feedback
* **🔊 Text-to-Speech** – OpenAI TTS for pronunciation practice
* **👤 Per-User Sessions** – Maintain independent exercise sessions for each user
* **🔐 Guild Restriction** – Bot restricted to operate only in "Chil's server"

---

## 📁 Project Structure

The codebase is organized into modular files for maintainability and clarity:

### Main Entry Point
- **main.py** – Unified bot entry point; initializes SpencerBot and Korean bot

### SpencerBot Files
- **config.py** – Constants, logging setup, and configuration loading
- **state.py** – BotState dataclass for managing bot state
- **events.py** – SpencerBot event handlers
- **handlers.py** – Command handlers (dominos, chat, TTS, etc.)
- **utils.py** – Utility functions (file I/O, formatting, message handling)
- **dapi.py** – Discord API wrapper (reply, react, speak, disconnect)
- **oai.py** – OpenAI/GPT integration
- **audio.py** – OpenAI TTS integration for Korean bot

### Korean Language Learning Bot Files
- **korean_events.py** – Event handlers for Korean bot (guild-restricted routing)
- **korean_config.py** – Korean bot configuration from .env
- **korean_state.py** – Per-user exercise session state management
- **anki_db.py** – Anki SQLite database reader
- **gpt.py** – AsyncOpenAI GPT-4o wrapper (14 exercise generation/grading functions)
- **audio.py** – OpenAI TTS wrapper for audio exercises
- **anki_manager.py** – AnkiWeb sync via subprocess

### Korean Bot Cogs (Exercise Handlers)
- **cogs/korean/vocab.py** – Vocabulary generation (stateless)
- **cogs/korean/translate.py** – Translation exercises
- **cogs/korean/audio_cog.py** – Audio listening with TTS
- **cogs/korean/dictation.py** – Dictation exercises
- **cogs/korean/cloze.py** – Fill-in-the-blank exercises
- **cogs/korean/reading.py** – Reading comprehension
- **cogs/korean/write.py** – Free writing exercises
- **cogs/korean/build.py** – Sentence building exercises

### Configuration & Logging
- **.env** – All configuration for both SpencerBot and Korean bot (gitignored)
- **.env.example** – Configuration template
- **spencerbot.log** – SpencerBot debug/info logging (auto-rotates)
- **korean_bot.log** – Korean bot debug/info logging (auto-rotates)

---

## 🚀 Commands

### SpencerBot Commands
All commands are prefixed with `@bot mention` or `!command`

| Command | Description | Usage |
|---------|-------------|-------|
| `dominos` | Check time since last Domino's | `@bot dominos` |
| `relapse` | Reset dominos timer | `@bot relapse` |
| `st` | Toggle TTS on/off | `@bot st` |
| `l` / `stop` | Leave voice channel | `@bot l` |
| `summarize` | Summarize message thread | Reply to message: `@bot summarize` |
| `check` | Fact-check a message | Reply to message: `@bot check` |
| (default) | Chat with GPT | `@bot your message here` |

### Korean Language Learning Bot Commands
Text input in exercise channels (case-insensitive):

| Input | Description |
|-------|-------------|
| `[deck name]` | Select an Anki deck to practice |
| `list` | Show active deck and word count |
| `skip` | Reveal answer and generate next exercise |
| `stop` | End the current session |
| `[answer]` | Submit your response to be graded |

**Slash Commands:**
- `/sync` – Sync your Anki collection to AnkiWeb (guild-restricted)

---

## 🏗️ Code Quality

This bot was refactored following modern Python best practices:

✅ **Type Hints** – Full type annotations throughout
✅ **Docstrings** – Google-style docstrings on all functions
✅ **Error Handling** – Try-except blocks with logging
✅ **Logging** – Structured logging to console and file
✅ **Constants** – All magic values extracted to constants
✅ **Modular Design** – Clear separation of concerns
✅ **PEP 8 Compliance** – Proper formatting and naming conventions

---

## 🔧 Setup

### Prerequisites
1. Install dependencies: `pip install -r requirements.txt`
2. Copy `.env.example` to `.env` and fill in all required values

### Basic Configuration (.env)
```bash
# Core credentials
DISCORD_TOKEN=your_discord_bot_token_here
OPENAI_API_KEY=your_openai_api_key_here

# Optional: SpencerBot features
HF_TOKEN=your_hugging_face_token_here
CALORIE_TOKEN=your_calorie_api_token_here
FFMPEG_PATH=path/to/ffmpeg.exe
```

### Running the Bot
```bash
python main.py
```

### Korean Language Learning Bot (Optional Features)
If you want to enable the Korean Language Learning Bot:

1. Set `ALLOWED_GUILD_ID` to your Discord server ID (guild restriction)
2. Create 8 Discord channels in that server: #vocab, #translate, #audio, #dictation, #cloze, #reading, #write, #build
3. Get channel IDs and add to `.env`:
   ```
   CHANNEL_VOCAB=your_channel_id
   CHANNEL_TRANSLATE=your_channel_id
   # ... etc for all 8 channels
   ```
4. Install Anki and create Korean vocabulary decks (Field 0: Korean, Field 1: English)
5. Fill in Anki configuration in `.env`:
   ```
   ANKI_PROFILE=User 1
   ANKIWEB_USER=your_ankiweb_username
   ANKIWEB_PASS=your_ankiweb_password
   ```

See [.env.example](.env.example) for complete configuration reference.

---

## 📝 Notes

* This is a personal/private bot, but feel free to use it as a template
* All commands and reactions are customizable in `config.py`
* Voice profiles can be added in `config.py` under `VOICE_PROFILES`
