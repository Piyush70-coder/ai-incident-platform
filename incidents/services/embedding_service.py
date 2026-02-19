from sentence_transformers import SentenceTransformer
from incidents.models import IncidentEmbedding

# Model ek baar load hoga
model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")


def get_embedding(text: str):
    """
    Text → vector (numbers)
    DB friendly list return karta hai
    """
    return model.encode(text).tolist()


def save_incident_embedding(incident, text: str):
    """
    Incident + text → embedding generate → DB me save
    """
    vector = get_embedding(text)

    IncidentEmbedding.objects.update_or_create(
        incident=incident,
        defaults={"vector": vector}
    )

    return vector
