"""Qist web API. Lovable (the website) calls this; all the real work is the same engine the Streamlit page uses.
Run locally:  uvicorn api.main:app --reload --port 7860"""
import io, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "app"))
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import analyze as A, engine

app = FastAPI(title="Qist API")
# The API stores nothing and has no logins or secrets, so any website may call it.
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

class Offer(BaseModel):
    text: str
    lang: str = "en"

class CostIn(BaseModel):
    price: float
    n: int
    instalment: float = 0
    fee: float = 0
    rate: float = 0
    rate_kind: str = "none"          # "monthly", "annual" or "none"
    fee_pct: float = 0
    fee_cap: float = 0

@app.on_event("startup")
def warm_up():
    """Train the wording model before the first visitor, so the first request does not pay for it."""
    import threading, ml
    threading.Thread(target=ml.model, daemon=True).start()

@app.get("/health")
def health():
    return {"ok": True}

@app.post("/analyze")
def analyze_text(o: Offer):
    if not o.text.strip(): raise HTTPException(400, "text is empty")
    return A.analyze(o.text[:20000], o.lang)

@app.post("/analyze-photo")
async def analyze_photo(file: UploadFile = File(...), lang: str = Form("en")):
    data = await file.read()
    if len(data) > 8_000_000: raise HTTPException(413, "photo is over 8 MB")
    try:
        from PIL import Image
        from ocr import read_photo
        text, note = read_photo(Image.open(io.BytesIO(data)))
    except Exception as e:
        raise HTTPException(400, f"could not read the photo: {type(e).__name__}")
    out = A.analyze(text, lang) if text.strip() else {"lang": lang, "terms": None}
    return {**out, "ocr_text": text, "ocr_note": note}

@app.post("/cost")
def recompute(c: CostIn):
    """Called when the user corrects a number on the website."""
    return {"cost": A.compute_cost(c.price, c.n, c.instalment, c.fee, c.rate, c.rate_kind, c.fee_pct, c.fee_cap)}
