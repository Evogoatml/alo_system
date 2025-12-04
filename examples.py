"""
Examples: Using ALO Programmatically
Demonstrates all features and capabilities
"""

import asyncio
import json
from pathlib import Path

from orchestrator import AutonomousOrchestrator, load_config, Learning
from advanced_capabilities import extend_orchestrator_with_advanced_capabilities
from datetime import datetime


# ============================================================================
# Example 1: Basic Task Execution
# ============================================================================

async def example_basic_task():
    """Execute a simple task"""
    print("\n" + "="*60)
    print("Example 1: Basic Task Execution")
    print("="*60)
    
    config = load_config()
    orchestrator = AutonomousOrchestrator(config)
    
    result = await orchestrator.execute_task(
        "Create a Python function that reverses a string"
    )
    
    print(f"\nSuccess: {result['success']}")
    print(f"Result: {result['result']}")
    print(f"Iterations: {result['iterations']}")
    print(f"Time: {result['execution_time']:.2f}s")


# ============================================================================
# Example 2: Knowledge Ingestion
# ============================================================================

async def example_knowledge_ingestion():
    """Add knowledge to the system"""
    print("\n" + "="*60)
    print("Example 2: Knowledge Ingestion")
    print("="*60)
    
    config = load_config()
    orchestrator = AutonomousOrchestrator(config)
    
    # Add documentation
    knowledge = """
    Python Best Practices:
    1. Always use context managers for file operations
    2. Use list comprehensions for simple transformations
    3. Follow PEP 8 style guide
    4. Write docstrings for all functions
    5. Use type hints for better code clarity
    """
    
    metadata = {
        'source': 'company_standards',
        'category': 'python',
        'timestamp': datetime.now().isoformat()
    }
    
    success = await orchestrator.ingest_knowledge(knowledge, metadata)
    print(f"\nKnowledge added: {success}")
    
    # Now execute a task that should use this knowledge
    result = await orchestrator.execute_task(
        "Create a Python function to read a file"
    )
    
    print(f"\nTask result: {result['result'][:200]}...")
    print("(Should include context manager based on learned knowledge)")


# ============================================================================
# Example 3: Multi-Step Complex Task
# ============================================================================

async def example_complex_task():
    """Execute a multi-step task"""
    print("\n" + "="*60)
    print("Example 3: Complex Multi-Step Task")
    print("="*60)
    
    config = load_config()
    orchestrator = AutonomousOrchestrator(config)
    
    complex_query = """
    Create a complete data analysis pipeline:
    1. Generate sample CSV data with 3 columns: name, age, score
    2. Write a Python script to load and analyze the data
    3. Calculate statistics (mean, median, std deviation)
    4. Create a summary report
    """
    
    result = await orchestrator.execute_task(complex_query)
    
    print(f"\nCompleted in {result['iterations']} iterations")
    print(f"Execution time: {result['execution_time']:.2f}s")
    
    # Show execution history
    print("\nExecution History:")
    for i, step in enumerate(result['history'], 1):
        print(f"  Step {i}: {step['thought'][:50]}...")


# ============================================================================
# Example 4: Using Advanced Capabilities
# ============================================================================

async def example_advanced_capabilities():
    """Use web search and API capabilities"""
    print("\n" + "="*60)
    print("Example 4: Advanced Capabilities")
    print("="*60)
    
    config = load_config()
    orchestrator = AutonomousOrchestrator(config)
    
    # Enable advanced features
    extend_orchestrator_with_advanced_capabilities(orchestrator)
    
    # Task that requires web search
    result = await orchestrator.execute_task(
        "Search for the latest Python version and create a summary"
    )
    
    print(f"\nResult: {result['result'][:300]}...")
    
    # Cleanup
    await orchestrator.advanced.close()


# ============================================================================
# Example 5: Learning and Improvement
# ============================================================================

async def example_learning_system():
    """Demonstrate learning and pattern recognition"""
    print("\n" + "="*60)
    print("Example 5: Learning System")
    print("="*60)
    
    config = load_config()
    orchestrator = AutonomousOrchestrator(config)
    
    # Execute similar tasks multiple times
    tasks = [
        "Create a function to calculate factorial",
        "Create a function to calculate fibonacci",
        "Create a function to check if a number is prime"
    ]
    
    print("\nExecuting multiple code generation tasks...")
    for task in tasks:
        result = await orchestrator.execute_task(task)
        print(f"  ✓ {task}: {result['iterations']} iterations")
    
    # Query learned patterns
    learnings = await orchestrator.query_memory("code generation")
    
    print(f"\nLearned patterns: {len(learnings)}")
    if learnings:
        print("\nMost relevant learning:")
        print(f"  {learnings[0]['content'][:200]}...")


# ============================================================================
# Example 6: Direct Component Usage
# ============================================================================

async def example_direct_component_usage():
    """Use individual components directly"""
    print("\n" + "="*60)
    print("Example 6: Direct Component Usage")
    print("="*60)
    
    config = load_config()
    orchestrator = AutonomousOrchestrator(config)
    
    # Use RAG system directly
    print("\n1. Using RAG System:")
    
    # Add documents
    await orchestrator.rag.add_document(
        content="FastAPI is a modern web framework for Python",
        metadata={'topic': 'web_frameworks'},
        collection='docs'
    )
    
    # Query
    results = await orchestrator.rag.query("Python web frameworks")
    print(f"   Found {len(results)} relevant documents")
    
    # Use executor directly
    print("\n2. Using Secure Executor:")
    
    success, output = await orchestrator.executor.execute_bash("echo 'Hello from bash'")
    print(f"   Bash execution: {output.strip()}")
    
    success, output = await orchestrator.executor.execute_python("print('Hello from Python')")
    print(f"   Python execution: {output.strip()}")
    
    # Use learning system directly
    print("\n3. Using Learning System:")
    
    custom_learning = Learning(
        task_type='custom_example',
        context='Example learning',
        successful_strategy=[],
        failure_modes=[],
        execution_time=1.0,
        confidence_score=0.9,
        timestamp=datetime.now(),
        prerequisites=[]
    )
    
    await orchestrator.learning.store_learning(custom_learning)
    print("   Custom learning stored")


# ============================================================================
# Example 7: Error Handling and Recovery
# ============================================================================

async def example_error_handling():
    """Demonstrate error handling"""
    print("\n" + "="*60)
    print("Example 7: Error Handling and Recovery")
    print("="*60)
    
    config = load_config()
    orchestrator = AutonomousOrchestrator(config)
    
    # Intentionally problematic task
    result = await orchestrator.execute_task(
        "This is a vague and unclear request"
    )
    
    print(f"\nSuccess: {result['success']}")
    print(f"Iterations attempted: {result['iterations']}")
    
    # Check execution history for errors
    failures = [
        step for step in result['history']
        if not step.get('success', True)
    ]
    
    print(f"\nEncountered {len(failures)} failures during execution")
    print("System learned from these failures for future improvements")


# ============================================================================
# Example 8: Batch Processing
# ============================================================================

async def example_batch_processing():
    """Process multiple tasks in batch"""
    print("\n" + "="*60)
    print("Example 8: Batch Task Processing")
    print("="*60)
    
    config = load_config()
    orchestrator = AutonomousOrchestrator(config)
    
    tasks = [
        "Create hello.txt with content 'Hello World'",
        "Create goodbye.txt with content 'Goodbye'",
        "List all txt files in workspace"
    ]
    
    print("\nProcessing batch of tasks...")
    results = []
    
    for i, task in enumerate(tasks, 1):
        print(f"\n  Task {i}/{len(tasks)}: {task}")
        result = await orchestrator.execute_task(task)
        results.append(result)
        print(f"    Status: {'✓' if result['success'] else '✗'}")
    
    # Summary
    successful = sum(1 for r in results if r['success'])
    print(f"\n✅ Batch complete: {successful}/{len(tasks)} successful")


# ============================================================================
# Example 9: Custom Action Extension
# ============================================================================

async def example_custom_action():
    """Add custom actions to the system"""
    print("\n" + "="*60)
    print("Example 9: Custom Action Extension")
    print("="*60)
    
    config = load_config()
    orchestrator = AutonomousOrchestrator(config)
    
    # Extend with custom action
    original_execute = orchestrator.react.execute_action
    
    async def custom_execute(action):
        if action.action_type == 'custom_hello':
            name = action.parameters.get('name', 'World')
            return True, f"Hello, {name}!"
        return await original_execute(action)
    
    orchestrator.react.execute_action = custom_execute
    
    print("\nCustom action 'custom_hello' added")
    print("System can now execute this new action type")


# ============================================================================
# Example 10: System Status and Monitoring
# ============================================================================

async def example_monitoring():
    """Monitor system status"""
    print("\n" + "="*60)
    print("Example 10: System Monitoring")
    print("="*60)
    
    config = load_config()
    orchestrator = AutonomousOrchestrator(config)
    
    # Get system status
    status = orchestrator.get_status()
    
    print("\nSystem Status:")
    for key, value in status.items():
        print(f"  {key}: {value}")
    
    # Get capabilities
    capabilities = orchestrator.get_capabilities()
    
    print("\nCapabilities:")
    for cap in capabilities:
        print(f"  • {cap}")
    
    # Check audit log
    print(f"\nAudit Log Entries: {len(orchestrator.executor.audit_log)}")
    if orchestrator.executor.audit_log:
        recent = orchestrator.executor.audit_log[-1]
        print(f"  Last Action: {recent['action']}")
        print(f"  Success: {recent['success']}")


# ============================================================================
# Run All Examples
# ============================================================================

async def run_all_examples():
    """Run all examples"""
    examples = [
        ("Basic Task", example_basic_task),
        ("Knowledge Ingestion", example_knowledge_ingestion),
        ("Complex Task", example_complex_task),
        # ("Advanced Capabilities", example_advanced_capabilities),  # Requires API keys
        ("Learning System", example_learning_system),
        ("Direct Components", example_direct_component_usage),
        ("Error Handling", example_error_handling),
        ("Batch Processing", example_batch_processing),
        ("Custom Actions", example_custom_action),
        ("Monitoring", example_monitoring),
    ]
    
    print("\n" + "="*60)
    print("Running ALO Examples")
    print("="*60)
    print(f"\nTotal examples: {len(examples)}\n")
    
    for name, example_func in examples:
        try:
            await example_func()
        except Exception as e:
            print(f"\n❌ Example '{name}' failed: {e}")
        
        input("\nPress Enter to continue...")
    
    print("\n" + "="*60)
    print("All Examples Complete!")
    print("="*60)


def main():
    """Main entry point"""
    print("""
╔═══════════════════════════════════════════════════════════╗
║          ALO Examples - Interactive Tutorial              ║
╚═══════════════════════════════════════════════════════════╝

This script demonstrates all features of the Autonomous Learning
Orchestrator through practical examples.

Available examples:
  1. Basic Task Execution
  2. Knowledge Ingestion
  3. Complex Multi-Step Tasks
  4. Advanced Web Capabilities
  5. Learning and Pattern Recognition
  6. Direct Component Usage
  7. Error Handling
  8. Batch Processing
  9. Custom Action Extension
  10. System Monitoring
""")
    
    print("Choose an option:")
    print("  [a] Run all examples")
    print("  [1-10] Run specific example")
    print("  [q] Quit")
    
    choice = input("\nChoice: ").strip().lower()
    
    if choice == 'q':
        return
    elif choice == 'a':
        asyncio.run(run_all_examples())
    elif choice.isdigit() and 1 <= int(choice) <= 10:
        example_map = {
            1: example_basic_task,
            2: example_knowledge_ingestion,
            3: example_complex_task,
            4: example_advanced_capabilities,
            5: example_learning_system,
            6: example_direct_component_usage,
            7: example_error_handling,
            8: example_batch_processing,
            9: example_custom_action,
            10: example_monitoring,
        }
        asyncio.run(example_map[int(choice)]())
    else:
        print("Invalid choice")


if __name__ == '__main__':
    main()
