# Transition Whitelist for dom-to-pptx

This document is the definitive reference for **slide-level transitions** supported by `dom-to-pptx` (defined in `transitions.css` and compiled into native PowerPoint `<p:transition>` structures on
the slide).

---

## 1. Supported Transition Classes

Transitions are applied directly to the `.slide` container element.

### Classic Slide Transitions

<!-- prettier-ignore -->
| Class | Action | Supported Modifiers (Directions / Options) |
| :--- | :--- | :--- |
| `slide-transition-fade` | Fades the slide in from black or the previous slide. | None |
| `slide-transition-cut` | Instantly displays the slide (no animation). | None |
| `slide-transition-push` | Slides the slide in, pushing the previous slide out. | Direction: `transition-dir-u` (up), `transition-dir-d` (down), `transition-dir-l` (left), `transition-dir-r` (right) |
| `slide-transition-wipe` | Wipes the slide in using a sliding edge. | Direction: `transition-dir-l` (left), `transition-dir-r` (right) |
| `slide-transition-pull` | Pulls the slide in, sliding over the previous slide. | Direction: `transition-dir-u` (up), `transition-dir-d` (down) |
| `slide-transition-split` | Splits the slide open from the center. | Orientation: `transition-orient-horz`, `transition-orient-vert`<br>Direction: `transition-dir-in`, `transition-dir-out` |
| `slide-transition-strips` | Reveals the slide in diagonal strips. | Direction: `transition-dir-ld` (left-down), `transition-dir-rd` (right-down) |
| `slide-transition-dissolve` | Dissolves the slide in using a pixelated noise mask. | None |
| `slide-transition-checker` | Tiles the slide in checkerboard style. | Direction: `transition-dir-horz` |
| `slide-transition-randomBar` | Reveals the slide using random stripes. | Direction: `transition-dir-horz`, `transition-dir-vert` |
| `slide-transition-circle` | Opens the slide using a circular scale zoom. | None |
| `slide-transition-comb` | Wipes the slide in using comb-like lines. | Direction: `transition-dir-vert` |
| `slide-transition-wheel` | Reveals the slide in spoke segments. | Spokes: `transition-spokes-1`, `transition-spokes-4` |
| `slide-transition-newsflash` | Spins the slide in from a distance. | None |
| `slide-transition-blinds` | Reveals the slide using window blinds stripes. | Direction: `transition-dir-vert` |
| `slide-transition-flash` | Flashes a bright light before showing the slide. | None |

### PowerPoint 2010 (P14) Transitions

<!-- prettier-ignore -->
| Class | Action | Supported Modifiers (Directions / Options) |
| :--- | :--- | :--- |
| `slide-transition-honeycomb` | Reveals the slide via a honeycomb cellular pattern. | None |
| `slide-transition-ripple` | Slides the slide in with liquid ripples. | None |
| `slide-transition-glitter` | Reveals the slide in hexagonal/diamond sparkles. | Pattern: `transition-pattern-hexagon`, `transition-pattern-diamond` |
| `slide-transition-vortex` | Spins the slide in like a circular vortex. | Direction: `transition-dir-l`, `transition-dir-r`, `transition-dir-u`, `transition-dir-d` |
| `slide-transition-shred-in` / `slide-transition-shred-out` | Shreds the slide in diagonal slats. | None |
| `slide-transition-shred-rect-in` / `slide-transition-shred-rect-out` | Shreds the slide in rectangular grid boxes. | None |
| `slide-transition-switch` | Switches slides by panning to the side. | Direction: `transition-dir-l`, `transition-dir-r` |
| `slide-transition-flip` | Flips the slide like a 3D board. | Direction: `transition-dir-l`, `transition-dir-r` |
| `slide-transition-gallery` | Pans slides like in a 3D image gallery. | Direction: `transition-dir-l`, `transition-dir-r` |
| `slide-transition-prism` | Rotates slides on a 3D prism. | Direction: `transition-dir-l`, `transition-dir-r` |
| `slide-transition-prism-inverted` / `slide-transition-prism-inverted-r` | Rotates slides on an inside-out 3D prism. | None |
| `slide-transition-warp` | Warps slides in/out from depth. | Direction: `transition-dir-in`, `transition-dir-out` |
| `slide-transition-doors` | Opens the slide like vertical/horizontal double doors. | Direction: `transition-dir-vert` |

### PowerPoint 2013+ (P15) Transitions

<!-- prettier-ignore -->
| Class | Action |
| :--- | :--- |
| `slide-transition-wind-left` / `slide-transition-wind-right` | Blows the slide away like wind. |
| `slide-transition-airplane-left` / `slide-transition-airplane-right` | Folds the slide into a paper plane and flies it away. |
| `slide-transition-origami-left` / `slide-transition-origami-right` | Folds the slide into an origami crane and flies it away. |
| `slide-transition-fallover-left` / `slide-transition-fallover-right` | Tips the slide forward, falling off-screen. |
| `slide-transition-drape-left` / `slide-transition-drape-right` | Drops the slide like a theatrical curtain drape. |
| `slide-transition-prestige` | Pulls the slide up like a rolling screen. |
| `slide-transition-fracture` | Shatters the slide like glass. |
| `slide-transition-crush` | Crushes the slide like paper and throws it away. |
| `slide-transition-pagecurldouble` / `slide-transition-pagecurldouble-r` | Curls slide like turning double book pages. |
| `slide-transition-pagecurlsingle` / `slide-transition-pagecurlsingle-r` | Curls slide like turning a single page. |
| `slide-transition-curtains` | Opens/closes slides like cinema stage curtains. |
| `slide-transition-peelOff` | Peels the slide off-screen like a sticky note. |

---

## 2. Transition Speed / Duration

Apply transition speed classes to define slide transition length:

- **Fast**: `transition-duration-fast` (approx. `1000ms`)
- **Normal**: `transition-duration-normal` (approx. `1500ms`)
- **Slow**: `transition-duration-slow` (approx. `2000ms`)
- **Custom**: `transition-dur-[MS]` (e.g. `transition-dur-800` or `transition-dur-3000` for customized millisecond timing)

---

## 3. Intelligent Transition Design & Tone Matching

When choosing transitions, align the transition type and speed with the presentation's genre and purpose:

1. **Executive / Professional Decks** (Board meetings, academic talks, sales reports):
   - **Approved Transitions**: Use subtle, classic changes like `slide-transition-fade` or `slide-transition-push` (with direction `transition-dir-l` or `transition-dir-r`).
   - **Guideline**: Transitions should be fast or normal (`transition-duration-fast` or `transition-duration-normal`). They must not distract the audience from the content.
2. **Creative / Launch Decks** (Product launches, creative design portfolios, portfolio lookbooks):
   - **Approved Transitions**: Use more premium, expressive transitions like `slide-transition-gallery`, `slide-transition-doors`, `slide-transition-wind-left`, `slide-transition-curtains` (excellent
     for slide 1/intro).
   - **Guideline**: Can use slower transition durations (e.g. `transition-duration-slow` or custom `transition-dur-2000`) for dramatic impact and pacing.

---

## See also

- [SAFE_HTML_TEMPLATE.md](SAFE_HTML_TEMPLATE.md) — a template that only uses ✅ items
- [STYLE_WHITELIST.md](STYLE_WHITELIST.md) — exhaustive allow/block list
- [VALIDATION.md](VALIDATION.md) — a scanner that flags ❌/⚠️ items in your DOM
- [ANIMATIONS_WHITELIST.md](ANIMATIONS_WHITELIST.md) — exhaustive list of whitelisted element-level animations, triggers, and text builds
- [TEMPLATE.md](TEMPLATE.md) — layout patterns using whitelisted features
