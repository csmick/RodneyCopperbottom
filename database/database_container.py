"""Configuration for the database client."""

from database_client import DatabaseClient
from dependency_injector import containers, providers
from psycopg2.pool import ThreadedConnectionPool


class DatabaseContainer(containers.DeclarativeContainer):
    """Container for database-related providers.

    Providers:
        config: configuration variables for the database client (see below)
        pool: database connection pool
        client: database client

    The following configuration properties are defined on the config provider:
        database_url: the databae url
        minconn: the minimum number of database connections to keep open
        maxconn: the maximum number of database connections to keep open
        sslmode: the sslmode for the database connection pool (see
            https://www.postgresql.org/docs/9.1/libpq-ssl.html for valid values)
    """
    config = providers.Configuration()

    pool = providers.ThreadSafeSingleton(ThreadedConnectionPool,
                                         config.minconn,
                                         config.maxconn,
                                         config.database_url,
                                         sslmode=config.sslmode)

    client = providers.ThreadSafeSingleton(DatabaseClient, pool)
