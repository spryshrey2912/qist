"""Photo to text with Tesseract (Arabic + English). On Windows set TESSERACT_CMD to the tesseract.exe path (see README)."""
import os

def read_photo(img):
    """Returns (text, note). note is '' when the read looks fine, else a short warning for the user."""
    import pytesseract
    if os.environ.get("TESSERACT_CMD"):
        pytesseract.pytesseract.tesseract_cmd = os.environ["TESSERACT_CMD"]
    import engine
    from PIL import ImageOps
    g = ImageOps.autocontrast(img.convert("L"))              # grey scale reads better
    W = 1300                                                 # small screenshots scaled UP (they misread '0%' as '096'), big phone photos DOWN (free server has little CPU and memory)
    if g.width != W: g = g.resize((W, round(g.height * W / g.width)))
    os.environ.setdefault("OMP_THREAD_LIMIT", "1")           # one Tesseract thread: the free server has one weak core
    def run(im, cfg):
        d = pytesseract.image_to_data(im, lang="ara+eng", config=cfg, output_type=pytesseract.Output.DICT, timeout=25)
        words = [(w, float(c)) for w, c in zip(d["text"], d["conf"]) if w.strip() and float(c) >= 0]
        conf = sum(c for _, c in words) / len(words) if len(words) >= 3 else -1.0
        return " ".join(w for w, _ in words), conf
    # One pass first. Only a weak read (low confidence) earns a second, black-and-white pass.
    best_im, best_cfg = g, "--psm 6"
    _, conf = run(g, best_cfg)
    if conf < 60:
        bw = g.point(lambda v: 255 if v > 150 else 0)
        _, conf2 = run(bw, best_cfg)
        if conf2 > conf: best_im = bw
    text = engine.clean(pytesseract.image_to_string(best_im, lang="ara+eng", config=best_cfg, timeout=25).strip())     # '096 for 3 months' -> '0% for 3 months'
    note = "" if len(text) >= 20 else "Very little text was read. Try a sharper, straighter photo, or paste the text. / لم يُقرأ إلا القليل من النص. جرّب صورة أوضح أو الصق النص."
    return text, note
