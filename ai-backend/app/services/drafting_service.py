"""Drafting service: builds prompt -> provider -> validate -> repair -> enrich"""
def build_prompt(draft: dict) -> str:
    return f"Draft: {draft.get('title','untitled')}"

def generate_document(draft: dict, provider) -> dict:
    prompt = build_prompt(draft)
    result = provider.generate(prompt)
    # naive return
    return {"title": draft.get("title"), "content": result}
