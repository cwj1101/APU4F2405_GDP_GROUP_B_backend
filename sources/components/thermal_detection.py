from flask import jsonify, Blueprint, request, session
from DB_connection import get_db_connection
from sources.scripts.thermal_script import CREATE_THERMAL_DETECTION_TABLE, CREATE_THERMAL_DETECTION_PARTITION_TABLE, \
    SELECT_THERMAL_DETECTION, INSERT_THERMAL_DETECTION

thermal_detection = Blueprint('thermal_detection', __name__)


@thermal_detection.route('/fetch-thermal-data', methods=['POST'])
def fetch_data():
    if request.method == 'POST':
        try:
            data = request.get_json()
            date = data.get("timestamp")
            conn = get_db_connection()
            with conn.cursor() as cursor:
                cursor.execute(SELECT_THERMAL_DETECTION, (date,))
                gas_data = cursor.fetchall()
                column_names = [desc[0] for desc in cursor.description]
                gas_data_list = [
                    dict(zip(column_names, row)) for row in gas_data
                ]
            return jsonify({"gasData": gas_data_list}), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500


def create_table_thermal_detection():
    conn = get_db_connection()
    with conn.cursor() as cursor:
        try:
            cursor.execute(CREATE_THERMAL_DETECTION_TABLE)
            cursor.execute(CREATE_THERMAL_DETECTION_PARTITION_TABLE)
            conn.commit()
        except Exception as e:
            conn.rollback()
            print(f"Error: {e}")


def insert_table_thermal_detection(response):
    if response.json():
        data = response.json()  # Parse JSON data
        thermal_temperature = data[0]['thermal_temp']
        print("Fetched data:", thermal_temperature)
        conn = get_db_connection()
        with conn.cursor() as cursor:
            try:
                cursor.execute(INSERT_THERMAL_DETECTION, (1, thermal_temperature))
                conn.commit()
            except Exception as e:
                conn.rollback()
                print(f"Error: {e}")
    else:
        return "no data in thermal cam"
