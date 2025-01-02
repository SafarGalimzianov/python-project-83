from psycopg2.extras import DictCursor


class AppRepository:
    def __init__(self, conn) -> None:
        self.conn = conn
        self.urls_table = 'urls'
        self.checks_table = 'url_checks'

    def get_urls(self):
        with self.conn.cursor(cursor_factory=DictCursor) as cur:
            cur.execute(f'''
                SELECT
                    ul.id AS id,
                    ul.url AS url,
                    uc.check_date AS check_date,
                    uc.response_code AS response_code
                FROM {self.urls_table} AS ul
                LEFT JOIN (
                    SELECT id, url_id, check_date, response_code
                    FROM {self.checks_table}
                    WHERE id IN (
                        SELECT MAX(id)
                        FROM {self.checks_table}
                        GROUP BY url_id
                    )
                ) AS uc ON ul.id = uc.url_id
                ORDER BY ul.id ASC;
            ''')
            return [dict(row) for row in cur.fetchall()]

    def get_urls_paginated(self, page: int, per_page: int) -> tuple:
        offset = (page - 1) * per_page
        with self.conn.cursor(cursor_factory=DictCursor) as cur:
            cur.execute(f'SELECT COUNT(*) FROM {self.urls_table}')
            total = cur.fetchone()[0]

            cur.execute(f'''
                SELECT
                    ul.id AS id,
                    ul.url AS url,
                    uc.check_date AS check_date,
                    uc.response_code AS response_code
                FROM {self.urls_table} AS ul
                LEFT JOIN (
                    SELECT id, url_id, check_date, response_code
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

            return [dict(row) for row in cur.fetchall()], total

    def get_url_info(self, url_id: int) -> dict:
        with self.conn.cursor(cursor_factory=DictCursor) as cur:
            cur.execute(f'''
                SELECT url, creation_date
                FROM {self.urls_table}
                WHERE id = %s;
            ''', (url_id,))
            row = cur.fetchone()
            return dict(row) if row else None

    def get_url_checks(self, url_id: int) -> list:
        with self.conn.cursor(cursor_factory=DictCursor) as cur:
            cur.execute(f'''
                SELECT
                    id, check_id, response_code,
                    h1_content, title_content,
                    description_content, check_date
                FROM {self.checks_table}
                WHERE url_id = %s;
            ''', (url_id,))
            return [dict(row) for row in cur.fetchall()]

    def get_url_address(self, url_id: int) -> dict:
        with self.conn.cursor(cursor_factory=DictCursor) as cur:
            cur.execute(f'''
                SELECT url
                FROM {self.urls_table}
                WHERE id = %s;
            ''', (url_id,))
            row = cur.fetchone()
            return dict(row) if row else None

    def check_url(self, data: dict) -> None:
        with self.conn.cursor(cursor_factory=DictCursor) as cur:
            cur.execute(f'''
                SELECT id
                FROM {self.urls_table}
                WHERE url = %s;
            ''', (data['url'],))

            try:
                url_id = cur.fetchone()['id']
            except TypeError:
                raise ValueError('URL not found in urls_list')

            cur.execute(f'''
                INSERT INTO {self.checks_table}(
                    url_id, response_code, h1_content,
                    title_content, description_content, check_date
                ) VALUES (%s, %s, %s, %s, %s, %s);
            ''', (
                url_id,
                data['response_code'],
                data['h1'],
                data['title'],
                data['description'],
                data['check_date']
            ))
        self.conn.commit()

    def add_url(self, url: str, creation_date: str) -> dict:
        with self.conn.cursor(cursor_factory=DictCursor) as cur:
            if not isinstance(url, str):
                raise TypeError("URL must be a string")
            if not isinstance(creation_date, str):
                raise TypeError("Creation date must be a string")

            cur.execute(f'''
                SELECT id
                FROM {self.urls_table}
                WHERE url = %s;
            ''', (url,))
            result = cur.fetchone()

            if result:
                url_id = dict(result)
            else:
                cur.execute(f'''
                    INSERT INTO {self.urls_table}(url, creation_date)
                    VALUES (%s, %s)
                    RETURNING id;
                ''', (url, creation_date))
                url_id = dict(cur.fetchone())

        self.conn.commit()
        return url_id
