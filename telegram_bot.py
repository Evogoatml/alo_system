"""
Telegram Bot Interface for Autonomous Learning Orchestrator
Handles user interactions, command routing, and response streaming
"""

import os
import asyncio
import json
import logging
from typing import Optional
from datetime import datetime
from pathlib import Path

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)
from telegram.constants import ParseMode, ChatAction

from orchestrator import AutonomousOrchestrator, load_config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TelegramBot:
    """Telegram bot for ALO interaction"""
    
    def __init__(self, token: str, admin_id: str, orchestrator: AutonomousOrchestrator):
        self.token = token
        self.admin_id = admin_id
        self.orchestrator = orchestrator
        
        # Rate limiting
        self.user_last_command = {}
        self.rate_limit_seconds = 5
        
        # Active tasks
        self.active_tasks = {}
        
        self.app = Application.builder().token(token).build()
        self._register_handlers()
        
        logger.info("Telegram bot initialized")
    
    def _register_handlers(self):
        """Register all command and message handlers"""
        self.app.add_handler(CommandHandler("start", self.cmd_start))
        self.app.add_handler(CommandHandler("help", self.cmd_help))
        self.app.add_handler(CommandHandler("task", self.cmd_task))
        self.app.add_handler(CommandHandler("learn", self.cmd_learn))
        self.app.add_handler(CommandHandler("status", self.cmd_status))
        self.app.add_handler(CommandHandler("memory", self.cmd_memory))
        self.app.add_handler(CommandHandler("config", self.cmd_config))
        self.app.add_handler(CommandHandler("cancel", self.cmd_cancel))
        self.app.add_handler(CommandHandler("audit", self.cmd_audit))
        
        # Callback query handler for confirmations
        self.app.add_handler(CallbackQueryHandler(self.handle_callback))
        
        # Document handler for file uploads
        self.app.add_handler(MessageHandler(filters.Document.ALL, self.handle_document))
        
        # Text message handler (for natural language tasks)
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
    
    def _check_admin(self, user_id: int) -> bool:
        """Check if user is admin"""
        return str(user_id) == self.admin_id
    
    def _check_rate_limit(self, user_id: int) -> bool:
        """Check rate limiting"""
        now = datetime.now()
        last_time = self.user_last_command.get(user_id)
        
        if last_time:
            elapsed = (now - last_time).total_seconds()
            if elapsed < self.rate_limit_seconds:
                return False
        
        self.user_last_command[user_id] = now
        return True
    
    async def cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        welcome_text = """🤖 *Autonomous Learning Orchestrator*

I'm an AI agent that can execute complex tasks autonomously using ReAct reasoning and self-learning capabilities.

*Key Features:*
• Multi-step reasoning and action execution
• Learning from experience
• Code execution (Python, Bash)
• File operations
• Knowledge retrieval from vector database

*Commands:*
/task [description] - Execute a task
/learn [source] - Add knowledge
/status - System status
/memory [query] - Query learned patterns
/help - Show detailed help

Send me a message describing what you need, and I'll figure out how to do it!"""
        
        await update.message.reply_text(
            welcome_text,
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def cmd_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_text = """📚 *Command Reference*

*Task Execution:*
`/task <description>` - Execute autonomous task
Example: `/task Create a Python script to analyze CSV files`

*Learning:*
`/learn <source>` - Ingest knowledge from text
Example: `/learn Python best practices: ...`

You can also upload documents directly.

*Status & Monitoring:*
`/status` - Current system status
`/memory <query>` - Search learned patterns
Example: `/memory file operations`

*Configuration:*
`/config` - View current configuration
`/audit` - View recent actions (admin only)
`/cancel` - Cancel active task

*Natural Language:*
You can also just send me messages describing what you need!

Example: "Create a backup script for my files"

*Security:*
• All actions are logged
• Safe mode can be enabled to restrict file system access
• Only admin can view audit logs"""
        
        await update.message.reply_text(
            help_text,
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def cmd_task(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /task command"""
        user_id = update.effective_user.id
        
        # Rate limiting
        if not self._check_rate_limit(user_id):
            await update.message.reply_text("⏳ Please wait a few seconds between commands")
            return
        
        # Extract task description
        if not context.args:
            await update.message.reply_text(
                "Please provide a task description.\nUsage: `/task <description>`",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        task_description = ' '.join(context.args)
        
        # Execute task
        await self._execute_task(update, task_description)
    
    async def _execute_task(self, update: Update, task_description: str, message=None):
        """Execute a task and stream updates"""
        if message is None:
            message = update.message
        
        user_id = update.effective_user.id
        
        # Check if user has active task
        if user_id in self.active_tasks:
            await message.reply_text("⚠️ You already have an active task. Use /cancel to stop it.")
            return
        
        # Mark task as active
        self.active_tasks[user_id] = True
        
        # Send initial message
        status_msg = await message.reply_text(
            "🤖 *Task Started*\n\n"
            f"Task: {task_description}\n\n"
            "⏳ Analyzing and planning...",
            parse_mode=ParseMode.MARKDOWN
        )
        
        try:
            # Send typing indicator
            await message.chat.send_action(ChatAction.TYPING)
            
            # Execute task
            result = await self.orchestrator.execute_task(task_description)
            
            # Format result
            if result['success']:
                response = f"""✅ *Task Completed*

*Result:*
{result['result']}

*Statistics:*
• Iterations: {result['iterations']}
• Time: {result['execution_time']:.2f}s

The system has learned from this execution and will perform better on similar tasks."""
            else:
                response = f"""⚠️ *Task Incomplete*

*Status:*
{result['result']}

*Statistics:*
• Iterations: {result['iterations']}
• Time: {result['execution_time']:.2f}s

The system is still learning. Try rephrasing or breaking down the task."""
            
            # Update status message
            await status_msg.edit_text(response, parse_mode=ParseMode.MARKDOWN)
            
            # If there's a file result, send it
            if 'file' in result.get('result', '').lower():
                # Check workspace for new files
                workspace = Path(self.orchestrator.config['WORKSPACE_PATH'])
                recent_files = sorted(workspace.glob('*'), key=lambda x: x.stat().st_mtime, reverse=True)
                
                if recent_files:
                    latest_file = recent_files[0]
                    if latest_file.stat().st_mtime > (datetime.now().timestamp() - 60):
                        try:
                            await message.reply_document(
                                document=open(latest_file, 'rb'),
                                filename=latest_file.name,
                                caption="Generated file"
                            )
                        except Exception as e:
                            logger.error(f"Error sending file: {e}")
        
        except Exception as e:
            logger.error(f"Task execution error: {e}")
            await status_msg.edit_text(
                f"❌ *Error*\n\n{str(e)}",
                parse_mode=ParseMode.MARKDOWN
            )
        
        finally:
            # Remove active task
            self.active_tasks.pop(user_id, None)
    
    async def cmd_learn(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /learn command"""
        if not context.args:
            await update.message.reply_text(
                "Please provide content to learn.\nUsage: `/learn <content>`\n"
                "Or upload a document.",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        content = ' '.join(context.args)
        
        # Add to knowledge base
        metadata = {
            'source': 'user_input',
            'user_id': str(update.effective_user.id),
            'timestamp': datetime.now().isoformat()
        }
        
        await update.message.reply_text("📚 Processing...")
        
        success = await self.orchestrator.ingest_knowledge(content, metadata)
        
        if success:
            await update.message.reply_text(
                "✅ Knowledge added to database!\n"
                "I'll use this information in future tasks."
            )
        else:
            await update.message.reply_text("❌ Failed to add knowledge")
    
    async def cmd_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status command"""
        status = self.orchestrator.get_status()
        capabilities = self.orchestrator.get_capabilities()
        
        status_text = f"""📊 *System Status*

*General:*
• Status: {'🟢 Online' if status['initialized'] else '🔴 Offline'}
• Workspace: `{status['workspace']}`
• Safe Mode: {'🔒 Enabled' if status['safe_mode'] else '🔓 Disabled'}

*Learning:*
• Learned Patterns: {status['patterns']}
• Audit Log Entries: {status['audit_entries']}

*Capabilities:*
{chr(10).join('• ' + cap for cap in capabilities)}

*Active Tasks:*
{len(self.active_tasks)} task(s) running"""
        
        await update.message.reply_text(
            status_text,
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def cmd_memory(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /memory command"""
        if not context.args:
            await update.message.reply_text(
                "Please provide a search query.\nUsage: `/memory <query>`",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        query = ' '.join(context.args)
        
        await update.message.reply_text("🔍 Searching memory...")
        
        learnings = await self.orchestrator.query_memory(query)
        
        if learnings:
            response = f"🧠 *Relevant Learnings for: {query}*\n\n"
            
            for i, learning in enumerate(learnings[:5], 1):
                content = learning['content'][:200]
                metadata = learning.get('metadata', {})
                
                response += f"{i}. {content}...\n"
                if 'task_type' in metadata:
                    response += f"   Type: {metadata['task_type']}\n"
                response += "\n"
            
            await update.message.reply_text(response, parse_mode=ParseMode.MARKDOWN)
        else:
            await update.message.reply_text("No relevant learnings found.")
    
    async def cmd_config(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /config command"""
        config_text = f"""⚙️ *Configuration*

*LLM:*
• Model: {self.orchestrator.config['LLM_MODEL']}
• Max Iterations: {self.orchestrator.config['MAX_ITERATIONS']}

*Security:*
• Safe Mode: {self.orchestrator.config['SAFE_MODE']}
• Workspace: `{self.orchestrator.config['WORKSPACE_PATH']}`

*RAG:*
• Embedding Model: {self.orchestrator.config['EMBEDDING_MODEL']}
• Chunk Size: {self.orchestrator.config['CHUNK_SIZE']}
• Chunk Overlap: {self.orchestrator.config['CHUNK_OVERLAP']}

*Storage:*
• Vector DB: `{self.orchestrator.config['VECTOR_DB_PATH']}`
• Memory: `{self.orchestrator.config['MEMORY_PATH']}`"""
        
        await update.message.reply_text(
            config_text,
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def cmd_cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /cancel command"""
        user_id = update.effective_user.id
        
        if user_id in self.active_tasks:
            self.active_tasks.pop(user_id)
            await update.message.reply_text("✅ Task cancelled")
        else:
            await update.message.reply_text("No active task to cancel")
    
    async def cmd_audit(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /audit command (admin only)"""
        if not self._check_admin(update.effective_user.id):
            await update.message.reply_text("⛔ Admin only command")
            return
        
        audit_log = self.orchestrator.executor.audit_log[-10:]
        
        if not audit_log:
            await update.message.reply_text("No audit entries")
            return
        
        response = "🔐 *Recent Audit Log*\n\n"
        
        for entry in audit_log:
            response += f"• {entry['timestamp']}\n"
            response += f"  Action: {entry['action']}\n"
            response += f"  Success: {entry['success']}\n"
            response += f"  Result: {entry['result'][:100]}...\n\n"
        
        await update.message.reply_text(response, parse_mode=ParseMode.MARKDOWN)
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle natural language messages"""
        message_text = update.message.text
        
        # Treat as task
        await self._execute_task(update, message_text)
    
    async def handle_document(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle document uploads"""
        document = update.message.document
        
        await update.message.reply_text("📥 Downloading document...")
        
        try:
            # Download file
            file = await context.bot.get_file(document.file_id)
            file_path = Path(self.orchestrator.config['WORKSPACE_PATH']) / document.file_name
            await file.download_to_drive(str(file_path))
            
            # Read content (text files only for now)
            if document.file_name.endswith(('.txt', '.md', '.py', '.json', '.yaml', '.yml')):
                content = file_path.read_text()
                
                # Add to knowledge base
                metadata = {
                    'source': 'document_upload',
                    'filename': document.file_name,
                    'user_id': str(update.effective_user.id),
                    'timestamp': datetime.now().isoformat()
                }
                
                success = await self.orchestrator.ingest_knowledge(content, metadata)
                
                if success:
                    await update.message.reply_text(
                        f"✅ Document '{document.file_name}' added to knowledge base!"
                    )
                else:
                    await update.message.reply_text("❌ Failed to process document")
            else:
                await update.message.reply_text(
                    f"✅ Document saved to workspace as '{document.file_name}'"
                )
        
        except Exception as e:
            logger.error(f"Document handling error: {e}")
            await update.message.reply_text(f"❌ Error: {str(e)}")
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle callback queries (button presses)"""
        query = update.callback_query
        await query.answer()
        
        # Parse callback data
        action = query.data
        
        if action == 'confirm_yes':
            await query.edit_message_text("✅ Confirmed. Executing...")
        elif action == 'confirm_no':
            await query.edit_message_text("❌ Cancelled")
    
    def run(self):
        """Start the bot"""
        logger.info("Starting Telegram bot...")
        self.app.run_polling(allowed_updates=Update.ALL_TYPES)


async def main():
    """Main entry point"""
    # Load configuration
    config = load_config()
    
    # Validate required config
    if not config['TELEGRAM_BOT_TOKEN']:
        raise ValueError("TELEGRAM_BOT_TOKEN not set")
    if not config['TELEGRAM_ADMIN_ID']:
        raise ValueError("TELEGRAM_ADMIN_ID not set")
    if not config['LLM_API_KEY']:
        raise ValueError("LLM_API_KEY not set")
    
    # Initialize orchestrator
    logger.info("Initializing orchestrator...")
    orchestrator = AutonomousOrchestrator(config)
    
    # Initialize bot
    bot = TelegramBot(
        token=config['TELEGRAM_BOT_TOKEN'],
        admin_id=config['TELEGRAM_ADMIN_ID'],
        orchestrator=orchestrator
    )
    
    # Run bot
    bot.run()


if __name__ == '__main__':
    asyncio.run(main())
