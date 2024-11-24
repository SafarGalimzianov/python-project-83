from psycopg.rows import dict_row


class AppRepository:
    def __init__(self, conn) -> None:
        self.conn = conn
        self.urls_table = 'urls_table'
        self.checks_table = 'checks_table'
        # Создание таблиц
        # Ни одно из полей не может быть NULL,
        # так как такие случаи предотвращаются в функции make_request() в app.py
        with self.conn.cursor() as cur:
            cur.execute(f'''
                CREATE TABLE IF NOT EXISTS {self.urls_table}(
                    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
                    url VARCHAR(255) NOT NULL,
                    creation_date DATE NOT NULL
                );
            ''')
            cur.execute(f'''
                CREATE TABLE IF NOT EXISTS {self.checks_table}(
                    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
                    url_id INTEGER REFERENCES {self.urls_table}(id) NOT NULL,
                    check_id INTEGER NOT NULL,
                    response_code INTEGER NOT NULL,
                    h1_content TEXT NOT NULL,
                    title_content TEXT NOT NULL,
                    description_content TEXT NOT NULL,
                    check_date DATE NOT NULL
                );
            ''')
            cur.execute(f'''
                CREATE INDEX IF NOT EXISTS
                idx_urls_table_url ON {self.urls_table}(url)
            ;''')
            cur.execute(f'''
                CREATE INDEX IF NOT EXISTS
                idx_checks_table_id ON {self.checks_table}(url_id)
            ;''')
            cur.execute(f'''
                CREATE INDEX IF NOT EXISTS
                idx_checks_table_check_date ON {self.checks_table}(check_date)
            ;''')

            # Создание последовательности для check_id
            cur.execute('''
                CREATE SEQUENCE IF NOT EXISTS check_id_seq
                START 1
            ;''')

            # Создание функции для установки check_id
            cur.execute(f'''
                CREATE OR REPLACE FUNCTION set_check_id()
                RETURNS TRIGGER AS $$
                BEGIN
                    NEW.check_id := COALESCE(
                        (SELECT MAX(check_id) + 1
                        FROM {self.checks_table}
                        WHERE url_id = NEW.url_id),
                        1
                    );
                    RETURN NEW;
                END;
                $$ LANGUAGE plpgsql
            ;''')

            # Создание триггера для установки check_id
            cur.execute(f'''
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1
                        FROM pg_trigger
                        WHERE tgname = 'before_insert_check_id'
                    ) THEN
                        CREATE TRIGGER before_insert_check_id
                        BEFORE INSERT ON {self.checks_table}
                        FOR EACH ROW
                        EXECUTE FUNCTION set_check_id();
                    END IF;
                END;
                $$
            ;''')
        self.conn.commit()

    # Метод получения всех URL с их последними проверками
    def get_urls(self):
        with self.conn.cursor(row_factory=dict_row) as cur:
            cur.execute(f'''
                SELECT
                    ul.id AS id,
                    ul.url AS url,
                    uc.check_date AS check_date,
                    uc.response_code AS response_code
                FROM {self.urls_table} AS ul
                LEFT JOIN(
                    SELECT id, url_id, check_date, response_code
                    FROM {self.checks_table}
                    WHERE id IN(
                        SELECT MAX(id)
                        FROM {self.checks_table}
                        GROUP BY url_id
                    )
                ) AS uc ON ul.id = uc.url_id
                ORDER BY ul.id ASC
            ''')
            return cur.fetchall()
        
    def get_urls_paginated(self, page: int, per_page: int) -> tuple:
        offset = (page - 1) * per_page
        
        with self.conn.cursor(row_factory=dict_row) as cur:
            # Get total count
            cur.execute(f'SELECT COUNT(*) FROM {self.urls_table}')
            total = cur.fetchone()['count']
            
            # Get paginated results
            cur.execute(f'''
                SELECT
                    ul.id AS id,
                    ul.url AS url,
                    uc.check_date AS check_date,
                    uc.response_code AS response_code
                FROM {self.urls_table} AS ul
                LEFT JOIN(
                    SELECT id, url_id, check_date, response_code
                    FROM {self.checks_table}
                    WHERE id IN(
                        SELECT MAX(id)
                        FROM {self.checks_table}
                        GROUP BY url_id
                    )
                ) AS uc ON ul.id = uc.url_id
                ORDER BY ul.id DESC
                LIMIT %(limit)s OFFSET %(offset)s
            ''', {
                'limit': per_page,
                'offset': offset
            })
            
            return cur.fetchall(), total

    # Метод получения информации о URL с его последней проверкой
    def get_url_info(self, url_id: int) -> dict:
        with self.conn.cursor(row_factory=dict_row) as cur:
            cur.execute(f'''
                    SELECT url, creation_date
                    FROM {self.urls_table}
                    WHERE id = %(url_id)s
            ''', {
                'url_id': url_id,
            })
            return cur.fetchone()

    # Метод поиска проверок URL по его имени
    def get_url_checks(self, url_id: int) -> list:
        with self.conn.cursor(row_factory=dict_row) as cur:
            cur.execute(f'''
                SELECT
                    id,
                    check_id,
                    response_code,
                    h1_content,
                    title_content,
                    description_content,
                    check_date
                FROM {self.checks_table}
                WHERE url_id = %(url_id)s
            ''', {
                'url_id': url_id,
            })
            return cur.fetchall()

    # Метод получения адреса URL по его id
    def get_url_address(self, url_id: int) -> dict:
        with self.conn.cursor(row_factory=dict_row) as cur:
            cur.execute(f'''
                SELECT url
                FROM {self.urls_table}
                WHERE id = %(url_id)s
            ''', {
                'url_id': url_id,
            })
            return cur.fetchone()

    # Метод проверки URL
    def check_url(self, data: dict) -> None:
        with self.conn.cursor(row_factory=dict_row) as cur:
            # Получение id URL
            cur.execute(f'''
                SELECT id
                FROM {self.urls_table}
                WHERE url = %(url)s
            ''', {
                'url': data['url'],
            })

            try:
                url_id = cur.fetchone()['id']
            except TypeError:
                raise ValueError('URL not found in urls_list')

            # Добавление данных проверки URL
            cur.execute(f'''
                INSERT INTO {self.checks_table}(
                        url_id,
                        response_code,
                        h1_content,
                        title_content,
                        description_content,
                        check_date
                ) VALUES (
                        %(url_id)s,
                        %(response_code)s,
                        %(h1_content)s,
                        %(title_content)s,
                        %(description_content)s,
                        %(check_date)s
                )
            ''', {
                'url_id': url_id,
                'response_code': data['response_code'],
                'h1_content': data['h1'],
                'title_content': data['title'],
                'description_content': data['description'],
                'check_date': data['check_date'],
            })
        self.conn.commit()

    # Методы добавления нового URL
    def add_url(self, url: str, creation_date: str) -> dict:
        with self.conn.cursor(row_factory=dict_row) as cur:
            if not isinstance(url, str):
                raise TypeError("URL must be a string")
            if not isinstance(creation_date, str):
                raise TypeError("Creation date must be a string")
            # Проверка на существование URL в базе данных
            cur.execute(f'''
                SELECT id
                FROM {self.urls_table}
                WHERE url = %(url)s
            ''', {
                'url': url,
            })
            result = cur.fetchone()
            # Если URL уже существует
            if result:
                # Возврат id уже существующего URL
                url_id = result
            else:
                # Добавление URL и получение его id
                cur.execute(f'''
                    INSERT INTO {self.urls_table}(url, creation_date)
                    VALUES (%(url)s, %(creation_date)s)
                    RETURNING id
                ''', {
                    'url': url,
                    'creation_date': creation_date,
                })
                url_id = cur.fetchone()

        self.conn.commit()
        return url_id
