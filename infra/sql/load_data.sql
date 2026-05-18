COPY businesses (id, name, business_type, description, neighborhood, metadata, created_at, updated_at)
FROM '/docker-entrypoint-initdb.d/businesses.csv'
DELIMITER ','
CSV HEADER;

COPY offers (id, business_id, title, description, starts_at, ends_at, price_amount, metadata, created_at, updated_at)
FROM '/docker-entrypoint-initdb.d/offers.csv'
DELIMITER ','
CSV HEADER;