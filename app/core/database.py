# File: agentic_rental_platform/app/core/database.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from typing import AsyncGenerator
import ssl
import os
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode

from app.core.config import settings
from app.core.logging import logger

db_url_str = str(settings.DATABASE_URL)
connect_args_main = {}
AIVEN_CA_CERT_PATH_MAIN_APP = os.path.join(settings.BASE_DIR, "ca.pem")
parsed_url_main = urlparse(db_url_str)
query_params_main = parse_qs(parsed_url_main.query)
original_sslmode_main = query_params_main.get('sslmode', [None])[0]
asyncpg_ssl_config_main = None

if original_sslmode_main == 'disable':
    asyncpg_ssl_config_main = False
    logger.info("Main app engine: DSN has sslmode=disable. Forcing asyncpg ssl=False.")
elif original_sslmode_main in ['require', 'prefer', 'allow'] or "aivencloud.com" in parsed_url_main.netloc.lower():
    if os.path.exists(AIVEN_CA_CERT_PATH_MAIN_APP):
        ssl_context = ssl.create_default_context(cafile=AIVEN_CA_CERT_PATH_MAIN_APP)
        asyncpg_ssl_config_main = ssl_context
        logger.info(f"Main app engine: Configuring asyncpg SSL with CA cert: {AIVEN_CA_CERT_PATH_MAIN_APP}")
    else:
        logger.warning(f"Main app engine: Aiven CA certificate not found at {AIVEN_CA_CERT_PATH_MAIN_APP}. Attempting SSL with system CAs. This might fail.")
        asyncpg_ssl_config_main = True
else:
    logger.info("Main app engine: No specific SSL mode detected. Asyncpg will use defaults.")

if asyncpg_ssl_config_main is not None:
    connect_args_main["ssl"] = asyncpg_ssl_config_main

query_params_main.pop('sslmode', None)
cleaned_query_string_main = urlencode(query_params_main, doseq=True)
cleaned_db_url_for_sqlalchemy_main = urlunparse(
    (parsed_url_main.scheme, parsed_url_main.netloc, parsed_url_main.path,
     parsed_url_main.params, cleaned_query_string_main, parsed_url_main.fragment)
)

try:
    engine = create_async_engine(
        cleaned_db_url_for_sqlalchemy_main,
        pool_pre_ping=True,
        connect_args=connect_args_main,
        # echo=settings.DEBUG,
    )
    logger.info(f"Main app async database engine created for URL: {cleaned_db_url_for_sqlalchemy_main.replace(settings.POSTGRES_PASSWORD, '********') if settings.POSTGRES_PASSWORD else cleaned_db_url_for_sqlalchemy_main} (SSL configured via connect_args if applicable)")
except Exception as e:
    logger.error(f"Failed to create main app database engine: {e}")
    raise

AsyncSessionLocal = sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False, autoflush=False, autocommit=False
)
Base = declarative_base()

async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        logger.debug(f"DB Session {id(session)} created for request.")
        try:
            yield session
        except Exception as e:
            logger.error(f"DB Session {id(session)} exception during request: {e}")
            await session.rollback()
            raise
        finally:
            logger.debug(f"DB Session {id(session)} closed for request.")