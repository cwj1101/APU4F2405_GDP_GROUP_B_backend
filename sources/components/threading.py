from threading import Thread, Event, Lock
import time
import requests
from ..ai.real_time_temperature_prediction import run_temp_ai
from .gas_detection import create_table_gas_detection, insert_table_gas_detection
from .thermal_detection import create_table_thermal_detection, insert_table_thermal_detection
from .globals import global_user_id

ESP32IP = "192.168.4.1"  # Default IP when using WiFi.softAP
ROUTER_THERMAL_DATA = "http://192.168.1.102:8000/thermal_data"
ROUTER_GAS_DATA = "http://192.168.1.102:8003/canbusgan"

stop_event = Event()
data_lock_1 = Lock()  # For temp_ai_thread
data_lock_2 = Lock()  # For gas_module
data_lock_3 = Lock()  # For thermal_data


data_thread_1 = None  # temp_ai_thread
data_thread_2 = None  # gas_module
data_thread_3 = None  # thermal data


def temp_ai_thread(app):
    with app.app_context():
        while not stop_event.is_set():
            try:
                with data_lock_1:
                    run_temp_ai(global_user_id)
            except requests.exceptions.RequestException as e:
                print(f"Error fetching temp ai data: {e}")
            time.sleep(1)


def gas_module(app):
    with app.app_context():
        while not stop_event.is_set():
            try:
                response = requests.get(ROUTER_GAS_DATA)
                response.raise_for_status()
                if response.status_code == 200:
                    with data_lock_2:
                        print(response.json())
                        create_table_gas_detection()
                        insert_table_gas_detection(response)
            except requests.exceptions.RequestException as e:
                print(f"Error fetching data: {e}")
            time.sleep(1)


def thermal_data(app):
    with app.app_context():
        while not stop_event.is_set():
            try:
                response = requests.get(ROUTER_THERMAL_DATA)
                response.raise_for_status()
                print(f"this is response {response}")
                if response.status_code == 200:
                    with data_lock_3:
                        create_table_thermal_detection()
                        insert_table_thermal_detection(response)
                        print(f"this is temperature from cam: {response.json()}")
            except requests.exceptions.RequestException as e:
                print(f"Error fetching data: {e}")
            time.sleep(1)


def start_background_threads(app):
    global data_thread_1, data_thread_2, data_thread_3
    print(f"this user data {global_user_id}")
    # data_thread_1 = Thread(target=temp_ai_thread, args=(app,))
    # data_thread_1.start()
    # data_thread_2 = Thread(target=gas_module, args=(app,))
    # data_thread_2.start()
    # data_thread_3 = Thread(target=thermal_data, args=(app,))
    # data_thread_3.start()


def stop_background_threads():
    stop_event.set()
    if data_thread_1 and data_thread_1.is_alive():
        data_thread_1.join()
    if data_thread_2 and data_thread_2.is_alive():
        data_thread_2.join()
    if data_thread_3 and data_thread_3.is_alive():
        data_thread_3.join()
