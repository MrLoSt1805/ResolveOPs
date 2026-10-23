
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

DUPLICATE_THRESHOLD = 0.65


def check_duplicate(new_text, existing_incidents):
    """
    existing_incidents must be a list of dictionaries:
    [
        {"id": 1, "description": "VPN is not connecting"}
    ]
    """

    if not existing_incidents:
        return {
            "is_duplicate": False,
            "duplicate_of": None,
            "similarity": 0.0
        }

    descriptions = [
        item["description"]
        for item in existing_incidents
    ]

    documents = descriptions + [new_text]

    vectorizer = TfidfVectorizer(
        lowercase=True,
        ngram_range=(1, 2),
        stop_words="english"
    )

    vectors = vectorizer.fit_transform(documents)

    similarities = cosine_similarity(
        vectors[-1],
        vectors[:-1]
    )[0]

    best_index = int(similarities.argmax())
    best_score = float(similarities[best_index])

    return {
        "is_duplicate": best_score >= DUPLICATE_THRESHOLD,
        "duplicate_of": (
            existing_incidents[best_index]["id"]
            if best_score >= DUPLICATE_THRESHOLD
            else None
        ),
        "similarity": round(best_score, 4)
    }


if __name__ == "__main__":
    existing = [
        {
            "id": 101,
            "description": "Corporate VPN is currently unavailable"
        },
        {
            "id": 102,
            "description": "Laptop keyboard is broken"
        }
    ]

    print(check_duplicate(
        "Corporate VPN is currently unavailable",
        existing
    ))
