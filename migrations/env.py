# File: migrations/env.py
import asyncio
from logging.config import fileConfig
import os
import sys
import ssl
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode

from sqlalchemy import pool
from sqlalchemy.ext.asyncio import create_async_engine

from alembic import context

# --- Path Setup ---
# env.py is in <PROJECT_ROOT>/migrations/env.py
# So, to get PROJECT_ROOT, we go one level up from the directory of env.py
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__)) # This is .../migrations
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)              # This is .../ (project root)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
print(f"DEBUG migrations/env.py: Calculated PROJECT_ROOT: {PROJECT_ROOT}") # For verification
# --- End Path Setup ---

# --- App Imports ---
from app.core.config import settings
from app.core.database import Base 
from app.core.logging import logger # Using your application's logger
# === IMPORTANT: Import ALL your ORM models here ===
from app.models.user import User # noqa
from app.models.property import Property # noqa
from app.models.property_image import PropertyImage # noqa
from app.models.property_embedding import PropertyEmbedding # noqa
# ... import other models ...
# --- End App Imports ---

config = context.config # Alembic Config object
# Interpret the config file for Python logging for Alembic's own operations.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)
print("DEBUG migrations/env.py: Starting SSL Configuration Block")

# --- Database URL and SSL Configuration for Alembic ---
original_db_url_str = str(settings.DATABASE_URL)
parsed_original_url = urlparse(original_db_url_str)
query_params_original = parse_qs(parsed_original_url.query) # Keep original query params
original_sslmode = query_params_original.get('sslmode', [None])[0]

asyncpg_ssl_connect_arg_value = None # This will hold False, True, or an SSLContext object
AIVEN_CA_CERT_PATH = os.path.join(PROJECT_ROOT, "ca.pem") # Path to ca.pem in project root

print(f"DEBUG migrations/env.py: Original DSN sslmode: {original_sslmode}")
print(f"DEBUG migrations/env.py: Checking for CA cert at: {AIVEN_CA_CERT_PATH}")

if original_sslmode == 'disable':
    asyncpg_ssl_connect_arg_value = False
    print("DEBUG migrations/env.py: DSN has sslmode=disable. Setting asyncpg_ssl_connect_arg_value=False.")
elif original_sslmode in ['require', 'prefer', 'allow'] or \
     (parsed_original_url.hostname and "aivencloud.com" in parsed_original_url.hostname.lower()):
    if os.path.exists(AIVEN_CA_CERT_PATH):
        try:
            ssl_context = ssl.create_default_context(cafile=AIVEN_CA_CERT_PATH)
            asyncpg_ssl_connect_arg_value = ssl_context
            print(f"DEBUG migrations/env.py: Successfully created SSLContext with CA cert: {AIVEN_CA_CERT_PATH}.")
        except Exception as e:
            print(f"DEBUG migrations/env.py: Error creating SSLContext with {AIVEN_CA_CERT_PATH}: {e}. Falling back to ssl=True.")
            asyncpg_ssl_connect_arg_value = True 
    else:
        print(f"DEBUG migrations/env.py: Aiven CA certificate NOT FOUND at {AIVEN_CA_CERT_PATH}. Setting asyncpg_ssl_connect_arg_value=True (system CAs).")
        asyncpg_ssl_connect_arg_value = True
else:
    print("DEBUG migrations/env.py: No specific SSL mode detected for asyncpg connect_args. Driver will use DSN or defaults.")

# Clean the URL for SQLAlchemy engine: remove 'sslmode' as we want to control SSL via connect_args
query_params_for_sqlalchemy_engine = parse_qs(parsed_original_url.query)
query_params_for_sqlalchemy_engine.pop('sslmode', None) # Remove sslmode for engine DSN
cleaned_query_string_for_engine = urlencode(query_params_for_sqlalchemy_engine, doseq=True)

# Use the original scheme (e.g., postgresql+asyncpg) for SQLAlchemy's engine creation
cleaned_db_url_for_sqlalchemy_engine = urlunparse(
    (parsed_original_url.scheme, parsed_original_url.netloc, parsed_original_url.path,
     parsed_original_url.params, cleaned_query_string_for_engine, parsed_original_url.fragment)
)

# For Alembic's offline context and config.set_main_option, it sometimes prefers no +driver part
# but it's generally safer to use the cleaned URL intended for the engine if it works.
# Let's use the same cleaned URL for consistency.
db_url_for_alembic_config = cleaned_db_url_for_sqlalchemy_engine

print(f"DEBUG migrations/env.py: DB URL for Alembic context config (sqlalchemy.url): {db_url_for_alembic_config.replace(settings.POSTGRES_PASSWORD, '********') if settings.POSTGRES_PASSWORD else db_url_for_alembic_config}")
print(f"DEBUG migrations/env.py: DB URL for create_async_engine (online): {cleaned_db_url_for_sqlalchemy_engine.replace(settings.POSTGRES_PASSWORD, '********') if settings.POSTGRES_PASSWORD else cleaned_db_url_for_sqlalchemy_engine}")

config.set_main_option("sqlalchemy.url", db_url_for_alembic_config)
target_metadata = Base.metadata
# --- End Database URL and SSL Configuration ---

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()

def do_run_migrations(connection):
    """Helper function to run migrations with a given connection."""
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()

async def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    print("DEBUG migrations/env.py: run_migrations_online started.")
    engine_args = {
        "poolclass": pool.NullPool,
        # "echo": settings.DEBUG, # Optional for debugging SQL
    }
    
    # asyncpg_ssl_connect_arg_value is determined in the global scope of this module
    if asyncpg_ssl_connect_arg_value is not None:
        engine_args["connect_args"] = {"ssl": asyncpg_ssl_connect_arg_value}
        print(f"DEBUG migrations/env.py: Passing connect_args={{'ssl': ... (type: {type(asyncpg_ssl_connect_arg_value)})}} to create_async_engine.")
    else:
        print("DEBUG migrations/env.py: No explicit 'ssl' connect_arg passed to create_async_engine.")
    
    connectable = create_async_engine(
        cleaned_db_url_for_sqlalchemy_engine, # Use the URL without ?sslmode in query for engine
        **engine_args
    )

    print("DEBUG migrations/env.py: Async engine created. Attempting to connect for migrations...")
    try:
        async with connectable.connect() as connection:
            print("DEBUG migrations/env.py: Successfully connected to database for migrations.")
            # Configure the Alembic context with the connection
            context.configure(
                connection=connection,
                target_metadata=target_metadata 
            )
            async with connection.begin(): # Start a transaction for migration steps
                print("DEBUG migrations/env.py: Began transaction for running migration steps.")
                await connection.run_sync(do_run_migrations) 
                print("DEBUG migrations/env.py: Migration steps (do_run_migrations) executed within transaction.")
            print("DEBUG migrations/env.py: Transaction for migration steps committed/rolled back.")
    except ssl.SSLCertVerificationError as e:
        print(f"DEBUG migrations/env.py: SSLCertVerificationError during connect/migrations: {e}")
        print("DEBUG migrations/env.py: Ensure ca.pem is correct, accessible, and server certificate is valid & matches the CA.")
        raise # Re-raise to see the full traceback from Alembic
    except Exception as e:
        print(f"DEBUG migrations/env.py: Other exception during connect/migrations: {e}")
        import traceback
        print(f"DEBUG migrations/env.py: Traceback: {traceback.format_exc()}")
        raise # Re-raise
    finally:
        if 'connectable' in locals():
            await connectable.dispose()
            print("DEBUG migrations/env.py: Engine disposed after migrations.")

# Main Alembic entry point
if context.is_offline_mode():
    print("DEBUG migrations/env.py: Running in offline mode.") # Use print for offline too
    run_migrations_offline()
else:
    print("DEBUG migrations/env.py: Running in online mode.") # Use print
    asyncio.run(run_migrations_online())