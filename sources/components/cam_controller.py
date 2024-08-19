from flask import Blueprint, request
import requests

cam_controller = Blueprint('cam_controller', __name__)
ROUTE_CONTROLLER = "http://192.168.1.102:8004/control"


@cam_controller.route('/cam_controller', methods=['POST'])
def fetch_data():
    if request.method == 'POST':
        try:
            data = request.get_json()
            # print(f"this is the control data {data}")
            control_command = data.get('control')
            response = requests.post(ROUTE_CONTROLLER, json={"control": control_command})  # Pass as JSON
            return f"Controller: {response.text}"  # Access response text
        except Exception as e:
            return f"Error in cam controller: {e}"
    else:
        return "Cam controller: not post request"
