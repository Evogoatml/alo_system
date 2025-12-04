"""Test Script - Validate ALO Installation"""
import sys
import os

def test_imports():
    """Test if all required modules can be imported"""
    print("Testing imports...")
    
    try:
        import config
        print("✅ config")
        
        import llm_interface
        print("✅ llm_interface")
        
        import rag_system
        print("✅ rag_system")
        
        import learning_system
        print("✅ learning_system")
        
        import action_executor
        print("✅ action_executor")
        
        import react_engine
        print("✅ react_engine")
        
        import prompts
        print("✅ prompts")
        
        import utils
        print("✅ utils")
        
        return True
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False

def test_dependencies():
    """Test if external dependencies are available"""
    print("\nTesting dependencies...")
    
    deps = [
        ("telegram", "python-telegram-bot"),
        ("anthropic", "anthropic"),
        ("openai", "openai"),
        ("chromadb", "chromadb"),
        ("sentence_transformers", "sentence-transformers"),
        ("requests", "requests"),
        ("dotenv", "python-dotenv")
    ]
    
    all_ok = True
    for module, package in deps:
        try:
            __import__(module)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} - Run: pip install {package}")
            all_ok = False
    
    return all_ok

def test_config():
    """Test if configuration is valid"""
    print("\nTesting configuration...")
    
    try:
        from config import config
        
        # Check critical values
        if not config.telegram.bot_token or config.telegram.bot_token == "your_bot_token_here":
            print("⚠️  TELEGRAM_BOT_TOKEN not set in .env")
            return False
        
        if not config.telegram.admin_id:
            print("⚠️  TELEGRAM_ADMIN_ID not set in .env")
            return False
        
        if config.llm.provider in ["anthropic", "openai"] and not config.llm.api_key:
            print(f"⚠️  LLM_API_KEY not set for {config.llm.provider}")
            return False
        
        print("✅ Configuration valid")
        return True
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return False

def test_directories():
    """Test if required directories exist"""
    print("\nTesting directories...")
    
    dirs = [
        "data/vectordb",
        "data/memory",
        "workspace",
        "logs"
    ]
    
    all_ok = True
    for dir_path in dirs:
        if os.path.exists(dir_path):
            print(f"✅ {dir_path}")
        else:
            print(f"⚠️  {dir_path} missing - will be created on first run")
    
    return True

def test_rag_system():
    """Test RAG system initialization"""
    print("\nTesting RAG system...")
    
    try:
        from rag_system import rag_system
        stats = rag_system.get_stats()
        print(f"✅ RAG initialized: {stats['total_chunks']} chunks")
        return True
    except Exception as e:
        print(f"❌ RAG system error: {e}")
        return False

def test_learning_system():
    """Test learning system initialization"""
    print("\nTesting learning system...")
    
    try:
        from learning_system import learning_system
        stats = learning_system.get_statistics()
        print(f"✅ Learning system initialized: {stats['total_experiences']} experiences")
        return True
    except Exception as e:
        print(f"❌ Learning system error: {e}")
        return False

def main():
    print("🧪 ALO System Validation\n")
    print("=" * 50)
    
    results = {
        "Imports": test_imports(),
        "Dependencies": test_dependencies(),
        "Configuration": test_config(),
        "Directories": test_directories(),
        "RAG System": test_rag_system(),
        "Learning System": test_learning_system()
    }
    
    print("\n" + "=" * 50)
    print("\n📊 Test Results:")
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {status} - {test_name}")
    
    all_passed = all(results.values())
    
    print("\n" + "=" * 50)
    if all_passed:
        print("\n✅ All tests passed! System ready to use.")
        print("\nRun: python main.py")
        return 0
    else:
        print("\n⚠️  Some tests failed. Please fix the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
