import pandas as pd
import numpy as np
from DB_connection import get_db_connection
import time
import os
from flask import jsonify, session
from scipy.signal import savgol_filter
from datetime import datetime, timedelta
from collections import deque
from sources.scripts.gas_script import SELECT_GAS_DATA_5_MIN_AGO, SELECT_GAS_DATA, CREATE_GAS_AI_TABLE, \
    CREATE_GAS_AI_PARTITION_TABLE, INSERT_TEMPERATURE_AI


# parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# model_path = os.path.join(parent_dir, 'best_model.keras')
# model1 = models.load_model(model_path)


temp = None


def get_float_data(his_gas_data):
    global temp
    print("HELLO 2")
    df = pd.DataFrame(his_gas_data)
    df.index = pd.to_datetime(df['timestamp'], format='%Y/%m/%d %H:%M:%S')
    df['temperature'] = pd.to_numeric(df['temperature'], errors='coerce')  # Convert to numeric
    temp = df['temperature']
    print(f"this is temp {temp}")
    print(f"Temperature data:\n{temp}")
    return df['temperature'].tolist()  # Return list of floats


def custom_filter(window_length, var):
    x = np.arange(len(var))
    if len(var) > window_length and window_length % 2 != 0:
        v_smooth = savgol_filter(var, window_length, 4)
        adjustment = np.mean(var) - np.mean(v_smooth)
        v_smooth_adjusted = v_smooth + adjustment
        return v_smooth_adjusted
    else:
        print("Error: window_length must be less than the length of V and an odd number")
        return None


def df_to_x_y(data, window_size):
    x, y = [], []
    for i in range(len(data) - window_size):
        row = [[r] for r in data[i:i + window_size]]
        x.append(row)
        label = data[i + window_size]
        y.append(label)
    return np.array(x), np.array(y)


def temp_smooth(var):
    global input_train_min, input_train_max, temp_train_min, temp_train_max
    if var is not None:
        print("HELLO 3")
        # print(f"this is var{var}")
        temp_smooth_input = custom_filter(31, var)
        if temp_smooth_input is not None:
            X, y = df_to_x_y(temp_smooth_input, 5)
            if X.size > 0 and y.size > 0:
                X_train1, y_train1 = X[:93], y[:93]
                input_train_min = np.min(X_train1[:, :, :])
                input_train_max = np.max(X_train1[:, :, :])
                temp_train_min = np.min(y_train1[:])
                temp_train_max = np.max(y_train1[:])
                print("done temp smooth")
            else:
                print("Error in df_to_x_y")
        else:
            print("Error in custom_filter")
    else:
        print("Temp is not set")


def preprocessX(var):
    var[:, :, :] = (var[:, :, :] - input_train_min) / (input_train_max - input_train_min)
    return var


def inverse_preprocessy(y_normalized, pow_train_min, pow_train_max):
    return y_normalized * (pow_train_max - pow_train_min) + pow_train_min


new_data = deque([{"temperature": 31.9}, {"temperature": 30.9}, {"temperature": 32.1}, {"temperature": 32.0},
                  {"temperature": 31.5}], maxlen=5)


def run_temperature_ai(temp_new, user_id, model):
    global temp
    # from main import model
    print("HELLO 4")
    # while True:
    print("HELLO 4 while")
    start_time = time.time()
    temperature_list = [item['temperature'] for item in new_data]

    # Log the new data being processed
    print(f"Processing new data: {new_data}")

    if new_data:
        temp = np.append(temp, [item['temperature'] for item in new_data])
        X_new = preprocessX(np.array(temperature_list).reshape(1, 5, 1))

        # Log the new input for prediction
        print(f"New input for prediction: {X_new}")

        new_prediction = model.predict(X_new).flatten()

        # Log the prediction result
        print(f"Prediction result: {new_prediction}")

        new_prediction_original = inverse_preprocessy(new_prediction, temp_train_min, temp_train_max)
        timestamp_now = datetime.now()
        future_timestamp = timestamp_now + timedelta(minutes=5)
        timestamp_new = future_timestamp.strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp_new}] Predicted Temperature: {new_prediction_original[0]} °C")

        # Ensure temperature is logged correctly before insertion
        print(f"Preparing to insert temperature: {float(new_prediction_original[0])}")
        inset_ai_temperature({"temperature": float(new_prediction_original[0])})
    else:
        timestamp_new = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp_new}] Receiving Data...")

    elapsed_time = time.time() - start_time
    sleep_time = max(300 - elapsed_time, 0)
    time.sleep(sleep_time)

    # Log user ID and data after each cycle
    print(f"User ID in AI thread: {user_id}")
    new_data.append({"temperature": temp_new[0]})
    print(f"New data after append: {new_data}")



def fetch_data():
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute(SELECT_GAS_DATA)
            gas_data = cursor.fetchall()
            column_names = [desc[0] for desc in cursor.description]
            gas_data_list = [dict(zip(column_names, row)) for row in gas_data]
        return gas_data_list  # Return list of dictionaries
    except Exception as e:
        print(e)
        return jsonify({"error": str(e)}), 500


def fetch_data_5min():
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute(SELECT_GAS_DATA_5_MIN_AGO, ("2024-07-20",))
            gas_data = cursor.fetchall()
            column_names = [desc[0] for desc in cursor.description]
            gas_data_list = [dict(zip(column_names, row)) for row in gas_data]
        return gas_data_list
    except Exception as e:
        print(e)
        return jsonify({"error": str(e)}), 500


def run_temp_ai(user_id):
    from main import model

    print(f"this is user id in ai thread: {user_id}")
    create_ai_temperature_table()
    data = fetch_data()
    data_5 = fetch_data_5min()
    temperature_data = get_float_data(data)
    temp_array = np.array(temperature_data)
    temp_smooth(temp_array)

    temperature_data_5 = get_float_data(data_5)
    temp_array = np.array(temperature_data_5)
    run_temperature_ai(temp_array, user_id, model)


def create_ai_temperature_table():
    conn = get_db_connection()
    print("HELLO 1")
    with conn.cursor() as cursor:
        try:
            cursor.execute(CREATE_GAS_AI_TABLE)
            cursor.execute(CREATE_GAS_AI_PARTITION_TABLE)
            conn.commit()
        except Exception as e:
            conn.rollback()
            print(f"Error: {e}")


def inset_ai_temperature(data):
    temperature = data.get("temperature")
    print(f"this is temperature {temperature}")
    conn = get_db_connection()
    with conn.cursor() as cursor:
        try:
            cursor.execute(INSERT_TEMPERATURE_AI, (1, temperature))
            conn.commit()
        except Exception as e:
            conn.rollback()
            print(f"Error: {e}")
