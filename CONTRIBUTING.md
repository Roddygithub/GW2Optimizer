# Contributing to GW2Optimizer

First off, thank you for considering contributing to GW2Optimizer! 🎉

It's people like you that make GW2Optimizer such a great tool for the Guild Wars 2 community.

---

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [How Can I Contribute?](#how-can-i-contribute)
- [Development Setup](#development-setup)
- [Pull Request Process](#pull-request-process)
- [Coding Standards](#coding-standards)
- [Testing Guidelines](#testing-guidelines)
- [Documentation](#documentation)
- [Community](#community)

---

## 📜 Code of Conduct

This project and everyone participating in it is governed by our Code of Conduct. By participating, you are expected to uphold this code. Please report unacceptable behavior to the project maintainers.

### Our Standards

- **Be respectful** and inclusive
- **Be collaborative** and constructive
- **Focus on what is best** for the community
- **Show empathy** towards other community members

---

## 🤝 How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check existing issues to avoid duplicates. When creating a bug report, include as many details as possible:

- **Use a clear and descriptive title**
- **Describe the exact steps to reproduce the problem**
- **Provide specific examples** (code snippets, screenshots)
- **Describe the behavior you observed** and what you expected
- **Include your environment details** (OS, Python version, Node version)

**Bug Report Template**:
```markdown
**Describe the bug**
A clear description of what the bug is.

**To Reproduce**
Steps to reproduce:
1. Go to '...'
2. Click on '...'
3. See error

**Expected behavior**
What you expected to happen.

**Screenshots**
If applicable, add screenshots.

**Environment:**
 - OS: [e.g. Ubuntu 22.04]
 - Python Version: [e.g. 3.11.5]
 - Node Version: [e.g. 18.17.0]
 - Browser: [e.g. Chrome 118]

**Additional context**
Any other context about the problem.
```

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion:

- **Use a clear and descriptive title**
- **Provide a detailed description** of the suggested enhancement
- **Explain why this enhancement would be useful**
- **List any alternatives** you've considered

**Enhancement Template**:
```markdown
**Is your feature request related to a problem?**
A clear description of the problem.

**Describe the solution you'd like**
A clear description of what you want to happen.

**Describe alternatives you've considered**
Any alternative solutions or features you've considered.

**Additional context**
Any other context or screenshots.
```

### Your First Code Contribution

Unsure where to begin? Look for issues labeled:
- `good first issue` - Good for newcomers
- `help wanted` - Extra attention needed
- `documentation` - Documentation improvements

---

## 🛠️ Development Setup

### Prerequisites

- **Python 3.11+**
- **Node.js 18+**
- **Git**
- **Ollama** with Mistral 7B model
- **Redis** (optional, uses disk fallback)

### Fork and Clone

1. Fork the repository on GitHub
2. Clone your fork locally:
```bash
git clone https://github.com/YOUR_USERNAME/GW2Optimizer.git
cd GW2Optimizer
```

3. Add upstream remote:
```bash
git remote add upstream https://github.com/ORIGINAL_OWNER/GW2Optimizer.git
```

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt  # Development dependencies

# Configure environment
cp .env.example .env
# Edit .env with your settings

# Run migrations
alembic upgrade head

# Start development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Configure environment
cp .env.example .env
# Edit .env with your settings

# Start development server
npm run dev
```

### Run Tests

```bash
# Backend tests
cd backend
pytest tests/ -v --cov=app --cov-report=html

# Frontend tests (when available)
cd frontend
npm test
```

---

## 🔄 Pull Request Process

### Before Submitting

1. **Create a feature branch** from `main`:
```bash
git checkout -b feature/your-feature-name
```

2. **Make your changes** following our coding standards

3. **Write or update tests** for your changes

4. **Run the test suite** and ensure all tests pass:
```bash
pytest tests/ -v
```

5. **Update documentation** if needed

6. **Commit your changes** with clear messages:
```bash
git commit -m "feat: add new AI agent for build optimization"
```

### Commit Message Format

We follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

**Examples**:
```
feat(ai): add synergy analysis agent
fix(auth): resolve token refresh issue
docs(api): update API guide with new endpoints
test(agents): add tests for optimizer agent
```

### Submitting the Pull Request

1. **Push your branch** to your fork:
```bash
git push origin feature/your-feature-name
```

2. **Open a Pull Request** on GitHub

3. **Fill out the PR template** with:
   - Description of changes
   - Related issue numbers
   - Testing performed
   - Screenshots (if UI changes)

4. **Wait for review** - maintainers will review your PR

5. **Address feedback** if requested

6. **Celebrate** when your PR is merged! 🎉

### PR Checklist

- [ ] Code follows project style guidelines
- [ ] Tests added/updated and passing
- [ ] Documentation updated
- [ ] Commit messages follow convention
- [ ] No merge conflicts
- [ ] PR description is clear and complete

---

## 💻 Coding Standards

### Python (Backend)

- **Follow PEP 8** style guide
- **Use type hints** for function signatures
- **Write docstrings** for classes and functions (Google style)
- **Keep functions small** and focused (< 50 lines)
- **Use meaningful variable names**

**Example**:
```python
from typing import List, Optional

def calculate_synergy_score(
    professions: List[str],
    game_mode: str
) -> float:
    """Calculate synergy score for team composition.
    
    Args:
        professions: List of profession names
        game_mode: Game mode (PvE, PvP, WvW)
        
    Returns:
        Synergy score between 0 and 100
        
    Raises:
        ValueError: If professions list is empty
    """
    if not professions:
        raise ValueError("Professions list cannot be empty")
    
    # Implementation here
    return score
```

### TypeScript (Frontend)

- **Use TypeScript** for all new code
- **Define interfaces** for props and state
- **Use functional components** with hooks
- **Follow React best practices**
- **Use meaningful component names**

**Example**:
```typescript
interface BuildCardProps {
  build: {
    id: string;
    name: string;
    profession: string;
    role: string;
  };
  onView?: (id: string) => void;
  onDelete?: (id: string) => void;
}

export const BuildCard: React.FC<BuildCardProps> = ({ 
  build, 
  onView, 
  onDelete 
}) => {
  // Implementation here
};
```

### General Guidelines

- **DRY** (Don't Repeat Yourself)
- **KISS** (Keep It Simple, Stupid)
- **YAGNI** (You Aren't Gonna Need It)
- **Write self-documenting code**
- **Comment complex logic**
- **Avoid premature optimization**

---

## 🧪 Testing Guidelines

### Writing Tests

- **Write tests for all new features**
- **Aim for high coverage** (target: 80%+)
- **Test edge cases** and error conditions
- **Use descriptive test names**
- **Keep tests independent**

### Test Structure

```python
import pytest
from app.agents.recommender_agent import RecommenderAgent

class TestRecommenderAgent:
    """Tests for RecommenderAgent."""
    
    @pytest.fixture
    def agent(self):
        """Create agent instance for testing."""
        return RecommenderAgent()
    
    def test_recommend_build_success(self, agent):
        """Test successful build recommendation."""
        # Arrange
        inputs = {
            "profession": "Guardian",
            "role": "Support",
            "game_mode": "WvW"
        }
        
        # Act
        result = agent.execute(inputs)
        
        # Assert
        assert result is not None
        assert "build_name" in result
        assert result["profession"] == "Guardian"
    
    def test_recommend_build_invalid_profession(self, agent):
        """Test build recommendation with invalid profession."""
        # Arrange
        inputs = {
            "profession": "InvalidClass",
            "role": "Support",
            "game_mode": "WvW"
        }
        
        # Act & Assert
        with pytest.raises(ValueError, match="Invalid profession"):
            agent.execute(inputs)
```

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_agents.py -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html

# Run specific test
pytest tests/test_agents.py::TestRecommenderAgent::test_recommend_build_success -v
```

---

## 📚 Documentation

### Code Documentation

- **Write docstrings** for all public functions/classes
- **Use type hints** in Python
- **Comment complex algorithms**
- **Keep comments up-to-date**

### Project Documentation

When adding features, update:
- **README.md** - If it affects setup or usage
- **API_GUIDE.md** - If adding/changing API endpoints
- **ARCHITECTURE.md** - If changing system design
- **CHANGELOG.md** - Add entry for your changes

### Documentation Style

- Use **clear, concise language**
- Include **code examples**
- Add **screenshots** for UI changes
- Use **proper Markdown formatting**

---

## 👥 Community

### Getting Help

- **GitHub Discussions** - Ask questions and discuss ideas
- **GitHub Issues** - Report bugs and request features
- **Discord** (if available) - Real-time chat with community

### Staying Updated

- **Watch the repository** for notifications
- **Follow the project** on GitHub
- **Read the CHANGELOG** for updates

---

## 🎯 Development Workflow

### Typical Workflow

1. **Check issues** for something to work on
2. **Comment on the issue** to claim it
3. **Create a branch** for your work
4. **Make changes** and commit regularly
5. **Write tests** for your changes
6. **Update documentation** as needed
7. **Run tests** and ensure they pass
8. **Push to your fork** and create PR
9. **Respond to feedback** from reviewers
10. **Celebrate** when merged! 🎉

### Branch Naming

- `feature/description` - New features
- `fix/description` - Bug fixes
- `docs/description` - Documentation
- `refactor/description` - Code refactoring
- `test/description` - Test additions/changes

---

## 🏆 Recognition

Contributors will be:
- **Listed in CONTRIBUTORS.md**
- **Mentioned in release notes**
- **Thanked in the community**

---

## ❓ Questions?

Don't hesitate to ask! We're here to help:
- Open a **GitHub Discussion**
- Comment on an **existing issue**
- Reach out to **maintainers**

---

## 📄 License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

**Thank you for contributing to GW2Optimizer! 🎮⚔️🛡️**

Together, we're building the best build optimizer for Guild Wars 2!
