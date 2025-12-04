#!/usr/bin/env python3
"""
Quick Start Script for ALO with All Features Enabled
Integrates orchestrator with advanced capabilities
"""

import os
import sys
import asyncio
import logging
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from orchestrator import AutonomousOrchestrator, load_config
from advanced_capabilities import extend_orchestrator_with_advanced_capabilities
from telegram_bot import TelegramBot


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def validate_config(config):
    """Validate required configuration"""
    required = ['TELEGRAM_BOT_TOKEN', 'TELEGRAM_ADMIN_ID', 'LLM_API_KEY']
    missing = [key for key in required if not config.get(key)]
    
    if missing:
        logger.error(f"Missing required configuration: {', '.join(missing)}")
        logger.error("Please configure .env file properly")
        sys.exit(1)


def print_banner():
    """Print startup banner"""
    banner = """
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║     Autonomous Learning Orchestrator (ALO)                ║
║     Production-Ready AI Agent System                      ║
║                                                           ║
║     • ReAct Reasoning Engine                              ║
║     • RAG Knowledge System                                ║
║     • Self-Learning Capabilities                          ║
║     • Telegram Interface                                  ║
║     • Advanced Web & API Integration                      ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
"""
    print(banner)


def print_capabilities(orchestrator):
    """Print system capabilities"""
    print("\n🚀 SYSTEM CAPABILITIES")
    print("=" * 60)
    
    capabilities = orchestrator.get_capabilities()
    for cap in capabilities:
        print(f"  ✓ {cap}")
    
    # Check for advanced capabilities
    if hasattr(orchestrator, 'advanced'):
        print("\n🌟 ADVANCED CAPABILITIES")
        print("  ✓ web_search - Search the internet")
        print("  ✓ web_scrape - Extract webpage content")
        print("  ✓ git_clone - Clone repositories")
        print("  ✓ git_commit - Commit changes")
        print("  ✓ parse_json - Parse JSON data")
        print("  ✓ parse_csv - Parse CSV data")
        print("  ✓ api_request - Make HTTP API calls")
    
    print("=" * 60)


def print_config_summary(config):
    """Print configuration summary"""
    print("\n⚙️  CONFIGURATION")
    print("=" * 60)
    print(f"  LLM Model:        {config['LLM_MODEL']}")
    print(f"  Max Iterations:   {config['MAX_ITERATIONS']}")
    print(f"  Safe Mode:        {config['SAFE_MODE']}")
    print(f"  Workspace:        {config['WORKSPACE_PATH']}")
    print(f"  Vector DB:        {config['VECTOR_DB_PATH']}")
    print("=" * 60)


async def run_demo_task(orchestrator):
    """Run a demonstration task"""
    print("\n🎯 RUNNING DEMO TASK")
    print("=" * 60)
    
    demo_query = "Create a Python script that generates the Fibonacci sequence"
    print(f"\nTask: {demo_query}\n")
    
    result = await orchestrator.execute_task(demo_query)
    
    if result['success']:
        print(f"✅ Task completed successfully!")
        print(f"   Iterations: {result['iterations']}")
        print(f"   Time: {result['execution_time']:.2f}s")
    else:
        print(f"⚠️  Task incomplete: {result['result']}")
    
    print("=" * 60)


def main():
    """Main entry point"""
    print_banner()
    
    # Load configuration
    logger.info("Loading configuration...")
    config = load_config()
    validate_config(config)
    
    print_config_summary(config)
    
    # Initialize orchestrator
    logger.info("Initializing orchestrator...")
    orchestrator = AutonomousOrchestrator(config)
    
    # Add advanced capabilities if web search is enabled
    if os.getenv('WEB_SEARCH_ENABLED', 'false').lower() == 'true':
        logger.info("Enabling advanced capabilities...")
        serpapi_key = os.getenv('SERPAPI_KEY')
        extend_orchestrator_with_advanced_capabilities(orchestrator, serpapi_key)
    
    print_capabilities(orchestrator)
    
    # Ask if user wants to run demo
    print("\n")
    response = input("Run demonstration task? (y/N): ")
    
    if response.lower() == 'y':
        asyncio.run(run_demo_task(orchestrator))
    
    # Start bot
    print("\n🤖 Starting Telegram bot...")
    print("=" * 60)
    print("\nBot is now running. Send /start to your bot to begin!")
    print("Press Ctrl+C to stop.\n")
    
    try:
        bot = TelegramBot(
            token=config['TELEGRAM_BOT_TOKEN'],
            admin_id=config['TELEGRAM_ADMIN_ID'],
            orchestrator=orchestrator
        )
        
        bot.run()
    
    except KeyboardInterrupt:
        print("\n\n✋ Shutting down...")
        
        # Cleanup
        if hasattr(orchestrator, 'advanced'):
            asyncio.run(orchestrator.advanced.close())
        
        print("✅ Shutdown complete")
    
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
