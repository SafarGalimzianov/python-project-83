from psycopg2.pool import SimpleConnectionPool
from contextlib import contextmanager
import psycopg2.extras

MIN_CONNS = 1
MAX_CONNS = 5


class ConnectionPool():
    def __init__(self, db_url, min_conns=MIN_CONNS, max_conns=MAX_CONNS):
        self.pool = None
        self.db_url = db_url
        self.min_conns = min_conns
        self.max_conns = max_conns

    def init_pool(self):
        if self.pool is not None:
            return

        try:
            self.pool = SimpleConnectionPool(
                self.min_conns,
                self.max_conns,
                dsn=self.db_url,
                cursor_factory=psycopg2.extras.DictCursor,
            )

            with self.pool.getconn() as conn:
                if conn.closed:
                    raise psycopg2.OperationalError

        except psycopg2.OperationalError as e:
            raise RuntimeError(f'Failed to connect to database: {str(e)}')

        except psycopg2.ProgrammingError as e:
            raise RuntimeError(f'Invalid connection parameters: {str(e)}')

        except TypeError as e:
            raise RuntimeError(f'Wrong parameter types: {str(e)}')

        except ValueError as e:
            raise RuntimeError(f'Wrong parameter values: {str(e)}')

    @contextmanager
    def get_connection(self):
        conn = None
        try:
            conn = self.pool.getconn()
            yield conn
        finally:
            if conn:
                self.pool.putconn(conn)

    @contextmanager
    def get_cursor(self, commit=False):
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                yield cur
                if commit:
                    conn.commit()
