# Autonomous Learning Orchestrator (ALO)

Production-ready autonomous AI agent with ReAct reasoning, RAG integration, self-learning, and Telegram interface.

## Features

- **ReAct Reasoning**: Multi-step thought → action → observation loops
- **RAG System**: Semantic search with ChromaDB & sentence transformers  
- **Self-Learning**: Learns from every interaction, builds strategy playbooks
- **Telegram Bot**: Natural language task execution interface
- **Multi-Provider LLM**: Anthropic, OpenAI, or local models (Ollama)
- **Action Execution**: Bash, Python, files, web, Git, APIs
- **Safe Execution**: Sandboxed with configurable safety modes
- **Experience Memory**: Stores and retrieves successful strategies

## Quick Start

### 1. Installation

```bash
# Clone repo
cd alo_system

# Install dependencies
pip install -r requirements.txt

# Configure
cp .env.template .env
# Edit .env with your credentials
```

### 2. Get Telegram Bot Token

1. Message @BotFather on Telegram
2. Use `/newbot` command
3. Save token to `.env` as `TELEGRAM_BOT_TOKEN`
4. Get your user ID from @userinfobot → `TELEGRAM_ADMIN_ID`

### 3. Configure LLM

```bash
# For Anthropic (recommended)
LLM_PROVIDER=anthropic
LLM_API_KEY=sk-ant-xxx
LLM_MODEL=claude-sonnet-4-20250514

# For OpenAI
LLM_PROVIDER=openai
LLM_API_KEY=sk-xxx
LLM_MODEL=gpt-4

# For Local (Ollama)
LLM_PROVIDER=local
LLM_MODEL=llama2
LLM_BASE_URL=http://localhost:11434
```

### 4. Run

```bash
python main.py
```

## Telegram Commands

| Command | Description |
|---------|-------------|
| `/task [description]` | Execute autonomous task |
| `/learn [source]` | Add knowledge from file/URL/text |
| `/status` | System statistics |
| `/memory [query]` | Search past learnings |
| `/config` | View configuration |

## Task Examples

```
/task Create a Python script to analyze CSV files

/task Search for recent AI papers and summarize top 3

/task Clone my GitHub repo and run tests

/task Install pandas and create data analysis module
```

## Architecture

```
Telegram Bot → ReAct Engine → [RAG System, Learning System, Action Executor]
                                       ↓
                                  LLM Provider
```

**ReAct Loop**: Thought → Action → Observation → Reflection → Learn

**Components**:
- `main.py` - Telegram bot interface
- `react_engine.py` - Core ReAct reasoning loop  
- `rag_system.py` - Vector DB & semantic search
- `learning_system.py` - Experience memory & self-improvement
- `action_executor.py` - Execute various actions
- `llm_interface.py` - Multi-provider LLM abstraction
- `prompts.py` - System prompts for guidance
- `config.py` - Configuration management

## Available Actions

- `bash_execute` - Run shell commands
- `python_execute` - Execute Python code
- `file_read/write` - File operations
- `web_search` - Search the web
- `web_scrape` - Extract webpage content
- `git_operation` - Git clone/pull/push/commit
- `api_call` - HTTP API requests
- `rag_query` - Search knowledge base
- `install_package` - Install pip/apt packages
- `self_modify` - Create extension modules

## Configuration

Key `.env` variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `TELEGRAM_BOT_TOKEN` | Bot token | Required |
| `TELEGRAM_ADMIN_ID` | Your user ID | Required |
| `LLM_PROVIDER` | anthropic/openai/local | anthropic |
| `LLM_API_KEY` | API key | Required |
| `MAX_ITERATIONS` | Max reasoning loops | 10 |
| `CODE_EXECUTION_ENABLED` | Enable code exec | true |
| `SAFE_MODE` | Restrict file access | false |
| `AUTO_LEARN` | Learn from tasks | true |

## Security

**Safe Mode** (`SAFE_MODE=true`):
- File ops restricted to workspace
- Dangerous bash commands blocked
- Self-modification disabled

**Sandboxing**:
- Isolated workspace execution
- Timeouts on operations
- File size limits
- Audit logging

## Data Storage

```
alo_system/
├── data/
│   ├── vectordb/              # ChromaDB
│   └── memory/
│       ├── experiences.jsonl  # Task history
│       ├── patterns.json      # Learned patterns
│       └── playbook.json      # Strategy library
├── workspace/                 # Execution sandbox
└── logs/alo.log              # System logs
```

## Learning System

1. **Task Execution**: System executes task via ReAct loop
2. **Experience Storage**: Stores strategy, outcome, context
3. **Pattern Recognition**: Identifies common approaches
4. **Playbook Building**: Adds successful strategies
5. **RAG Integration**: Embeddings for semantic retrieval
6. **Future Use**: Leverages past learnings for new tasks

## Troubleshooting

**Bot not responding?**
- Verify token and admin ID in `.env`
- Check logs: `tail -f logs/alo.log`

**LLM errors?**
- Confirm API key validity
- Check model name spelling
- Verify quota/credits

**Installation issues?**
```bash
# ChromaDB issues
pip install chromadb --no-cache-dir

# Torch for embeddings
pip install torch --index-url https://download.pytorch.org/whl/cpu
```

## Performance

- Typical task: 10-30 seconds
- Memory: 500MB-2GB (depends on embedding model)
- Token usage: 2K-10K per task

## Extending

**Add custom action**:
```python
# In action_executor.py
def _your_action(self, params):
    return {"success": True, "output": "result"}
```

**Add knowledge**:
```python
from rag_system import rag_system
rag_system.add_directory("/path/to/docs")
```

## Requirements

- Python 3.9+
- Telegram bot token
- LLM API key (or local model)

## License

MIT License

## Security Note

This is an autonomous agent with code execution. Use responsibly and review generated code before production use.

---

Built with Anthropic Claude, ChromaDB, sentence-transformers, and python-telegram-bot.
# alo_system
