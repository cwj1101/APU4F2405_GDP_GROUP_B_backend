from datetime import datetime

now = datetime.utcnow()
month = now.month
year = now.year
start_date = f'{year}-{month:02d}-01'
if month == 12:
    end_date = f'{year + 1}-01-01'
else:
    end_date = f'{year}-{month + 1:02d}-01'

partition_table_name = f'thermal_data_{year}_{month:02d}'

CREATE_THERMAL_DETECTION_TABLE = '''
CREATE TABLE IF NOT EXISTS thermal_detection (
    id SERIAL,
    user_id INT,
    thermal_temperature FLOAT,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (id, timestamp),
    FOREIGN KEY (user_id) REFERENCES user_info(user_id) ON DELETE CASCADE
    ) PARTITION BY RANGE (timestamp);
'''

CREATE_THERMAL_DETECTION_PARTITION_TABLE = f''' 
    CREATE TABLE IF NOT EXISTS {partition_table_name} PARTITION OF thermal_detection
    FOR VALUES FROM ('{start_date}') TO ('{end_date}');
'''

INSERT_THERMAL_DETECTION = '''
    INSERT INTO thermal_detection (user_id, thermal_temperature)
    VALUES (%s, %s)
'''

SELECT_THERMAL_DETECTION = '''
    SELECT * FROM public.thermal_detection WHERE timestamp::date = %s
'''