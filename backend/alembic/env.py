"""Alembic environment: the database URL comes from the application settings."""
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

import app.models  # noqa: F401  (registers every table on the metadata)
from app.core.config import get_settings
from app.core.db import Base

config = context.config
if config.config_file_name:
    fileConfig(config.config_file_name)
config.set_main_option("sqlalchemy.url", get_settings().database_url)
target_metadata = Base.metadata
# Objects created by hand in migrations (expression or NULLS NOT DISTINCT indexes) that the models cannot express
HAND_MADE = {"ix_vacancies_search_trgm", "uq_report_slots_placement_kind_week"}


def include_object(obj, name, type_, reflected, compare_to):
    return not (type_ == "index" and name in HAND_MADE)


def run_migrations_offline() -> None:
    context.configure(url=config.get_main_option("sqlalchemy.url"), target_metadata=target_metadata,
                      literal_binds=True, compare_type=True,
                      include_object=include_object)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(config.get_section(config.config_ini_section, {}), prefix="sqlalchemy.",
                                     poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata, compare_type=True,
                          include_object=include_object)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
