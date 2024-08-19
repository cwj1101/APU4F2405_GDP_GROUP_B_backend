CREATE_USER_INFO_TABLE = """
    CREATE TABLE IF NOT EXISTS user_info (
        user_id SERIAL PRIMARY KEY,
        user_name VARCHAR,
        password VARCHAR,
        access_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
"""
INSERT_USER_INFO = "INSERT INTO public.user_info (user_name, password, email) values (%s, %s, %s) RETURNING user_id"

SELECT_USER_INFO = "SELECT * FROM public.user_info"

SELECT_USER_INFO_BY_USERNAME = "SELECT * FROM public.user_info WHERE email = %s"
