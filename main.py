from __future__ import annotations

import sys
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from textwrap import dedent


import typer
from InquirerPy import inquirer


class DatabaseChoice(str, Enum):
    NONE = "none"
    SQLITE = "sqlite"
    MYSQL = "mysql"
    POSTGRESQL = "postgresql"


class ORMChoice(str, Enum):
    NONE = "none"
    SQLALCHEMY = "sqlalchemy"
    SQLMODEL = "sqlmodel"


class LinterChoice(str, Enum):
    NONE = "none"
    BLACK = "black"
    RUFF = "ruff"


class TestChoice(str, Enum):
    NONE = "none"
    PYTEST = "pytest"
    PYTEST_ASYNCIO = "pytest-asyncio"


@dataclass
class ProjectConfig:
    name: str
    database: DatabaseChoice
    orm: ORMChoice
    linter: LinterChoice
    test_framework: TestChoice
    docker: bool


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def render_app_main(config: ProjectConfig) -> str:
    return dedent(
        f"""
        from fastapi import FastAPI

        from app.api import api_router


        app = FastAPI(title="{config.name}")
        app.include_router(api_router)


        @app.get("/health")
        async def health_check():
            return {{"status": "ok"}}
        """
    ).lstrip()


def render_app_api_init() -> str:
    return dedent(
        """
        from fastapi import APIRouter

        from .v1 import users

        api_router = APIRouter()
        api_router.include_router(users.router)
        """
    ).lstrip()


def render_app_api_deps() -> str:
    return dedent(
        """
        from typing import Annotated

        from fastapi import Depends


        def get_current_user():
            return {"id": 1, "email": "user@example.com"}


        CurrentUser = Annotated[dict, Depends(get_current_user)]
        """
    ).lstrip()


def render_app_api_v1_users() -> str:
    return dedent(
        """
        from fastapi import APIRouter

        from app.schemas.user import User
        from app.services.user_service import get_dummy_users


        router = APIRouter(prefix="/users", tags=["users"])


        @router.get("/", response_model=list[User])
        async def list_users():
            return get_dummy_users()
        """
    ).lstrip()


def render_core_config() -> str:
    return dedent(
        """
        from pydantic_settings import BaseSettings


        class Settings(BaseSettings):
            app_name: str = "FastAPI Initializer App"
            debug: bool = True

            class Config:
                env_file = ".env"


        settings = Settings()
        """
    ).lstrip()


def render_core_security() -> str:
    return dedent(
        """
        from fastapi.security import OAuth2PasswordBearer


        oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
        """
    ).lstrip()


def render_models_user(orm: ORMChoice) -> str:
    if orm == ORMChoice.SQLMODEL:
        return dedent(
            """
            from sqlmodel import Field, SQLModel


            class User(SQLModel, table=True):
                id: int | None = Field(default=None, primary_key=True)
                email: str
                is_active: bool = True
            """
        ).lstrip()
    else:
        return dedent(
            """
            from sqlalchemy import Boolean, Column, Integer, String

            from app.db.base import Base


            class User(Base):
                __tablename__ = "users"

                id = Column(Integer, primary_key=True, index=True)
                email = Column(String, unique=True, index=True, nullable=False)
                is_active = Column(Boolean, default=True)
            """
        ).lstrip()


def render_schemas_user() -> str:
    return dedent(
        """
        from pydantic import BaseModel


        class User(BaseModel):
            id: int
            email: str
            is_active: bool = True
        """
    ).lstrip()


def render_services_user_service() -> str:
    return dedent(
        """
        from app.schemas.user import User


        def get_dummy_users() -> list[User]:
            return [
                User(id=1, email="user1@example.com", is_active=True),
                User(id=2, email="user2@example.com", is_active=False),
            ]
        """
    ).lstrip()


def render_db_session(database: DatabaseChoice, orm: ORMChoice) -> str:
    if database == DatabaseChoice.SQLITE:
        url = "sqlite:///./app.db"
    elif database == DatabaseChoice.MYSQL:
        url = "mysql+pymysql://user:password@localhost:3306/app"
    elif database == DatabaseChoice.POSTGRESQL:
        url = "postgresql+psycopg2://user:password@localhost:5432/app"
    else:
        url = "sqlite:///./app.db"

    if orm == ORMChoice.SQLMODEL:
        return dedent(
            f"""
            import os
            from collections.abc import Generator

            from sqlmodel import Session, create_engine

            DATABASE_URL = os.getenv("DATABASE_URL", "{url}")

            engine = create_engine(DATABASE_URL, echo=False)


            def get_session() -> Generator[Session, None, None]:
                with Session(engine) as session:
                    yield session
            """
        ).lstrip()
    else:
        return dedent(
            f"""
            import os
            from collections.abc import Generator

            from sqlalchemy import create_engine
            from sqlalchemy.orm import Session, sessionmaker

            DATABASE_URL = os.getenv("DATABASE_URL", "{url}")

            engine = create_engine(DATABASE_URL, echo=False)
            SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


            def get_session() -> Generator[Session, None, None]:
                db = SessionLocal()
                try:
                    yield db
                finally:
                    db.close()
            """
        ).lstrip()


def render_db_base(orm: ORMChoice) -> str:
    if orm == ORMChoice.SQLMODEL:
        return dedent(
            """
            from sqlmodel import SQLModel


            Base = SQLModel
            """
        ).lstrip()
    else:
        return dedent(
            """
            from sqlalchemy.orm import declarative_base


            Base = declarative_base()
            """
        ).lstrip()


def render_tests(test_framework: TestChoice) -> str:
    if test_framework in {TestChoice.PYTEST, TestChoice.PYTEST_ASYNCIO}:
        return dedent(
            """
            import pytest
            from httpx import AsyncClient

            from app.main import app


            @pytest.mark.asyncio
            async def test_health():
                async with AsyncClient(app=app, base_url="http://test") as client:
                    response = await client.get("/health")
                assert response.status_code == 200
                assert response.json()["status"] == "ok"
            """
        ).lstrip()
    return ""


def render_env(config: ProjectConfig) -> str:
    return dedent(
        f"""
        APP_NAME="{config.name}"
        DEBUG=true
        """
    ).lstrip()


def render_dockerfile() -> str:
    return dedent(
        """
        FROM python:3.11-slim

        WORKDIR /app

        COPY pyproject.toml uv.lock ./
        RUN pip install uv && uv sync

        COPY . .

        CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
        """
    ).lstrip()


def render_docker_compose() -> str:
    return dedent(
        """
        version: "3.9"

        services:
          api:
            build: .
            ports:
              - "8000:8000"
            env_file:
              - .env
        """
    ).lstrip()


def render_dockerignore() -> str:
    return dedent(
        """
        __pycache__
        .venv
        .env
        uv.lock
        """
    ).lstrip()


def render_gitignore() -> str:
    return dedent(
        """
        # Python
        __pycache__/
        *.py[oc]
        *.egg-info/
        dist/
        build/

        # Virtual environments
        .venv/

        # Environment variables
        .env

        # IDE
        .vscode/
        .idea/
        """
    ).lstrip()


def render_pyproject(config: ProjectConfig) -> str:
    deps: list[str] = ["fastapi", "uvicorn[standard]", "pydantic", "pydantic-settings", "python-dotenv"]

    if config.orm in {ORMChoice.SQLALCHEMY, ORMChoice.SQLMODEL}:
        deps.append("sqlalchemy")
    if config.orm == ORMChoice.SQLMODEL:
        deps.append("sqlmodel")

    if config.test_framework == TestChoice.PYTEST:
        deps.extend(["pytest", "httpx"])
    elif config.test_framework == TestChoice.PYTEST_ASYNCIO:
        deps.extend(["pytest", "pytest-asyncio", "httpx"])

    if config.linter == LinterChoice.BLACK:
        deps.append("black")
    elif config.linter == LinterChoice.RUFF:
        deps.append("ruff")

    # Database drivers based on URL scheme
    if config.database == DatabaseChoice.MYSQL:
        deps.append("pymysql")
    elif config.database == DatabaseChoice.POSTGRESQL:
        deps.append("psycopg2-binary")

    deps_lines = "\n".join(f'    "{dep}",' for dep in deps)

    return (
        "[project]\n"
        f'name = "{config.name}"\n'
        'version = "0.1.0"\n'
        'description = "FastAPI project generated by FastAPI Initializer"\n'
        'readme = "README.md"\n'
        'requires-python = ">=3.10"\n'
        "dependencies = [\n"
        f"{deps_lines}\n"
        "]\n"
    )


def render_readme(config: ProjectConfig) -> str:
    # --- build the folder-tree block dynamically ---------------------------
    tree_lines = [
        f"{config.name}/",
        "├── app/",
        "│   ├── api/",
        "│   │   ├── v1/",
        "│   │   │   └── users.py        # User endpoints",
        "│   │   ├── __init__.py          # Mounts versioned routers",
        "│   │   └── deps.py              # Shared dependencies",
        "│   ├── core/",
        "│   │   ├── config.py            # App settings (pydantic-settings)",
        "│   │   └── security.py          # OAuth2 / auth utilities",
    ]

    if config.orm != ORMChoice.NONE:
        tree_lines += [
            "│   ├── models/",
            "│   │   └── user.py            # ORM model",
        ]

    if config.database != DatabaseChoice.NONE or config.orm != ORMChoice.NONE:
        db_files = ["│   ├── db/", "│   │   ├── base.py             # ORM Base class"]
        if config.database != DatabaseChoice.NONE:
            db_files.append("│   │   └── session.py          # Engine & get_session()")
        tree_lines += db_files

    tree_lines += [
        "│   ├── schemas/",
        "│   │   └── user.py            # Pydantic request / response models",
        "│   ├── services/",
        "│   │   └── user_service.py     # Business logic",
        "│   └── main.py                 # FastAPI app entry-point",
    ]

    if config.test_framework != TestChoice.NONE:
        tree_lines += [
            "├── tests/",
            "│   └── test_users.py          # Smoke tests",
        ]

    if config.docker:
        tree_lines += [
            "├── Dockerfile",
            "├── docker-compose.yml",
            "├── .dockerignore",
        ]

    tree_lines += [
        "├── .env                         # Environment variables",
        "├── .gitignore",
        "├── pyproject.toml",
        "└── README.md",
    ]

    tree_block = "\n".join(tree_lines)

    # --- optional sections -------------------------------------------------
    db_section = ""
    if config.database != DatabaseChoice.NONE:
        db_label = config.database.value.title()
        db_section = dedent(f"""
            ## Database

            This project is pre-configured for **{db_label}**.

            - Connection URL is set via the `DATABASE_URL` environment variable (see `.env`).
            - A `get_session()` dependency is provided in `app/db/session.py` — inject it into any route with `Depends(get_session)`.
        """)

    orm_section = ""
    if config.orm != ORMChoice.NONE:
        orm_label = "SQLModel" if config.orm == ORMChoice.SQLMODEL else "SQLAlchemy"
        orm_section = dedent(f"""
            ## ORM

            Models use **{orm_label}** and inherit from the shared `Base` in `app/db/base.py`.

            To add a new model:
            1. Create a file in `app/models/` (e.g. `item.py`).
            2. Import `Base` from `app.db.base`.
            3. Import the model in `app/models/__init__.py` so migrations can discover it.
        """)

    docker_section = ""
    if config.docker:
        docker_section = dedent("""
            ## Docker

            ```bash
            # Build and start
            docker compose up --build

            # Or run directly
            docker build -t app .
            docker run -p 8000:8000 --env-file .env app
            ```
        """)

    test_section = ""
    if config.test_framework != TestChoice.NONE:
        test_section = dedent("""
            ## Testing

            ```bash
            uv run pytest
            ```

            Tests live in the `tests/` directory. Every async test needs the `@pytest.mark.asyncio` decorator.
        """)

    linter_section = ""
    if config.linter == LinterChoice.RUFF:
        linter_section = dedent("""
            ## Linting & Formatting

            ```bash
            uv run ruff check .     # Lint
            uv run ruff format .    # Format
            ```
        """)
    elif config.linter == LinterChoice.BLACK:
        linter_section = dedent("""
            ## Formatting

            ```bash
            uv run black .
            ```
        """)

    # --- env vars table ----------------------------------------------------
    env_rows = [
        "| Variable | Default | Description |",
        "|----------|---------|-------------|",
        f'| `APP_NAME` | `"{config.name}"` | Display name used in OpenAPI docs. |',
        "| `DEBUG` | `true` | Enable debug mode. |",
    ]
    if config.database != DatabaseChoice.NONE:
        env_rows.append("| `DATABASE_URL` | *(see .env)* | Database connection string. |")
    env_table = "\n".join(env_rows)

    # --- tech stack --------------------------------------------------------
    stack_items = ["- **FastAPI** — async web framework", "- **Pydantic** — data validation"]
    if config.orm == ORMChoice.SQLMODEL:
        stack_items.append("- **SQLModel** — ORM (SQLAlchemy + Pydantic)")
    elif config.orm == ORMChoice.SQLALCHEMY:
        stack_items.append("- **SQLAlchemy** — ORM")
    if config.database != DatabaseChoice.NONE:
        stack_items.append(f"- **{config.database.value.title()}** — database")
    if config.test_framework != TestChoice.NONE:
        stack_items.append("- **pytest** + **httpx** — testing")
    if config.linter == LinterChoice.RUFF:
        stack_items.append("- **Ruff** — linter & formatter")
    elif config.linter == LinterChoice.BLACK:
        stack_items.append("- **Black** — code formatter")
    if config.docker:
        stack_items.append("- **Docker** — containerisation")
    tech_stack = "\n".join(stack_items)

    # --- assemble ----------------------------------------------------------
    return dedent(
        f"""\
# {config.name}

Generated with **FastAPI Initializer**.

## Getting Started

```bash
# Install dependencies
uv sync

# Run the development server
uv run uvicorn app.main:app --reload
```

Then open **http://127.0.0.1:8000/docs** to explore the interactive API documentation.

## Project Structure

```
{tree_block}
```

| Folder | Purpose |
|--------|---------|
| `app/api/` | HTTP route definitions, organised by API version. |
| `app/core/` | App-wide configuration (`Settings`) and security utilities. |
| `app/schemas/` | Pydantic models for request / response validation. |
| `app/services/` | Business-logic layer — keeps route handlers thin. |
{"| `app/models/` | ORM model classes mapped to database tables. |" if config.orm != ORMChoice.NONE else ""}\
{"| `app/db/` | Database engine, session management, and ORM base class. |" if (config.database != DatabaseChoice.NONE or config.orm != ORMChoice.NONE) else ""}\
{"| `tests/` | Automated test suite. |" if config.test_framework != TestChoice.NONE else ""}
{db_section}\
{orm_section}\
{docker_section}\
{test_section}\
{linter_section}\
## Environment Variables

{env_table}

## Tech Stack

{tech_stack}
"""
    )


def render_readme_app() -> str:
    return dedent(
        """
        # `app/` — Application Package

        This is the root Python package for the FastAPI application.

        ## Files

        | File | Description |
        |------|-------------|
        | `__init__.py` | Makes `app` a Python package. |
        | `main.py` | Application entry-point — creates the `FastAPI` instance, mounts routers, and defines the `/health` endpoint. |

        ## Sub-packages

        | Folder | Description |
        |--------|-------------|
        | `api/` | HTTP route definitions organised by version. |
        | `core/` | App-wide configuration and security utilities. |
        | `models/` | ORM / database model classes *(present only when an ORM is selected)*. |
        | `schemas/` | Pydantic models used for request / response validation. |
        | `services/` | Business-logic layer — keeps routes thin. |
        | `db/` | Database engine, session, and base model setup *(present only when a database or ORM is selected)*. |
        """
    ).lstrip()


def render_readme_api() -> str:
    return dedent(
        """
        # `app/api/` — API Routes

        All HTTP endpoint definitions live here, organised by API version.

        ## Files

        | File | Description |
        |------|-------------|
        | `__init__.py` | Creates the top-level `api_router` and includes versioned sub-routers. |
        | `deps.py` | Shared **dependencies** — e.g. `get_current_user` — injected into route handlers via `Depends()`. |

        ## Sub-packages

        | Folder | Description |
        |--------|-------------|
        | `v1/` | Version 1 endpoints. Add `v2/`, `v3/`, etc. as needed. |
        """
    ).lstrip()


def render_readme_api_v1() -> str:
    return dedent(
        """
        # `app/api/v1/` — Version 1 Endpoints

        Each file in this folder is a **router module** for a single resource.

        ## Files

        | File | Description |
        |------|-------------|
        | `__init__.py` | Package marker. |
        | `users.py` | `GET /users/` — returns a list of users. Add more CRUD routes here. |

        ## Adding a new resource

        1. Create a new file, e.g. `items.py`, with its own `router = APIRouter(...)`.
        2. Import and include it in `app/api/__init__.py`:
           ```python
           from .v1 import items
           api_router.include_router(items.router)
           ```
        """
    ).lstrip()


def render_readme_core() -> str:
    return dedent(
        """
        # `app/core/` — Configuration & Security

        App-wide settings and security utilities that are used across the entire application.

        ## Files

        | File | Description |
        |------|-------------|
        | `__init__.py` | Package marker. |
        | `config.py` | `Settings` class (powered by **pydantic-settings**). Reads values from environment variables and `.env`. Import as `from app.core.config import settings`. |
        | `security.py` | OAuth2 scheme definition and any future auth helpers (JWT encoding, password hashing, etc.). |
        """
    ).lstrip()


def render_readme_models() -> str:
    return dedent(
        """
        # `app/models/` — Database Models

        ORM model classes that map directly to database tables.

        ## Files

        | File | Description |
        |------|-------------|
        | `__init__.py` | Package marker. Import all models here so Alembic can discover them. |
        | `user.py` | `User` model with `id`, `email`, and `is_active` columns. |

        ## Notes

        - Models import `Base` from `app.db.base` — make sure every new model does the same.
        - To add a new model, create a file (e.g. `item.py`), define the class, then import it in `__init__.py`.
        """
    ).lstrip()


def render_readme_schemas() -> str:
    return dedent(
        """
        # `app/schemas/` — Pydantic Schemas

        Data-validation and serialisation models used in request bodies and responses.

        ## Files

        | File | Description |
        |------|-------------|
        | `__init__.py` | Package marker. |
        | `user.py` | `User` schema with `id`, `email`, and `is_active` fields. |

        ## Conventions

        - **One file per resource** (e.g. `user.py`, `item.py`).
        - Use `Create`, `Update`, and `Read` suffixes when you need separate shapes for different operations, e.g. `UserCreate`, `UserRead`.
        """
    ).lstrip()


def render_readme_services() -> str:
    return dedent(
        """
        # `app/services/` — Business Logic

        The service layer keeps route handlers thin by encapsulating business rules and data access.

        ## Files

        | File | Description |
        |------|-------------|
        | `__init__.py` | Package marker. |
        | `user_service.py` | `get_dummy_users()` — returns sample user data. Replace with real DB queries. |

        ## Guidelines

        - Each service should focus on a **single resource** or **domain concept**.
        - Services receive a database session (from `app.db.session.get_session`) and return schema objects.
        """
    ).lstrip()


def render_readme_db() -> str:
    return dedent(
        """
        # `app/db/` — Database Configuration

        Everything related to the database connection, session management, and ORM base class.

        ## Files

        | File | Description |
        |------|-------------|
        | `__init__.py` | Package marker. |
        | `base.py` | Declares the ORM `Base` class that all models inherit from. |
        | `session.py` | Creates the database `engine`, and exposes `get_session()` — a FastAPI dependency that yields a database session. |

        ## Usage

        Inject a session into any route:
        ```python
        from fastapi import Depends
        from app.db.session import get_session

        @router.get("/")
        def list_items(session = Depends(get_session)):
            ...
        ```
        """
    ).lstrip()


def render_readme_tests() -> str:
    return dedent(
        """
        # `tests/` — Test Suite

        Automated tests for the application, using **pytest** and **httpx**.

        ## Files

        | File | Description |
        |------|-------------|
        | `__init__.py` | Package marker. |
        | `test_users.py` | Smoke test — calls `GET /health` and asserts a 200 response. |

        ## Running tests

        ```bash
        uv run pytest
        ```

        ## Tips

        - Name test files `test_<module>.py` so pytest discovers them automatically.
        - Use `@pytest.mark.asyncio` on every `async def test_...` function.
        - Add a `conftest.py` for shared fixtures (app client, test DB, etc.).
        """
    ).lstrip()


def scaffold_project(config: ProjectConfig, target_dir: Path) -> None:
    if target_dir.exists() and any(target_dir.iterdir()):
        raise SystemExit(f"Target directory '{target_dir}' already exists and is not empty.")

    # Core app structure
    write_file(target_dir / "app" / "__init__.py", "")
    write_file(target_dir / "app" / "main.py", render_app_main(config))
    write_file(target_dir / "app" / "README.md", render_readme_app())

    # API
    write_file(target_dir / "app" / "api" / "__init__.py", render_app_api_init())
    write_file(target_dir / "app" / "api" / "deps.py", render_app_api_deps())
    write_file(target_dir / "app" / "api" / "README.md", render_readme_api())
    write_file(target_dir / "app" / "api" / "v1" / "__init__.py", "")
    write_file(target_dir / "app" / "api" / "v1" / "users.py", render_app_api_v1_users())
    write_file(target_dir / "app" / "api" / "v1" / "README.md", render_readme_api_v1())

    # Core config & security
    write_file(target_dir / "app" / "core" / "__init__.py", "")
    write_file(target_dir / "app" / "core" / "config.py", render_core_config())
    write_file(target_dir / "app" / "core" / "security.py", render_core_security())
    write_file(target_dir / "app" / "core" / "README.md", render_readme_core())

    # Models
    if config.orm != ORMChoice.NONE:
        write_file(target_dir / "app" / "models" / "__init__.py", "")
        write_file(target_dir / "app" / "models" / "user.py", render_models_user(config.orm))
        write_file(target_dir / "app" / "models" / "README.md", render_readme_models())

    # Schemas / Services
    write_file(target_dir / "app" / "schemas" / "__init__.py", "")
    write_file(target_dir / "app" / "schemas" / "user.py", render_schemas_user())
    write_file(target_dir / "app" / "schemas" / "README.md", render_readme_schemas())
    write_file(target_dir / "app" / "services" / "__init__.py", "")
    write_file(target_dir / "app" / "services" / "user_service.py", render_services_user_service())
    write_file(target_dir / "app" / "services" / "README.md", render_readme_services())

    # DB
    if config.database != DatabaseChoice.NONE or config.orm != ORMChoice.NONE:
        write_file(target_dir / "app" / "db" / "__init__.py", "")
        write_file(target_dir / "app" / "db" / "base.py", render_db_base(config.orm))
        write_file(target_dir / "app" / "db" / "README.md", render_readme_db())
    if config.database != DatabaseChoice.NONE:
        write_file(target_dir / "app" / "db" / "session.py", render_db_session(config.database, config.orm))

    # Tests
    if config.test_framework != TestChoice.NONE:
        write_file(target_dir / "tests" / "__init__.py", "")
        write_file(target_dir / "tests" / "test_users.py", render_tests(config.test_framework))
        write_file(target_dir / "tests" / "README.md", render_readme_tests())

    # Root-level files
    write_file(target_dir / ".env", render_env(config))
    write_file(target_dir / ".gitignore", render_gitignore())
    if config.docker:
        write_file(target_dir / ".dockerignore", render_dockerignore())
        write_file(target_dir / "Dockerfile", render_dockerfile())
        write_file(target_dir / "docker-compose.yml", render_docker_compose())
    write_file(target_dir / "pyproject.toml", render_pyproject(config))
    write_file(target_dir / "README.md", render_readme(config))


def _choice_prompt(title: str, options: list[str], default_index: int = 0) -> str:
    """Arrow-key selection using InquirerPy."""
    return inquirer.select(
        message=title,
        choices=options,
        default=options[default_index],
        pointer=">",
        qmark="❯",
        amark="✔",
    ).execute()


def main(
    name: str = typer.Argument(..., help="Project name / folder name"),
) -> None:
    typer.echo(typer.style("FastAPI Initializer", fg=typer.colors.CYAN, bold=True))
    # Validate project name
    sanitised = name.replace("-", "_")
    if not sanitised.isidentifier():
        raise SystemExit(
            f"Invalid project name '{name}'. "
            "Use only letters, digits, hyphens, and underscores, and start with a letter."
        )

    typer.echo(f"Creating project: {name}")

    db_text = _choice_prompt(
        "What kind of database do you want to use?",
        ["None", "SQLite", "MySQL", "PostgreSQL"],
        default_index=1,
    )
    orm_text = _choice_prompt(
        "Which ORM do you want to use?",
        ["None", "SQLAlchemy", "SQLModel"],
        default_index=1,
    )
    linter_text = _choice_prompt(
        "What linter do you want to use?",
        ["None", "Black", "Ruff"],
        default_index=2,
    )
    test_text = _choice_prompt(
        "What testing framework do you like to use?",
        ["None", "PyTest", "pytest-async-io"],
        default_index=1,
    )
    docker_text = _choice_prompt(
        "Do you want to create a Docker file for this project?",
        ["Yes", "No"],
        default_index=0,
    )

    db_map = {
        "None": DatabaseChoice.NONE,
        "SQLite": DatabaseChoice.SQLITE,
        "MySQL": DatabaseChoice.MYSQL,
        "PostgreSQL": DatabaseChoice.POSTGRESQL,
    }
    orm_map = {
        "None": ORMChoice.NONE,
        "SQLAlchemy": ORMChoice.SQLALCHEMY,
        "SQLModel": ORMChoice.SQLMODEL,
    }
    linter_map = {
        "None": LinterChoice.NONE,
        "Black": LinterChoice.BLACK,
        "Ruff": LinterChoice.RUFF,
    }
    test_map = {
        "None": TestChoice.NONE,
        "PyTest": TestChoice.PYTEST,
        "pytest-async-io": TestChoice.PYTEST_ASYNCIO,
    }

    config = ProjectConfig(
        name=name,
        database=db_map[db_text],
        orm=orm_map[orm_text],
        linter=linter_map[linter_text],
        test_framework=test_map[test_text],
        docker=(docker_text == "Yes"),
    )

    target_dir = Path(name).resolve()
    scaffold_project(config, target_dir)

    # Success message and next steps
    typer.echo()
    typer.echo(typer.style(f"✔ FastAPI project '{name}' created successfully!", fg=typer.colors.GREEN, bold=True))
    typer.echo()
    typer.echo(typer.style("Next steps:", fg=typer.colors.CYAN, bold=True))
    typer.echo(f"  1. cd {name}")
    typer.echo("  2. uv sync")
    typer.echo("  3. uv run uvicorn app.main:app --reload")
    typer.echo("  4. Open http://127.0.0.1:8000 in your browser")


def cli() -> None:
    """Entry point for the fastapi-init console script."""
    typer.run(main)


if __name__ == "__main__":
    cli()

