from psycopg.rows import dict_row


class AppRepository:
    def __init__(self, conn):
        self.conn = conn
        self.urls_table = 'urls_table'
        self.checks_table = 'checks_table'
        with self.conn.cursor() as cur:
            cur.execute(f'''
                CREATE TABLE IF NOT EXISTS {self.urls_table}(
                id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
                url VARCHAR(255),
                creation_date DATE
            );''')
            cur.execute(f'''
                CREATE TABLE IF NOT EXISTS {self.checks_table}(
                id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
                url_id INTEGER REFERENCES {self.urls_table}(id),
                check_id INTEGER,
                response_code INTEGER,
                h1_content TEXT,
                title_content TEXT,
                description_content TEXT,
                check_date DATE
            );''')
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

    # Метод получения всех сайтов с их последними проверками
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

    # Метод получения информации о сайте с его последней проверкой
    def get_url_info(self, url_id):
        with self.conn.cursor(row_factory=dict_row) as cur:
            cur.execute(f'''
                    SELECT url, creation_date
                    FROM {self.urls_table}
                    WHERE id = %(url_id)s
            ''', {
                'url_id': url_id,
            })
            return cur.fetchone()

    # Метод поиска проверок сайта по его имени
    def get_url_checks(self, url_id):
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

    # Метод получения адреса сайта
    def get_url_address(self, url_id):
        with self.conn.cursor(row_factory=dict_row) as cur:
            cur.execute(f'''
                SELECT url
                FROM {self.urls_table}
                WHERE id = %(url_id)s
            ''', {
                'url_id': url_id,
            })
            return cur.fetchone()

    # Метод проверки сайта
    def check_url(self, data):
        with self.conn.cursor(row_factory=dict_row) as cur:
            # Получение id URL
            cur.execute(f'''
                SELECT id
                FROM {self.urls_table}
                WHERE url = %(url)s
            ''', {
                'url': data['url'],
            })

            url_id = cur.fetchone()['id']

            if not url_id:
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
                'h1_content': data['h1_content'],
                'title_content': data['title_content'],
                'description_content': data['description_content'],
                'check_date': data['check_date'],
            })
        self.conn.commit()

    # Методы добавления нового сайта
    def add_url(self, url, creation_date):
        with self.conn.cursor(row_factory=dict_row) as cur:
            # Check if the URL already exists
            cur.execute(f'''
                SELECT id
                FROM {self.urls_table}
                WHERE url = %(url)s
            ''', {
                'url': url,
            })
            result = cur.fetchone()

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
