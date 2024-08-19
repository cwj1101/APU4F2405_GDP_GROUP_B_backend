from flask import Flask
from flask_cors import CORS
# from threading import Thread, Event
# import requests
# import time
import os
# from ..ai.real_time_temperature_prediction import run_temp_ai
from.gas_detection import create_table_gas_detection, insert_table_gas_detection


# ESP32IP = "192.168.4.1"  # Default IP when using WiFi.softAP
# # latest_data = None
# stop_event = Event()
#
#
# def gas_detection_thread():
#     # global latest_data
#     with current_app.app_context():
#         while not stop_event.is_set():
#             try:
#                 run_temp_ai()
#                 # response = requests.get(f"http://{ESP32IP}/sensors")
#                 # response.raise_for_status()  # Check for HTTP errors
#                 # if response.status_code == 200:
#                 #     print(response.json())
#                 #     create_table_gas_detection()
#                 #     insert_table_gas_detection(response)
#
#
#             except requests.exceptions.RequestException as e:
#                 print(f"Error fetching data: {e}")
#             time.sleep(1)  # Polling interval (5 seconds)


def create_app():
    app = Flask(__name__)
    app.config.from_object(__name__)
    CORS(app, resources={r"/*": {'origins': "*"}})
    app.config['SECRET_KEY'] = '8b50274970c5403d9e807c607980ed77'
    app.config['DATABASE_URL'] = os.getenv('DATABASE_URL')

    from .auth import auth
    from .dashboard import dashboard
    from .gas_detection import gas_detection
    from .cam_controller import cam_controller
    # from DB_connection import DB_connection
    #
    # app.register_blueprint(DB_connection)
    app.register_blueprint(auth, url_prefix='/')
    app.register_blueprint(dashboard, url_prefix='/')
    app.register_blueprint(gas_detection, url_prefix='/')
    app.register_blueprint(cam_controller, url_prefix='/')

    return app


# data_thread = Thread(target=gas_detection_thread).start()
