
from pathlib import Path
import joblib

MODEL_FILE = (
    Path(__file__).resolve().parent
    / "incident_classifier.joblib"
)

_model = None


def get_model():
    global _model

    if _model is None:
        if not MODEL_FILE.exists():
            raise FileNotFoundError(
                "Model not found. Run: python -m ml.train"
            )

        _model = joblib.load(MODEL_FILE)

    return _model


def classify_incident(text):
    if not text or not text.strip():
        raise ValueError("Incident text cannot be empty")

    model = get_model()

    category = str(model.predict([text])[0])
    probabilities = model.predict_proba([text])[0]
    confidence = float(max(probabilities))

    return {
        "category": category,
        "confidence": round(confidence, 4)
    }


if __name__ == "__main__":
    example = (
        "My company VPN is not connecting "
        "and I have an urgent client meeting"
    )

    print(classify_incident(example))
