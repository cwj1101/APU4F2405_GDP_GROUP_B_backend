from flask import jsonify, Blueprint, request, session
from DB_connection import get_db_connection
from sources.scripts.gas_script import CREATE_GAS_DETECTION_TABLE, CREATE_GAS_DETECTION_PARTITION_TABLE, \
    INSERT_GAS_DETECTION, SELECT_GAS_DATA_BY_DATE, SELECT_TEMPERATURE_AI, SELECT_GAS_DATA_5_MIN_INTERVAL
# from. import latest_data  # Import the global latest_data

gas_detection = Blueprint('gas_detection', __name__)


@gas_detection.route('/fetch-gas-data', methods=['POST'])
def fetch_data():
    if request.method == 'POST':
        try:
            data = request.get_json()
            date = data.get("timestamp")
            print(f"this is date{date}")
            conn = get_db_connection()
            with conn.cursor() as cursor:
                cursor.execute(SELECT_GAS_DATA_BY_DATE, (date,))
                gas_data = cursor.fetchall()
                column_names = [desc[0] for desc in cursor.description]
                gas_data_list = [
                    dict(zip(column_names, row)) for row in gas_data
                ]
            return jsonify({"gasData": gas_data_list}), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500


@gas_detection.route('/fetch-temp-ai', methods=['POST'])
def fetch_ai():
    if request.method == 'POST':
        try:
            data = request.get_json()
            date = data.get("timestamp")
            conn = get_db_connection()
            with conn.cursor() as cursor:
                cursor.execute(SELECT_TEMPERATURE_AI, (date,))
                gas_data = cursor.fetchall()
                column_names = [desc[0] for desc in cursor.description]
                gas_data_list = [
                    dict(zip(column_names, row)) for row in gas_data
                ]
            return jsonify({"temp_ai": gas_data_list}), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500


def create_table_gas_detection():
    conn = get_db_connection()
    with conn.cursor() as cursor:
        try:
            cursor.execute(CREATE_GAS_DETECTION_TABLE)
            cursor.execute(CREATE_GAS_DETECTION_PARTITION_TABLE)
            conn.commit()
        except Exception as e:
            conn.rollback()
            print(f"Error: {e}")


def insert_table_gas_detection(response):
    data = response.json()  # Parse JSON data
    print("Fetched data:", data)
    mq2 = data.get("MQ2")
    mq3 = data.get("MQ3")
    mq5 = data.get("MQ5")
    mq9 = data.get("MQ9")
    temperature = data.get("temperature")
    humidity = data.get("humidity")
    dallas_temp = data.get("DallasTemp")
    mq2_alert = data.get("mq2_alert")
    mq3_alert = data.get("mq3_alert")
    mq5_alert = data.get("mq5_alert")
    mq9_alert = data.get("mq9_alert")

    conn = get_db_connection()
    with conn.cursor() as cursor:
        try:
            cursor.execute(INSERT_GAS_DETECTION, (1, mq2, mq3, mq5, mq9, temperature, humidity, dallas_temp,mq2_alert,
                                                  mq3_alert, mq5_alert, mq9_alert))
            conn.commit()
        except Exception as e:
            conn.rollback()
            print(f"Error: {e}")


@gas_detection.route('/fetch-5min-interval', methods=['POST'])
def select_data_5min_interval():
    if request.method == 'POST':
        try:
            data = request.get_json()
            start_date = data.get("timestamp")
            end_date = data.get("timestamp")
            print(f"this is data {data}")
            print(f"this is time {data}")
            conn = get_db_connection()
            with conn.cursor() as cursor:
                cursor.execute(SELECT_GAS_DATA_5_MIN_INTERVAL, (start_date, end_date))
                gas_data = cursor.fetchall()
                column_names = [desc[0] for desc in cursor.description]
                gas_data_list = [
                    dict(zip(column_names, row)) for row in gas_data
                ]
                print(gas_data_list)
            return jsonify({"intervalData": gas_data_list}), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500
