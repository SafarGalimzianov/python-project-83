DROP TABLE IF EXISTS urls CASCADE;
DROP TABLE IF EXISTS url_checks CASCADE;


CREATE TABLE IF NOT EXISTS urls(
    id SERIAL PRIMARY KEY,
    url VARCHAR(255) NOT NULL,
    creation_date DATE NOT NULL
);

CREATE TABLE IF NOT EXISTS url_checks(
    id SERIAL PRIMARY KEY,
    url_id INTEGER REFERENCES urls_table(id) NOT NULL,
    check_id INTEGER NOT NULL,
    response_code INTEGER NOT NULL,
    h1_content TEXT NOT NULL,
    title_content TEXT NOT NULL, 
    description_content TEXT NOT NULL,
    check_date DATE NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_urls_table_url 
ON urls_table(url);

CREATE INDEX IF NOT EXISTS idx_checks_table_id 
ON checks_table(url_id);

CREATE INDEX IF NOT EXISTS idx_checks_table_check_date 
ON checks_table(check_date);


CREATE SEQUENCE IF NOT EXISTS check_id_seq START 1;


CREATE OR REPLACE FUNCTION set_check_id()
RETURNS TRIGGER AS $$
BEGIN
    NEW.check_id := COALESCE(
        (SELECT MAX(check_id) + 1
        FROM checks_table
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
        BEFORE INSERT ON checks_table
        FOR EACH ROW
        EXECUTE FUNCTION set_check_id();
    END IF;
END;
$$;