"""Client for database queries."""

from psycopg2.pool import AbstractConnectionPool
from typing import Dict, List, Tuple


class DatabaseClient:
    """Client for database queries."""
    def __init__(self, connection_pool: AbstractConnectionPool):
        """Initialize the database connection.

        Args:
            connection_pool: database connection pool
        """
        self._pool = connection_pool

    def add_subgroup_members(self, group_name: str, uids: List[str],
                             members: Dict[str, str]) -> None:
        """Add members to a subgroup.

        Args:
            group_name: name of the group
            uids: list of user IDs to add to the groups
            members: dict from user ID to username
        """
        conn = self._pool.getconn()
        cur = conn.cursor()
        for uid in uids:
            cur.execute(('INSERT INTO groups (group_name, uid, username)'
                         ' VALUES (%s, %s, %s)'
                         ' ON CONFLICT (group_name, uid) DO NOTHING;'),
                        (group_name, uid, members[uid]))
        cur.close()
        conn.commit()
        self._pool.putconn(conn)

    def delete_subgroup(self, group_name: str) -> None:
        """Delete a subgroup.

        Args:
            group_name: name of the group
        """
        conn = self._pool.getconn()
        cur = conn.cursor()
        cur.execute('DELETE FROM groups WHERE group_name = %s;',
                    (group_name, ))
        cur.close()
        conn.commit()
        self._pool.putconn(conn)

    def get_subgroup_members(self, groups: List[str]) -> List[Tuple[str, str]]:
        """Get a list of the members of a list of subgroups.

        Args:
            groups: list of group names

        Returns: list of tuples containing user IDs and usernames
        """
        conn = self._pool.getconn()
        cur = conn.cursor()
        cur.execute(
            'SELECT uid, username FROM groups WHERE group_name = ANY(%s);',
            (groups, ))
        members = cur.fetchall()
        cur.close()
        self._pool.putconn(conn)
        return members

    def get_subgroups(self) -> List[str]:
        """Get a list of the subgroups in the group.

        Returns: list of subgroup names
        """
        conn = self._pool.getconn()
        cur = conn.cursor()
        cur.execute('SELECT DISTINCT group_name FROM groups;')
        subgroups = map(lambda row: row[0], cur.fetchall())
        cur.close()
        self._pool.putconn(conn)
        return subgroups

    def has_subgroup(self, group_name: str) -> bool:
        """Determine whether or not the subgroup exists within the group.

        Args:
            group_name: name of the group

        Returns: True if the subgroup exists, False otherwise
        """
        conn = self._pool.getconn()
        cur = conn.cursor()
        cur.execute(
            'SELECT EXISTS(SELECT 1 FROM groups WHERE group_name = %s);',
            (group_name, ))
        exists = cur.fetchone()[0]
        cur.close()
        self._pool.putconn(conn)
        return exists

    def remove_subgroup_members(self, group_name: str,
                                uids: List[str]) -> None:
        """Remove members from the subgroup.

        Args:
            group_name: name of the group
            uids: list of user IDs to remove from the group
        """
        conn = self._pool.getconn()
        cur = conn.cursor()
        for uid in uids:
            cur.execute(
                'DELETE FROM groups WHERE group_name = %s AND uid = %s;', (
                    group_name,
                    uid,
                ))
        cur.close()
        conn.commit()
        self._pool.putconn(conn)
