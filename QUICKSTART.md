# ALO Quick Start Guide

Get up and running in 5 minutes.

## Step 1: Install Dependencies

```bash
# Run setup script
bash setup.sh

# Or manually:
pip install -r requirements.txt
```

## Step 2: Get Telegram Bot Token

1. Open Telegram and message [@BotFather](https://t.me/BotFather)
2. Send `/newbot`
3. Follow instructions to create bot
4. Copy the token (looks like: `1234567890:ABCdefGHIjklMNOpqrsTUVwxyz`)

## Step 3: Get Your Telegram User ID

1. Message [@userinfobot](https://t.me/userinfobot)
2. Copy your user ID (number like: `123456789`)

## Step 4: Configure

Edit `.env` file:

```bash
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_ADMIN_ID=123456789

# For Anthropic
LLM_PROVIDER=anthropic
LLM_API_KEY=sk-ant-xxxxx
LLM_MODEL=claude-sonnet-4-20250514

# OR for OpenAI
LLM_PROVIDER=openai
LLM_API_KEY=sk-xxxxx
LLM_MODEL=gpt-4

# OR for Local (Ollama)
LLM_PROVIDER=local
LLM_MODEL=llama2
LLM_BASE_URL=http://localhost:11434
```

## Step 5: Test Installation

```bash
python test_system.py
```

Should see all green checkmarks.

## Step 6: Start Bot

```bash
python main.py
```

You should see: "Bot started successfully"

## Step 7: Test in Telegram

1. Open Telegram
2. Find your bot (the name you gave BotFather)
3. Send `/start`
4. Try: `/task Create a hello world Python script`

## Common Commands

```
/task [description]  - Execute autonomous task
/learn [source]      - Add knowledge  
/status              - System info
/memory [query]      - Search learnings
```

## Example Tasks

```
/task Analyze this CSV file and create a summary
/task Search for recent AI news and summarize
/task Create a Python script to fetch weather data
/task Install pandas and create a data analyzer
/task Clone my repo and run tests
```

## Troubleshooting

**Bot doesn't respond?**
- Check token and admin ID in `.env`
- Look at logs: `tail -f logs/alo.log`

**Import errors?**
- Run: `pip install -r requirements.txt`
- Try: `pip install chromadb --no-cache-dir`

**LLM errors?**
- Verify API key is correct
- Check you have credits/quota
- Try different model

## Next Steps

- Read [README.md](README.md) for full documentation
- Add your own knowledge: `/learn [URL]`
- Try complex multi-step tasks
- Check system status: `/status`

## Architecture Overview

```
You → Telegram Bot → ReAct Engine → Actions
                         ↓
                    RAG + Learning
                         ↓
                    LLM Provider
```

The system:
1. Understands your task
2. Plans approach using past learnings
3. Executes actions (code, web, files, etc.)
4. Reflects on results
5. Learns for next time

## Resources

- Full docs: [README.md](README.md)
- Configuration: `.env.template`
- Test system: `python test_system.py`
- Setup: `bash setup.sh`

---

**Ready to build autonomous agents? Start with `/task` and let ALO handle the rest!**
