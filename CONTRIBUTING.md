# Contributing to Digital Overload AI

Thank you for your interest in contributing! Here's how to get started.

---

## Getting Started

1. **Fork** the repository on GitHub
2. **Clone** your fork locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/digital-overload-ai.git
   cd digital-overload-ai
   ```
3. **Create a branch** for your change:
   ```bash
   git checkout -b feature/your-feature-name
   ```

---

## Development Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Add your GROQ_API_KEY to .env
```

---

## Before Submitting

- Run all tests and ensure they pass:
  ```bash
  pytest tests/ -v
  ```
- Add tests for any new scoring logic or recommendation rules
- Follow existing code style: type hints + docstrings on all public functions
- Do not commit `.env` or `.streamlit/secrets.toml`

---

## Opening a Pull Request

1. Push your branch to your fork
2. Open a PR against the `main` branch of this repo
3. Describe what you changed and why
4. Link any relevant issues

---

## Questions?

Open a GitHub Issue and describe what you're trying to do.
