# Contributing to AI-Powered Cribl Log Analysis Platform

First off, thank you for considering contributing to this project! It's people like you that make this tool better for everyone in the cybersecurity community.

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [How Can I Contribute?](#how-can-i-contribute)
- [Development Guidelines](#development-guidelines)
- [Pull Request Process](#pull-request-process)
- [Issue Guidelines](#issue-guidelines)
- [Community](#community)

## 📜 Code of Conduct

This project and everyone participating in it is governed by our commitment to creating a welcoming and inclusive environment. By participating, you are expected to uphold professional standards and treat all contributors with respect.

### Our Standards

**Examples of behavior that contributes to a positive environment:**
- Using welcoming and inclusive language
- Being respectful of differing viewpoints and experiences
- Gracefully accepting constructive criticism
- Focusing on what is best for the community
- Showing empathy towards other community members

**Examples of unacceptable behavior:**
- The use of sexualized language or imagery and unwelcome sexual attention or advances
- Trolling, insulting/derogatory comments, and personal or political attacks
- Public or private harassment
- Publishing others' private information without explicit permission
- Other conduct which could reasonably be considered inappropriate in a professional setting

## 🚀 Getting Started

### Prerequisites

Before you begin contributing, make sure you have:

- Python 3.8 or higher installed
- Git installed and configured
- A Google Gemini AI API key for testing
- Basic understanding of Flask, Streamlit, and AI/ML concepts
- Familiarity with cybersecurity and log analysis concepts

### Development Setup

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/your-username/Cribl_Log_API.git
   cd Cribl_Log_API
   ```

3. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

4. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt  # If available
   ```

5. **Set up environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

6. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

## 🤝 How Can I Contribute?

### 🐛 Reporting Bugs

**Before creating bug reports**, please check the issue tracker to avoid duplicates.

When you create a bug report, please include:

- **Use a clear and descriptive title**
- **Describe the exact steps to reproduce the problem**
- **Provide specific examples** (log outputs, error messages, etc.)
- **Describe the behavior you observed** and what you expected
- **Include screenshots** if they help explain the problem
- **Environment details** (OS, Python version, dependency versions)

Use this template for bug reports:

```markdown
**Bug Description**
A clear and concise description of what the bug is.

**To Reproduce**
Steps to reproduce the behavior:
1. Go to '...'
2. Click on '....'
3. Scroll down to '....'
4. See error

**Expected Behavior**
A clear description of what you expected to happen.

**Screenshots**
If applicable, add screenshots to help explain your problem.

**Environment:**
- OS: [e.g. iOS]
- Python Version: [e.g. 3.9.7]
- Flask Version: [e.g. 3.1.1]
- Streamlit Version: [e.g. 1.28.0]

**Additional Context**
Add any other context about the problem here.
```

### ✨ Suggesting Enhancements

Enhancement suggestions are welcome! Please provide:

- **Use a clear and descriptive title**
- **Provide a step-by-step description** of the suggested enhancement
- **Provide specific examples** to demonstrate the feature
- **Describe the current behavior** and explain which behavior you expected
- **Explain why this enhancement would be useful**

### 🔧 Contributing Code

#### Types of Contributions Welcomed

- **Bug fixes**
- **New features** (AI analysis improvements, UI enhancements, etc.)
- **Performance improvements**
- **Documentation improvements**
- **Test coverage improvements**
- **Security enhancements**
- **Cribl Stream integration improvements**

#### Areas for Contribution

1. **AI Analysis Engine**
   - Improve prompt engineering
   - Add new analysis models
   - Enhance threat detection algorithms
   - Optimize response parsing

2. **User Interface**
   - Flask dashboard enhancements
   - Streamlit chatbot improvements
   - Mobile responsiveness
   - Accessibility improvements

3. **Integration & APIs**
   - Additional webhook endpoints
   - Database integration
   - External service integrations
   - API improvements

4. **Security & Performance**
   - Security hardening
   - Performance optimizations
   - Error handling improvements
   - Logging enhancements

## 📝 Development Guidelines

### Code Style

We follow Python best practices and PEP 8 guidelines:

- **Use Black** for code formatting: `black .`
- **Use isort** for import sorting: `isort .`
- **Use flake8** for linting: `flake8 .`
- **Maximum line length**: 88 characters (Black default)
- **Use type hints** where appropriate
- **Write comprehensive docstrings** for all functions and classes

### Code Quality Standards

- **Write clean, readable code** with meaningful variable names
- **Add comprehensive docstrings** for all public functions
- **Include error handling** for all external API calls
- **Add logging** for important operations and errors
- **Follow security best practices** (input validation, secure defaults)
- **Write unit tests** for new functionality
- **Update documentation** for API changes

### Git Commit Guidelines

We follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only changes
- `style`: Changes that do not affect code meaning (white-space, formatting, etc.)
- `refactor`: Code change that neither fixes a bug nor adds a feature
- `perf`: Performance improvement
- `test`: Adding missing tests or correcting existing tests
- `build`: Changes that affect the build system or external dependencies
- `ci`: Changes to CI configuration files and scripts
- `chore`: Other changes that don't modify src or test files

**Examples:**
```
feat(api): add new webhook endpoint for real-time analysis
fix(ui): resolve mobile responsive layout issues
docs(readme): add deployment instructions
refactor(ai): optimize prompt engineering for better accuracy
```

### Testing

- **Write tests** for all new functionality
- **Ensure tests pass** before submitting PR
- **Include integration tests** for API endpoints
- **Test error handling** scenarios
- **Test with different data formats**

Run tests with:
```bash
python -m pytest tests/ -v
```

### Documentation

- **Update README.md** if adding new features
- **Add docstrings** to all new functions and classes
- **Update API documentation** for endpoint changes
- **Include usage examples** for new features
- **Update configuration documentation** if needed

## 🔄 Pull Request Process

### Before Submitting

1. **Ensure your code follows** the style guidelines
2. **Run all tests** and ensure they pass
3. **Update documentation** as needed
4. **Add or update tests** for your changes
5. **Check for security implications**
6. **Test with real Cribl Stream data** if possible

### PR Submission

1. **Create a pull request** with a clear title and description
2. **Reference any related issues** (e.g., "Closes #123")
3. **Provide a comprehensive description** of changes
4. **Include screenshots** for UI changes
5. **List any breaking changes**
6. **Update the CHANGELOG.md** if necessary

### PR Template

```markdown
## Description
Brief description of what this PR does.

## Type of Change
- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update

## Testing
- [ ] Tests pass locally
- [ ] Added tests for new functionality
- [ ] Tested with real data
- [ ] No security vulnerabilities introduced

## Checklist
- [ ] My code follows the style guidelines
- [ ] I have performed a self-review of my code
- [ ] I have commented my code, particularly in hard-to-understand areas
- [ ] I have made corresponding changes to the documentation
- [ ] My changes generate no new warnings
- [ ] New and existing unit tests pass locally
```

### Review Process

1. **Automated checks** must pass (CI/CD pipeline)
2. **At least one reviewer** must approve the PR
3. **Address reviewer feedback** promptly
4. **Rebase and squash commits** if requested
5. **Final approval** and merge by maintainers

## 📝 Issue Guidelines

### Creating Issues

- **Search existing issues** before creating new ones
- **Use appropriate labels** (bug, enhancement, question, etc.)
- **Provide clear, descriptive titles**
- **Include all relevant information** using provided templates
- **Be respectful** and constructive in discussions

### Issue Labels

- `bug`: Something isn't working
- `enhancement`: New feature or request
- `documentation`: Improvements or additions to documentation
- `good first issue`: Good for newcomers
- `help wanted`: Extra attention is needed
- `question`: Further information is requested
- `security`: Security-related issues
- `performance`: Performance improvements

## 🌟 Recognition

Contributors will be recognized in:

- **README.md** contributors section
- **CHANGELOG.md** for significant contributions
- **GitHub releases** notes
- **Project documentation** where appropriate

## 💬 Community

### Getting Help

- **GitHub Discussions**: For questions and general discussion
- **GitHub Issues**: For bugs and feature requests
- **Email**: For private/security-related inquiries

### Communication Guidelines

- **Be respectful** and professional
- **Stay on topic** in discussions
- **Provide constructive feedback**
- **Help newcomers** get started
- **Share knowledge** and best practices

## 📚 Additional Resources

### Documentation
- [Flask Documentation](https://flask.palletsprojects.com/)
- [Streamlit Documentation](https://docs.streamlit.io/)
- [Google Gemini AI Documentation](https://ai.google.dev/docs)
- [Cribl Stream Documentation](https://docs.cribl.io/stream/)

### Security Resources
- [OWASP Security Guidelines](https://owasp.org/)
- [Python Security Best Practices](https://python-security.readthedocs.io/)
- [Insider Threat Mitigation](https://www.cisa.gov/insider-threat-mitigation)

### Development Tools
- [Black Code Formatter](https://black.readthedocs.io/)
- [isort Import Sorter](https://pycqa.github.io/isort/)
- [flake8 Linter](https://flake8.pycqa.org/)
- [pytest Testing Framework](https://pytest.org/)

---

Thank you for contributing to the AI-Powered Cribl Log Analysis Platform! Your efforts help make cybersecurity better for everyone. 🛡️✨
