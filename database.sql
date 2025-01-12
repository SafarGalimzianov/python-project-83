DROP FUNCTION IF EXISTS set_check_id() CASCADE;
-- Но не надо так удалять триггеры, так как они всегда удаляются с таблицами
DROP TABLE IF EXISTS urls CASCADE;
DROP TABLE IF EXISTS url_checks CASCADE;


CREATE TABLE IF NOT EXISTS urls(
    id SERIAL PRIMARY KEY,
    url VARCHAR(255) NOT NULL,
    created_at DATE NOT NULL
);

CREATE TABLE IF NOT EXISTS url_checks(
    id SERIAL PRIMARY KEY,
    url_id INTEGER REFERENCES urls(id) NOT NULL,
    check_id INTEGER NOT NULL,
    status_code INTEGER NOT NULL,
    h1 VARCHAR(255),
    title VARCHAR(255), 
    description TEXT,
    created_at DATE NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_urls_table_url 
ON urls(url);

CREATE INDEX IF NOT EXISTS idx_url_checks_table_id 
ON url_checks(url_id);

CREATE INDEX IF NOT EXISTS idx_url_checks_table_check_date 
ON url_checks(created_at);


/*
Чтобы каждая новая проверка на каждом уникальном url (то есть url_id) начиналась с 1,
создадим последовательность для подсчета числа проверок check_id каждом url_id.
Не используем сортировку и затем MAX по всем проверка url: с ростом числа проверок
сортировка по url_id и MAX будут выполняться все медленнее,
и замедлится добавление проверок в базу данных
Это важно, так как проверки url происходят чаще, чем добавление url
*/
CREATE FUNCTION set_check_id()
RETURNS TRIGGER AS $$
DECLARE
    seq_name TEXT;
BEGIN
    -- Каждая последовательность имеет уникальное имя:
    -- url_checks_seq_1, url_checks_seq_2 и так далее
    seq_name := 'url_checks_seq_' || NEW.url_id;

    --Создание последовательности
    IF NOT EXISTS (
        SELECT 1 FROM pg_sequences WHERE sequencename = seq_name
        ) THEN
        EXECUTE 'CREATE SEQUENCE ' || seq_name || ' START 1';

    END IF;

    -- Получение значения из последовательности
    EXECUTE 'SELECT nextval(''' || seq_name || ''')' INTO NEW.check_id;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Триггер перед каждым добавлением записи (то есть перед каждой проверкой url)
CREATE TRIGGER before_insert_check_id
    BEFORE INSERT ON url_checks
    FOR EACH ROW
    EXECUTE FUNCTION set_check_id();