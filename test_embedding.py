from incidents.services.embedding_service import get_embedding

vector = get_embedding("Database connection timeout error")

print(len(vector))
print(vector[:5])

from incidents.services.text_generation import generate_root_cause

result = generate_root_cause(
    "Explain the root cause of database timeout during high traffic"
)

print(result)


from incidents.services.similarity_service import find_similar_texts

incident = "Database connection timeout error"

past_incidents = [
    "Database timeout during peak traffic",
    "User login failed due to wrong password",
    "API timeout error from payment service",
    "Server restarted successfully"
]

results = find_similar_texts(incident, past_incidents)

for text, score in results:
    print(text, "=>", round(score, 2))
