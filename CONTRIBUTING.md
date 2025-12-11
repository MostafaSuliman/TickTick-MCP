# Contributing to TickTick MCP Server

Thank you for your interest in contributing to the TickTick MCP Server! This document provides guidelines and instructions for contributing.

## Code of Conduct

By participating in this project, you agree to maintain a respectful and inclusive environment for everyone.

## How to Contribute

### Reporting Bugs

1. Check if the bug has already been reported in [Issues](https://github.com/MostafaSuliman/TickTick-MCP/issues)
2. If not, create a new issue using the bug report template
3. Include:
   - Clear description of the bug
   - Steps to reproduce
   - Expected vs actual behavior
   - Environment details (OS, Python version, etc.)
   - Relevant logs or error messages

### Suggesting Features

1. Check existing issues and discussions for similar suggestions
2. Create a new issue using the feature request template
3. Explain the use case and proposed solution
4. Indicate if the feature is supported by TickTick's API

### Pull Requests

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Make your changes
4. Write or update tests
5. Update documentation if needed
6. Run tests and linting: `pytest && ruff check src/`
7. Commit with clear messages
8. Push and create a pull request

## Development Setup

### Prerequisites

- Python 3.10 or higher
- Git

### Installation

```bash
# Clone the repository
git clone https://github.com/MostafaSuliman/TickTick-MCP.git
cd TickTick-MCP

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/ticktick_mcp --cov-report=html

# Run specific test file
pytest tests/test_tasks.py
```

### Code Style

We use:
- **Black** for code formatting
- **Ruff** for linting
- **mypy** for type checking

```bash
# Format code
black src/ tests/

# Check linting
ruff check src/

# Type check
mypy src/ticktick_mcp
```

### Project Structure

```
src/ticktick_mcp/
├── api/           # API client and endpoints
├── cache/         # Local task cache
├── models/        # Pydantic data models
├── services/      # Business logic
└── tools/         # MCP tool definitions
```

### Adding New Tools

1. **Create service methods** in `services/` if needed
2. **Define input models** using Pydantic in the tools file
3. **Register the tool** in `tools/__init__.py`
4. **Write tests** in `tests/`
5. **Update documentation** in README

Example tool structure:

```python
# tools/my_tools.py
from pydantic import BaseModel, Field

class MyToolInput(BaseModel):
    """Input for my tool."""
    param: str = Field(..., description="Parameter description")

def register_my_tools(mcp, my_service):
    @mcp.tool(
        name="ticktick_my_tool",
        annotations={
            "title": "My Tool",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
        }
    )
    async def my_tool(params: MyToolInput) -> str:
        """Tool description for Claude."""
        result = await my_service.do_something(params.param)
        return format_result(result)
```

### API Guidelines

- **v1 API** (Official): Use for basic task/project operations
- **v2 API** (Internal): Use for extended features (habits, focus, tags)
- Always check `is_v2_available` before using v2 endpoints
- Handle API errors gracefully
- Use retry logic for network errors

### Commit Messages

Follow conventional commits:

```
type(scope): description

[optional body]

[optional footer]
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Formatting
- `refactor`: Code restructuring
- `test`: Adding tests
- `chore`: Maintenance

Example:
```
feat(tasks): add batch update functionality

Implements batch task updates using v2 API.
Falls back to sequential updates for v1 API.

Closes #123
```

## Questions?

- Open a [Discussion](https://github.com/MostafaSuliman/TickTick-MCP/discussions)
- Check existing issues
- Review the documentation

Thank you for contributing!
