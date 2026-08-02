-- 001_init.sql

CREATE TABLE tenants (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    subdomain TEXT UNIQUE NOT NULL,
    tax_id TEXT,
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now()
);

CREATE TABLE tenant_users (
    id SERIAL PRIMARY KEY,
    telegram_user_id BIGINT UNIQUE NOT NULL,
    tenant_id INT REFERENCES tenants(id) NOT NULL,
    name TEXT NOT NULL,
    role TEXT CHECK (role IN ('admin','manager','mechanic')) NOT NULL,
    active BOOLEAN DEFAULT true,
    email TEXT,
    password_hash TEXT,
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now()
);
CREATE INDEX ON tenant_users (telegram_user_id) WHERE active = true;
CREATE UNIQUE INDEX tenant_users_email_unique ON tenant_users (email) WHERE email IS NOT NULL;

CREATE TABLE pending_users (
    id SERIAL PRIMARY KEY,
    telegram_user_id BIGINT NOT NULL,
    username TEXT,
    name TEXT,
    tenant_hint TEXT,
    created_at TIMESTAMP DEFAULT now(),
    resolved BOOLEAN DEFAULT false
);
CREATE UNIQUE INDEX pending_users_telegram_id_unresolved
    ON pending_users (telegram_user_id) WHERE resolved = false;

CREATE TABLE customers (
    id SERIAL PRIMARY KEY,
    tenant_id INT REFERENCES tenants(id) NOT NULL,
    name TEXT,
    contact TEXT,
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now(),
    created_by_type TEXT,
    created_by_id INT,
    updated_by_type TEXT,
    updated_by_id INT,
    deleted_at TIMESTAMP
);

CREATE TABLE vehicles (
    id SERIAL PRIMARY KEY,
    tenant_id INT REFERENCES tenants(id) NOT NULL,
    plate TEXT NOT NULL,
    customer_id INT REFERENCES customers(id),
    brand TEXT,
    model TEXT,
    color TEXT,
    displacement TEXT,
    profile_complete BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now(),
    created_by_type TEXT,
    created_by_id INT,
    updated_by_type TEXT,
    updated_by_id INT,
    deleted_at TIMESTAMP
);
CREATE UNIQUE INDEX ON vehicles (tenant_id, plate) WHERE deleted_at IS NULL;

CREATE TABLE services (
    id SERIAL PRIMARY KEY,
    tenant_id INT REFERENCES tenants(id) NOT NULL,
    vehicle_id INT REFERENCES vehicles(id),
    mechanic_id INT REFERENCES tenant_users(id) NOT NULL,
    total_amount NUMERIC(10,2) NOT NULL,
    pending_amount NUMERIC(10,2) DEFAULT 0,
    description TEXT NOT NULL,
    performed_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now(),
    updated_by_type TEXT,
    updated_by_id INT,
    deleted_at TIMESTAMP,
    CHECK (pending_amount <= total_amount)
);

CREATE INDEX ON services (tenant_id, performed_at) WHERE deleted_at IS NULL;
CREATE INDEX ON services (tenant_id, vehicle_id) WHERE deleted_at IS NULL;
CREATE INDEX ON customers (tenant_id) WHERE deleted_at IS NULL;

CREATE TABLE activity_logs (
    id SERIAL PRIMARY KEY,
    tenant_id INT REFERENCES tenants(id) NOT NULL,
    actor_type TEXT NOT NULL,
    actor_id INT,
    action TEXT NOT NULL,
    entity TEXT NOT NULL,
    entity_id INT,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT now()
);
CREATE INDEX ON activity_logs (tenant_id, created_at DESC);
CREATE INDEX ON activity_logs (tenant_id, entity, entity_id);

-- Row Level Security
ALTER TABLE tenant_users ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_tenant_users ON tenant_users
    USING (tenant_id = current_setting('app.current_tenant')::INT);

ALTER TABLE customers ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_customers ON customers
    USING (tenant_id = current_setting('app.current_tenant')::INT);

ALTER TABLE vehicles ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_vehicles ON vehicles
    USING (tenant_id = current_setting('app.current_tenant')::INT);

ALTER TABLE services ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_services ON services
    USING (tenant_id = current_setting('app.current_tenant')::INT);

ALTER TABLE activity_logs ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_activity_logs ON activity_logs
    USING (tenant_id = current_setting('app.current_tenant')::INT);