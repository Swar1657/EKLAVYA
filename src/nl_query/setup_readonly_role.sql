-- Run with psql -v readonly_password='a-strong-secret' -f setup_readonly_role.sql.
-- The password is a psql variable, never stored in this repository.
CREATE ROLE eklavya_readonly LOGIN PASSWORD 'readonly_password';
GRANT CONNECT ON DATABASE eklavya TO eklavya_readonly;
GRANT USAGE ON SCHEMA public TO eklavya_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO eklavya_readonly;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO eklavya_readonly;
