import numpy as np
import faiss
from incidents.models import IncidentEmbedding
from incidents.services.embedding_service import get_embedding, model


def normalize_vectors(vectors):
    """
    Vectors ko normalize karta hai taaki Cosine Similarity kaam kare
    (FAISS L2 index ke saath normalized vectors = Cosine Similarity)
    """
    faiss.normalize_L2(vectors)
    return vectors


def find_similar_incidents_db(target_text, top_k=3):
    """
    FAISS ka use karke DB me se similar incidents dhoondta hai.
    (Previous 'cosine_similarity' logic se 100x fast hai)
    """
    # 1. Target ka embedding nikalo
    target_vector = np.array([get_embedding(target_text)]).astype('float32')
    normalize_vectors(target_vector)

    # 2. DB se saare vectors fetch karo
    embeddings = IncidentEmbedding.objects.select_related("incident")
    if not embeddings.exists():
        return []

    # Vectors ko numpy array me convert karo
    db_vectors = [e.vector for e in embeddings]
    db_vectors_np = np.array(db_vectors).astype('float32')
    normalize_vectors(db_vectors_np)

    incidents = [e.incident for e in embeddings]

    # 3. FAISS Index banao (Inner Product for Cosine Similarity)
    dimension = db_vectors_np.shape[1]
    index = faiss.IndexFlatIP(dimension)
    index.add(db_vectors_np)

    # 4. Search karo
    distances, indices = index.search(target_vector, top_k)

    # 5. Results format karo
    results = []
    for i in range(top_k):
        idx = indices[0][i]
        score = distances[0][i]
        if idx != -1 and idx < len(incidents):
            results.append((incidents[idx], float(score)))

    return results


def filter_relevant_logs(query_text, log_lines, top_k=10):
    """
    Log lines me se sirf wo lines nikalta hai jo query (error) se match karti hain.
    Ye RAG (Retrieval Augmented Generation) ka core part hai.
    """
    if not log_lines:
        return []

    # Agar logs bahut kam hain, toh filter karne ki zaroorat nahi
    if len(log_lines) <= top_k:
        return log_lines

    # 1. Saari log lines ka embedding ek saath nikalo (Batch Processing)
    # Note: 'model' ko direct use kar rahe hain speed ke liye
    try:
        line_vectors = model.encode(log_lines)
        line_vectors = np.array(line_vectors).astype('float32')
        normalize_vectors(line_vectors)
    except Exception as e:
        print(f"Error embedding logs: {e}")
        return log_lines[:top_k]  # Fallback

    # 2. Query (Incident Title/Desc) ka embedding
    query_vector = np.array([get_embedding(query_text)]).astype('float32')
    normalize_vectors(query_vector)

    # 3. FAISS Index banao
    dimension = line_vectors.shape[1]
    index = faiss.IndexFlatIP(dimension)
    index.add(line_vectors)

    # 4. Search karo sabse relevant lines
    distances, indices = index.search(query_vector, top_k)

    # 5. Original lines wapas return karo
    relevant_lines = []
    found_indices = sorted(indices[0])  # Sort indices to keep logs in original order (time order)

    for idx in found_indices:
        if idx != -1 and idx < len(log_lines):
            relevant_lines.append(log_lines[idx])

    return relevant_lines