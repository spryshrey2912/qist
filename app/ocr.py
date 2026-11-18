"""Photo to text with Tesseract (Arabic + English). On Windows set TESSERACT_CMD to the tesseract.exe path (see README)."""
import os

def read_photo(img):
    """Returns (text, note). note is '' when the read looks fine, else a short warning for the user."""
    import pytesseract
    if os.environ.get("TESSERACT_CMD"):
        pytesseract.pytesseract.tesseract_cmd = os.environ["TESSERACT_CMD"]
    img = img.convert("L")                                   # grey scale reads better
    if img.width > 1600:                                     # big phone photos can use too much memory on a free server
        img = img.resize((1600, round(img.height * 1600 / img.width)))
    text = pytesseract.image_to_string(img, lang="ara+eng").strip()
    note = "" if len(text) >= 20 else "Very little text was read. Try a sharper, straighter photo, or paste the text. / لم يُقرأ إلا القليل من النص. جرّب صورة أوضح أو الصق النص."
    return text, note
