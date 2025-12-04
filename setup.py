#!/usr/bin/env python3
"""
Setup script for Autonomous Learning Orchestrator
Handles initial installation and configuration
"""

import os
import sys
import subprocess
from pathlib import Path
import shutil


def print_header(text):
    """Print formatted header"""
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60 + "\n")


def check_python_version():
    """Ensure Python 3.10+"""
    print_header("Checking Python Version")
    
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 10):
        print("❌ Python 3.10+ required")
        print(f"   Current version: {sys.version}")
        sys.exit(1)
    
    print(f"✅ Python {version.major}.{version.minor}.{version.micro}")


def create_directories():
    """Create necessary directories"""
    print_header("Creating Directories")
    
    dirs = [
        'data/vectordb',
        'data/memory',
        'workspace',
        'logs'
    ]
    
    for dir_path in dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        print(f"✅ Created: {dir_path}")


def install_dependencies():
    """Install Python dependencies"""
    print_header("Installing Dependencies")
    
    print("This may take a few minutes...")
    
    try:
        subprocess.check_call([
            sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'
        ])
        print("\n✅ All dependencies installed")
    except subprocess.CalledProcessError:
        print("\n❌ Failed to install dependencies")
        print("   Try manually: pip install -r requirements.txt")
        sys.exit(1)


def setup_env_file():
    """Setup .env file"""
    print_header("Configuring Environment")
    
    if Path('.env').exists():
        print("⚠️  .env already exists")
        response = input("   Overwrite? (y/N): ")
        if response.lower() != 'y':
            print("   Keeping existing .env")
            return
    
    # Copy template
    shutil.copy('.env.template', '.env')
    print("✅ Created .env from template")
    
    # Collect user input
    print("\nLet's configure the essential settings:")
    
    # Telegram Bot Token
    print("\n1. Telegram Bot Token")
    print("   Get this from @BotFather on Telegram")
    bot_token = input("   Token: ").strip()
    
    # Admin ID
    print("\n2. Your Telegram User ID")
    print("   Get this from @userinfobot on Telegram")
    admin_id = input("   User ID: ").strip()
    
    # LLM API Key
    print("\n3. Anthropic API Key")
    print("   Get this from https://console.anthropic.com/")
    api_key = input("   API Key: ").strip()
    
    # Update .env file
    env_content = Path('.env').read_text()
    env_content = env_content.replace('your_telegram_bot_token_here', bot_token)
    env_content = env_content.replace('your_admin_user_id_here', admin_id)
    env_content = env_content.replace('your_anthropic_api_key_here', api_key)
    
    Path('.env').write_text(env_content)
    print("\n✅ Configuration saved to .env")


def download_embedding_model():
    """Pre-download embedding model"""
    print_header("Downloading Embedding Model")
    
    print("Downloading sentence-transformers model...")
    print("This is a one-time download (~90MB)")
    
    try:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
        print("✅ Model downloaded and cached")
    except Exception as e:
        print(f"⚠️  Model download failed: {e}")
        print("   The model will download on first use")


def run_tests():
    """Run test suite"""
    print_header("Running Tests")
    
    response = input("Run tests? (Y/n): ")
    if response.lower() == 'n':
        print("Skipping tests")
        return
    
    try:
        subprocess.check_call([sys.executable, '-m', 'pytest', 'tests/', '-v'])
        print("\n✅ All tests passed")
    except subprocess.CalledProcessError:
        print("\n⚠️  Some tests failed")
        print("   The system should still work, but please review the errors")


def create_systemd_service():
    """Create systemd service file (Linux only)"""
    if sys.platform != 'linux':
        return
    
    print_header("Create Systemd Service?")
    
    response = input("Create systemd service for auto-start? (y/N): ")
    if response.lower() != 'y':
        return
    
    service_content = f"""[Unit]
Description=Autonomous Learning Orchestrator
After=network.target

[Service]
Type=simple
User={os.getenv('USER')}
WorkingDirectory={Path.cwd()}
Environment="PATH={Path(sys.executable).parent}"
ExecStart={sys.executable} telegram_bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
"""
    
    service_file = Path('alo.service')
    service_file.write_text(service_content)
    
    print(f"✅ Service file created: {service_file}")
    print("\nTo install:")
    print(f"  sudo cp {service_file} /etc/systemd/system/")
    print("  sudo systemctl daemon-reload")
    print("  sudo systemctl enable alo")
    print("  sudo systemctl start alo")


def print_next_steps():
    """Print what to do next"""
    print_header("Setup Complete! 🎉")
    
    print("Next steps:\n")
    print("1. Review your .env configuration:")
    print("   nano .env")
    print("")
    print("2. Start the bot:")
    print("   python telegram_bot.py")
    print("")
    print("3. Open Telegram and send a message to your bot")
    print("   Try: /start or /help")
    print("")
    print("4. Test with a simple task:")
    print("   /task Create a hello world Python script")
    print("")
    print("Documentation: README.md")
    print("Logs: alo.log")
    print("Workspace: ./workspace/")
    print("")


def main():
    """Main setup flow"""
    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║  Autonomous Learning Orchestrator (ALO) - Setup Wizard   ║
    ╚═══════════════════════════════════════════════════════════╝
    """)
    
    try:
        check_python_version()
        create_directories()
        install_dependencies()
        setup_env_file()
        download_embedding_model()
        run_tests()
        create_systemd_service()
        print_next_steps()
    
    except KeyboardInterrupt:
        print("\n\n⚠️  Setup cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Setup failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
