"""
Test Suite for Autonomous Learning Orchestrator
Tests all core components and integration
"""

import pytest
import asyncio
import json
import tempfile
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch, MagicMock

# Import components to test
import sys
sys.path.insert(0, str(Path(__file__).parent))

from orchestrator import (
    Action, Learning, SecureExecutor, RAGSystem,
    LearningSystem, ReActEngine, AutonomousOrchestrator
)


@pytest.fixture
def temp_workspace():
    """Create temporary workspace"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def mock_llm_client():
    """Mock LLM client"""
    mock = Mock()
    mock.messages = Mock()
    mock.messages.create = AsyncMock()
    return mock


@pytest.fixture
def test_config(temp_workspace):
    """Test configuration"""
    return {
        'TELEGRAM_BOT_TOKEN': 'test_token',
        'TELEGRAM_ADMIN_ID': '12345',
        'LLM_API_KEY': 'test_key',
        'LLM_MODEL': 'test_model',
        'VECTOR_DB_PATH': str(temp_workspace / 'vectordb'),
        'EMBEDDING_MODEL': 'sentence-transformers/all-MiniLM-L6-v2',
        'MEMORY_PATH': str(temp_workspace / 'memory'),
        'WORKSPACE_PATH': str(temp_workspace / 'workspace'),
        'MAX_ITERATIONS': 5,
        'SAFE_MODE': False,
        'CHUNK_SIZE': 512,
        'CHUNK_OVERLAP': 50,
    }


# ============================================================================
# Action Tests
# ============================================================================

class TestAction:
    """Test Action dataclass"""
    
    def test_action_creation(self):
        action = Action(
            action_type='bash_execute',
            parameters={'command': 'ls'}
        )
        
        assert action.action_type == 'bash_execute'
        assert action.parameters['command'] == 'ls'
        assert action.timestamp is not None
    
    def test_action_to_dict(self):
        action = Action(
            action_type='python_execute',
            parameters={'code': 'print("test")'}
        )
        
        data = action.to_dict()
        
        assert data['action_type'] == 'python_execute'
        assert 'timestamp' in data
        assert isinstance(data['timestamp'], str)


# ============================================================================
# Learning Tests
# ============================================================================

class TestLearning:
    """Test Learning dataclass"""
    
    def test_learning_creation(self):
        learning = Learning(
            task_type='file_operation',
            context='Read a file',
            successful_strategy=[],
            failure_modes=[],
            execution_time=1.5,
            confidence_score=0.8,
            timestamp=datetime.now(),
            prerequisites=[]
        )
        
        assert learning.task_type == 'file_operation'
        assert learning.confidence_score == 0.8
    
    def test_learning_serialization(self):
        learning = Learning(
            task_type='test',
            context='test context',
            successful_strategy=[],
            failure_modes=[],
            execution_time=1.0,
            confidence_score=0.9,
            timestamp=datetime.now(),
            prerequisites=[]
        )
        
        data = learning.to_dict()
        restored = Learning.from_dict(data)
        
        assert restored.task_type == learning.task_type
        assert restored.confidence_score == learning.confidence_score


# ============================================================================
# SecureExecutor Tests
# ============================================================================

class TestSecureExecutor:
    """Test secure execution environment"""
    
    @pytest.mark.asyncio
    async def test_bash_execute_success(self, temp_workspace):
        executor = SecureExecutor(str(temp_workspace), safe_mode=False)
        
        success, output = await executor.execute_bash('echo "test"')
        
        assert success is True
        assert 'test' in output
    
    @pytest.mark.asyncio
    async def test_bash_execute_safe_mode(self, temp_workspace):
        executor = SecureExecutor(str(temp_workspace), safe_mode=True)
        
        success, output = await executor.execute_bash('rm -rf /')
        
        assert success is False
        assert 'blocked' in output.lower()
    
    @pytest.mark.asyncio
    async def test_python_execute(self, temp_workspace):
        executor = SecureExecutor(str(temp_workspace), safe_mode=False)
        
        code = 'print("Hello from Python")'
        success, output = await executor.execute_python(code)
        
        assert success is True
        assert 'Hello from Python' in output
    
    @pytest.mark.asyncio
    async def test_file_read(self, temp_workspace):
        executor = SecureExecutor(str(temp_workspace), safe_mode=False)
        
        # Create test file
        test_file = temp_workspace / 'test.txt'
        test_file.write_text('test content')
        
        success, content = await executor.read_file(str(test_file))
        
        assert success is True
        assert content == 'test content'
    
    @pytest.mark.asyncio
    async def test_file_write(self, temp_workspace):
        executor = SecureExecutor(str(temp_workspace), safe_mode=False)
        
        test_file = temp_workspace / 'output.txt'
        success, message = await executor.write_file(
            str(test_file),
            'new content'
        )
        
        assert success is True
        assert test_file.read_text() == 'new content'
    
    @pytest.mark.asyncio
    async def test_path_validation(self, temp_workspace):
        executor = SecureExecutor(str(temp_workspace), safe_mode=False)
        
        # Should allow workspace paths
        assert executor.validate_path(str(temp_workspace / 'test.txt'))
        
        # Should block outside paths
        assert not executor.validate_path('/etc/passwd')
    
    def test_audit_logging(self, temp_workspace):
        executor = SecureExecutor(str(temp_workspace), safe_mode=False)
        
        executor.audit('test_action', {'param': 'value'}, 'result', True)
        
        assert len(executor.audit_log) == 1
        assert executor.audit_log[0]['action'] == 'test_action'
        assert executor.audit_log[0]['success'] is True


# ============================================================================
# RAG System Tests
# ============================================================================

class TestRAGSystem:
    """Test vector database and retrieval"""
    
    @pytest.mark.asyncio
    async def test_rag_initialization(self, test_config):
        rag = RAGSystem(
            db_path=test_config['VECTOR_DB_PATH'],
            embedding_model=test_config['EMBEDDING_MODEL']
        )
        
        assert rag.collections is not None
        assert 'docs' in rag.collections
        assert 'learnings' in rag.collections
    
    @pytest.mark.asyncio
    async def test_add_document(self, test_config):
        rag = RAGSystem(
            db_path=test_config['VECTOR_DB_PATH'],
            embedding_model=test_config['EMBEDDING_MODEL']
        )
        
        success = await rag.add_document(
            content='This is a test document about Python programming',
            metadata={'source': 'test'},
            collection='docs'
        )
        
        assert success is True
    
    @pytest.mark.asyncio
    async def test_query_documents(self, test_config):
        rag = RAGSystem(
            db_path=test_config['VECTOR_DB_PATH'],
            embedding_model=test_config['EMBEDDING_MODEL']
        )
        
        # Add document
        await rag.add_document(
            content='Python is a programming language',
            metadata={'source': 'test'},
            collection='docs'
        )
        
        # Query
        results = await rag.query('programming language', collection='docs', n_results=1)
        
        assert len(results) > 0
        assert 'Python' in results[0]['content']
    
    def test_chunk_text(self, test_config):
        rag = RAGSystem(
            db_path=test_config['VECTOR_DB_PATH'],
            embedding_model=test_config['EMBEDDING_MODEL'],
            chunk_size=50,
            chunk_overlap=10
        )
        
        text = 'A' * 120
        chunks = rag.chunk_text(text)
        
        assert len(chunks) > 1
        # Check overlap
        assert chunks[0][-10:] == chunks[1][:10]


# ============================================================================
# Learning System Tests
# ============================================================================

class TestLearningSystem:
    """Test self-improvement and pattern recognition"""
    
    @pytest.mark.asyncio
    async def test_learning_system_initialization(self, test_config):
        rag = RAGSystem(
            db_path=test_config['VECTOR_DB_PATH'],
            embedding_model=test_config['EMBEDDING_MODEL']
        )
        
        learning_system = LearningSystem(
            memory_path=test_config['MEMORY_PATH'],
            rag=rag
        )
        
        assert learning_system.patterns is not None
        assert 'task_patterns' in learning_system.patterns
    
    @pytest.mark.asyncio
    async def test_store_learning(self, test_config):
        rag = RAGSystem(
            db_path=test_config['VECTOR_DB_PATH'],
            embedding_model=test_config['EMBEDDING_MODEL']
        )
        
        learning_system = LearningSystem(
            memory_path=test_config['MEMORY_PATH'],
            rag=rag
        )
        
        learning = Learning(
            task_type='file_operation',
            context='test context',
            successful_strategy=[],
            failure_modes=[],
            execution_time=1.0,
            confidence_score=0.8,
            timestamp=datetime.now(),
            prerequisites=[]
        )
        
        await learning_system.store_learning(learning)
        
        # Check file was created
        learnings_file = Path(test_config['MEMORY_PATH']) / 'learnings.jsonl'
        assert learnings_file.exists()
    
    @pytest.mark.asyncio
    async def test_get_relevant_learnings(self, test_config):
        rag = RAGSystem(
            db_path=test_config['VECTOR_DB_PATH'],
            embedding_model=test_config['EMBEDDING_MODEL']
        )
        
        learning_system = LearningSystem(
            memory_path=test_config['MEMORY_PATH'],
            rag=rag
        )
        
        # Store a learning
        learning = Learning(
            task_type='file_operation',
            context='Reading files efficiently',
            successful_strategy=[],
            failure_modes=[],
            execution_time=1.0,
            confidence_score=0.9,
            timestamp=datetime.now(),
            prerequisites=[]
        )
        
        await learning_system.store_learning(learning)
        
        # Query
        results = await learning_system.get_relevant_learnings('file operations')
        
        assert len(results) > 0
    
    def test_classify_task(self, test_config):
        rag = RAGSystem(
            db_path=test_config['VECTOR_DB_PATH'],
            embedding_model=test_config['EMBEDDING_MODEL']
        )
        
        learning_system = LearningSystem(
            memory_path=test_config['MEMORY_PATH'],
            rag=rag
        )
        
        assert learning_system._classify_task('read a file') == 'file_operation'
        assert learning_system._classify_task('write some code') == 'code_generation'
        assert learning_system._classify_task('install numpy') == 'system_setup'


# ============================================================================
# ReAct Engine Tests
# ============================================================================

class TestReActEngine:
    """Test ReAct reasoning loop"""
    
    @pytest.mark.asyncio
    async def test_execute_action(self, test_config, mock_llm_client):
        executor = SecureExecutor(test_config['WORKSPACE_PATH'], safe_mode=False)
        rag = RAGSystem(
            db_path=test_config['VECTOR_DB_PATH'],
            embedding_model=test_config['EMBEDDING_MODEL']
        )
        learning_system = LearningSystem(
            memory_path=test_config['MEMORY_PATH'],
            rag=rag
        )
        
        react = ReActEngine(
            llm_client=mock_llm_client,
            executor=executor,
            rag=rag,
            learning=learning_system,
            max_iterations=5
        )
        
        action = Action(
            action_type='bash_execute',
            parameters={'command': 'echo "test"'}
        )
        
        success, output = await react.execute_action(action)
        
        assert success is True
        assert 'test' in output
    
    @pytest.mark.asyncio
    async def test_complete_action(self, test_config, mock_llm_client):
        executor = SecureExecutor(test_config['WORKSPACE_PATH'], safe_mode=False)
        rag = RAGSystem(
            db_path=test_config['VECTOR_DB_PATH'],
            embedding_model=test_config['EMBEDDING_MODEL']
        )
        learning_system = LearningSystem(
            memory_path=test_config['MEMORY_PATH'],
            rag=rag
        )
        
        react = ReActEngine(
            llm_client=mock_llm_client,
            executor=executor,
            rag=rag,
            learning=learning_system,
            max_iterations=5
        )
        
        action = Action(
            action_type='complete',
            parameters={'result': 'Task completed successfully'}
        )
        
        success, output = await react.execute_action(action)
        
        assert success is True
        assert 'completed' in output.lower()


# ============================================================================
# Integration Tests
# ============================================================================

class TestIntegration:
    """Integration tests for full system"""
    
    @pytest.mark.asyncio
    async def test_full_task_execution(self, test_config):
        """Test complete task execution flow"""
        # This would require a real LLM, so we'll mock it
        with patch('orchestrator.anthropic.Anthropic') as mock_anthropic:
            mock_client = Mock()
            mock_response = Mock()
            mock_response.content = [Mock(text=json.dumps({
                'thought': 'Task is complete',
                'action': {
                    'action_type': 'complete',
                    'parameters': {'result': 'Successfully created file'}
                },
                'confidence': 1.0
            }))]
            
            mock_client.messages.create.return_value = mock_response
            mock_anthropic.return_value = mock_client
            
            orchestrator = AutonomousOrchestrator(test_config)
            
            result = await orchestrator.execute_task('Create a test file')
            
            assert result['success'] is True
            assert result['iterations'] > 0
    
    @pytest.mark.asyncio
    async def test_knowledge_ingestion(self, test_config):
        """Test adding knowledge to RAG"""
        with patch('orchestrator.anthropic.Anthropic') as mock_anthropic:
            mock_client = Mock()
            mock_anthropic.return_value = mock_client
            
            orchestrator = AutonomousOrchestrator(test_config)
            
            success = await orchestrator.ingest_knowledge(
                content='Test documentation about Python',
                metadata={'source': 'test'}
            )
            
            assert success is True
    
    def test_get_status(self, test_config):
        """Test status reporting"""
        with patch('orchestrator.anthropic.Anthropic') as mock_anthropic:
            mock_client = Mock()
            mock_anthropic.return_value = mock_client
            
            orchestrator = AutonomousOrchestrator(test_config)
            status = orchestrator.get_status()
            
            assert 'initialized' in status
            assert 'workspace' in status
            assert status['initialized'] is True


# ============================================================================
# Performance Tests
# ============================================================================

class TestPerformance:
    """Performance and benchmark tests"""
    
    @pytest.mark.asyncio
    async def test_rag_query_performance(self, test_config):
        """Test RAG query response time"""
        rag = RAGSystem(
            db_path=test_config['VECTOR_DB_PATH'],
            embedding_model=test_config['EMBEDDING_MODEL']
        )
        
        # Add some documents
        for i in range(10):
            await rag.add_document(
                content=f'Test document number {i} with various content',
                metadata={'id': i},
                collection='docs'
            )
        
        # Measure query time
        start = datetime.now()
        results = await rag.query('test document', collection='docs', n_results=5)
        duration = (datetime.now() - start).total_seconds()
        
        assert duration < 1.0  # Should be fast
        assert len(results) > 0


# ============================================================================
# Pytest Configuration
# ============================================================================

def pytest_configure(config):
    """Configure pytest"""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
