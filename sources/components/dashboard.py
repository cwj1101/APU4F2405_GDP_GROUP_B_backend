import logging
# import DB_connection
from flask import Blueprint, jsonify, request, current_app

# Configure logging
logging.basicConfig(level=logging.DEBUG)

dashboard = Blueprint('dashboard', __name__)

