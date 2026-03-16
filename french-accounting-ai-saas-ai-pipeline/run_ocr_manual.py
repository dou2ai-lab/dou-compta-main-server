from ai_pipeline.ocr_service.worker import extract_text

FILE_PATH = "/Users/nancygautam/Downloads/Sample Invoice.png"

r = extract_text(FILE_PATH)
print("Text length:", len(r["text"]))
print("Confidence:", r["confidence"])
print("--- First 500 chars ---")
print(r["text"][:500])