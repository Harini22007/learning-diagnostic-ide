import httpx

client = httpx.Client(base_url="http://127.0.0.1:8000")

# 1. Test health
res = client.get("/health")
print("Health status:", res.status_code, res.json())

# 2. Test analyze without API key (expect 400 with helpful message)
res = client.post("/analyze-material", json={"text": "Photosynthesis is the process of converting light into energy."})
print("Analyze status without key:", res.status_code, res.json())
