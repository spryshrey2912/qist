"""Look and feel for Qist: 'Kinetic Orange', a brutalist theme. Orange page, black panels, white accents, 2px borders,
Archivo Black headings, Space Mono labels, marquees. No gradients, no shadows, sharp corners (pills only for the language switch and buttons).
Everything is CSS + inline SVG/HTML; the Google Fonts are optional and fall back to system fonts."""
import base64
import os
from html import escape


def h(s):
    """Collapse HTML to one line. Streamlit's markdown treats blank lines and indented lines as code blocks, so keep it flat."""
    return " ".join(line.strip() for line in s.strip().splitlines())


# ---- fonts you add: put files named  <family>-<weight>.<ext>  in app/fonts/  (e.g. ronzino-700.woff2). They are embedded, so no hosting is needed.
FONT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts")
FONT_FMT = {".woff2": "woff2", ".woff": "woff", ".ttf": "truetype", ".otf": "opentype"}


def custom_fonts():
    """@font-face rules for every font file in FONT_DIR. The family name is the part of the file name before the dash, capitalised (ronzino-700.woff2 -> 'Ronzino')."""
    out = []
    if os.path.isdir(FONT_DIR):
        for fn in sorted(os.listdir(FONT_DIR)):
            stem, ext = os.path.splitext(fn)
            if ext.lower() not in FONT_FMT or "-" not in stem:
                continue
            fam, weight = stem.rsplit("-", 1)
            if not weight.isdigit():
                continue
            data = base64.b64encode(open(os.path.join(FONT_DIR, fn), "rb").read()).decode()
            fmt = FONT_FMT[ext.lower()]
            out.append(f"@font-face{{font-family:'{fam.capitalize()}';font-weight:{weight};font-display:swap;src:url(data:font/{fmt};base64,{data}) format('{fmt}');}}")
    return "".join(out)


UPLOAD_SVG = ("<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64' fill='none'>"
              "<rect x='6' y='12' width='46' height='38' stroke='#000' stroke-width='3.5'/>"
              "<circle cx='19' cy='25' r='4.5' fill='#FF4D00'/>"
              "<path d='M6 46l14-14 10 10 8-8 14 12' stroke='#000' stroke-width='3.5'/>"
              "<circle cx='50' cy='46' r='12' fill='#FF4D00' stroke='#000' stroke-width='3.5'/>"
              "<path d='M50 52V40M44 46l6-6 6 6' stroke='#000' stroke-width='3.5' stroke-linecap='square'/></svg>")


def css(lang):
    from urllib.parse import quote
    upicon = "data:image/svg+xml," + quote(UPLOAD_SVG, safe="/:=' ,.-")
    ar = lang == "ar"
    rtl = "direction:rtl;text-align:right;" if ar else ""
    body = "'Tajawal','Inter',system-ui,sans-serif" if ar else "'Inter','Tajawal',system-ui,sans-serif"
    head = "'Tajawal','Archivo Black',Impact,sans-serif" if ar else "'Archivo Black',Impact,'Arial Black','Tajawal',sans-serif"
    fn = "'Ronzino','Tajawal','Inter',system-ui,sans-serif"
    mono = "'Tajawal','Space Mono',ui-monospace,monospace" if ar else "'Space Mono',ui-monospace,'Courier New','Tajawal',monospace"
    return "<style>" + custom_fonts() + h("""
@import url('https://fonts.googleapis.com/css2?family=Archivo+Black&family=Space+Mono:wght@400;700&family=Inter:wght@400;500;600;700&family=Tajawal:wght@400;500;700;800;900&display=swap');
:root{--o:#FF4D00;--k:#000;--w:#fff;--fn:%(fn)s;--head:%(head)s;--mono:%(mono)s;--ls:%(ls)s;--lh:%(lh)s;}
html,body{font-size:17px;}
.stApp,.stApp :is(p,li,label,button,input,textarea,small,[data-testid="stMarkdownContainer"]){font-family:%(body)s;}
::selection{background:#000;color:#FF4D00;}
.stApp{background:var(--o);color:var(--k);overflow-x:hidden;}
.block-container{max-width:1040px;padding-top:.8rem;padding-bottom:0;%(rtl)s}
[data-testid="stHeader"]{background:transparent;}
#MainMenu,footer{visibility:hidden;}
[data-testid="stSidebar"]{display:none;}
.stApp p,.stApp li{color:inherit;}
/* language switch: two buttons inside one black pill; the active one is white */
[data-testid="stHorizontalBlock"]:has(.st-key-lang_en){width:max-content;max-width:100%%;margin:.2rem auto .6rem;gap:.25rem!important;background:#000;border-radius:999px;padding:.3rem;flex-wrap:nowrap!important;}
.st-key-lang_en button>div,.st-key-lang_ar button>div{border-radius:999px;}
[data-testid="stHorizontalBlock"]:has(.st-key-lang_en)>[data-testid="stColumn"],[data-testid="stHorizontalBlock"]:has(.st-key-lang_en)>div{flex:0 0 auto!important;width:auto!important;min-width:0!important;}
.st-key-lang_en,.st-key-lang_ar{width:100%%;}
.st-key-lang_en button,.st-key-lang_ar button{min-height:46px;min-width:8.2rem;width:100%%;border-radius:999px!important;padding:.3rem 1.3rem;border:0!important;background:transparent!important;color:#fff!important;font-family:var(--mono);font-size:13px;transition:transform .15s,background .15s;}
.st-key-lang_en button p,.st-key-lang_ar button p{color:inherit!important;font-family:var(--mono);}
.st-key-lang_en button[kind="primary"],.st-key-lang_ar button[kind="primary"],.st-key-lang_en button[data-testid="stBaseButton-primary"],.st-key-lang_ar button[data-testid="stBaseButton-primary"]{background:#fff!important;color:#000!important;}
.st-key-lang_en button:hover,.st-key-lang_ar button:hover{background:#fff!important;color:#000!important;}
/* black panels: the tool */
[class*="st-key-panel_"]{background:#000;color:#fff;border:2px solid #000!important;border-radius:0!important;padding:1.1rem 1.3rem 1.3rem;margin-bottom:1.1rem;}
[class*="st-key-panel_"] [data-testid="stWidgetLabel"] p,[class*="st-key-panel_"] label p{color:#fff!important;font-family:var(--mono);font-size:14px;letter-spacing:0;}
[class*="st-key-panel_"] [data-testid="stCaptionContainer"],[class*="st-key-panel_"] [data-testid="stCaptionContainer"] p{color:rgba(255,255,255,.8)!important;}
textarea,input,[data-baseweb="select"]>div,[data-baseweb="base-input"]{background:#fff!important;color:#000!important;border-radius:0!important;border:2px solid #fff!important;}
input{font-family:var(--fn)!important;font-weight:500;font-size:1.05rem!important;}
textarea:focus,input:focus{border-color:#FF4D00!important;box-shadow:none!important;outline:2px solid #FF4D00;}
[data-testid="stFileUploaderDropzone"]{position:relative;min-height:132px;display:grid;place-items:center;background:#fff url("%(upicon)s") center/58px no-repeat!important;border:2px dashed #FF4D00!important;border-radius:0!important;cursor:pointer;transition:transform .2s;}
[data-testid="stFileUploaderDropzone"]:hover{transform:scale(1.03);}
[data-testid="stFileUploaderDropzone"]>*:not(button){display:none!important;}
[data-testid="stFileUploaderDropzoneInstructions"],[data-testid="stFileUploaderDropzone"] small{display:none!important;}
[data-testid="stFileUploaderFile"] *{color:#fff!important;}
[data-testid="stFileUploaderDropzone"] button{position:absolute;inset:0;width:100%%;height:100%%;opacity:0;cursor:pointer;transform:none!important;font-size:0!important;}
[class*="st-key-sample_"] button{min-height:44px;border-radius:999px!important;border:2px solid #fff!important;background:transparent!important;color:#fff!important;font-family:var(--mono);font-weight:700;font-size:13px;transition:transform .15s,background .15s,color .15s;}
[class*="st-key-sample_"] button p{color:inherit!important;font-family:var(--mono);font-size:13px;}
[class*="st-key-sample_"] button:hover{transform:scale(1.05);background:#FF4D00!important;border-color:#FF4D00!important;color:#000!important;}
[class*="st-key-sample_"] button:active{transform:scale(.97);}
a{color:inherit;background:linear-gradient(currentColor,currentColor) 0 100%%/0 2px no-repeat;transition:background-size .25s;}
a:hover{background-size:100%% 2px;}
.q-h1{font-family:var(--head);text-transform:uppercase;text-align:center;font-size:clamp(3rem,13vw,10rem);line-height:var(--lh);letter-spacing:var(--ls);margin:1.4rem 0 1.6rem;animation:rise .6s both;}
/* wordmark + hero */
.q-nav{display:flex;align-items:center;justify-content:space-between;margin:.2rem 0 .4rem;}
.q-mark{font-family:var(--head);font-size:1.7rem;text-transform:uppercase;letter-spacing:var(--ls);line-height:1;}
.q-mark span{margin-inline-start:.5rem;}
.q-hero{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:2rem;align-items:center;padding:.6rem 0 1.6rem;animation:rise .6s both;}
.q-sub{font-size:1.1rem;line-height:1.6;margin:0;max-width:30rem;font-weight:500;}
@media(max-width:820px){.q-hero{grid-template-columns:1fr;gap:1.2rem;}}
.q-demo{display:grid;grid-template-columns:1fr auto 1fr;gap:.6rem;align-items:stretch;}
.q-demo .pane{padding:.85rem 1rem;border:2px solid #000;transition:transform .2s;}
.q-demo .pane:hover{transform:translateX(4px);}
.q-demo .p1{background:#fff;color:#000;}.q-demo .p2{background:#000;color:#fff;}
.q-demo .lab{font-family:var(--mono);font-size:11px;font-weight:700;text-transform:uppercase;margin-bottom:.5rem;opacity:.75;}
.q-demo .ln{font-family:var(--mono);font-size:.82rem;line-height:1.9;}
.q-demo .arrow{align-self:center;font-family:var(--head);font-size:1.6rem;}
.q-rtl .q-demo .arrow{transform:scaleX(-1);}
.q-demo .row{display:flex;justify-content:space-between;align-items:baseline;gap:.6rem;padding:.3rem 0;border-bottom:1px solid rgba(255,255,255,.25);font-family:var(--fn);font-weight:500;font-size:.9rem;}
.q-demo .row:last-of-type{border-bottom:0;}
.q-demo .row b{font-family:var(--fn);font-size:1.3rem;font-weight:700;font-variant-numeric:lining-nums tabular-nums;}
.q-demo .row b.bad{color:#FF4D00;}
.q-demo .flag{margin-top:.55rem;padding:.4rem .6rem;background:#FF4D00;color:#000;font-family:var(--mono);font-size:.74rem;font-weight:700;}
@media(max-width:560px){.q-demo{grid-template-columns:1fr;}.q-demo .arrow{transform:rotate(90deg);justify-self:center;}.q-rtl .q-demo .arrow{transform:rotate(90deg);}}
@keyframes rise{from{opacity:0;transform:translateY(12px);}to{opacity:1;transform:none;}}
/* metadata row with the spinning scroll badge */
.q-meta{display:grid;grid-template-columns:1fr auto 1fr;gap:1rem;align-items:center;border-top:2px solid #000;padding:1rem 0 1.2rem;font-family:var(--mono);font-size:12px;line-height:1.7;text-transform:uppercase;}
.q-meta .r{text-align:end;}
@media(max-width:640px){.q-meta{grid-template-columns:1fr;justify-items:center;text-align:center;}.q-meta .r{text-align:center;}}
.q-spin{width:144px;height:144px;position:relative;}
.q-spin svg.t{width:100%%;height:100%%;animation:spin 12s linear infinite;}
.q-spin svg.a{position:absolute;inset:0;margin:auto;width:28px;height:28px;}
@keyframes spin{to{transform:rotate(360deg);}}
/* full-bleed bands */
.q-bleed{margin-left:calc(50%% - 50vw);margin-right:calc(50%% - 50vw);}
.q-mq{background:#000;overflow:hidden;transform:skewY(-2deg);margin-top:2.6rem;margin-bottom:2.6rem;padding:.9rem 0;direction:ltr;}
.q-mq .st1{color:#FF4D00;font-family:var(--head);text-transform:uppercase;text-align:center;font-size:clamp(1.6rem,6vw,5.4rem);line-height:var(--lh);letter-spacing:var(--ls);padding:.1rem 1rem .5rem;text-wrap:balance;}
.q-mq .row{white-space:nowrap;overflow:hidden;color:#fff;opacity:.85;}
.q-mq .trk{display:inline-block;animation:mq 40s linear infinite;animation-direction:reverse;font-family:var(--mono);font-size:clamp(.9rem,2.4vw,1.5rem);text-transform:uppercase;line-height:1.6;}
@keyframes mq{to{transform:translateX(-50%%);}}
.q-svc{background:#000;color:#fff;margin-top:2.6rem;padding:2.2rem 0 1rem;}
.q-svc .in{max-width:1040px;margin:0 auto;padding:0 1rem;%(rtl)s}
.q-svc .kick{font-family:var(--mono);font-size:12px;text-transform:uppercase;color:#FF4D00;margin-bottom:1rem;}
.q-svc .it{display:grid;grid-template-columns:3.2rem 1fr auto;gap:1rem;align-items:center;border-top:1px solid rgba(255,255,255,.2);padding:1.3rem .4rem;transition:background .2s;}
.q-svc .it:hover{background:rgba(255,255,255,.05);}
.q-svc .n{font-family:var(--mono);color:#FF4D00;font-size:.95rem;}
.q-svc .t{font-family:var(--head);text-transform:uppercase;font-size:clamp(1.8rem,5.6vw,4.6rem);letter-spacing:var(--ls);line-height:var(--lh);transition:transform .25s;}
.q-svc .it:hover .t{transform:translateX(16px);}
.q-rtl .q-svc .it:hover .t,.q-svc .q-rtl .it:hover .t{transform:translateX(-16px);}
.q-svc .tags{display:flex;gap:.4rem;flex-wrap:wrap;margin-top:.7rem;}
.q-svc .tags span{font-family:var(--mono);font-size:11px;text-transform:uppercase;border:1px solid rgba(255,255,255,.55);border-radius:999px;padding:.2rem .7rem;}
.q-svc .go{width:44px;height:44px;color:#FF4D00;opacity:0;transition:opacity .2s,transform .25s;}
.q-svc .it:hover .go{opacity:1;transform:rotate(45deg);}
.q-cta{text-align:center;padding:3.2rem 0 2rem;}
.q-cta .big{font-family:var(--head);text-transform:uppercase;font-size:clamp(2.6rem,11vw,8.5rem);letter-spacing:var(--ls);line-height:var(--lh);}
.q-cta .mono{font-family:var(--mono);font-size:12px;text-transform:uppercase;margin-top:1rem;}
.q-foot{display:flex;justify-content:space-between;gap:1rem;border-top:2px solid #000;padding:1rem 0 1.4rem;font-family:var(--mono);font-size:12px;text-transform:uppercase;}
/* section titles inside the black panels */
.q-sec{display:flex;align-items:center;gap:.8rem;margin:.1rem 0 .9rem;font-family:var(--fn);font-weight:700;font-size:1.7rem;letter-spacing:0;line-height:1.15;color:#fff;}
.q-num{display:inline-grid;place-items:center;min-width:2.1rem;height:2.1rem;padding:0 .3rem;background:#FF4D00;color:#000;font-family:var(--mono);font-size:.85rem;font-weight:700;letter-spacing:0;}
.q-chip{display:inline-flex;align-items:center;gap:.5rem;padding:.35rem .8rem;background:#FF4D00;color:#000;font-family:var(--fn);font-size:.95rem;font-weight:700;margin:.2rem 0 .6rem;}
.q-chip i{width:7px;height:7px;background:#000;}
/* result cards */
.q-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:.8rem;margin:.6rem 0 1rem;}
.q-card{padding:.95rem 1.1rem;border:2px solid #fff;animation:rise .5s both;transition:transform .2s,background .2s;}
.q-card:hover{transform:translateY(-2px);background:rgba(255,255,255,.07);}
.q-card .k{font-family:var(--fn);font-weight:500;font-size:1rem;opacity:.9;}
.q-card .v{font-family:var(--fn);font-weight:700;font-size:2.3rem;margin-top:.3rem;line-height:1.05;font-variant-numeric:lining-nums tabular-nums;}
.q-card.bad{border-color:#FF4D00;}.q-card.bad .v,.q-card.hi .v{color:#FF4D00;}
/* gauge + split */
.q-row{display:grid;grid-template-columns:200px 1fr;gap:1rem;align-items:center;margin:.2rem 0 1rem;}
@media(max-width:640px){.q-row{grid-template-columns:1fr;justify-items:center;}}
.q-gauge{position:relative;width:170px;height:170px;}
.q-gauge svg{transform:rotate(-90deg);}
.q-gauge .ring{stroke-dasharray:326.7;stroke-dashoffset:326.7;animation:fill 1.4s .2s cubic-bezier(.2,.8,.2,1) forwards;}
@keyframes fill{to{stroke-dashoffset:var(--off);}}
.q-gauge .mid{position:absolute;inset:0;display:grid;place-content:center;text-align:center;}
.q-gauge .mid b{font-family:var(--fn);font-weight:700;font-size:1.8rem;}.q-gauge .mid span{font-family:var(--fn);font-weight:500;font-size:.82rem;max-width:96px;line-height:1.25;opacity:.9;}
.q-split{width:100%%;}
.q-split .bar{display:flex;height:26px;border:2px solid #fff;}
.q-split .seg{height:100%%;width:0;animation:grow 1.2s .2s cubic-bezier(.2,.8,.2,1) forwards;}
@keyframes grow{to{width:var(--w);}}
.q-split .a{background:#fff;}.q-split .b{background:#FF4D00;}
.q-split .lg{display:flex;justify-content:space-between;gap:1rem;flex-wrap:wrap;margin-top:.5rem;font-family:var(--fn);font-weight:500;font-size:.95rem;}
.q-split .lg b{font-weight:700;}
.q-dot{display:inline-block;width:10px;height:10px;margin-inline-end:.4rem;}
/* timeline */
.q-tl{display:flex;flex-wrap:wrap;gap:.4rem;margin:.5rem 0 .2rem;}
.q-tl span{display:grid;place-items:center;min-width:2.1rem;height:2.1rem;padding:0 .35rem;border:1px solid #fff;font-family:var(--fn);font-size:.95rem;font-weight:700;opacity:0;animation:pop .4s calc(var(--i)*45ms + .3s) cubic-bezier(.2,1.2,.4,1) forwards;}
.q-tl span.fee{background:#FF4D00;border-color:#FF4D00;color:#000;}
.q-tl span.more{border-style:dashed;}
@keyframes pop{from{opacity:0;transform:scale(.5) translateY(6px);}to{opacity:1;transform:none;}}
/* verdict banners: icon + label carry the meaning, not colour alone */
.q-v{display:flex;gap:.8rem;align-items:flex-start;padding:.85rem 1rem;margin:.5rem 0;border:2px solid #fff;animation:rise .5s both;line-height:1.55;}
.q-v .ic{flex:0 0 auto;width:28px;height:28px;display:grid;place-items:center;font-family:var(--mono);font-weight:700;background:#fff;color:#000;}
.q-v b{display:block;font-family:var(--fn);font-size:1.02rem;font-weight:700;margin-bottom:.15rem;}
.q-v.ok{background:#fff;color:#000;border-color:#fff;}.q-v.ok .ic{background:#000;color:#fff;}
.q-v.warn{background:#FF4D00;color:#000;border-color:#FF4D00;}.q-v.warn .ic{background:#000;color:#FF4D00;}
.q-v.bad{background:#FF4D00;color:#000;border-color:#fff;}.q-v.bad .ic{background:#000;color:#FF4D00;}
.q-v.note{background:transparent;color:#fff;border-style:dashed;}
.q-sama{margin-top:1rem;padding:.85rem 1rem;border:1px solid rgba(255,255,255,.35);color:rgba(255,255,255,.88);font-size:.86rem;line-height:1.65;}
.q-sama .t{display:flex;gap:.45rem;align-items:center;font-family:var(--mono);font-size:.78rem;text-transform:uppercase;color:#FF4D00;margin-bottom:.3rem;}
.q-disc{text-align:center;color:rgba(255,255,255,.7);font-family:var(--mono);font-size:11px;margin-top:1rem;}
/* alerts must stand out: solid colour, thick outline, bigger bold text, a pop-in and three pulses (then still) */
.q-v.warn,.q-v.bad{border-width:3px;border-color:#fff;font-size:1.12rem;font-weight:600;box-shadow:0 0 0 0 rgba(255,255,255,.75);animation:rise .5s both,pulse 1.5s .6s 3;}
.q-v.warn .ic,.q-v.bad .ic{width:38px;height:38px;font-size:1.3rem;}
.q-v.warn b,.q-v.bad b{font-size:1.25rem;}
.q-v strong,.q-alert strong{font-weight:800;}
.q-v.warn strong,.q-v.bad strong{background:rgba(0,0,0,.22);padding:0 .25em;border-radius:3px;}
@keyframes pulse{0%%{box-shadow:0 0 0 0 rgba(255,255,255,.8);}100%%{box-shadow:0 0 0 18px rgba(255,255,255,0);}}
.q-alert{display:flex;gap:1rem;align-items:flex-start;background:#FF4D00;color:#000;border:4px solid #fff;padding:1.1rem 1.3rem;margin:.2rem 0 1.1rem;animation:pop .5s both,pulse 1.5s .6s 3;}
.q-alert .ic{flex:0 0 auto;width:48px;height:48px;display:grid;place-items:center;background:#000;color:#FF4D00;font-family:var(--fn);font-weight:800;font-size:1.8rem;}
.q-alert .t{font-family:var(--fn);font-weight:800;font-size:1.5rem;line-height:1.15;margin-bottom:.25rem;}
.q-alert .m{font-family:var(--fn);font-weight:500;font-size:1.12rem;line-height:1.5;}
/* tooltips: a small (i) that opens a white bubble on hover or keyboard focus */
.q-tip{position:relative;display:inline-grid;place-items:center;width:1.2rem;height:1.2rem;margin-inline-start:.5rem;border:1.5px solid currentColor;border-radius:50%%;font-family:var(--mono);font-size:.72rem;font-weight:700;line-height:1;cursor:help;vertical-align:middle;text-transform:none;letter-spacing:0;}
.q-tip::after{content:attr(data-tip);position:absolute;bottom:calc(100%% + 10px);inset-inline-start:-.5rem;width:max-content;max-width:min(270px,72vw);padding:.6rem .8rem;background:#fff;color:#000;border:2px solid #000;font-family:var(--fn);font-size:.9rem;font-weight:500;line-height:1.45;text-align:start;opacity:0;transform:translateY(4px);pointer-events:none;transition:opacity .15s,transform .15s;z-index:30;}
.q-tip:hover::after,.q-tip:focus::after{opacity:1;transform:none;}
.q-tip:focus{outline:2px solid #FF4D00;outline-offset:2px;}
.q-alert .q-tip{color:#000;}
.q-ev{border:2px solid #fff;margin:0 0 1.1rem;padding:.9rem 1.1rem;}
.q-ev .t{font-family:var(--fm);font-size:.78rem;letter-spacing:.12em;text-transform:uppercase;margin-bottom:.6rem;}
.q-ev .k{font-family:var(--fm);font-size:.72rem;letter-spacing:.1em;text-transform:uppercase;opacity:.85;margin-top:.55rem;}
.q-ev .q{font-family:var(--fn);font-size:1.02rem;line-height:1.5;border-inline-start:4px solid #fff;padding:.25rem .8rem;margin-top:.2rem;background:rgba(0,0,0,.28);overflow-wrap:anywhere;}
.q-ev mark{background:#fff;color:#000;font-weight:800;padding:0 .2em;}
.q-ev .w{margin-top:.75rem;font-size:.98rem;line-height:1.5;}
[data-testid="stTooltipIcon"] svg,[data-testid="stTooltipHoverTarget"] svg{color:#fff!important;fill:#fff!important;}
@media (prefers-reduced-motion:reduce){*,*::before,*::after{animation-duration:.01ms!important;animation-iteration-count:1!important;animation-delay:0s!important;transition:none!important;}.q-gauge .ring{stroke-dashoffset:var(--off)!important;}.q-split .seg{width:var(--w)!important;}.q-tl span{opacity:1!important;}.q-v,.q-alert{box-shadow:none!important;}.q-mq .trk{animation:none!important;}}
""") % {"upicon": upicon, "fn": fn, "body": body, "head": head, "mono": mono, "rtl": rtl, "ls": "0" if ar else "-.04em", "lh": "1.2" if ar else ".9"} + "</style>"


def _cls(lang):
    return "q-rtl" if lang == "ar" else ""


def hero_top(T, lang):
    """The wordmark. The headline itself is the falling-letters component under it (kept here as a hidden h1 for screen readers)."""
    return h(f"""<div class="q-nav {_cls(lang)}"><div class="q-mark">{escape(T["brand"])}<span>{escape(T["brand2"])}</span></div></div><div class="q-h1 {_cls(lang)}" role="heading" aria-level="1">{T["h1big"]}</div>""")


def hero_body(T, demo, lang):
    """One plain sentence, the product itself (an offer in, the real cost out), then the metadata row with the spinning badge.
    `demo` holds numbers computed by the cost engine (see app.py), so the hero never shows an invented figure."""
    D = T["demo"]
    lines = "".join(f"<div>{escape(x)}</div>" for x in D["lines"])
    badge = escape(T["scroll"]) * 4
    return h(f"""<div class="q-hero {_cls(lang)}"><p class="q-sub">{escape(T["sub"])}</p>
<div class="q-demo"><div class="pane p1"><div class="lab">{escape(D["in"])}</div><div class="ln">{lines}</div></div><div class="arrow">&#8594;</div>
<div class="pane p2"><div class="lab">{escape(D["out"])}</div>
<div class="row"><span>{escape(T["total"])}</span><b>{money(demo["total_paid"])}</b></div>
<div class="row"><span>{escape(T["extra"])}</span><b class="bad">{money(demo["extra_cost"])}</b></div>
<div class="row"><span>{escape(T["ear"])}</span><b>{demo["effective_annual_rate"]:.1f}%</b></div>
<div class="flag">! {escape(D["flag"])}</div></div></div></div>
<div class="q-meta {_cls(lang)}"><div>{T["meta_l"]}</div>
<div class="q-spin"><svg class="t" viewBox="0 0 144 144" direction="ltr" style="direction:ltr"><defs><path id="qc" d="M72 72m-54 0a54 54 0 1 1 108 0a54 54 0 1 1 -108 0"/></defs>
<text font-family="Space Mono,Tajawal,monospace" font-size="9" font-weight="700" fill="#000" letter-spacing="1"><textPath href="#qc">{badge}</textPath></text></svg>
<svg class="a" viewBox="0 0 24 24" fill="none" stroke="#000" stroke-width="2.4" stroke-linecap="square"><path d="M12 5v14"/><path d="M19 12l-7 7-7-7"/></svg></div>
<div class="r">{T["meta_r"]}</div></div>""")


def marquee(T):
    unit = escape(T["mq2"]) + " &bull; "
    return h(f'<div class="q-bleed q-mq"><div class="st1">{escape(T["mq1"])}</div><div class="row"><div class="trk">{unit * 8}</div></div></div>')


ARROW = '<svg class="go" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="square"><path d="M7 17L17 7"/><path d="M8 7h9v9"/></svg>'


def services(T, lang):
    items = ""
    for i, (title, tags) in enumerate(T["svc"], 1):
        pills = "".join(f"<span>{escape(t)}</span>" for t in tags)
        items += f'<div class="it"><span class="n">{i:02d}</span><div><div class="t">{escape(title)}</div><div class="tags">{pills}</div></div>{ARROW}</div>'
    return h(f'<div class="q-bleed q-svc"><div class="in {_cls(lang)}"><div class="kick">{escape(T["svc_kick"])}</div>{items}</div></div>')


def closer(T, lang):
    return h(f"""<div class="q-cta {_cls(lang)}"><div class="big">{T["cta"]}</div><div class="mono">{escape(T["cta_note"])}</div></div>
<div class="q-foot {_cls(lang)}"><span>&copy; 2026 Qist</span><span>WAICY 2026</span></div>""")


def section(n, title):
    return f'<div class="q-sec"><span class="q-num">{n:02d}</span>{escape(title)}</div>'


def chip(text):
    return f'<div class="q-chip"><i></i>{escape(text)}</div>'


# ---------------------------------------------------------------- results
def money(x):
    return f"{x:,.2f}"


import re as _re


def bold(escaped):
    """**text** -> <strong>text</strong>, applied after HTML escaping."""
    return _re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", escaped)


def tip(text):
    t = escape(text, quote=True)
    return f'<span class="q-tip" tabindex="0" role="note" aria-label="{t}" data-tip="{t}">i</span>'


def alert(title, msg, tip_text=""):
    """The loud banner at the top of the result: solid orange, thick white outline, big bold type."""
    return h(f'''<div class="q-alert" role="alert"><div class="ic">!</div><div><div class="t">{escape(title)}{tip(tip_text) if tip_text else ""}</div><div class="m">{bold(escape(msg))}</div></div></div>''')


def _mark(loc):
    line, a, b = loc
    return escape(line[:a]) + "<mark>" + escape(line[a:b]) + "</mark>" + escape(line[b:])

def evidence(T, ev):
    """'Where we found it': the promise line and the fee line from the user's own text, highlighted, and one sentence on why it is easy to miss."""
    if not ev["fee"]: return ""
    rows = (f'<div class="k">{escape(T["ev_claim"])}</div><div class="q">{_mark(ev["claim"])}</div>' if ev["claim"] and not ev["same_line"] else "")
    rows += f'<div class="k">{escape(T["ev_fee"])}</div><div class="q">{_mark(ev["fee"])}</div>'
    why = T["ev_same"] if ev["same_line"] else T["ev_diff"]
    return h(f'''<div class="q-ev"><div class="t">{escape(T["ev_t"])}</div>{rows}<div class="w">{bold(escape(why))}</div></div>''')


def cards(T, r):
    ear = r["effective_annual_rate"]
    extra_cls = "good" if r["extra_cost"] <= 0.005 else "bad"
    return h(f"""<div class="q-grid">
<div class="q-card"><div class="k">{escape(T["monthly"])}{tip(T["tips"]["monthly"])}</div><div class="v">{money(r["instalment"])}</div></div>
<div class="q-card hi"><div class="k">{escape(T["total"])}{tip(T["tips"]["total"])}</div><div class="v">{money(r["total_paid"])}</div></div>
<div class="q-card {extra_cls}"><div class="k">{escape(T["extra"])}{tip(T["tips"]["extra"])}</div><div class="v">{money(r["extra_cost"])}</div></div>
<div class="q-card"><div class="k">{escape(T["ear"])}{tip(T["tips"]["ear"])}</div><div class="v">{(f"{ear:.2f}%" if ear <= 150 else ">150%")}</div></div></div>""")


def gauge(T, ear):
    shown = max(0.0, min(ear, 100.0))
    off = 326.7 * (1 - shown / 100)
    col = "#ffffff" if ear < 12 else "#FF4D00"
    label = f"{ear:.1f}%" if ear <= 150 else ">150%"
    return h(f"""<div class="q-gauge"><svg width="170" height="170" viewBox="0 0 120 120"><circle cx="60" cy="60" r="52" fill="none" stroke="rgba(255,255,255,.18)" stroke-width="10"/>
<circle class="ring" style="--off:{off:.1f}" cx="60" cy="60" r="52" fill="none" stroke="{col}" stroke-width="10" stroke-linecap="butt"/></svg>
<div class="mid"><b style="color:{col}">{label}</b><span>{escape(T["ear"])}</span></div></div>""")


def split(T, price, extra):
    total = price + max(extra, 0)
    a = 100 * price / total if total else 100
    b = 100 - a
    segs = f'<div class="seg a" style="--w:{a:.2f}%"></div>' + (f'<div class="seg b" style="--w:{b:.2f}%"></div>' if b > 0.2 else "")
    return h(f"""<div class="q-split"><div class="bar">{segs}</div><div class="lg">
<span><i class="q-dot" style="background:#fff"></i>{escape(T["price"])}: <b>{money(price)}</b></span>
<span><i class="q-dot" style="background:#FF4D00"></i>{escape(T["extra"])}: <b>{money(max(extra, 0))}</b></span></div></div>""")


def timeline(T, n, fee):
    items = []
    if fee > 0:
        items.append(f'<span class="fee" style="--i:0" title="{escape(T["fee"])}">{fee:g}</span>')
    shown = min(n, 24)
    for k in range(1, shown + 1):
        items.append(f'<span style="--i:{k}">{k}</span>')
    if n > shown:
        items.append(f'<span class="more" style="--i:{shown + 1}">+{n - shown}</span>')
    return h(f'<div class="q-tl">{"".join(items)}</div>')


def results(T, r, price, n, fee):
    return h(f"""{cards(T, r)}<div class="q-row">{gauge(T, r["effective_annual_rate"])}{split(T, price, r["extra_cost"])}</div>
<div class="q-sec" style="font-size:1rem">{escape(T["timeline"])}{tip(T["tips"]["timeline"])}</div>{timeline(T, n, fee)}""")


ICON = {"ok": "&#10003;", "warn": "!", "bad": "&#10005;", "note": "i"}


def verdict(kind, title, msg, tip_text=""):
    t = f"<b>{escape(title)}{tip(tip_text) if tip_text else ''}</b>" if title else ""
    return h(f'<div class="q-v {kind}"' + (' role="alert"' if kind in ("warn", "bad") else "") + f'><div class="ic">{ICON[kind]}</div><div>{t}{bold(escape(msg))}</div></div>')


def sama(T, rules, disc):
    return h(f"""<div class="q-sama"><div class="t">&#9878; {escape(T["sama"])}</div>{escape(rules)}</div><div class="q-disc">{escape(disc)}</div>""")
