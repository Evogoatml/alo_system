"""
Autonomous Learning Orchestrator (ALO)
Production-ready ReAct agent with RAG and self-improvement capabilities
"""

import os
import json
import asyncio
import hashlib
import subprocess
import traceback
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import logging

import anthropic
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('alo.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


@dataclass
class Action:
    """Represents an executable action"""
    action_type: str
    parameters: Dict[str, Any]
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
    
    def to_dict(self) -> Dict:
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data


@dataclass
class Learning:
    """Represents stored learning from task execution"""
    task_type: str
    context: str
    successful_strategy: List[Dict]
    failure_modes: List[str]
    execution_time: float
    confidence_score: float
    timestamp: datetime
    prerequisites: List[str]
    
    def to_dict(self) -> Dict:
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data
    
    @staticmethod
    def from_dict(data: Dict) -> 'Learning':
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return Learning(**data)


class SecureExecutor:
    """Secure execution environment with sandboxing"""
    
    def __init__(self, workspace_path: str, safe_mode: bool = False):
        self.workspace_path = Path(workspace_path)
        self.workspace_path.mkdir(parents=True, exist_ok=True)
        self.safe_mode = safe_mode
        self.audit_log = []
        
    def audit(self, action: str, parameters: Dict, result: str, success: bool):
        """Log all actions for security audit"""
        entry = {
            'timestamp': datetime.now().isoformat(),
            'action': action,
            'parameters': parameters,
            'result': result[:500],  # Truncate long results
            'success': success
        }
        self.audit_log.append(entry)
        logger.info(f"AUDIT: {action} - Success: {success}")
    
    def validate_path(self, path: str) -> bool:
        """Ensure path is within workspace"""
        try:
            resolved = Path(path).resolve()
            return resolved.is_relative_to(self.workspace_path)
        except:
            return False
    
    async def execute_bash(self, command: str) -> Tuple[bool, str]:
        """Execute bash command with safety checks"""
        # Block dangerous commands in safe mode
        if self.safe_mode:
            dangerous = ['rm -rf /', 'dd if=', 'mkfs', ':(){:|:&};:', 'fork bomb']
            if any(d in command.lower() for d in dangerous):
                return False, "Command blocked by safe mode"
        
        try:
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(self.workspace_path)
            )
            stdout, stderr = await process.communicate()
            
            output = stdout.decode() + stderr.decode()
            success = process.returncode == 0
            
            self.audit('bash_execute', {'command': command}, output, success)
            return success, output
        except Exception as e:
            error = str(e)
            self.audit('bash_execute', {'command': command}, error, False)
            return False, error
    
    async def execute_python(self, code: str) -> Tuple[bool, str]:
        """Execute Python code in isolated environment"""
        # Create temporary file
        code_hash = hashlib.sha256(code.encode()).hexdigest()[:8]
        code_file = self.workspace_path / f"temp_{code_hash}.py"
        
        try:
            code_file.write_text(code)
            
            process = await asyncio.create_subprocess_exec(
                'python3', str(code_file),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(self.workspace_path)
            )
            stdout, stderr = await process.communicate()
            
            output = stdout.decode() + stderr.decode()
            success = process.returncode == 0
            
            self.audit('python_execute', {'code': code[:200]}, output, success)
            return success, output
        except Exception as e:
            error = str(e)
            self.audit('python_execute', {'code': code[:200]}, error, False)
            return False, error
        finally:
            if code_file.exists():
                code_file.unlink()
    
    async def read_file(self, filepath: str) -> Tuple[bool, str]:
        """Read file with path validation"""
        if not self.validate_path(filepath):
            return False, "Path outside workspace"
        
        try:
            path = Path(filepath)
            if not path.exists():
                return False, "File not found"
            
            content = path.read_text()
            self.audit('file_read', {'filepath': filepath}, f"Read {len(content)} chars", True)
            return True, content
        except Exception as e:
            error = str(e)
            self.audit('file_read', {'filepath': filepath}, error, False)
            return False, error
    
    async def write_file(self, filepath: str, content: str) -> Tuple[bool, str]:
        """Write file with path validation"""
        if not self.validate_path(filepath):
            return False, "Path outside workspace"
        
        try:
            path = Path(filepath)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content)
            
            self.audit('file_write', {'filepath': filepath}, f"Wrote {len(content)} chars", True)
            return True, f"Wrote {len(content)} characters to {filepath}"
        except Exception as e:
            error = str(e)
            self.audit('file_write', {'filepath': filepath}, error, False)
            return False, error


class RAGSystem:
    """Vector database and retrieval system"""
    
    def __init__(self, db_path: str, embedding_model: str, chunk_size: int = 512, chunk_overlap: int = 50):
        self.db_path = Path(db_path)
        self.db_path.mkdir(parents=True, exist_ok=True)
        
        self.embedding_model = SentenceTransformer(embedding_model)
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        # Initialize ChromaDB
        self.client = chromadb.PersistentClient(
            path=str(self.db_path),
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Collections for different knowledge types
        self.collections = {
            'code': self._get_or_create_collection('code'),
            'docs': self._get_or_create_collection('docs'),
            'learnings': self._get_or_create_collection('learnings'),
            'conversations': self._get_or_create_collection('conversations')
        }
        
        logger.info("RAG system initialized")
    
    def _get_or_create_collection(self, name: str):
        """Get or create a collection"""
        try:
            return self.client.get_collection(name)
        except:
            return self.client.create_collection(name)
    
    def chunk_text(self, text: str) -> List[str]:
        """Split text into overlapping chunks"""
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + self.chunk_size
            chunk = text[start:end]
            chunks.append(chunk)
            start += self.chunk_size - self.chunk_overlap
        
        return chunks
    
    async def add_document(self, content: str, metadata: Dict, collection: str = 'docs') -> bool:
        """Add document to vector database"""
        try:
            chunks = self.chunk_text(content)
            
            # Generate embeddings
            embeddings = self.embedding_model.encode(chunks).tolist()
            
            # Create unique IDs
            base_id = hashlib.sha256(content.encode()).hexdigest()[:16]
            ids = [f"{base_id}_{i}" for i in range(len(chunks))]
            
            # Add to collection
            self.collections[collection].add(
                embeddings=embeddings,
                documents=chunks,
                metadatas=[metadata] * len(chunks),
                ids=ids
            )
            
            logger.info(f"Added document with {len(chunks)} chunks to {collection}")
            return True
        except Exception as e:
            logger.error(f"Error adding document: {e}")
            return False
    
    async def query(self, query_text: str, collection: str = 'docs', n_results: int = 5) -> List[Dict]:
        """Semantic search in vector database"""
        try:
            # Generate query embedding
            query_embedding = self.embedding_model.encode([query_text]).tolist()
            
            # Search
            results = self.collections[collection].query(
                query_embeddings=query_embedding,
                n_results=n_results
            )
            
            # Format results
            formatted = []
            if results['documents']:
                for i, doc in enumerate(results['documents'][0]):
                    formatted.append({
                        'content': doc,
                        'metadata': results['metadatas'][0][i] if results['metadatas'] else {},
                        'distance': results['distances'][0][i] if results['distances'] else None
                    })
            
            return formatted
        except Exception as e:
            logger.error(f"Error querying: {e}")
            return []
    
    async def add_learning(self, learning: Learning) -> bool:
        """Add learning to knowledge base"""
        content = f"""
Task: {learning.task_type}
Context: {learning.context}
Strategy: {json.dumps(learning.successful_strategy)}
Failures: {json.dumps(learning.failure_modes)}
Prerequisites: {json.dumps(learning.prerequisites)}
"""
        
        metadata = {
            'task_type': learning.task_type,
            'confidence': learning.confidence_score,
            'timestamp': learning.timestamp.isoformat()
        }
        
        return await self.add_document(content, metadata, 'learnings')


class LearningSystem:
    """Self-improvement and pattern recognition"""
    
    def __init__(self, memory_path: str, rag: RAGSystem):
        self.memory_path = Path(memory_path)
        self.memory_path.mkdir(parents=True, exist_ok=True)
        self.rag = rag
        
        self.learnings_file = self.memory_path / 'learnings.jsonl'
        self.patterns_file = self.memory_path / 'patterns.json'
        
        self.patterns = self._load_patterns()
        logger.info("Learning system initialized")
    
    def _load_patterns(self) -> Dict:
        """Load identified patterns"""
        if self.patterns_file.exists():
            return json.loads(self.patterns_file.read_text())
        return {'task_patterns': {}, 'failure_patterns': {}, 'success_patterns': {}}
    
    def _save_patterns(self):
        """Save patterns to disk"""
        self.patterns_file.write_text(json.dumps(self.patterns, indent=2))
    
    async def store_learning(self, learning: Learning):
        """Store a learning experience"""
        # Append to JSONL
        with open(self.learnings_file, 'a') as f:
            f.write(json.dumps(learning.to_dict()) + '\n')
        
        # Add to RAG
        await self.rag.add_learning(learning)
        
        # Update patterns
        self._update_patterns(learning)
        
        logger.info(f"Stored learning for task type: {learning.task_type}")
    
    def _update_patterns(self, learning: Learning):
        """Update pattern recognition"""
        task_type = learning.task_type
        
        # Track successful patterns
        if task_type not in self.patterns['success_patterns']:
            self.patterns['success_patterns'][task_type] = []
        
        self.patterns['success_patterns'][task_type].append({
            'strategy': learning.successful_strategy,
            'confidence': learning.confidence_score,
            'timestamp': learning.timestamp.isoformat()
        })
        
        # Track failure patterns
        for failure in learning.failure_modes:
            if failure not in self.patterns['failure_patterns']:
                self.patterns['failure_patterns'][failure] = 0
            self.patterns['failure_patterns'][failure] += 1
        
        self._save_patterns()
    
    async def get_relevant_learnings(self, query: str, n_results: int = 3) -> List[Dict]:
        """Retrieve relevant past learnings"""
        return await self.rag.query(query, collection='learnings', n_results=n_results)
    
    async def reflect_on_task(self, query: str, history: List[Dict], final_result: str, execution_time: float) -> Learning:
        """Create learning from task execution"""
        # Extract task type from query
        task_type = self._classify_task(query)
        
        # Identify successful actions
        successful_actions = [
            h for h in history if h.get('success', False)
        ]
        
        # Identify failures
        failures = [
            h['observation'] for h in history if not h.get('success', False)
        ]
        
        # Calculate confidence based on success rate
        total_actions = len(history)
        successful_count = len(successful_actions)
        confidence = successful_count / total_actions if total_actions > 0 else 0.0
        
        # Extract prerequisites
        prerequisites = self._extract_prerequisites(history)
        
        learning = Learning(
            task_type=task_type,
            context=query,
            successful_strategy=[a['action'].to_dict() if hasattr(a['action'], 'to_dict') else a['action'] for a in successful_actions],
            failure_modes=failures,
            execution_time=execution_time,
            confidence_score=confidence,
            timestamp=datetime.now(),
            prerequisites=prerequisites
        )
        
        await self.store_learning(learning)
        return learning
    
    def _classify_task(self, query: str) -> str:
        """Classify task type from query"""
        query_lower = query.lower()
        
        if any(kw in query_lower for kw in ['file', 'read', 'write', 'create']):
            return 'file_operation'
        elif any(kw in query_lower for kw in ['search', 'find', 'look']):
            return 'information_retrieval'
        elif any(kw in query_lower for kw in ['code', 'script', 'program', 'function']):
            return 'code_generation'
        elif any(kw in query_lower for kw in ['install', 'setup', 'configure']):
            return 'system_setup'
        elif any(kw in query_lower for kw in ['analyze', 'check', 'test']):
            return 'analysis'
        else:
            return 'general_task'
    
    def _extract_prerequisites(self, history: List[Dict]) -> List[str]:
        """Extract prerequisites from execution history"""
        prereqs = []
        
        for entry in history:
            action = entry.get('action', {})
            if isinstance(action, Action):
                action = action.to_dict()
            
            action_type = action.get('action_type', '')
            
            if 'install' in action_type or 'pip' in str(action.get('parameters', {})):
                prereqs.append(f"dependency: {action.get('parameters', {})}")
            elif action_type == 'file_read':
                prereqs.append(f"requires file: {action.get('parameters', {}).get('filepath')}")
        
        return list(set(prereqs))


class ReActEngine:
    """ReAct reasoning and action loop"""
    
    def __init__(self, llm_client, executor: SecureExecutor, rag: RAGSystem, 
                 learning: LearningSystem, max_iterations: int = 10):
        self.llm = llm_client
        self.executor = executor
        self.rag = rag
        self.learning = learning
        self.max_iterations = max_iterations
        
        self.system_prompt = """You are an autonomous AI agent with ReAct (Reasoning + Acting) capabilities.

Your goal is to solve tasks through iterative reasoning and action execution.

For each step, you must:
1. THINK: Analyze the current situation and plan your next move
2. ACT: Execute a specific action
3. OBSERVE: Examine the result
4. REFLECT: Evaluate if you're making progress toward the goal

Available actions:
- bash_execute: Run shell commands
- python_execute: Execute Python code
- file_read: Read file contents
- file_write: Write content to file
- rag_query: Search knowledge base
- web_search: Search the internet (if available)
- install_dependency: Install required packages

Respond in this JSON format:
{
    "thought": "Your reasoning about what to do next",
    "action": {
        "action_type": "one of the available actions",
        "parameters": {"key": "value"}
    },
    "confidence": 0.0-1.0,
    "requires_confirmation": false
}

If the task is complete, respond:
{
    "thought": "Task completed successfully",
    "action": {"action_type": "complete", "parameters": {"result": "final result"}},
    "confidence": 1.0
}

Be efficient, security-conscious, and learn from failures."""
        
        logger.info("ReAct engine initialized")
    
    async def execute_action(self, action: Action) -> Tuple[bool, str]:
        """Execute an action and return result"""
        action_type = action.action_type
        params = action.parameters
        
        try:
            if action_type == 'bash_execute':
                return await self.executor.execute_bash(params.get('command', ''))
            
            elif action_type == 'python_execute':
                return await self.executor.execute_python(params.get('code', ''))
            
            elif action_type == 'file_read':
                return await self.executor.read_file(params.get('filepath', ''))
            
            elif action_type == 'file_write':
                return await self.executor.write_file(
                    params.get('filepath', ''),
                    params.get('content', '')
                )
            
            elif action_type == 'rag_query':
                results = await self.rag.query(
                    params.get('query', ''),
                    params.get('collection', 'docs'),
                    params.get('n_results', 5)
                )
                return True, json.dumps(results, indent=2)
            
            elif action_type == 'install_dependency':
                package = params.get('package', '')
                return await self.executor.execute_bash(f"pip install {package}")
            
            elif action_type == 'complete':
                return True, params.get('result', 'Task completed')
            
            else:
                return False, f"Unknown action type: {action_type}"
        
        except Exception as e:
            logger.error(f"Action execution error: {e}")
            return False, str(e)
    
    async def think_and_act(self, query: str, context: str, history: List[Dict]) -> Dict:
        """Generate thought and action using LLM"""
        # Format history for context
        history_text = "\n".join([
            f"Step {i+1}:\nThought: {h['thought']}\nAction: {h['action']}\nObservation: {h['observation'][:200]}"
            for i, h in enumerate(history[-5:])  # Last 5 steps
        ])
        
        user_message = f"""Task: {query}

Relevant Knowledge:
{context}

Execution History:
{history_text}

What should you do next?"""
        
        try:
            response = self.llm.messages.create(
                model=os.getenv('LLM_MODEL', 'claude-sonnet-4-20250514'),
                max_tokens=2000,
                system=self.system_prompt,
                messages=[{'role': 'user', 'content': user_message}]
            )
            
            content = response.content[0].text
            
            # Parse JSON response
            # Handle markdown code blocks
            if '```json' in content:
                content = content.split('```json')[1].split('```')[0].strip()
            elif '```' in content:
                content = content.split('```')[1].split('```')[0].strip()
            
            decision = json.loads(content)
            return decision
        
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response: {content}")
            return {
                'thought': 'Error parsing response',
                'action': {'action_type': 'complete', 'parameters': {'result': 'Error in reasoning'}},
                'confidence': 0.0
            }
        except Exception as e:
            logger.error(f"LLM error: {e}")
            return {
                'thought': f'LLM error: {str(e)}',
                'action': {'action_type': 'complete', 'parameters': {'result': 'Error'}},
                'confidence': 0.0
            }
    
    async def run(self, query: str) -> Dict:
        """Execute full ReAct loop"""
        start_time = datetime.now()
        
        # Retrieve relevant context from RAG
        context_docs = await self.rag.query(query, collection='docs', n_results=3)
        context_learnings = await self.learning.get_relevant_learnings(query, n_results=2)
        
        context = "Relevant Documents:\n"
        for doc in context_docs:
            context += f"- {doc['content'][:200]}...\n"
        
        context += "\nPrevious Learnings:\n"
        for learning in context_learnings:
            context += f"- {learning['content'][:200]}...\n"
        
        history = []
        iteration = 0
        
        logger.info(f"Starting ReAct loop for query: {query}")
        
        while iteration < self.max_iterations:
            # THINK & ACT
            decision = await self.think_and_act(query, context, history)
            
            thought = decision.get('thought', '')
            action_dict = decision.get('action', {})
            confidence = decision.get('confidence', 0.5)
            
            logger.info(f"Iteration {iteration+1}: {thought}")
            
            # Create Action object
            action = Action(
                action_type=action_dict.get('action_type', 'complete'),
                parameters=action_dict.get('parameters', {})
            )
            
            # Check if complete
            if action.action_type == 'complete':
                result = action.parameters.get('result', 'Task completed')
                
                # Calculate execution time
                execution_time = (datetime.now() - start_time).total_seconds()
                
                # REFLECT & LEARN
                if os.getenv('REFLECTION_ENABLED', 'true').lower() == 'true':
                    learning = await self.learning.reflect_on_task(
                        query, history, result, execution_time
                    )
                
                logger.info(f"Task completed in {execution_time:.2f}s after {iteration+1} iterations")
                
                return {
                    'success': True,
                    'result': result,
                    'iterations': iteration + 1,
                    'execution_time': execution_time,
                    'history': history
                }
            
            # EXECUTE
            success, observation = await self.execute_action(action)
            
            # Record step
            history.append({
                'thought': thought,
                'action': action,
                'observation': observation,
                'success': success,
                'confidence': confidence
            })
            
            # Update context with observation
            if success and len(observation) < 1000:
                context += f"\nLatest observation: {observation}\n"
            
            iteration += 1
        
        # Max iterations reached
        execution_time = (datetime.now() - start_time).total_seconds()
        
        logger.warning(f"Max iterations reached for query: {query}")
        
        return {
            'success': False,
            'result': 'Max iterations reached without completing task',
            'iterations': iteration,
            'execution_time': execution_time,
            'history': history
        }


class AutonomousOrchestrator:
    """Main orchestrator coordinating all systems"""
    
    def __init__(self, config: Dict):
        self.config = config
        
        # Initialize LLM client
        self.llm_client = anthropic.Anthropic(api_key=config['LLM_API_KEY'])
        
        # Initialize components
        self.executor = SecureExecutor(
            workspace_path=config['WORKSPACE_PATH'],
            safe_mode=config.get('SAFE_MODE', False)
        )
        
        self.rag = RAGSystem(
            db_path=config['VECTOR_DB_PATH'],
            embedding_model=config['EMBEDDING_MODEL'],
            chunk_size=config.get('CHUNK_SIZE', 512),
            chunk_overlap=config.get('CHUNK_OVERLAP', 50)
        )
        
        self.learning = LearningSystem(
            memory_path=config['MEMORY_PATH'],
            rag=self.rag
        )
        
        self.react = ReActEngine(
            llm_client=self.llm_client,
            executor=self.executor,
            rag=self.rag,
            learning=self.learning,
            max_iterations=config.get('MAX_ITERATIONS', 10)
        )
        
        logger.info("Autonomous Orchestrator initialized")
    
    async def execute_task(self, query: str) -> Dict:
        """Execute a task using ReAct loop"""
        return await self.react.run(query)
    
    async def ingest_knowledge(self, content: str, metadata: Dict, collection: str = 'docs') -> bool:
        """Add knowledge to RAG system"""
        return await self.rag.add_document(content, metadata, collection)
    
    async def query_memory(self, query: str) -> List[Dict]:
        """Query learned patterns and experiences"""
        return await self.learning.get_relevant_learnings(query)
    
    def get_status(self) -> Dict:
        """Get system status"""
        return {
            'initialized': True,
            'workspace': str(self.executor.workspace_path),
            'safe_mode': self.executor.safe_mode,
            'patterns': len(self.learning.patterns.get('success_patterns', {})),
            'audit_entries': len(self.executor.audit_log)
        }
    
    def get_capabilities(self) -> List[str]:
        """List current capabilities"""
        return [
            'bash_execute',
            'python_execute',
            'file_operations',
            'rag_query',
            'pattern_learning',
            'self_reflection',
            'dependency_installation'
        ]


def load_config() -> Dict:
    """Load configuration from environment"""
    from dotenv import load_dotenv
    load_dotenv()
    
    config = {
        'TELEGRAM_BOT_TOKEN': os.getenv('TELEGRAM_BOT_TOKEN'),
        'TELEGRAM_ADMIN_ID': os.getenv('TELEGRAM_ADMIN_ID'),
        'LLM_API_KEY': os.getenv('LLM_API_KEY'),
        'LLM_MODEL': os.getenv('LLM_MODEL', 'claude-sonnet-4-20250514'),
        'VECTOR_DB_PATH': os.getenv('VECTOR_DB_PATH', './data/vectordb'),
        'EMBEDDING_MODEL': os.getenv('EMBEDDING_MODEL', 'sentence-transformers/all-MiniLM-L6-v2'),
        'MEMORY_PATH': os.getenv('MEMORY_PATH', './data/memory'),
        'WORKSPACE_PATH': os.getenv('WORKSPACE_PATH', './workspace'),
        'MAX_ITERATIONS': int(os.getenv('MAX_ITERATIONS', '10')),
        'SAFE_MODE': os.getenv('SAFE_MODE', 'false').lower() == 'true',
        'CHUNK_SIZE': int(os.getenv('CHUNK_SIZE', '512')),
        'CHUNK_OVERLAP': int(os.getenv('CHUNK_OVERLAP', '50')),
    }
    
    return config


if __name__ == '__main__':
    # Test the orchestrator
    async def test():
        config = load_config()
        orchestrator = AutonomousOrchestrator(config)
        
        result = await orchestrator.execute_task("Create a Python script that lists all files in the workspace")
        print(json.dumps(result, indent=2, default=str))
    
    asyncio.run(test())
