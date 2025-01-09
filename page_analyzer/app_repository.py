from psycopg2.extras import DictCursor


class AppRepository:
    def __init__(self, conn) -> None:
        self.conn = conn
        self.urls_table = 'urls'
        self.checks_table = 'url_checks'

    def get_url_by_name(self, name: str) -> dict:
        with self.conn.cursor(cursor_factory=DictCursor) as cur:
            cur.execute(f'''
                SELECT id
                FROM {self.urls_table}
                WHERE url = %s;
            ''', (name,))
            return cur.fetchone()

    def get_urls_paginated(self, page: int, per_page: int) -> tuple:
        offset = (page - 1) * per_page
        with self.conn.cursor(cursor_factory=DictCursor) as cur:
            cur.execute(f'SELECT COUNT(*) FROM {self.urls_table}')
            total = cur.fetchone()[0]

            cur.execute(f'''
                SELECT
                    ul.id AS id,
                    ul.url AS url,
                    uc.created_at AS created_at,
                    uc.status_code AS status_code
                FROM {self.urls_table} AS ul
                LEFT JOIN (
                    SELECT id, url_id, created_at, status_code
                    FROM {self.checks_table}
                    WHERE id IN (
                        SELECT MAX(id)
                        FROM {self.checks_table}
                        GROUP BY url_id
                    )
                ) AS uc ON ul.id = uc.url_id
                ORDER BY ul.id DESC
                LIMIT %s OFFSET %s;
            ''', (per_page, offset))

            return cur.fetchall(), total

    def get_url_info(self, url_id: int) -> dict:
        with self.conn.cursor(cursor_factory=DictCursor) as cur:
            cur.execute(f'''
                SELECT url AS name, created_at
                FROM {self.urls_table}
                WHERE id = %s;
            ''', (url_id,))
            return cur.fetchone()

    def get_url_checks(self, url_id: int) -> list:
        with self.conn.cursor(cursor_factory=DictCursor) as cur:
            cur.execute(f'''
                SELECT
                    check_id, status_code, h1,
                    title, description, created_at
                FROM {self.checks_table}
                WHERE url_id = %s
                ORDER BY id DESC;
            ''', (url_id,))
            return cur.fetchall()

    def get_url_address(self, url_id: int) -> dict:
        with self.conn.cursor(cursor_factory=DictCursor) as cur:
            cur.execute(f'''
                SELECT url AS name
                FROM {self.urls_table}
                WHERE id = %s;
            ''', (url_id,))
            return cur.fetchone()

    def check_url(self, data: dict) -> None:
        with self.conn.cursor(cursor_factory=DictCursor) as cur:
            cur.execute(f'''
                SELECT id
                FROM {self.urls_table}
                WHERE url = %s;
            ''', (data['name'],))

            try:
                url_id = cur.fetchone()['id']
            except TypeError:
                raise ValueError('URL not found in urls_list')

            cur.execute(f'''
                INSERT INTO {self.checks_table}(
                    url_id, status_code, h1,
                    title, description, created_at
                ) VALUES (%s, %s, %s, %s, %s, %s);
            ''', (
                url_id,
                data['status_code'],
                data['h1'],
                data['title'],
                data['description'],
                data['created_at']
            ))
        self.conn.commit()

    def add_url(self, name: str, creation_date: str) -> dict:
        with self.conn.cursor(cursor_factory=DictCursor) as cur:
            cur.execute(f'''
                SELECT id
                FROM {self.urls_table}
                WHERE url = %s;
            ''', (name,))
            url_id = cur.fetchone()

            if not url_id:
                cur.execute(f'''
                    INSERT INTO {self.urls_table}(url, created_at)
                    VALUES (%s, %s)
                    RETURNING id;
                ''', (name, creation_date))
                url_id = cur.fetchone()

        self.conn.commit()
        return url_id
