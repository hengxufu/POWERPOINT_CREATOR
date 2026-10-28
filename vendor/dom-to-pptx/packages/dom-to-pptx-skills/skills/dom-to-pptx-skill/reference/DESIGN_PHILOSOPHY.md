# Design Philosophy: Premium UI/UX Engine

This document outlines the elite design principles for generating breathtaking PowerPoint slides using the `dom-to-pptx` skill.

## 1. Aesthetic Signatures

### Luminous Design Bias

Prioritize "Luminous Design Systems." Light themes are highly appreciated as they evoke clarity, premium editorial quality, and high-end brand sophistication (reminiscent of Apple, Leica, or Aesop).
Use off-whites, bone, ivory, and light-grey washes to create sophisticated layers.

### Typography Soul

- **Super-Titles**: `font-size: 80px; font-weight: 200; tracking: -0.05em; line-height: 1.1;`
- **Sub-Titles**: `font-size: 14px; font-weight: 800; tracking: 0.3em; text-transform: uppercase; color: [ACCENT];`
- **Body Copy**: `font-size: 24px; font-weight: 400; line-height: 1.6; color: [TYPE-SECONDARY];`

### Materiality & Physics

- **Glassmorphism (Safe)**: Use `background: rgba(255,255,255,0.8)` with a 1px solid white border. Do NOT use `backdrop-filter`.
- **Shadow Layering**: Use multi-layered shadows for depth. Example: `box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1), 0 2px 4px -1px rgba(0,0,0,0.06);`
- **Micro-Details**: Add subtle aesthetic details like a glowing dot next to a title or a 1px separator line (`height: 1px; width: 48px; background: [ACCENT]; margin-bottom: 16px;`).

---

## 2. Advanced Layout Strategies

### The Asymmetrical Editorial

Staggered layout where text and images overlap slightly.

- Massive image (e.g., width: 60%) positioned on one side.
- Floating text card overlapping the image by 10% (use `left` or `right` math to overlap).

### The Dynamic Bento-Box

Utilize a structured grid of cards with varying sizes.

- Never make boxes equal sizes.
- One "Hero" box spans two columns/rows.
- Smaller adjacent boxes for secondary data or icons.

### The Typographic Poster

For key quotes or statements.

- Massive, overlapping typography as the primary visual element.
- Treat text as art: `font-size: 200px; opacity: 0.05; position: absolute; top: -40px;`

### The Vogue Split-Screen

- One half: Stunning edge-to-edge masked image (`border-radius: 32px`).
- Other half: Vertically centered, highly spaced typography with generous padding.

---

## 3. Spatial Geometry & Anti-Overflow

### The Rule of Three

Never stack 3 or more cards vertically in a single column. If you have 3+ items, distribute them horizontally or use a Bento layout.

### Ruthless Brevity

Limit body text to a maximum of 15 words per block. Edit down content to its most punchy form.

### CSS Shrink-Wrapping

Every flex child and text container must have `min-height: 0` and `overflow: hidden`. This prevents vertical blowout, which is a critical failure in PPT exports.

---

## 4. Imagery

Images must feel premium and be locally accessible for high-fidelity rendering.

- **Prompting**: Use keywords like "cinematic lighting", "minimalist studio", "high-end editorial", "architectural photography".
- **Local Storage**: Always save generated images into an `images/` directory in the project root.
- **Relative Pathing**: Reference images in HTML using `/images/filename.png` to ensure compatibility with local dev servers.
- **Styling**: Always use `object-fit: cover` and `border-radius: 32px`.

---

## 5. Motion Design & Staging

Every presentation should feel alive and dynamic, but motion must be handled with precision and taste. Never use animations or transitions arbitrarily.

### The Complete Staging Rule (No Floating Orphans)

A slide is a coordinated visual stage. If a slide uses entry animations, **every foreground element** (titles, subtitles, body text, cards, images, lists) must be part of that entry sequence.

- **The Problem**: Animating a title while leaving description text or cards statically visible on slide load looks broken. The static content is exposed first, and the title animates in later,
  destroying the visual hierarchy.
- **The Solution**: Chain animations sequentially or stagger them in parallel using triggers:
  - **Sequential Sequence**: Title plays on click (`animate-trigger-on-click`), subtitle plays immediately after (`animate-trigger-after`), and the body text/cards play after that.
  - **Staggered Group Sequence**: The parent element or first element starts on-click, and subsequent items build with a small delay (`animate-trigger-with` combined with `animate-delay-[150]`).

### Tone-Matching Matrix

Choose slide transitions and element animations that fit the audience and deck purpose:

<!-- prettier-ignore -->
| Genre / Mood | Approved Transitions | Approved Animations | Best Practices |
| :--- | :--- | :--- | :--- |
| **Executive / Corporate**<br>_(Investor pitch, board meeting, tech architecture)_ | `slide-transition-fade`<br>`slide-transition-push` (with `transition-dir-l` / `transition-dir-u`) | `fade-in`<br>`fly-in` (with `to-up` or `to-right`) | Keep durations standard (`700ms` to `1000ms`). Avoid goofy motion. Transitions should feel like clean slide changes. |
| **Creative / Editorial**<br>_(Design studio, fashion lookbook, event announcement)_ | `slide-transition-gallery`<br>`slide-transition-wind-left`<br>`slide-transition-flip`<br>`slide-transition-doors` | `zoom-in`<br>`bounce-in`<br>`wipe-in`<br>Letter/Paragraph builds | Use dramatic entries and custom delays to create theatrical suspense. Pair circular and zoom effects with bold graphics. |
| **Tech Launch / Product Demo**<br>_(Interactive demo, feature highlight, landing page)_ | `slide-transition-split`<br>`slide-transition-push`<br>`slide-transition-checker` | `split-in`<br>`fly-in`<br>`random-bars-in`<br>`wheel` | Focus on grid-wise reveals. Reveal feature cards from different directions to imply structure and dimensionality. |

### Motion Recipes & Combinations

#### Recipe A: The Premium Typing / Text Reveal

Use this to reveal main titles or key quotes letter-by-letter with a high-end, smooth fade.

- **Classes to apply**: `fade-in letter animate-duration-[400] animate-trigger-on-click`
- **Effect**: The letters rapidly build from left to right as if typing, while fading in smoothly.
- **Usage**: Keep the duration short (`300ms` - `500ms`) so it doesn't slow down the presenter.

#### Recipe B: The Staggered Grid Reveal

For bento grids, card groups, or 3-column feature lists.

- **Structure**:
  - _Card 1_: `fly-in to-up animate-duration-[700] animate-trigger-after`
  - _Card 2_: `fly-in to-up animate-duration-[700] animate-delay-[150] animate-trigger-with`
  - _Card 3_: `fly-in to-up animate-duration-[700] animate-delay-[300] animate-trigger-with`
- **Effect**: The cards rise up smoothly from the bottom in a quick, elegant sequence (Card 1, then Card 2, then Card 3) after the previous animation (e.g. the slide title) completes.

#### Recipe C: Asymmetric Split Reveal

Perfect for a split-screen layout (Image on left, text on right).

- _Left (Image)_: `wipe-in to-right animate-duration-[900] animate-trigger-after`
- _Right (Text Container)_: `fly-in to-left animate-duration-[750] animate-delay-[200] animate-trigger-with`
- **Effect**: The image wipes in from left-to-right, and just as it finishes, the text flies in from the right edge.

## See Also

<!-- prettier-ignore -->
| File | Purpose |
| --- | --- |
| [SAFE_HTML_TEMPLATE.md](reference/SAFE_HTML_TEMPLATE.md) | Copy-paste skeleton that satisfies every compatibility rule; validator + export pre-wired |
| [STYLE_WHITELIST.md](reference/STYLE_WHITELIST.md) | Definitive ✅/⚠️/❌ list of CSS & HTML features, with alternatives |
| [ANIMATIONS_WHITELIST.md](reference/ANIMATIONS_WHITELIST.md) | Exhaustive list of whitelisted element-level animations, triggers, and text builds. |
| [TRANSITIONS_WHITELIST.md](reference/TRANSITIONS_WHITELIST.md) | Exhaustive list of whitelisted slide-level transition effects and durations. |
| [VALIDATION.md](reference/VALIDATION.md) | Pre-export runnable scanner (`window.validateSlides()`) and manual checklist |
| [SAMPLE_PROMPTS.md](reference/SAMPLE_PROMPTS.md) | 14 ready-to-use prompts for common slide layouts updated for premium aesthetics. |
| [STYLE_PRESETS.md](reference/STYLE_PRESETS.md) | dom-to-pptx-compatible visual presets with HEX hierarchies and materiality descriptions. |
| [TEMPLATE.md](reference/TEMPLATE.md) | HTML structure and layout pattern library (cards, sidebars, steps, …) |
