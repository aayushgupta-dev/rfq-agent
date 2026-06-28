# Aerchain Design Language

> Reverse-engineered from **aerchain.io** (home, Sourcing Agent, About Us, Why Aerchain) on
> 2026-06-28 via live DOM inspection + screenshots. This is the visual reference for revamping
> **Bid Desk** (`apps/web`) so our buyer UI reads as a credible member of the Aerchain product family.
>
> Assets live in [`./assets/`](./assets) (logo, mark, favicon — SVG + PNG). Reference screenshots
> are in the repo root (`aerchain-*.jpeg/png`).

The site is built on **Webflow**. The aesthetic is **enterprise SaaS, AI-forward**: a clean
near-white canvas, a deep-indigo/violet brand core, pastel gradient atmospheres, and dark
"intelligence" sections punctuated by neon/warm glows. Confident but not loud — lots of whitespace,
big bold indigo headings, soft rounded cards, and product-UI mockups as the hero proof.

---

## 1. Company context (why the design looks the way it does)

Aerchain is an **AI-/agent-native enterprise procurement platform** — it automates the source-to-pay
cycle through a suite of specialized **AI agents** (Intake, Sourcing, Vendor Onboarding, Evaluation,
Negotiation, Invoice; Contract + Analytics "coming soon") fronted by a conversational assistant
called **Aera**. Core message: procurement is *"moving from forms to conversations"* and the future is
*"agent-augmented."*

- **Buyer/user:** enterprise procurement teams (sourcing managers, procurement ops, CPO/finance).
- **Tier & traction:** enterprise (not SMB); claims 40+ countries, 150K+ suppliers, $15B+ spend
  managed. Named logos: AB InBev, Cars24, WeWork, Relaxo, Infosys, Manjushree.
- **Company:** Bengaluru, India; ~$17M raised (incl. $13M Series A led by Pavestone, IndiaMART
  participating); originated from AB InBev's "Beer Garage" accelerator.
- **Category & rivals:** Source-to-Pay / Procure-to-Pay; competes with Coupa, SAP Ariba, GEP,
  JAGGAER, Ivalua, Zip. Differentiator: *agent-native + conversational + fast to deploy* vs.
  heavy legacy suites.

**Why this matters for us:** Bid Desk is the same shape — an agentic procurement copilot (RFQ →
extraction → comparison). Their **Sourcing Agent** and **Evaluation Agent** are conceptual cousins of
our extraction/comparison agents. Matching their design language makes our prototype look like it
belongs in their portfolio. Their tone — *evidence-led, "AI that empowers not replaces," compliance
and accuracy front-and-center* — is exactly our rubric (evidence over assertion, absence first-class).

**Voice / copy patterns to echo:** short punchy gradient headlines built on transformation
("From Chaos to Clarity", "Sourcing, Reinvented", "From Strategy to Selection"), metric-led proof
("40% more accurate", "5x faster"), and a Before-vs-After framing.

---

## 2. Brand assets

| Asset | File | Format | Use |
|---|---|---|---|
| Brand **mark** (coral ribbon "a") | [`assets/favicon.svg`](./assets/favicon.svg) | SVG, 32×32, scalable | **Favicon, app icon, loading mark, compact nav.** Best format — vector, tiny (1.4 KB). |
| Brand mark (square raster) | [`assets/logo-mark.png`](./assets/logo-mark.png) | PNG 976×976 | Fallback where SVG can't be used (OG image, social). |
| Full **wordmark** lockup | [`assets/wordmark.png`](./assets/wordmark.png) | PNG 4016×577, transparent | **Primary logo** in header/footer. High-res; scale down. |
| Wordmark (standard res) | [`assets/logo.png`](./assets/logo.png) | PNG 713×110, transparent | Header logo at normal DPI. |

**The mark:** an abstract coral-orange ribbon forming a stylized lowercase **"a"** with a dot — it
*replaces the "A" in "CHAIN"* in the wordmark. It's the single warm accent against an otherwise
near-black wordmark, and it's the lone element in the favicon. Mark fill is **`#EF5433`**.

**Wordmark:** the word `AERCHAIN` in heavy near-black (`#242526`), all-caps, geometric — the coral
mark is the only color. Always on a light background; keep generous clear space.

> ⚠️ The site's live font is **Avenir** (licensed, not web-free). Do **not** try to ship Avenir.
> They also load **Geist** (free, Vercel) — use that for our wordmark/UI substitute. See §4.

---

## 3. Color system

Indigo/violet is the spine; coral is the single warm spark; pastel gradients are the "air"; deep navy
is the "intelligence/depth" surface. Hex values below are sampled from computed styles.

### Core brand
| Token | Hex | RGB | Role |
|---|---|---|---|
| `indigo-900` (brand) | `#373192` | 55, 49, 146 | **Primary brand** — all headings, key labels, the "ink" color. |
| `navy-950` (depth) | `#0E0D59` / `#100E5B` | 14,13,89 / 16,14,91 | Dark sections (Before/After, bento, footer top). |
| `violet-deep` | `#201045` | 32,16,69 | Darkest cards on dark sections. |
| `coral` (mark) | `#EF5433` | 239, 84, 51 | **The accent.** Brand mark only — use sparingly for highlights/flags. |

### Action / interactive
| Token | Hex | Role |
|---|---|---|
| `violet-cta-from` | `#3B03C5` | Primary button gradient start. |
| `violet-cta-to` | `#9B38FC` | Primary button gradient end. |
| `blue-electric` | `#2D62FF` | Secondary accent / links / data viz. |
| `blue-tint` | `#D9E5FF` | Light blue chip/pill background. |
| `indigo-tint` | `rgba(55,49,146,0.10)` | Soft indigo chip / icon-bubble background. |

**Primary CTA = the signature gradient:** `linear-gradient(90deg, #3B03C5 → #9B38FC)`, white text,
`10px` radius. This is the most repeated interactive element on the site.

### Neutrals
| Token | Hex | Role |
|---|---|---|
| `ink` | `#242526` | Body text (dark). |
| `black` | `#000000` | Secondary body text. |
| `paper` | `#F4F7FB` (≈`#F5F7FB`) | Page/section background (off-white, slightly cool). |
| `white` | `#FFFFFF` | Cards, nav. |
| `off-white-on-dark` | `#F4F7FB` | Text/labels on dark sections. |

### Gradients (the "atmosphere")
| Name | Value | Where |
|---|---|---|
| **Hero headline (cyan→violet)** | `radial-gradient(circle at 0 100%, #00D1FF, #8F33EB)` (also linear variants) | Big hero headlines, clipped to text. |
| **CTA / brand fill** | `linear-gradient(90deg, #3B03C5, #9B38FC)` | Buttons, full-width CTA bands, footer. |
| **Dark depth fill** | `linear-gradient(#100E5B, #39208E)` | Stats card, dark panels. |
| **Warm metric (orange→yellow)** | `linear-gradient(#F37A27, #FFE742)` clipped to text | Standout metrics on dark sections ("5x faster"). |
| **Pastel hero wash** | soft lavender → pink → mint, very low saturation, behind a faint grid | Full-bleed hero/section backgrounds. |
| **Fade-to-paper** | `linear-gradient(0deg, #F5F7FB, transparent)` | Section transitions. |

Dark sections also use **radial neon glow blobs** (cyan `#00D1FF`, magenta/violet `#8F33EB`, warm
`#F37A27`) bleeding behind/within dark cards — the "AI intelligence" motif.

---

## 4. Typography

**Live stack:** `Avenir, Impact, sans-serif` (geometric humanist sans). Multiple families are loaded
in `@font-face`, signaling their direction and accent usage:

| Family | Weights loaded | Role on site |
|---|---|---|
| **Avenir** (AvenirLTStd) | 300, 400, 500, 900 | Live primary — body + headings. **Licensed — don't ship.** |
| **Geist** | 100–900 (full) | Loaded; Vercel's free geometric sans — **our recommended substitute.** |
| **Inter** | 300–900 | Loaded; UI/body alternative. |
| **Instrument Serif** | 400 + italic | Editorial/italic accent ("We build the future of sourcing"). |
| **Playfair Display** | 400 + italic | High-contrast serif accent. |

### Type scale (from computed styles)
| Element | Size / line-height | Weight | Color | Notes |
|---|---|---|---|---|
| `h1` (hero) | 58px / 1.1 | **900** (Black) | `#373192` | Tight leading, can be gradient-clipped. |
| `h2` / `h3` | 32px / 1.2 | **900** | `#373192` | Section titles. |
| Body `p` | 16–18px / 1.5 | 400 (some 500) | `#000`–`#242526` | Generous line-height. |
| Button | 16px / 1.2 | 500 (Medium) | `#F4F7FB` (white) | — |
| Eyebrow / label | ~14px | 500 | indigo / muted | Above section titles. |

**Rules of the type system:** headings are **heavy (900) indigo, tight, often centered**; body is
regular-weight near-black at comfortable measure; a **serif italic** appears once or twice for an
editorial/emotional beat. Letter-spacing stays `normal` throughout.

### Recommendation for Bid Desk
Avenir is licensed — **use Geist** (they already ship it; free; ideal for Next.js via
`next/font`) as our body + heading face, with **weight 800–900 for headings, indigo `#373192`**.
Pair with **Instrument Serif (italic)** from Google Fonts for the occasional editorial accent. This
matches their direction without a font license.

---

## 5. Shape, depth & spacing

**Corner radii** (most→least used): `20px` (cards — the default), `24px`, `16px`, `12px`, `10px`
(buttons), `8px`; **pills** at `72px`/`160px` (badges, chips, image masks). Everything is soft —
nothing sharp.

**Shadows** (soft, diffuse, low-opacity — never harsh):
```
subtle    rgba(0,0,0,0.05)  5px 4px 5px            /* resting cards */
card      rgba(49,49,49,0.1) 3.2px 3.2px 27.81px   /* feature cards */
elevated  rgba(0,0,0,0.15)  10.8px 13.5px 40.5px   /* raised mockups */
floating  rgba(0,0,0,0.25)  16px 20px 60px         /* hero product-UI float */
```

**Layout:** centered max-width container (~1200px), heavy vertical whitespace between sections,
generous internal card padding. Section rhythm alternates **light (`#F4F7FB`) ↔ dark (`#0E0D59`)** to
create chapters. Faint **grid/graph-paper lines** sit behind pastel hero washes.

---

## 6. Component & section patterns ("UI/UX inks")

These are the recurring building blocks — replicate these, not pixel-exact pages.

1. **Top nav** — white, slim, sticky. Left: wordmark. Center: text links with dropdown carets
   (`AI Agents`, `Enterprise AI`, `Why Aerchain`, `Resources`, `About Us`). Right: one solid
   **violet-gradient "Book Demo"** pill. Mega-dropdowns list agents with small line-icons.

2. **Gradient hero** — centered, huge 900-weight headline with **cyan→violet gradient-clipped** key
   words, a one-line subhead, then **two CTAs**: primary violet-gradient button + a secondary
   ghost/outline button with a small play icon ("Play Video"). Background: pastel wash + faint grid.

3. **Floating product-UI mockup** — on product pages, a realistic app screenshot (vendor table,
   pricing, colored avatars) floats beside the headline with the `floating` shadow. *Proof through
   product, not stock art.*

4. **Feature checklist** — eyebrow + centered title, then a 2–3 column grid of items, each with a
   small **violet circular check icon** + short label. Used for "From Strategy to Selection".

5. **Alternating feature cards** — full-width rounded `20px` cards stacked vertically, alternating
   between **light lavender-tint** (dark text) and **solid violet-gradient** (white text), image on
   one side / copy on the other, flipping each row.

6. **Dark bento grid** — on a `#0E0D59` section, a grid of dark cards each holding a **radial neon
   glow blob** (cyan/magenta/orange) + a label. The "AI-First / intelligence" showcase.

7. **Before-vs-After / impact** — dark navy section, vertical timeline or split, with **warm
   orange→yellow gradient-clipped metrics** ("5x faster", "40% more accurate"). High-contrast proof.

8. **Mini data-viz cards** — impact cards with small bar rows and **green-check ✓ / red-✗ markers**
   (e.g. "40% More Accurate Vendor Selection"). *Directly relevant to our present/missing flags.*

9. **Stats card** — dark violet-gradient rounded card with **big white numbers** (count-up animated)
   + small labels, separated by thin dividers ("$15B+ spend managed").

10. **Logo wall** — "Trusted by Global Enterprises" + a row of **grayscale customer logos**.

11. **Founder / team cards** — white rounded cards: name, then a **small violet pill badge** for role
    ("CEO & Co-Founder"). Real team photos in a rounded mixed-size collage.

12. **Full-width CTA band** — a single violet-gradient rounded block, big white heading
    ("Experience the Future of Sourcing"), white button.

13. **Footer** — opens with a violet-gradient band, transitions into a dark navy footer with link
    columns in off-white.

**Icons:** thin **line/stroke icons** (20×20, 2px stroke, rounded caps), often inside a soft
**indigo-tint circular bubble**. Carets/arrows are stroked chevrons. No filled/glyph icon sets.

**Imagery:** real product screenshots + real team photography (rounded corners), plus abstract **3D
gradient orbs/spheres** with a sparkle motif for "AI". No generic stock illustration.

**Motion:** count-up number animations, scroll-triggered reveals, subtle gradient/orb drift. Tasteful,
not flashy.

---

## 7. Experience topology (page rhythm)

Standard page flow Aerchain repeats:

```
Sticky nav
  → Gradient hero (headline + dual CTA + floating product mockup)
  → Logo wall ("Trusted by…")
  → Dark "intelligence" section (bento / capability grid)
  → Light feature sections (alternating lavender ↔ violet cards)
  → Dark Before-vs-After / impact metrics (warm-gradient numbers)
  → Stats + social proof (numbers, founders, backers)
  → Full-width violet-gradient CTA band
  → Gradient → dark footer
```

The **light↔dark alternation** is the backbone: light = clarity/product, dark = AI depth/proof.

---

## 8. Applying this to Bid Desk (`apps/web`)

We use **Tailwind v4 + shadcn/ui**. Drop these tokens into the global stylesheet's `@theme` block,
then theme shadcn variables off them. This is the "best usable form" of the brand for our stack.

```css
/* apps/web/app/globals.css — Aerchain-derived tokens */
@theme {
  /* brand */
  --color-brand:        #373192;  /* indigo — headings, primary ink */
  --color-brand-navy:   #0E0D59;  /* dark sections */
  --color-brand-violet: #201045;  /* darkest cards */
  --color-accent:       #EF5433;  /* coral mark — flags/highlights, sparing */
  --color-electric:     #2D62FF;  /* secondary accent / data viz */

  /* surfaces */
  --color-paper:        #F4F7FB;  /* page background */
  --color-ink:          #242526;  /* body text */
  --color-tint-blue:    #D9E5FF;
  --color-tint-indigo:  oklch(from #373192 l c h / 0.10);

  /* radii & type */
  --radius-card: 20px;
  --radius-btn:  10px;
  --font-sans:   "Geist", ui-sans-serif, system-ui, sans-serif;
  --font-serif:  "Instrument Serif", Georgia, serif; /* editorial italic accents */
}
```

```css
/* signature primary button */
.btn-primary {
  background: linear-gradient(90deg, #3B03C5, #9B38FC);
  color: #F4F7FB; border-radius: 10px; font-weight: 500;
}
/* hero gradient headline */
.headline-gradient {
  background: radial-gradient(circle at 0 100%, #00D1FF, #8F33EB);
  -webkit-background-clip: text; background-clip: text; color: transparent;
  font-weight: 900; line-height: 1.1;
}
```

**Screen-by-screen mapping (our 5 buyer screens → their patterns):**

| Bid Desk screen | Borrow from Aerchain |
|---|---|
| **RFQ Overview** | Gradient hero headline + eyebrow; light section with feature checklist (violet check icons) for scope/items; stats card for the procurement event summary. |
| **Vendor Upload** | Clean white card on `#F4F7FB`, `20px` radius, soft shadow; violet-gradient primary action; ghost secondary. |
| **Extraction Review** | Mini data-viz cards with **✓/✗ markers** for present/missing/conflicting flags; indigo-tint chips for field labels; coral `#EF5433` reserved for risk/conflict highlights; evidence snippets in a quiet bordered block. |
| **Vendor Comparison** | Before-vs-After / side-by-side rhythm; dark section with warm-gradient standout metrics; comparability surfaced with the green-check/red-X language; alternating cards per vendor. |
| **Prompt Trace** | Dark `#0E0D59` "intelligence" panel with neon-glow accent; monospace blocks; the input→prompt→output flow as a vertical timeline. |

**Guardrails so we don't over-borrow** (per our `frontend-design` + rubric — *AI behavior beats UI
polish*): keep the gradient headline and violet CTA as **signatures, not wallpaper**; reserve coral
for genuine flags/risks (it's their scarcest color — make it mean something, which aligns with our
"absence is first-class" principle); keep the light↔dark section rhythm; don't fabricate stat numbers
to fill a stats card (use real extraction counts only).

---

## 9. Quick-reference cheat sheet

- **Ink/brand:** indigo `#373192` · **Depth:** navy `#0E0D59` · **Accent:** coral `#EF5433`
- **Primary button:** `linear-gradient(90deg,#3B03C5,#9B38FC)`, white text, `10px`
- **Hero headline:** cyan→violet gradient `#00D1FF → #8F33EB`, weight 900, clipped to text
- **Standout metric (dark):** warm gradient `#F37A27 → #FFE742`, clipped to text
- **Surface:** paper `#F4F7FB` · card radius `20px` · button radius `10px`
- **Font:** Avenir live → **use Geist** (free) + Instrument Serif italic accents
- **Shadows:** soft & diffuse, ≤0.25 opacity
- **Motifs:** floating product mockups · dark bento + neon glows · ✓/✗ data viz · violet check
  bubbles · grayscale logo wall · violet pill badges · light↔dark section rhythm
```
