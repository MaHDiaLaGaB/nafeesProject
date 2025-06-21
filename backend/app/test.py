from huggingface_hub import InferenceClient

client = InferenceClient(token="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", model="MadCodex/gemstones_image_detection", provider="auto")
with open("/Users/madcodex/nafeesProject/nafeesProject/ai_model/data/archive/train/Almandine/almandine_0.jpg","rb") as f:
    img_bytes = f.read()

# This should print [{"label": "...", "score": ...}]
print(client.image_classification(image=img_bytes, top_k=1))
