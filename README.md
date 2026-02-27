# FastAPI Initializer

[![PyPI version](https://img.shields.io/pypi/v/fastapi-initializer.svg)](https://pypi.org/project/fastapi-initializer/)
[![Python](https://img.shields.io/pypi/pyversions/fastapi-initializer.svg)](https://pypi.org/project/fastapi-initializer/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

An interactive CLI tool that scaffolds **production-ready FastAPI projects** with sensible defaults — so you can skip the boilerplate and start building right away.

![fastapi-init demo](https://raw.githubusercontent.com/DasunNethsara-04/fastapi-initializer/main/assets/demo.gif)

---

## ✨ What Does It Do?

Run a single command, answer a few prompts, and get a fully structured FastAPI project with:

- 🗂️ **Clean project layout** - `api/`, `core/`, `models/`, `schemas/`, `services/`
- 🗃️ **Database support** - SQLite, MySQL, or PostgreSQL
- 🔧 **ORM of your choice** - SQLAlchemy or SQLModel
- 🧪 **Testing setup** - pytest / pytest-asyncio with httpx, ready to go
- 🧹 **Linter config** - Black or Ruff
- 🐳 **Docker ready** - optional `Dockerfile` & `docker-compose.yml`
- ⚙️ **Environment config** - pydantic-settings with `.env` support
- 📖 **Documentation** - every folder gets a README explaining its purpose

---

## 📦 Installation

### Install from PyPI

```bash
pip install fastapi-initializer
```

Or with [uv](https://docs.astral.sh/uv/):

```bash
uv pip install fastapi-initializer
```

### Install from Source (for development)

```bash
# Clone the repository
git clone https://github.com/DasunNethsara-04/fastapi-initializer.git
cd fastapi-initializer

# Create a virtual environment and install dependencies
uv sync

# Run the CLI directly
uv run fastapi-init my-project
```

---

## 🚀 Usage

```bash
fastapi-init my-project
```

You'll be guided through interactive prompts:

```
❯ FastAPI Initializer
Creating project: my-project

❯ What kind of database do you want to use?
  > SQLite / MySQL / PostgreSQL / None

❯ Which ORM do you want to use?
  > SQLAlchemy / SQLModel / None

❯ What linter do you want to use?
  > Ruff / Black / None

❯ What testing framework do you like to use?
  > PyTest / pytest-async-io / None

❯ Do you want to create a Docker file for this project?
  > Yes / No

✔ FastAPI project 'my-project' created successfully!
```

Then get started in seconds:

```bash
cd my-project
uv sync
uv run uvicorn app.main:app --reload
```

Open **http://127.0.0.1:8000/docs** to see the interactive API docs.

---

## 📁 Generated Project Structure

The generated project follows a modular, production-style layout:

```
my-project/
├── app/
│   ├── api/
│   │   ├── v1/
│   │   │   └── users.py            # User endpoints
│   │   ├── __init__.py              # Mounts versioned routers
│   │   └── deps.py                  # Shared dependencies (e.g. auth)
│   ├── core/
│   │   ├── config.py                # App settings via pydantic-settings
│   │   └── security.py              # OAuth2 / auth utilities
│   ├── models/
│   │   └── user.py                  # ORM model (SQLAlchemy / SQLModel)
│   ├── schemas/
│   │   └── user.py                  # Pydantic request / response models
│   ├── services/
│   │   └── user_service.py          # Business logic layer
│   ├── db/
│   │   ├── base.py                  # ORM Base class
│   │   └── session.py               # Engine & get_session() dependency
│   └── main.py                      # FastAPI app entry-point
├── tests/
│   └── test_users.py                # Smoke test with httpx
├── .env                             # Environment variables
├── .gitignore
├── pyproject.toml
├── Dockerfile                       # (optional)
├── docker-compose.yml               # (optional)
└── README.md                        # Auto-generated project docs
```

> **Note:** Folders like `models/`, `db/`, `tests/`, and Docker files are only generated when you select the corresponding options.

### What Each Folder Does

| Folder | Purpose |
|--------|---------|
| `app/api/` | HTTP route definitions, versioned (`v1/`, `v2/`, …). |
| `app/core/` | App-wide settings (`Settings` class) and security helpers. |
| `app/models/` | ORM model classes mapped to database tables. |
| `app/schemas/` | Pydantic models for request validation and response serialisation. |
| `app/services/` | Business-logic layer — keeps route handlers thin and testable. |
| `app/db/` | Database engine, session factory, and `get_session()` dependency. |
| `tests/` | Automated test suite using pytest + httpx. |

---

## 🛠️ Configuration Options

| Prompt | Choices | What It Generates |
|--------|---------|-------------------|
| **Database** | SQLite, MySQL, PostgreSQL, None | `app/db/session.py` with connection URL and driver dependency |
| **ORM** | SQLAlchemy, SQLModel, None | `app/models/` with model classes and `app/db/base.py` |
| **Linter** | Ruff, Black, None | Adds the linter to `pyproject.toml` dependencies |
| **Test framework** | pytest, pytest-asyncio, None | `tests/` directory with async smoke test |
| **Docker** | Yes, No | `Dockerfile`, `docker-compose.yml`, `.dockerignore` |

---

## 🤝 Contributing

Contributions are welcome! Here's how to get started:

```bash
# 1. Fork and clone
git clone https://github.com/DasunNethsara-04/fastapi-initializer.git
cd fastapi-initializer

# 2. Install dependencies
uv sync

# 3. Make your changes, then test
uv run fastapi-init test-project

# 4. Submit a pull request
```

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).

---

## 🙏 Acknowledgements

Built with:

- [FastAPI](https://fastapi.tiangolo.com/) — the framework this tool scaffolds
- [Typer](https://typer.tiangolo.com/) — CLI framework
- [InquirerPy](https://inquirerpy.readthedocs.io/) — interactive prompts
