"""Tests for the database client."""

import psycopg2
import pytest
import testing.postgresql

from database_container import DatabaseContainer


def init_db(db_instance):
    conn = psycopg2.connect(**db_instance.dsn())
    cur = conn.cursor()
    cur.execute('CREATE TABLE groups'
                ' (group_name varchar, uid varchar, username varchar(64),'
                ' PRIMARY KEY(group_name, uid));')
    cur.execute('INSERT INTO groups (group_name, uid, username)'
                ' VALUES (\'foo\', \'1\', \'Alice\');')
    cur.execute('INSERT INTO groups (group_name, uid, username)'
                ' VALUES (\'foo\', \'2\', \'Becky\');')
    cur.execute('INSERT INTO groups (group_name, uid, username)'
                ' VALUES (\'bar\', \'3\', \'Cameron\');')
    cur.close()
    conn.commit()
    conn.close()


@pytest.fixture(name='database_factory', scope='module')
def fixture_database_factory():
    """Initialize the database factory."""
    db_factory = testing.postgresql.PostgresqlFactory(
        cache_initialized_db=True, on_initialized=init_db)
    yield db_factory
    # Clean up the database Factory
    db_factory.clear_cache()


@pytest.fixture(name='database_instance')
def fixture_database_instance(database_factory):
    """Initialize a database instance from the factory."""
    db_instance = database_factory()
    yield db_instance
    # Clean up the database instance
    db_instance.stop()


@pytest.fixture(name='database_client')
def fixture_database_client(database_instance):
    """Initialize a database client that can query the database instance."""
    DatabaseContainer.config.override({
        'database_url': database_instance.url(),
        'sslmode': 'disable',
        'minconn': 1,
        'maxconn': 1,
    })
    yield DatabaseContainer.client()
    # Reset the database client configuration
    DatabaseContainer.client.reset()
    DatabaseContainer.pool.reset()


def test_add_subgroup_members(database_client):
    database_client.add_subgroup_members('foo', ['4'], {'4': 'Dan'})
    assert sorted(database_client.get_subgroup_members(['foo'
                                                        ])) == [('1', 'Alice'),
                                                                ('2', 'Becky'),
                                                                ('4', 'Dan')]


def test_delete_subgroup(database_client):
    database_client.delete_subgroup('foo')
    assert sorted(database_client.get_subgroups()) == ['bar']


def test_get_subgroup_members(database_client):
    assert sorted(database_client.get_subgroup_members(['foo'
                                                        ])) == [('1', 'Alice'),
                                                                ('2', 'Becky')]


def test_get_subgroups(database_client):
    assert sorted(database_client.get_subgroups()) == ['bar', 'foo']


def test_has_subgroup(database_client):
    assert database_client.has_subgroup('foo')
    assert database_client.has_subgroup('bar')
    assert not database_client.has_subgroup('baz')


def test_remove_subgroup_members(database_client):
    database_client.remove_subgroup_members('foo', ['1'])
    assert sorted(database_client.get_subgroup_members(['foo'])) == [('2',
                                                                      'Becky')]
