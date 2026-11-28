Build a single-page web app called **Qist (قسط)**. It checks Saudi instalment, buy-now-pay-later and card-financing offers. The user pastes or photographs an offer, and the app shows the real cost in SAR, shows exactly where a hidden fee is written, and explains it. All the calculations happen in my own backend API (below). **Do not calculate anything in the browser and do not invent numbers.** Only show what the API returns.

## Languages
English and Arabic, with a pill toggle at the top (two equal pill buttons, the active one white with black text). Arabic uses `dir="rtl"`. All text comes from `src/i18n/strings.json` (I attach it; copy it exactly, do not rewrite the wording). Remember the chosen language in state.

## Look (follow exactly)
- Flat orange page background `#FF4D00`. No gradients, no shadows, no rounded corners, except the language pill.
- Content panels are solid black `#000` with a 2px white border; text white. Each panel has a numbered heading ("01", "02"…) in a mono font.
- Fonts from Google Fonts: **Archivo Black** for the huge headline and buttons, **Space Mono** for small labels (uppercase, letter-spacing .12em), **Inter** for body text, **Tajawal** for all Arabic. Numbers and result cards use Inter 700.
- Sharp 2px borders everywhere. Buttons: white background, black text, 2px black border; on hover they invert. Sample chips are small versions of the same.
- Hero: a huge two-line headline from `h1big` (it must fit on a 390px phone), the `sub` line under it, and a scrolling marquee strip (black on white, Space Mono).
- Large readable text (16px minimum), high contrast, good for elderly users. Respect `prefers-reduced-motion`.

## Page sections
1. **Add the offer.** A "Try a sample" row of 4 chip buttons (`samples` keys: tasaheal, bsf, aljazira, kia). Clicking one puts the matching text from `samples.json` into the textarea. Below: a large textarea (`paste`) and a photo upload (`upload`) drawn as a square icon tile (a black frame with orange corner marks and an up-arrow) instead of a text dropzone. A black "Analyse" button underneath. If a photo is chosen, send it to `/analyze-photo` and put the returned `ocr_text` into the textarea so the user can correct it.
2. **What we found.** Show the product type (`product_name`) as a chip. Editable number fields for: cash price, number of instalments, instalment amount, late fee, admin fee, fee %, profit rate, and a select for rate kind (`none`, `monthly`, `annual`). If `terms.plans` has entries, show a select to choose the plan (`plan_fmt`); picking a plan sets the number of instalments and the rate. If `terms.price_is_example` is true show the `example` caption. Each field has an info tooltip (a small "i" button) with the text from `help`. When the user changes any field, call `POST /cost` after 400 ms and update section 3.
3. **The real cost.**
   - If `hidden_fee` is not null: a loud banner first. Solid orange block with a thick 4px white outline, a black square with "!", the `alert_title` in big bold type and `alert_msg` with `{fee}` = `hidden_fee.amount`. It pops in with a quick scale animation. Directly under it a black box titled `ev_t` ("Where we found it") showing the user's own text: a row labelled `ev_claim` with `hidden_fee.promise.line` and the characters from `start` to `end` highlighted (white background, black text), then a row labelled `ev_fee` with `hidden_fee.fee.line` highlighted the same way, then one sentence: `ev_same` if `same_line` is true, else `ev_diff`. Skip the `ev_claim` row if `same_line` is true.
   - If `cost` is null: show `needs`.
   - Else show cards: monthly payment (`cost.instalment`), total you pay (`cost.total_paid`), extra cost (`cost.extra_cost`), effective annual rate (`cost.effective_annual_rate`, as a percent, big, with a circular gauge), a split bar of price vs extra, and a timeline with one square per month, where the first square is the fee paid today (`cost.fee_total`). Under it, `assume` plus `cost.how`. Show each string in `cost.warnings` using `w_below_price` / `w_extreme_rate`.
4. **Wording check.** For every item in `flags`: a warning block (bold, 3px white border, "!" icon) if `code` is `zero_but_fee`, otherwise a note block, showing `message` (it contains **bold** markers: render them as bold). If `flags` is empty show `message_if_no_flag`. Then an "AI wording model" block (`ml_t`): if `ml_p_misleading` ≥ 0.5 show `ml_hi`, otherwise `ml_lo`, with `{p}` = the percent rounded. Then a box titled `sama` with the `sama` text from the API, and the `disclaimer` in small type.
5. Footer with the brand. Keep it simple.

## Backend API (already running; do not build a backend)
Base URL is `import.meta.env.VITE_API_BASE_URL`. Put every call in one file `src/services/backendApi.ts` with a 60 second timeout and clear error messages (the server may be waking up: show "Waking up the server, this can take up to a minute…" after 5 seconds of waiting).
- `POST /analyze` body `{ "text": string, "lang": "en" | "ar" }` returns the analysis object (see `api_example.json`).
- `POST /analyze-photo` multipart form with `file` and `lang` returns the same object plus `ocr_text` and `ocr_note`.
- `POST /cost` body `{ price, n, instalment, fee, rate, rate_kind, fee_pct, fee_cap }` returns `{ "cost": {...} | null }`.
- `GET /health`.
Call `/analyze` again when the language changes, so the explanations switch language.

## Rules
- Never show invented data. If the API fails, show a clear error with a retry button.
- Mobile first. Must look right at 390px, and in Arabic RTL.
- Nothing the user pastes is stored. Add no login and no database.
