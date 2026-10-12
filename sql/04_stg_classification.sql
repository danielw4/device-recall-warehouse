CREATE OR REPLACE TABLE stg_classification AS
SELECT * REPLACE (
    trim(product_code) AS product_code,
    nullif(trim(device_name), '') AS device_name,
    nullif(trim(device_class), '') AS device_class,
    nullif(trim(medical_specialty), '') AS medical_specialty,
    nullif(trim(medical_specialty_description), '') AS medical_specialty_description,
    nullif(trim(regulation_number), '') AS regulation_number
)
FROM raw.classification;
