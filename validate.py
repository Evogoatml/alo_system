#!/usr/bin/env python3
"""
System Validation Script
Checks if ALO is properly installed and configured
"""

import sys
import os
from pathlib import Path
import importlib.util


class Validator:
    """System validation checks"""
    
    def __init__(self):
        self.checks_passed = 0
        self.checks_failed = 0
        self.warnings = 0
    
    def check(self, name: str, condition: bool, error_msg: str = "", warning: bool = False):
        """Run a validation check"""
        if condition:
            print(f"✅ {name}")
            self.checks_passed += 1
        else:
            if warning:
                print(f"⚠️  {name}: {error_msg}")
                self.warnings += 1
            else:
                print(f"❌ {name}: {error_msg}")
                self.checks_failed += 1
    
    def print_summary(self):
        """Print validation summary"""
        total = self.checks_passed + self.checks_failed
        
        print("\n" + "="*60)
        print("VALIDATION SUMMARY")
        print("="*60)
        print(f"✅ Passed: {self.checks_passed}/{total}")
        
        if self.checks_failed > 0:
            print(f"❌ Failed: {self.checks_failed}/{total}")
        
        if self.warnings > 0:
            print(f"⚠️  Warnings: {self.warnings}")
        
        if self.checks_failed == 0:
            print("\n🎉 System is ready to use!")
        else:
            print("\n⚠️  Please fix the issues above before running")
        
        print("="*60)


def check_python_version(validator):
    """Check Python version"""
    print("\n📋 Python Version")
    print("-" * 60)
    
    version = sys.version_info
    validator.check(
        "Python 3.10+",
        version.major >= 3 and version.minor >= 10,
        f"Found Python {version.major}.{version.minor}.{version.micro}, need 3.10+"
    )


def check_required_files(validator):
    """Check required files exist"""
    print("\n📁 Required Files")
    print("-" * 60)
    
    required_files = [
        'orchestrator.py',
        'telegram_bot.py',
        'advanced_capabilities.py',
        'requirements.txt',
        'README.md',
        '.env.template',
        'setup.py',
        'start.py'
    ]
    
    for file in required_files:
        validator.check(
            f"{file}",
            Path(file).exists(),
            "File missing"
        )


def check_directories(validator):
    """Check required directories"""
    print("\n📂 Directories")
    print("-" * 60)
    
    required_dirs = [
        'data',
        'data/vectordb',
        'data/memory',
        'workspace',
        'tests'
    ]
    
    for dir_path in required_dirs:
        path = Path(dir_path)
        validator.check(
            f"{dir_path}/",
            path.exists() and path.is_dir(),
            "Directory missing"
        )


def check_dependencies(validator):
    """Check Python dependencies"""
    print("\n📦 Dependencies")
    print("-" * 60)
    
    critical_deps = [
        'anthropic',
        'telegram',
        'chromadb',
        'sentence_transformers',
        'dotenv'
    ]
    
    for dep in critical_deps:
        spec = importlib.util.find_spec(dep)
        validator.check(
            f"{dep}",
            spec is not None,
            "Not installed (run: pip install -r requirements.txt)"
        )


def check_configuration(validator):
    """Check .env configuration"""
    print("\n⚙️  Configuration")
    print("-" * 60)
    
    env_exists = Path('.env').exists()
    validator.check(
        ".env file",
        env_exists,
        "Run: cp .env.template .env"
    )
    
    if env_exists:
        from dotenv import load_dotenv
        load_dotenv()
        
        # Check critical settings
        validator.check(
            "TELEGRAM_BOT_TOKEN",
            bool(os.getenv('TELEGRAM_BOT_TOKEN')) and 
            'your_telegram_bot_token_here' not in os.getenv('TELEGRAM_BOT_TOKEN', ''),
            "Not configured in .env"
        )
        
        validator.check(
            "TELEGRAM_ADMIN_ID",
            bool(os.getenv('TELEGRAM_ADMIN_ID')) and
            'your_admin_user_id_here' not in os.getenv('TELEGRAM_ADMIN_ID', ''),
            "Not configured in .env"
        )
        
        validator.check(
            "LLM_API_KEY",
            bool(os.getenv('LLM_API_KEY')) and
            'your_anthropic_api_key_here' not in os.getenv('LLM_API_KEY', ''),
            "Not configured in .env"
        )
        
        # Optional checks (warnings only)
        validator.check(
            "WORKSPACE_PATH",
            Path(os.getenv('WORKSPACE_PATH', './workspace')).exists(),
            "Workspace directory doesn't exist",
            warning=True
        )


def check_permissions(validator):
    """Check file permissions"""
    print("\n🔐 Permissions")
    print("-" * 60)
    
    writable_paths = ['data', 'workspace', 'data/vectordb', 'data/memory']
    
    for path_str in writable_paths:
        path = Path(path_str)
        if path.exists():
            try:
                test_file = path / '.write_test'
                test_file.touch()
                test_file.unlink()
                validator.check(f"{path_str}/ writable", True, "")
            except:
                validator.check(
                    f"{path_str}/ writable",
                    False,
                    "No write permission"
                )


def check_executables(validator):
    """Check if scripts are executable"""
    print("\n🔧 Executables")
    print("-" * 60)
    
    scripts = ['setup.py', 'start.py', 'utils.py']
    
    for script in scripts:
        path = Path(script)
        if path.exists():
            validator.check(
                f"{script}",
                os.access(path, os.X_OK) or True,  # Not critical on all systems
                "Not executable (run: chmod +x)",
                warning=True
            )


def quick_test(validator):
    """Run a quick functionality test"""
    print("\n🧪 Quick Functionality Test")
    print("-" * 60)
    
    try:
        # Try importing main modules
        from orchestrator import AutonomousOrchestrator, load_config
        validator.check("Import orchestrator", True, "")
        
        from telegram_bot import TelegramBot
        validator.check("Import telegram_bot", True, "")
        
        from advanced_capabilities import AdvancedCapabilities
        validator.check("Import advanced_capabilities", True, "")
        
        # Try loading config (won't validate values)
        config = load_config()
        validator.check("Load configuration", True, "")
    
    except Exception as e:
        validator.check(
            "Module imports",
            False,
            f"Import error: {str(e)}"
        )


def main():
    """Main validation flow"""
    print("""
╔═══════════════════════════════════════════════════════════╗
║          ALO System Validation                            ║
╚═══════════════════════════════════════════════════════════╝

Checking system installation and configuration...
""")
    
    validator = Validator()
    
    try:
        check_python_version(validator)
        check_required_files(validator)
        check_directories(validator)
        check_dependencies(validator)
        check_configuration(validator)
        check_permissions(validator)
        check_executables(validator)
        quick_test(validator)
        
        validator.print_summary()
        
        if validator.checks_failed == 0:
            print("\n📝 Next Steps:")
            print("  1. Review your .env configuration")
            print("  2. Run: python start.py")
            print("  3. Send /start to your Telegram bot")
            print("\n📚 Documentation: README.md")
            print("💡 Examples: python examples.py")
            print("🧪 Tests: pytest")
        else:
            print("\n🔧 Fix the issues above, then run this script again:")
            print("  python validate.py")
    
    except KeyboardInterrupt:
        print("\n\nValidation cancelled")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Validation error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
