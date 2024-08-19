import os
from keras import models

_model = None  # Initialize model to None


def load_model():
    global _model
    if _model is None:
        print("Model is loading...")
        parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        model_path = os.path.join(parent_dir, 'best_model.keras')
        _model = models.load_model(model_path)
    return _model
