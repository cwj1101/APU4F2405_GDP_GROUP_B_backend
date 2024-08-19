from datetime import datetime

now = datetime.utcnow()
month = now.month
year = now.year
date = now.date()
start_date = f'{year}-{month:02d}-01'
if month == 12:
    end_date = f'{year + 1}-01-01'
else:
    end_date = f'{year}-{month + 1:02d}-01'

partition_table_name = f'gas_data_{year}_{month:02d}'

CREATE_GAS_DETECTION_TABLE = '''
CREATE TABLE IF NOT EXISTS gas_detection (
    id SERIAL,
    user_id INT,
    mq2 INT,
    mq3 INT,
    mq5 INT,
    mq9 INT,
    temperature FLOAT,
    humidity FLOAT,
    dallasTemp FLOAT,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    mq2_alert INT,
    mq3_alert INT,
    mq5_alert INT,
    mq9_alert INT,
    PRIMARY KEY (id, timestamp),
    FOREIGN KEY (user_id) REFERENCES user_info(user_id) ON DELETE CASCADE
    ) PARTITION BY RANGE (timestamp);
'''

CREATE_GAS_DETECTION_PARTITION_TABLE = f''' 
    CREATE TABLE IF NOT EXISTS {partition_table_name} PARTITION OF gas_detection
    FOR VALUES FROM ('{start_date}') TO ('{end_date}');
'''

CREATE_GAS_AI_TABLE = '''
    CREATE TABLE IF NOT EXISTS temperature_ai (
        id SERIAL,
        user_id INT,
        temperature FLOAT,
        timestamp TIMESTAMPTZ DEFAULT NOW(),
        PRIMARY KEY (id, user_id, timestamp),
        FOREIGN KEY (user_id) REFERENCES user_info(user_id) ON DELETE CASCADE
    );
'''

CREATE_GAS_AI_PARTITION_TABLE = f''' 
    CREATE TABLE IF NOT EXISTS {partition_table_name} PARTITION OF temperature_ai
    FOR VALUES FROM ('{start_date}') TO ('{end_date}');
'''

INSERT_GAS_DETECTION = '''
    INSERT INTO gas_detection (user_id ,mq2, mq3, mq5, mq9, temperature, humidity, dallasTemp, mq2_alert,
     mq3_alert, mq5_alert, mq9_alert)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
'''

INSERT_TEMPERATURE_AI = '''
    INSERT INTO temperature_ai (user_id,temperature)
    VALUES (%s,%s)
'''

SELECT_GAS_DATA = f'''
    SELECT * FROM public.gas_detection
'''

SELECT_GAS_DATA_BY_DATE = '''
    SELECT * FROM public.gas_detection where timestamp::date = %s::date
'''

SELECT_GAS_DATA_5_MIN_AGO = '''
    WITH recent AS (
        SELECT MAX(timestamp) AS most_recent_time
        FROM public.gas_detection
    )
    SELECT *
    FROM public.gas_detection
    WHERE timestamp >= (SELECT most_recent_time - INTERVAL '5 minutes' FROM recent)
    ORDER BY timestamp ASC
    LIMIT 1;
'''

SELECT_GAS_DATA_5_MIN_INTERVAL = f'''
   WITH min_timestamp_cte AS (
    -- Calculate the minimum timestamp in your dataset
    SELECT
        MIN(timestamp) AS min_timestamp
    FROM
        gas_detection
    WHERE
        timestamp >= %s::date
    ),
    ranked_data AS (
        SELECT
            gd.id,
            gd.mq2,
            gd.mq3,
            gd.mq5,
            gd.mq9,
            gd.temperature,
            gd.humidity,
            gd.dallastemp,
            gd.timestamp,
            gd.user_id,
            -- Use the calculated minimum timestamp from the CTE
            date_bin(
                '5 minutes',
                gd.timestamp,
                min_timestamp_cte.min_timestamp
            ) AS interval,
            ROW_NUMBER() OVER (
                PARTITION BY date_bin('5 minutes', gd.timestamp, min_timestamp_cte.min_timestamp)
                ORDER BY gd.timestamp
            ) AS row_num
        FROM
            gas_detection gd
        CROSS JOIN
            min_timestamp_cte
        WHERE
            gd.timestamp::date = %s::date
    )
    SELECT
        id,
        mq2,
        mq3,
        mq5,
        mq9,
        temperature,
        humidity,
        dallastemp,
        timestamp,
        user_id,
        interval
    FROM
        ranked_data
    WHERE
        row_num = 1
    ORDER BY
        interval;
'''




SELECT_TEMPERATURE_AI = '''
    SELECT *
    FROM public.temperature_ai WHERE timestamp::date = %s
'''
