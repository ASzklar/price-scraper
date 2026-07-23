-- Modelo dimensional para Price Scraper
-- Ejecutar en Supabase SQL Editor

-- ============================================================
-- DIMENSIONES
-- ============================================================

CREATE TABLE IF NOT EXISTS dim_producto (
    id        SERIAL PRIMARY KEY,
    nombre    TEXT NOT NULL UNIQUE,
    marca     TEXT NOT NULL CHECK (marca IN ('not', 'vegetalex', 'felices_las_vacas'))
);

CREATE TABLE IF NOT EXISTS dim_supermercado (
    id     SERIAL PRIMARY KEY,
    nombre TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS dim_fecha (
    id          SERIAL PRIMARY KEY,
    fecha       DATE    NOT NULL UNIQUE,
    anio        INTEGER NOT NULL,
    mes         INTEGER NOT NULL,
    dia         INTEGER NOT NULL,
    dia_semana  INTEGER NOT NULL  -- 0=lunes, 6=domingo
);

-- ============================================================
-- TABLA DE HECHOS
-- ============================================================

CREATE TABLE IF NOT EXISTS fact_precios (
    id               SERIAL PRIMARY KEY,
    fecha_id         INTEGER NOT NULL REFERENCES dim_fecha(id),
    producto_id      INTEGER NOT NULL REFERENCES dim_producto(id),
    supermercado_id  INTEGER NOT NULL REFERENCES dim_supermercado(id),
    precio           NUMERIC(12, 2),
    UNIQUE (fecha_id, producto_id, supermercado_id)
);

-- ============================================================
-- ÍNDICES para consultas frecuentes del dashboard
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_fact_fecha     ON fact_precios (fecha_id);
CREATE INDEX IF NOT EXISTS idx_fact_producto  ON fact_precios (producto_id);
CREATE INDEX IF NOT EXISTS idx_fact_super     ON fact_precios (supermercado_id);

-- ============================================================
-- SEED: supermercados (fijos, nunca cambian)
-- ============================================================

INSERT INTO dim_supermercado (nombre) VALUES
    ('carrefour'),
    ('coope'),
    ('coto'),
    ('dia'),
    ('disco'),
    ('vea')
ON CONFLICT (nombre) DO NOTHING;
