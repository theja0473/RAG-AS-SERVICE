# Contributing to OpenAgentRAG

Thank you for your interest in contributing to OpenAgentRAG! This document provides guidelines and instructions for contributing to the project.

## Table of Contents

1. [Code of Conduct](#code-of-conduct)
2. [Getting Started](#getting-started)
3. [Development Setup](#development-setup)
4. [Making Changes](#making-changes)
5. [Pull Request Process](#pull-request-process)
6. [Code Style Guidelines](#code-style-guidelines)
7. [Testing Requirements](#testing-requirements)
8. [Branch Strategy](#branch-strategy)
9. [Commit Message Convention](#commit-message-convention)
10. [Documentation](#documentation)

---

## Code of Conduct

This project adheres to a code of conduct that all contributors are expected to follow:

- Be respectful and inclusive
- Welcome newcomers and help them get started
- Focus on what is best for the community
- Show empathy towards other community members
- Accept constructive criticism gracefully

---

## Getting Started

### Prerequisites

Before you begin, ensure you have:

- Git installed and configured
- Docker 24.0+ and Docker Compose 2.0+
- Python 3.9+ (for backend development)
- Node.js 18+ (for frontend development)
- A GitHub account
- Familiarity with RAG concepts and multi-agent systems

### Finding Issues to Work On

1. Browse the [Issues](https://github.com/yourusername/open-agent-rag/issues) page
2. Look for issues labeled `good first issue` or `help wanted`
3. Comment on the issue to express your interest
4. Wait for maintainer confirmation before starting work

### Reporting Bugs

When reporting bugs, please include:

- Clear, descriptive title
- Steps to reproduce the issue
- Expected behavior vs. actual behavior
- Environment details (OS, Docker version, Python version)
- Relevant logs or error messages
- Screenshots if applicable

### Suggesting Enhancements

For feature requests or enhancements:

- Check if the feature has already been requested
- Provide a clear use case and rationale
- Describe the expected behavior
- Consider implementation complexity
- Be open to discussion and feedback

---

## Development Setup

### 1. Fork and Clone

```bash
# Fork the repository on GitHub, then clone your fork
git clone https://github.com/YOUR_USERNAME/open-agent-rag.git
cd open-agent-rag

# Add upstream remote
git remote add upstream https://github.com/yourusername/open-agent-rag.git
```

### 2. Environment Setup

```bash
# Copy environment template
cp .env.example .env

# Start dependencies via Docker
docker compose up -d ollama chromadb

# Wait for services to be ready
sleep 30

# Pull the LLM model
docker compose exec ollama ollama pull llama3
```

### 3. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt  # Development dependencies

# Run backend locally
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

### 5. Verify Setup

```bash
# Check backend health
curl http://localhost:8000/health

# Access frontend
open http://localhost:3000

# Run tests
cd backend && pytest
cd frontend && npm test
```

---

## Making Changes

### Workflow

1. **Create a branch** from `development` (not `main`)
   ```bash
   git checkout development
   git pull upstream development
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** following code style guidelines

3. **Add tests** for new functionality

4. **Run the test suite** to ensure nothing breaks
   ```bash
   # Backend
   cd backend && pytest tests/ --cov=app

   # Frontend
   cd frontend && npm test
   ```

5. **Update documentation** if needed

6. **Commit your changes** using conventional commits

7. **Push to your fork**
   ```bash
   git push origin feature/your-feature-name
   ```

8. **Open a Pull Request** to the `development` branch

---

## Pull Request Process

### Before Submitting

- [ ] Code follows project style guidelines
- [ ] All tests pass locally
- [ ] New tests added for new functionality
- [ ] Documentation updated (if applicable)
- [ ] No merge conflicts with `development` branch
- [ ] Commit messages follow convention
- [ ] PR title is clear and descriptive

### PR Template

When creating a PR, include:

```markdown
## Description
Brief description of what this PR does.

## Motivation
Why is this change necessary? What problem does it solve?

## Changes
- List of key changes made
- Breaking changes (if any)

## Testing
How was this tested? What test cases were added?

## Screenshots (if applicable)
Before/after screenshots for UI changes

## Checklist
- [ ] Tests pass
- [ ] Documentation updated
- [ ] No breaking changes (or documented if present)
```

### Review Process

1. A maintainer will review your PR within 3-5 business days
2. Address any requested changes by pushing new commits
3. Once approved, a maintainer will merge your PR
4. Delete your feature branch after merge

### Merge Requirements

- At least one approving review from a maintainer
- All CI checks must pass
- No merge conflicts
- Branch is up-to-date with `development`

---

## Code Style Guidelines

### Python (Backend)

- **Style**: Follow PEP 8
- **Formatter**: Use `black` with default settings
- **Linter**: Use `ruff` for linting
- **Type hints**: Required for all function signatures
- **Docstrings**: Google-style for all public functions

```python
from typing import List, Optional

def process_query(
    query: str,
    top_k: int = 5,
    filters: Optional[dict] = None
) -> List[dict]:
    """
    Process a user query and retrieve relevant documents.

    Args:
        query: The user's query string
        top_k: Number of documents to retrieve
        filters: Optional metadata filters

    Returns:
        List of retrieved documents with metadata

    Raises:
        ValueError: If query is empty
    """
    if not query.strip():
        raise ValueError("Query cannot be empty")

    # Implementation
    pass
```

**Run formatters**:
```bash
cd backend
black app/
ruff check app/ --fix
mypy app/
```

### TypeScript/React (Frontend)

- **Style**: Follow Airbnb JavaScript Style Guide
- **Formatter**: Prettier with project config
- **Linter**: ESLint with Next.js rules
- **Components**: Use functional components with hooks
- **Types**: Define interfaces for all props

```typescript
interface QueryInputProps {
  onSubmit: (query: string) => void;
  placeholder?: string;
  disabled?: boolean;
}

export function QueryInput({
  onSubmit,
  placeholder = "Ask a question...",
  disabled = false
}: QueryInputProps) {
  const [value, setValue] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (value.trim()) {
      onSubmit(value);
      setValue("");
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      {/* Component implementation */}
    </form>
  );
}
```

**Run formatters**:
```bash
cd frontend
npm run lint
npm run format
```

### General Guidelines

- **Naming**: Use descriptive, unambiguous names
- **Functions**: Keep functions small and focused (< 50 lines)
- **Comments**: Explain "why", not "what"
- **Magic numbers**: Use named constants
- **Error handling**: Always handle errors explicitly

---

## Testing Requirements

### Backend Tests

- **Unit tests**: Test individual functions and classes
- **Integration tests**: Test component interactions
- **Coverage**: Minimum 80% for new code

```python
# tests/test_rag.py
import pytest
from app.rag import QueryExpander

def test_query_expansion():
    expander = QueryExpander(num_variations=2)
    query = "What is RAG?"
    variations = expander.expand(query)

    assert len(variations) == 3  # Original + 2 variations
    assert query in variations
    assert all(isinstance(v, str) for v in variations)
```

**Run tests**:
```bash
cd backend
pytest tests/ -v --cov=app --cov-report=html
```

### Frontend Tests

- **Component tests**: Test React components
- **Integration tests**: Test user flows
- **Snapshot tests**: For UI regression prevention

```typescript
// __tests__/QueryInput.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { QueryInput } from '../components/QueryInput';

describe('QueryInput', () => {
  it('submits query on form submission', () => {
    const handleSubmit = jest.fn();
    render(<QueryInput onSubmit={handleSubmit} />);

    const input = screen.getByPlaceholderText(/ask a question/i);
    fireEvent.change(input, { target: { value: 'test query' } });
    fireEvent.submit(input.closest('form')!);

    expect(handleSubmit).toHaveBeenCalledWith('test query');
  });
});
```

**Run tests**:
```bash
cd frontend
npm test -- --coverage
```

---

## Branch Strategy

We follow a modified Git Flow strategy:

### Branch Types

- **`main`**: Production-ready code (protected)
- **`development`**: Integration branch for features (protected)
- **`feature/*`**: New features or enhancements
- **`bugfix/*`**: Bug fixes
- **`hotfix/*`**: Urgent production fixes
- **`docs/*`**: Documentation updates

### Branch Naming

```
feature/add-graph-rag-support
bugfix/fix-chunking-overlap
hotfix/patch-security-vulnerability
docs/update-deployment-guide
```

### Workflow

1. Create feature branch from `development`
2. Develop and test locally
3. Open PR to `development`
4. After review, merge to `development`
5. Periodically, `development` is merged to `main` for releases

---

## Commit Message Convention

We follow [Conventional Commits](https://www.conventionalcommits.org/):

### Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

- **feat**: New feature
- **fix**: Bug fix
- **docs**: Documentation changes
- **style**: Code style changes (formatting)
- **refactor**: Code refactoring
- **perf**: Performance improvements
- **test**: Adding or updating tests
- **chore**: Maintenance tasks
- **ci**: CI/CD changes

### Examples

```
feat(agents): add evaluation agent for quality assessment

Implements a CrewAI agent that evaluates RAG responses using
multiple metrics including relevance, groundedness, and coherence.

Closes #123
```

```
fix(chunking): resolve overlap calculation error

The chunk overlap was being calculated incorrectly for documents
with varying paragraph lengths. Updated to use character-based
overlap instead of token-based.

Fixes #456
```

---

## Documentation

### Code Documentation

- **Python**: Use Google-style docstrings
- **TypeScript**: Use JSDoc comments
- **Inline comments**: For complex logic only

### Project Documentation

Update relevant docs when making changes:

- `README.md`: For user-facing changes
- `docs/Technical_Architecture.md`: For architectural changes
- `docs/Agent_Workflow.md`: For agent modifications
- `docs/Deployment_Guide.md`: For deployment changes

### Adding New Documentation

1. Create Markdown file in `docs/`
2. Follow existing documentation style
3. Add to documentation index if needed
4. Include code examples and diagrams

---

## Questions?

If you have questions about contributing:

- Check existing documentation in `docs/`
- Search [closed issues](https://github.com/yourusername/open-agent-rag/issues?q=is%3Aissue+is%3Aclosed)
- Ask in [GitHub Discussions](https://github.com/yourusername/open-agent-rag/discussions)
- Reach out to maintainers

---

**Thank you for contributing to OpenAgentRAG!**
