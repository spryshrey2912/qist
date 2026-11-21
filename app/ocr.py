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
    W = 1600                                                 # small screenshots are scaled UP (they misread '0%' as '096'), huge phone photos DOWN (free-server memory)
    if g.width != W: g = g.resize((W, round(g.height * W / g.width)))
    # Three quick tries (plain, black-and-white, other layout mode); keep the one Tesseract is most confident about.
    tries = [(g, "--psm 6"), (g.point(lambda v: 255 if v > 150 else 0), "--psm 6"), (g, "--psm 3")]
    best, best_conf = None, -1.0
    for im, cfg in tries:
        d = pytesseract.image_to_data(im, lang="ara+eng", config=cfg, output_type=pytesseract.Output.DICT)
        c = [float(x) for x, w in zip(d["conf"], d["text"]) if w.strip() and float(x) >= 0]
        conf = sum(c) / len(c) if len(c) >= 3 else -1.0
        if conf > best_conf: best, best_conf = (im, cfg), conf
    im, cfg = best or tries[0]
    text = engine.clean(pytesseract.image_to_string(im, lang="ara+eng", config=cfg).strip())     # '096 for 3 months' -> '0% for 3 months'
    note = "" if len(text) >= 20 else "Very little text was read. Try a sharper, straighter photo, or paste the text. / لم يُقرأ إلا القليل من النص. جرّب صورة أوضح أو الصق النص."
    return text, note
