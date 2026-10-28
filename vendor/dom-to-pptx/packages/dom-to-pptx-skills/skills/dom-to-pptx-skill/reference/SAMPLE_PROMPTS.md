# Sample Prompts for Common Slide Layouts

Copy-paste prompts that produce dom-to-pptx-safe HTML for the layouts people ask for most. Each prompt is self-contained — drop in your content, adjust the style preset, and the result can go straight
into the template from [SAFE_HTML_TEMPLATE.md](SAFE_HTML_TEMPLATE.md).

Every prompt below already bakes in the constraints from [STYLE_WHITELIST.md](STYLE_WHITELIST.md): fixed 1920×1080, inline styles, absolute/flex layout, https images, slide transitions and element
animations via whitelisted CSS classes, and no custom keyframes or blocked properties.

---

## The Design Engine (Global Instructions)

When generating slides, always adhere to these elite design principles:

- **Aesthetics:** Clean, modern, "Apple Keynote" style. Use multi-layered shadows, subtle gradients, and large rounded corners (`32px`).
- **Typography:** Create dramatic contrast. Pair massive, ultra-thin headers with bold, wide-tracked subheaders.
- **Layout:** Prioritize whitespace (60%+). Implement **Advanced Layouts** from `DESIGN_PHILOSOPHY.md` (Bento-Box, Asymmetrical Editorial, Typographic Poster).
- **Anti-Overflow:** Every container must have `overflow: hidden` and `min-height: 0`. Limit body text to 12-15 words max.
- **Images:** Use hyper-aesthetic custom made images or use images from Pexels, Unsplash, URL from internet. Style them with `object-fit: cover` and `32px` border-radius.

---

## Theme Directive Snippet

Copy and paste this into any prompt to apply a specific theme:

```
<THEME_CONFIG>
  - Palette: [HEX1 (BG)], [HEX2 (SURFACE)], [HEX3 (ACCENT)], [HEX4 (TEXT1)], [HEX5 (TEXT2)]
  - Vibe: [PRESET NAME] from STYLE_PRESETS.md
  - Logic: Use HEX1 for slide background, HEX2 for cards, HEX3 for highlights, HEX4 for headings.
</THEME_CONFIG>
```

---

```
<SLIDE_CONFIG>
  <TYPE>Title Slide</TYPE>
  <CANVAS>1920x1080, position: relative, overflow: hidden</CANVAS>
  <CONTENT>
    <TITLE>[MAIN TITLE]</TITLE>
    <SUBTITLE>[SUBTITLE / TAGLINE]</SUBTITLE>
    <META>[NAME • DATE]</META>
  </CONTENT>
  <VISUALS>
    - Background: Linear-gradient (135deg, HEX1 0%, HEX2 100%)
    - Accent: A single geometric shape (bar or circle) in HEX3
    - Image (optional): You can use any image from the web, from Pexels, Unsplash, URL from internet, or any ai image generator.
  </VISUALS>
  <TYPOGRAPHY>
    - Title: 96px, weight 800, tracking-tight, Arial/Helvetica
    - Subtitle: 36px, weight 400, opacity 0.8
    - Meta: 20px, uppercase, tracking-widest
  </TYPOGRAPHY>
  <CONSTRAINTS>No transforms except rotate; slide transitions and element animations via whitelisted CSS classes only; inline layout styles only.</CONSTRAINTS>
</SLIDE_CONFIG>
```

---

## 2. Agenda / section list

```
Generate a dom-to-pptx-safe agenda slide (1920×1080, class="slide") listing:

1. [ITEM 1]
2. [ITEM 2]
3. [ITEM 3]
4. [ITEM 4]
5. [ITEM 5]

Requirements:
- Left-aligned numbered list, each row = number circle + title + optional one-line description.
- Use display: flex on each row; circles are 72×72 px with border-radius: 50%.
- Absolute-position the list block at left: 120px; top: 200px.
- Heading "Agenda" (or equivalent) at top: 100px.
- Inline styles, https images only (skip images if not needed), no transforms except rotate.
```

---

## 3. Content slide — bullets (4–6 points)

```
<SLIDE_CONFIG>
  <TYPE>Bullet List</TYPE>
  <CANVAS>1920x1080, background: #FFFFFF</CANVAS>
  <CONTENT>
    <HEADING>[SECTION HEADING]</HEADING>
    <LIST>
      - [POINT 1]
      - [POINT 2]
      - [POINT 3]
      - [POINT 4]
    </LIST>
  </CONTENT>
  <LAYOUT>
    - Heading at top: 100px, left: 120px (font-size 64px)
    - List container at top: 280px, left: 120px, max-width: 1400px
    - Spacing: gap-8 between points
  </LAYOUT>
  <TYPOGRAPHY>
    - Bullets: 32px, line-height 1.6, Arial/Helvetica
  </TYPOGRAPHY>
  <CONSTRAINTS>ul list-style: disc; margin-bottom: 32px per li; inline styles only.</CONSTRAINTS>
</SLIDE_CONFIG>
```

---

## 4. Two-column: text + image

```
<SLIDE_CONFIG>
  <TYPE>Visual Split</TYPE>
  <CANVAS>1920x1080</CANVAS>
  <CONTENT>
    <LEFT_COL>
      <HEADING>[HEADING]</HEADING>
      <BODY>[BODY COPY]</BODY>
      <CTA>[CTA]</CTA>
    </LEFT_COL>
    <RIGHT_COL>
      <IMAGE>https://www.example.com/image.png</IMAGE>
    </RIGHT_COL>
  </CONTENT>
  <LAYOUT>
    - Split: 45/55 ratio
    - Left Col: Absolute top: 200px, left: 120px, width: 700px
    - Right Col: Absolute top: 120px, right: 100px, width: 900px, height: 840px
  </LAYOUT>
  <VISUALS>
    - Image: object-fit: cover, border-radius: 32px, shadow-2xl
  </VISUALS>
  <CONSTRAINTS>No backdrop-filter; inline styles; absolute positioning for columns.</CONSTRAINTS>
</SLIDE_CONFIG>
```

---

## 5. Two-column: text + text (compare/contrast)

```
Generate a dom-to-pptx-safe comparison slide (1920×1080, class="slide").

Left column: "[LEFT LABEL]"
- [LEFT POINT 1]
- [LEFT POINT 2]
- [LEFT POINT 3]

Right column: "[RIGHT LABEL]"
- [RIGHT POINT 1]
- [RIGHT POINT 2]
- [RIGHT POINT 3]

Requirements:
- Two cards side-by-side starting at top:200px, left:120px / left:1000px. Each card 800×720, padding 60px, border-radius 16px, box-shadow.
- Left card background #ffffff, right card background linear-gradient(135deg, #4361ee 0%, #667eea 100%) with white text.
- Column headers 40px, bullets 26px, line-height 1.5.
- No transforms except rotate; inline styles.
```

---

## 6. Stats / big-number slide

```
Generate a dom-to-pptx-safe stats slide (1920×1080, class="slide") with three big numbers:

Stat 1: [NUMBER] — [LABEL]
Stat 2: [NUMBER] — [LABEL]
Stat 3: [NUMBER] — [LABEL]

Optional: [SHORT INTRO LINE ABOVE THE STATS]

Requirements:
- Intro line (if provided) at top:160px, centered, 32px, muted color.
- Stats row at top:400px using display: flex; justify-content: space-around; left/right 120px.
- Each stat: number 120–140px, label 26px below with 16px gap.
- Different accent color per number from the chosen palette.
- Background: #ffffff; no transforms except rotate; inline styles.
```

---

## 7. Quote / pull-quote slide

```
Generate a dom-to-pptx-safe quote slide (1920×1080, class="slide").

Quote: "[QUOTE TEXT]"
Attribution: [NAME, ROLE]

Requirements:
- Dark background (#0f0f0f or #1a1a1a) with a single decorative element — a thin accent line above the quote.
- Quote text centered, Georgia serif, italic, 52–60px, line-height 1.4, max width 1400px.
- Attribution 24px, muted color (#9a9590), 40px below the quote.
- Absolute-position the block around top:300px.
- Inline styles, no transforms except rotate.
```

---

## 8. Image-hero / full-bleed image with title

```
Generate a dom-to-pptx-safe hero slide (1920×1080, class="slide").

Background image: [HTTPS URL]
Title: [HERO TITLE]
Subtitle: [HERO SUBTITLE]

Requirements:
- <img> at position:absolute; top:0; left:0; width:1920; height:1080; object-fit:cover.
- Dark gradient overlay: a div at position:absolute covering the whole slide, background linear-gradient(180deg, rgba(0,0,0,0) 0%, rgba(0,0,0,0.7) 100%).
- Title 88px white, subtitle 32px #e0e0e0, both absolute-positioned bottom-left (left:120px; bottom:160px / bottom:100px).
- No transforms except rotate; no backdrop-filter; inline styles only.
```

---

## 9. Numbered steps / process

```
Generate a dom-to-pptx-safe 3-step process slide (1920×1080, class="slide").

Title: [PROCESS NAME]
Step 1: [TITLE] — [1-sentence description]
Step 2: [TITLE] — [1-sentence description]
Step 3: [TITLE] — [1-sentence description]

Requirements:
- Title 52px at top:100px, left:120px.
- Steps stacked vertically starting at top:240px OR horizontally in a 3-column flex row.
- Each step: 80×80 circle with the step number (36px, bold, white) + title (32px) + description (22px, #666).
- Use display:flex; align-items:flex-start; margin-bottom:48px between rows.
- Accent color for the circles from the chosen palette.
- Inline styles; no transforms except rotate.
```

---

## 10. Card grid (2×2 or 3-across)

```
Generate a dom-to-pptx-safe card-grid slide (1920×1080, class="slide") with [2x2 / 3 cards].

Section title: [SECTION TITLE]

Card 1: [TITLE] — [1-line description]
Card 2: [TITLE] — [1-line description]
Card 3: [TITLE] — [1-line description]
(Card 4: [TITLE] — [1-line description])

Requirements:
- Section title 48px at top:80px, left:120px.
- Grid container at top:240px, left:120px; use display: flex; flex-wrap: wrap; gap: 32px.
- Each card: fixed 800×320 (2x2) or 540×420 (3-across), background #ffffff, border-radius 16px, padding 40px, box-shadow 0 8px 32px rgba(0,0,0,0.1).
- Card title 32px, description 20px, color #666.
- Optional icon on each card: a 48×48 rounded square filled with the accent color.
- Inline styles, no transforms except rotate, no backdrop-filter.
```

---

## 11. Sidebar + content

```
Generate a dom-to-pptx-safe sidebar slide (1920×1080, class="slide").

Sidebar (left, 400px wide, dark):
- Brand / logo placeholder (80×80 accent-color square with border-radius:12px)
- Brand name: [NAME]
- Tagline: [ONE LINE]

Main content (right):
- Heading: [HEADING]
- Paragraph: [BODY]
- Optional bulleted list: [3–4 POINTS]

Requirements:
- Sidebar: position: absolute; left:0; top:0; width:400; height:1080; background: #1a1a1a; padding:60px 40px.
- Main: position: absolute; left:500px; top:100px; right:100px.
- Heading 48px, body 24px line-height 1.6, bullets 22px.
- Inline styles, no transforms except rotate.
```

---

## 12. Table / grid of data

```
Generate a dom-to-pptx-safe table slide (1920×1080, class="slide").

Heading: [TABLE TITLE]
Columns: [COL 1], [COL 2], [COL 3], [COL 4]
Rows:
  - [ROW 1 VALUES]
  - [ROW 2 VALUES]
  - [ROW 3 VALUES]
  - [ROW 4 VALUES]

Requirements:
- Use a native <table> (dom-to-pptx v1.1.6+ renders this as a native PPTX table).
- Heading 48px at top:80px, left:120px; table at top:200px, left:120px, width:1680.
- Header row background #1a1a1a, white text, font-weight 700.
- Body rows alternate backgrounds (#ffffff / #f5f5f5), text #333 at 22px.
- border-collapse: collapse; cell padding 20px 24px; 1px solid #e0e0e0 borders.
- Inline styles; no transforms except rotate.
```

---

## 13. Timeline (horizontal)

```
Generate a dom-to-pptx-safe horizontal timeline slide (1920×1080, class="slide") with 4 events.

Title: [TIMELINE TITLE]
Event 1 — [DATE]: [LABEL]
Event 2 — [DATE]: [LABEL]
Event 3 — [DATE]: [LABEL]
Event 4 — [DATE]: [LABEL]

Requirements:
- Title at top:100px, left:120px (48px).
- A horizontal rule at top:540px, left:120px, width:1680, height:4px, background:#cccccc — serves as the axis.
- Four dots (24×24, border-radius:50%, accent color) absolute-positioned along the axis (e.g., left:160, 640, 1120, 1600 at top:530px).
- Above each dot: date (20px bold); below each dot: label (22px, 180px-wide column, centered).
- Use position:absolute with explicit left/top values (no translate).
- Inline styles; no transforms except rotate.
```

---

## 14. Closing / thank-you slide

```
Generate a dom-to-pptx-safe closing slide (1920×1080, class="slide").

Big message: [THANK YOU / CALL TO ACTION]
Secondary: [NEXT-STEP LINE, URL, OR CONTACT]
Optional: [SMALL FOOTER — NAME, LOGO TEXT]

Requirements:
- Centered composition using flex: position:relative + an inner flex container with justify-content:center; align-items:center; flex-direction:column; width/height 1920×1080.
- Big message 96–120px; secondary 32px with 40px top margin.
- Background: linear-gradient or solid from the chosen palette.
- Optional decorative accent bar (120×6, accent color) 40px above the message.
- Inline styles; no transforms except rotate; no backdrop-filter.
```

---

## 15. Full deck (multi-slide) — combined prompt

When you want the whole deck in one shot:

```
Generate a complete dom-to-pptx-safe HTML deck with [N] slides, using the safe template structure.

Deck outline:
1. Title — [MAIN TITLE] / [SUBTITLE]
2. Agenda — [3–5 ITEMS]
3. [SECTION 1 CONTENT]
4. [SECTION 2 CONTENT]
...
N. Thank you — [CLOSING]

Global requirements:
- Use the [PRESET NAME] palette from STYLE_PRESETS.md for backgrounds, accents, and text.
- Every slide: 1920×1080, class="slide", position: relative, overflow: hidden, inline styles.
- No transforms except rotate; slide transitions and element animations via whitelisted CSS classes only; no backdrop-filter, radial-gradient, or viewport units.
- All images: https:// CORS-enabled URL (Unsplash preferred), object-fit: cover, border-radius where appropriate.
- Google Fonts <link> in <head> with crossorigin="anonymous".
- Wrap all slides in <div class="slide-stage"> and include the export button + validator + export script from SAFE_HTML_TEMPLATE.md.

Return a single valid HTML file ready to open in a browser.
```

---

## Prompt-writing tips

- **Always specify 1920×1080** in the prompt — otherwise the model may default to responsive sizing, which breaks the exporter.
- **Mention "inline styles only"** — otherwise `<style>` tags with classes tend to appear, which works but is harder to debug.
- **Name the blocked and allowed motion properties explicitly** ("no transforms except rotate; slide transitions and element animations only via whitelisted classes; no backdrop-filter,
  radial-gradient") — vague guidance like "be compatible" isn't enough.
- **Instruct the AI to apply the "Complete Staging Rule" for motion**: If any element is animated, _all_ foreground elements on the slide must be animated in a coordinated chain or stagger. Ensure
  there are no static foreground elements showing before their containing slides/headers animate in.
- **Specify the Motion Tone & Pacing**: Explicitly prompt for the transition style (e.g. subtle `fade`/`push` for professional decks, or expressive `gallery`/`doors` for creative launches) and specify
  normal/fast speeds.
- **Request specific motion recipes**: Ask the model to use the typing reveal effect (`fade-in letter animate-duration-[400]`) on titles, or staggered parallel entry on card grids.
- **Pin image sources** — give a fallback Unsplash URL in the prompt so the model doesn't invent unreachable URLs.
- **Append the validator** — every prompt above assumes the output will be dropped into the safe template, which already runs `window.validateSlides()` before export.

---

## See also

- [SAFE_HTML_TEMPLATE.md](SAFE_HTML_TEMPLATE.md) — the shell the generated slides drop into
- [STYLE_WHITELIST.md](STYLE_WHITELIST.md) — what these prompts are working around
- [VALIDATION.md](VALIDATION.md) — runs after generation to catch regressions
- [ANIMATIONS_WHITELIST.md](ANIMATIONS_WHITELIST.md) — exhaustive list of whitelisted element-level animations, triggers, and text builds
- [TRANSITIONS_WHITELIST.md](TRANSITIONS_WHITELIST.md) — exhaustive list of whitelisted slide-level transition effects and durations
- [STYLE_PRESETS.md](STYLE_PRESETS.md) — palettes referenced in the prompts
- [TEMPLATE.md](TEMPLATE.md) — more hand-written layout examples
