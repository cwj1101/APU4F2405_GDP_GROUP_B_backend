from dotenv import load_dotenv
from sources.components import create_app
from sources.components.threading import start_background_threads, stop_background_threads
from sources.components.model_loader import load_model

load_dotenv()
model = load_model()  # Initialize the model here

if __name__ == "__main__":
    app = create_app()
    try:
        start_background_threads(app)  # Pass the model to threads
        app.run(debug=True, use_reloader=False)
    finally:
        stop_background_threads()
