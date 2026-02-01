"""Alembic environment configuration."""

from logging.config import fileConfig

from sqlalchemy import pool, engine_from_config
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# Import models for autogenerate support
from app.db.base import Base
from app.db.models import user, project, segment, voice  # noqa: F401
from app.config import settings

# this is the Alembic Config object
config = context.config

# Override sqlalchemy.url from settings (convert async to sync driver)
sync_url = settings.DATABASE_URL.replace("+asyncpg", "").replace("+aiosqlite", "")
config.set_main_option("sqlalchemy.url", sync_url)

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Add your model's MetaData object here for 'autogenerate' support
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    For SQLite, we use sync engine. For PostgreSQL async, we'd use async engine.
    """
    url = config.get_main_option("sqlalchemy.url")
    
    # For SQLite, use sync mode
    if url.startswith("sqlite"):
        connectable = engine_from_config(
            config.get_section(config.config_ini_section, {}),
            prefix="sqlalchemy.",
            poolclass=pool.NullPool,
        )

        with connectable.connect() as connection:
            do_run_migrations(connection)
        
        connectable.dispose()
    else:
        # For PostgreSQL, use async mode
        import asyncio
        
        async def run_async_migrations() -> None:
            connectable = async_engine_from_config(
                config.get_section(config.config_ini_section, {}),
                prefix="sqlalchemy.",
                poolclass=pool.NullPool,
            )

            async with connectable.connect() as connection:
                await connection.run_sync(do_run_migrations)

            await connectable.dispose()
        
        asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
