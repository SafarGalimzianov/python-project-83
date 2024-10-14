from psycopg2.extras import RealDictCursor


class AppRepository:
    def __init__(self, conn):
        self.conn = conn
        self.urls_table = 'urls_list'
        self.checks_table = 'urls_checks'
        with self.conn.cursor() as cur:
            cur.execute(f'''
                CREATE TABLE IF NOT EXISTS {self.urls_table}(
                id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
                url VARCHAR(255)
            );''')
            cur.execute(f'''
                CREATE TABLE IF NOT EXISTS {self.checks_table}(
                id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
                url_id INTEGER REFERENCES {self.urls_table}(id),
                response_code INTEGER,
                h1_content VARCHAR(100),
                title_content VARCHAR(100),
                description_content VARCHAR(100),
                check_date DATE
            );''')
            cur.execute('CREATE INDEX IF NOT EXISTS idx_urls_list_url ON urls_list(url);')
            cur.execute('CREATE INDEX IF NOT EXISTS idx_urls_checks_url_id ON urls_checks(url_id);')
            cur.execute('CREATE INDEX IF NOT EXISTS idx_urls_checks_check_date ON urls_checks(check_date);')
        self.conn.commit()


    def _fetch_url_info(self, url_id=None):
        query = f'''
            SELECT
                ul.id AS id,
                ul.url AS url,
                uc.check_date AS check_date,
                uc.response_code AS response_code
            FROM {self.urls_table} ul
            INNER JOIN(
                SELECT id, url_id, check_date, response_code
                FROM {self.checks_table}
                WHERE id IN(
                    SELECT MAX(id)
                    FROM {self.checks_table}
                    GROUP BY url_id
                )
            ) uc ON ul.id = uc.url_id
        '''
        params = ()
        if url_id is not None:
            query += ' WHERE ul.id = %s'
            params = (url_id,)

        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, params)
            return cur.fetchall() if url_id is None else cur.fetchone()


    # Метод получения всех сайтов с их последними проверками
    def get_urls(self):
        return self._fetch_url_info()


    # Метод получения информации о сайте с его последней проверкой
    def get_url_info(self, url_id):
        return self._fetch_url_info(url_id)


    # Метод поиска проверок сайта по его имени
    def get_url_checks(self, url_id):
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(f'''
                SELECT id, response_code, h1_content, title_content, description_content, check_date
                FROM {self.checks_table}
                WHERE url_id = %s
            ''', (url_id,))
            return cur.fetchone()


    # Метод получения адреса сайта
    def get_url_address(self, url_id):
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(f'''
                SELECT url
                FROM {self.urls_table}
                WHERE id = %s
            ''', (url_id,))
            return cur.fetchone()[0]


    # Метод проверки сайта
    def check_url(self, data):
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            # 
            cur.execute('''
                SELECT id
                FROM urls_list
                WHERE url = %(url)s
            ''', {'url': data['url']})
            
            url_id = cur.fetchone()[0] if cur.rowcount > 0 else None
            
            if url_id is None:
                raise ValueError("URL not found in urls_list")
            
            # 
            cur.execute('''
                INSERT INTO urls_checks(
                        url_id, response_code, h1_content, title_content, description_content, check_date
                ) VALUES (
                        %(url_id)s, %(response_code)s, %(h1_content)s, %(title_content)s, %(description_content)s, %(check_date)s
                )
            ''', {
                'url_id': url_id,
                'response_code': data['response_code'],
                'h1_content': data['h1_content'],
                'title_content': data['title_content'],
                'description_content': data['description_content'],
                'check_date': data['check_date'],
            })
        self.conn.commit()


    # Методы добавления нового сайта
    def add_url(self, data):
        with self.conn.cursor() as cur:
            cur.execute('''
                INSERT INTO urls_list(
                    url, check_date
                ) VALUES (
                        %(url)s, %(check_date)s
                )
                RETURNING id
            ''', {
                'url': data['url'],
                'check_date': data['check_date']
            })
            url_id = cur.fetchone()[0]
        self.conn.commit()
        return url_id