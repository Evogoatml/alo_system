"""Action Executor - Execute various actions with sandboxing"""
import os
import sys
import subprocess
import logging
import tempfile
import requests
from typing import Dict, Any, Optional
import json
import shutil
from pathlib import Path
from config import config
from rag_system import rag_system

logger = logging.getLogger(__name__)

class ActionExecutor:
    def __init__(self):
        self.workspace = Path(config.execution.workspace_path)
        self.workspace.mkdir(parents=True, exist_ok=True)
        self.safe_mode = config.execution.safe_mode
        
    def execute(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute an action and return observation
        action: {"action_type": str, "parameters": dict}
        """
        action_type = action.get("action_type", "unknown")
        parameters = action.get("parameters", {})
        
        logger.info(f"Executing action: {action_type}")
        
        try:
            if action_type == "bash_execute":
                return self._bash_execute(parameters)
            elif action_type == "python_execute":
                return self._python_execute(parameters)
            elif action_type == "file_read":
                return self._file_read(parameters)
            elif action_type == "file_write":
                return self._file_write(parameters)
            elif action_type == "web_search":
                return self._web_search(parameters)
            elif action_type == "web_scrape":
                return self._web_scrape(parameters)
            elif action_type == "git_operation":
                return self._git_operation(parameters)
            elif action_type == "api_call":
                return self._api_call(parameters)
            elif action_type == "rag_query":
                return self._rag_query(parameters)
            elif action_type == "install_package":
                return self._install_package(parameters)
            elif action_type == "self_modify":
                return self._self_modify(parameters)
            else:
                return {
                    "success": False,
                    "output": f"Unknown action type: {action_type}",
                    "action_type": action_type
                }
        except Exception as e:
            logger.error(f"Error executing {action_type}: {e}")
            return {
                "success": False,
                "output": str(e),
                "action_type": action_type,
                "error": str(e)
            }
    
    def _bash_execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute bash command"""
        command = params.get("command", "")
        
        if not config.execution.code_execution_enabled:
            return {"success": False, "output": "Code execution is disabled"}
        
        if self.safe_mode and any(dangerous in command.lower() 
                                 for dangerous in ["rm -rf", "dd if=", "mkfs", "> /dev/"]):
            return {"success": False, "output": "Command blocked in safe mode"}
        
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=config.execution.timeout,
                cwd=str(self.workspace)
            )
            
            return {
                "success": result.returncode == 0,
                "output": result.stdout or result.stderr,
                "return_code": result.returncode,
                "action_type": "bash_execute"
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "output": "Command timed out", "action_type": "bash_execute"}
        except Exception as e:
            return {"success": False, "output": str(e), "action_type": "bash_execute"}
    
    def _python_execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute Python code in isolated environment"""
        code = params.get("code", "")
        
        if not config.execution.code_execution_enabled:
            return {"success": False, "output": "Code execution is disabled"}
        
        # Create temporary file for code
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, dir=str(self.workspace)) as f:
            f.write(code)
            temp_file = f.name
        
        try:
            result = subprocess.run(
                [sys.executable, temp_file],
                capture_output=True,
                text=True,
                timeout=config.execution.timeout,
                cwd=str(self.workspace)
            )
            
            return {
                "success": result.returncode == 0,
                "output": result.stdout or result.stderr,
                "return_code": result.returncode,
                "action_type": "python_execute"
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "output": "Execution timed out", "action_type": "python_execute"}
        except Exception as e:
            return {"success": False, "output": str(e), "action_type": "python_execute"}
        finally:
            # Clean up temp file
            try:
                os.unlink(temp_file)
            except:
                pass
    
    def _file_read(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Read file contents"""
        filepath = params.get("path", "")
        
        # Resolve path relative to workspace if not absolute
        if not os.path.isabs(filepath):
            filepath = os.path.join(self.workspace, filepath)
        
        # Safety check
        if self.safe_mode and not str(Path(filepath).resolve()).startswith(str(self.workspace.resolve())):
            return {"success": False, "output": "Access denied: file outside workspace"}
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if len(content) > config.execution.max_file_size:
                content = content[:config.execution.max_file_size] + "\n... (truncated)"
            
            return {
                "success": True,
                "output": content,
                "action_type": "file_read",
                "filepath": filepath
            }
        except Exception as e:
            return {"success": False, "output": str(e), "action_type": "file_read"}
    
    def _file_write(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Write content to file"""
        filepath = params.get("path", "")
        content = params.get("content", "")
        
        # Resolve path relative to workspace
        if not os.path.isabs(filepath):
            filepath = os.path.join(self.workspace, filepath)
        
        # Safety check
        if self.safe_mode and not str(Path(filepath).resolve()).startswith(str(self.workspace.resolve())):
            return {"success": False, "output": "Access denied: file outside workspace"}
        
        try:
            # Create parent directories
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return {
                "success": True,
                "output": f"Written {len(content)} bytes to {filepath}",
                "action_type": "file_write",
                "filepath": filepath
            }
        except Exception as e:
            return {"success": False, "output": str(e), "action_type": "file_write"}
    
    def _web_search(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Search the web (requires DuckDuckGo or similar API)"""
        query = params.get("query", "")
        
        try:
            # Using DuckDuckGo instant answer API (no key required)
            response = requests.get(
                "https://api.duckduckgo.com/",
                params={"q": query, "format": "json"},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                result = {
                    "abstract": data.get("Abstract", ""),
                    "url": data.get("AbstractURL", ""),
                    "related": [r.get("Text", "") for r in data.get("RelatedTopics", [])[:5]]
                }
                
                return {
                    "success": True,
                    "output": json.dumps(result, indent=2),
                    "action_type": "web_search",
                    "data": result
                }
            else:
                return {"success": False, "output": f"Search failed: {response.status_code}"}
        except Exception as e:
            return {"success": False, "output": str(e), "action_type": "web_search"}
    
    def _web_scrape(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Scrape webpage content"""
        url = params.get("url", "")
        
        try:
            response = requests.get(url, timeout=30, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            })
            
            if response.status_code == 200:
                # Simple text extraction (in production, use BeautifulSoup)
                content = response.text[:10000]  # Limit to 10KB
                
                return {
                    "success": True,
                    "output": content,
                    "action_type": "web_scrape",
                    "url": url,
                    "status_code": response.status_code
                }
            else:
                return {"success": False, "output": f"HTTP {response.status_code}"}
        except Exception as e:
            return {"success": False, "output": str(e), "action_type": "web_scrape"}
    
    def _git_operation(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Perform git operations"""
        operation = params.get("operation", "")  # clone, pull, push, commit
        repo_url = params.get("repo_url", "")
        message = params.get("message", "")
        
        try:
            if operation == "clone":
                result = subprocess.run(
                    ["git", "clone", repo_url],
                    capture_output=True,
                    text=True,
                    cwd=str(self.workspace),
                    timeout=config.execution.timeout
                )
            elif operation == "pull":
                result = subprocess.run(
                    ["git", "pull"],
                    capture_output=True,
                    text=True,
                    cwd=str(self.workspace),
                    timeout=config.execution.timeout
                )
            elif operation == "commit":
                subprocess.run(["git", "add", "."], cwd=str(self.workspace))
                result = subprocess.run(
                    ["git", "commit", "-m", message],
                    capture_output=True,
                    text=True,
                    cwd=str(self.workspace)
                )
            elif operation == "push":
                result = subprocess.run(
                    ["git", "push"],
                    capture_output=True,
                    text=True,
                    cwd=str(self.workspace),
                    timeout=config.execution.timeout
                )
            else:
                return {"success": False, "output": f"Unknown git operation: {operation}"}
            
            return {
                "success": result.returncode == 0,
                "output": result.stdout or result.stderr,
                "action_type": "git_operation",
                "operation": operation
            }
        except Exception as e:
            return {"success": False, "output": str(e), "action_type": "git_operation"}
    
    def _api_call(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Make HTTP API call"""
        method = params.get("method", "GET").upper()
        url = params.get("url", "")
        headers = params.get("headers", {})
        data = params.get("data")
        
        try:
            response = requests.request(
                method,
                url,
                headers=headers,
                json=data if data else None,
                timeout=30
            )
            
            return {
                "success": response.status_code < 400,
                "output": response.text[:5000],  # Limit response size
                "action_type": "api_call",
                "status_code": response.status_code,
                "data": response.json() if response.headers.get("content-type", "").startswith("application/json") else None
            }
        except Exception as e:
            return {"success": False, "output": str(e), "action_type": "api_call"}
    
    def _rag_query(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Query RAG system"""
        query = params.get("query", "")
        n_results = params.get("n_results", 5)
        
        try:
            results = rag_system.search(query, n_results=n_results)
            
            formatted_output = "\n\n".join([
                f"[Similarity: {r['similarity']:.2f}] {r['text'][:200]}..."
                for r in results
            ])
            
            return {
                "success": True,
                "output": formatted_output,
                "action_type": "rag_query",
                "results": results
            }
        except Exception as e:
            return {"success": False, "output": str(e), "action_type": "rag_query"}
    
    def _install_package(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Install Python package or system package"""
        package_type = params.get("type", "pip")  # pip or apt
        package_name = params.get("package", "")
        
        try:
            if package_type == "pip":
                result = subprocess.run(
                    [sys.executable, "-m", "pip", "install", package_name],
                    capture_output=True,
                    text=True,
                    timeout=300
                )
            elif package_type == "apt":
                result = subprocess.run(
                    ["apt-get", "install", "-y", package_name],
                    capture_output=True,
                    text=True,
                    timeout=300
                )
            else:
                return {"success": False, "output": f"Unknown package type: {package_type}"}
            
            return {
                "success": result.returncode == 0,
                "output": result.stdout or result.stderr,
                "action_type": "install_package",
                "package": package_name,
                "type": package_type
            }
        except Exception as e:
            return {"success": False, "output": str(e), "action_type": "install_package"}
    
    def _self_modify(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Modify system capabilities (very careful with this!)"""
        module_name = params.get("module", "")
        code = params.get("code", "")
        
        if self.safe_mode:
            return {"success": False, "output": "Self-modification disabled in safe mode"}
        
        # Only allow creating new modules in workspace/extensions
        extensions_dir = self.workspace / "extensions"
        extensions_dir.mkdir(exist_ok=True)
        
        module_path = extensions_dir / f"{module_name}.py"
        
        try:
            with open(module_path, 'w') as f:
                f.write(code)
            
            return {
                "success": True,
                "output": f"Created extension module: {module_path}",
                "action_type": "self_modify",
                "module": module_name
            }
        except Exception as e:
            return {"success": False, "output": str(e), "action_type": "self_modify"}

action_executor = ActionExecutor()
