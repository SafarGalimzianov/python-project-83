DROP TABLE IF EXISTS urls CASCADE;
DROP TABLE IF EXISTS url_checks CASCADE;


CREATE TABLE IF NOT EXISTS urls(
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    created_at DATE NOT NULL
);

CREATE TABLE IF NOT EXISTS url_checks(
    id SERIAL PRIMARY KEY,
    url_id INTEGER REFERENCES urls(id) NOT NULL,
    check_id INTEGER NOT NULL,
    status_code INTEGER NOT NULL,
    h1 VARCHAR(255) NOT NULL,
    title VARCHAR(255) NOT NULL, 
    description TEXT NOT NULL,
    created_at DATE NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_urls_table_url 
ON urls(url);

CREATE INDEX IF NOT EXISTS idx_url_checks_table_id 
ON url_checks(url_id);

CREATE INDEX IF NOT EXISTS idx_url_checks_table_check_date 
ON url_checks(created_at);


CREATE SEQUENCE IF NOT EXISTS check_id_seq START 1;


CREATE OR REPLACE FUNCTION set_check_id()
RETURNS TRIGGER AS $$
BEGIN
    NEW.check_id := COALESCE(
        (SELECT MAX(check_id) + 1
        FROM url_checks
        WHERE url_id = NEW.url_id),
        1
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;


DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger 
        WHERE tgname = 'before_insert_check_id'
    ) THEN
        CREATE TRIGGER before_insert_check_id
        BEFORE INSERT ON url_checks
        FOR EACH ROW
        EXECUTE FUNCTION set_check_id();
    END IF;
END;
$$;