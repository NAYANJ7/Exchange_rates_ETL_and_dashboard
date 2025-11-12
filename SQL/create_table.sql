CREATE TABLE IF NOT EXISTS exchange_rates (
    id SERIAL PRIMARY KEY,
    base_currency VARCHAR(10) NOT NULL,
    target_currency VARCHAR(10) NOT NULL,
    rate NUMERIC(18,8) NOT NULL,
    fetched_at TIMESTAMP WITH TIME ZONE NOT NULL,
    source VARCHAR(255)
);

CREATE INDEX IF NOT EXISTS idx_exchange_rates_fetched_at ON exchange_rates(fetched_at);
CREATE INDEX IF NOT EXISTS idx_exchange_rates_target ON exchange_rates(target_currency);
