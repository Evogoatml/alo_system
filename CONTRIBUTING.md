# Contributing to Autonomous Learning Orchestrator (ALO)

Thank you for your interest in contributing to ALO! This document provides guidelines and instructions for contributing to the project.

## 🎯 Ways to Contribute

- **Bug Reports**: Report issues you encounter
- **Feature Requests**: Suggest new features or improvements
- **Code Contributions**: Submit pull requests
- **Documentation**: Improve or translate documentation
- **Testing**: Write tests or test new features
- **Examples**: Add usage examples

## 🚀 Getting Started

### 1. Fork and Clone

```bash
# Fork the repository on GitHub
# Then clone your fork
git clone https://github.com/YOUR_USERNAME/alo_system.git
cd alo_system

# Add upstream remote
git remote add upstream https://github.com/ORIGINAL_OWNER/alo_system.git
```

### 2. Setup Development Environment

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install pytest pytest-asyncio pytest-cov black flake8 mypy

# Run setup
python setup.py
```

### 3. Create a Branch

```bash
# Create a feature branch
git checkout -b feature/your-feature-name

# Or for bug fixes
git checkout -b fix/bug-description
```

## 📝 Development Guidelines

### Code Style

- Follow PEP 8 style guide
- Use type hints for function signatures
- Maximum line length: 100 characters
- Use meaningful variable and function names

```python
# Good
async def execute_task(self, query: str, max_iterations: int = 10) -> Dict[str, Any]:
    """
    Execute a task using ReAct reasoning loop.
    
    Args:
        query: The task description
        max_iterations: Maximum number of ReAct iterations
        
    Returns:
        Dict containing execution results
    """
    pass

# Bad
async def exec(q, m=10):
    pass
```

### Code Formatting

Use `black` for automatic formatting:

```bash
black orchestrator.py telegram_bot.py
```

### Linting

Run `flake8` before committing:

```bash
flake8 orchestrator.py --max-line-length=100
```

### Type Checking

Use `mypy` for type checking:

```bash
mypy orchestrator.py --ignore-missing-imports
```

## 🧪 Testing

### Writing Tests

- Write tests for all new features
- Maintain or improve code coverage
- Use descriptive test names
- Include both unit and integration tests

```python
class TestNewFeature:
    """Test new feature functionality"""
    
    @pytest.mark.asyncio
    async def test_feature_success_case(self):
        """Test successful execution of new feature"""
        # Arrange
        config = get_test_config()
        orchestrator = AutonomousOrchestrator(config)
        
        # Act
        result = await orchestrator.new_feature()
        
        # Assert
        assert result['success'] is True
```

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_orchestrator.py

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test
pytest tests/test_orchestrator.py::TestClass::test_method -v
```

## 📚 Documentation

### Code Documentation

- Add docstrings to all public functions and classes
- Use Google-style docstrings
- Include examples in docstrings where helpful

```python
def add_document(self, content: str, metadata: Dict) -> bool:
    """
    Add a document to the vector database.
    
    Args:
        content: The document text content
        metadata: Document metadata (source, timestamp, etc.)
        
    Returns:
        True if successful, False otherwise
        
    Example:
        >>> rag = RAGSystem(...)
        >>> success = await rag.add_document(
        ...     content="Python is a programming language",
        ...     metadata={'source': 'docs'}
        ... )
    """
```

### README Updates

- Update README.md for significant changes
- Add new features to feature list
- Update examples if needed

## 🔐 Security

### Security Issues

- **DO NOT** open public issues for security vulnerabilities
- Email security@yourproject.com instead
- Include detailed steps to reproduce

### Security Best Practices

- Never commit API keys or secrets
- Use `.env` for sensitive configuration
- Validate all user inputs
- Sanitize file paths
- Use parameterized queries for databases

## 📋 Commit Guidelines

### Commit Message Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Build process or auxiliary tool changes

**Examples:**

```
feat(orchestrator): add support for custom actions

- Implemented custom action registration
- Added validation for action types
- Updated documentation

Closes #123
```

```
fix(telegram): handle rate limiting correctly

Fixed issue where rate limiting wasn't applied
consistently across all commands.

Fixes #456
```

## 🔄 Pull Request Process

### Before Submitting

1. ✅ Run all tests and ensure they pass
2. ✅ Update documentation if needed
3. ✅ Add tests for new features
4. ✅ Run linters and formatters
5. ✅ Update CHANGELOG.md (if applicable)

### PR Description Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
Describe the tests you ran

## Checklist
- [ ] Tests pass locally
- [ ] Code follows style guidelines
- [ ] Documentation updated
- [ ] No new warnings
- [ ] Added tests for changes
```

### Review Process

1. Automated tests will run
2. Maintainers will review your code
3. Address any feedback
4. Once approved, your PR will be merged

## 🎨 Feature Development Workflow

### Planning

1. Open an issue to discuss the feature
2. Get feedback from maintainers
3. Design the solution
4. Create implementation plan

### Implementation

1. Create feature branch
2. Implement in small, logical commits
3. Write tests as you go
4. Update documentation
5. Submit PR

### Example Feature Implementation

```python
# 1. Add to orchestrator.py
class NewCapability:
    """New capability description"""
    
    async def execute(self, params: Dict) -> Tuple[bool, str]:
        """Execute the capability"""
        # Implementation
        pass

# 2. Integrate into ReActEngine
async def execute_action(self, action: Action):
    if action.action_type == 'new_capability':
        return await self.new_capability.execute(action.parameters)
    # ... existing code

# 3. Add tests
class TestNewCapability:
    @pytest.mark.asyncio
    async def test_new_capability(self):
        # Test implementation
        pass

# 4. Update documentation
# - README.md: Add to capabilities list
# - examples.py: Add usage example
```

## 🐛 Bug Fix Workflow

### Reporting

1. Check if bug already reported
2. Provide detailed reproduction steps
3. Include system information
4. Add error messages/logs

### Fixing

1. Write a test that reproduces the bug
2. Fix the bug
3. Ensure test passes
4. Verify no regressions
5. Submit PR

## 📊 Performance Improvements

- Profile code before optimizing
- Include benchmarks in PR
- Don't sacrifice readability for minor gains
- Document performance-critical sections

## 🤝 Code Review Guidelines

### As a Reviewer

- Be respectful and constructive
- Explain the "why" behind suggestions
- Approve when ready, request changes when needed
- Review within 48 hours if possible

### As an Author

- Respond to all comments
- Ask questions if unclear
- Don't take feedback personally
- Update based on feedback

## 📌 Release Process

1. Update version in `__init__.py`
2. Update CHANGELOG.md
3. Create release branch
4. Run full test suite
5. Create GitHub release
6. Tag with version number

## 💬 Communication

- **GitHub Issues**: Bug reports, feature requests
- **Pull Requests**: Code contributions
- **Discussions**: Questions, ideas
- **Email**: security@yourproject.com for security issues

## 📄 License

By contributing, you agree that your contributions will be licensed under the MIT License.

## 🙏 Recognition

Contributors will be recognized in:
- README.md contributors section
- CHANGELOG.md for significant contributions
- Release notes

## ❓ Questions?

- Check existing issues and discussions
- Read the documentation
- Ask in GitHub Discussions
- Email: support@yourproject.com

---

Thank you for contributing to ALO! 🚀
