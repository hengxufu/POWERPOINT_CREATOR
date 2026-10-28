# Animation Whitelist for dom-to-pptx

This document is the definitive reference for the **element-level animations** supported by `dom-to-pptx` (defined in `animations.css` and compiled into native PowerPoint `<p:timing>` structures).

---

## 1. Supported Animation Presets

Animations are split into **Entrance** and **Exit** classes.

### Entrance Animations (10)

<!-- prettier-ignore -->
| Class | Action | Supported Modifiers / Parameters |
| :--- | :--- | :--- |
| `fade-in` | Fades element in from `opacity: 0` to `1`. | None |
| `appear` | Instantly displays element at start. | None |
| `zoom-in` | Grows element from `scale(0.1)` to full scale. | None |
| `fly-in` | Flies element in from the slide boundary. | Direction: `to-up` (default), `to-down`, `to-left`, `to-right` |
| `wipe-in` | Wipes element in (clip mask sweep). | Direction: `to-up`, `to-down` (default), `to-left`, `to-right` |
| `split-in` | Splits element open from the center. | Orientation: `vertical` (default), `horizontal` |
| `wheel` | Spreads element out in a clockwise circular mask. | None |
| `bounce-in` | Flies element in with a spring bounce effect. | None |
| `checkerboard-in` | Transitions element using square grid tiles. | None |
| `random-bars-in` | Wipes element in using horizontal stripes. | Orientation: `vertical`, `horizontal` (default) |

> [!NOTE] Animation presets also accept aliases for compatibility (e.g. `fly-in-left` maps to `fly-in` with `to-left`, and `rise-up` or `drop-in` map to `fade-in`).

### Exit Animations (10)

<!-- prettier-ignore -->
| Class | Action | Supported Modifiers / Parameters |
| :--- | :--- | :--- |
| `fade-out` | Fades element out from `1` to `opacity: 0`. | None |
| `disappear` | Instantly hides element at end. | None |
| `zoom-out` | Shrinks element from full scale down to `scale(0.1)`. | None |
| `fly-out` | Flies element out past the slide boundary. | Direction: `to-up`, `to-down` (default), `to-left`, `to-right` |
| `wipe-out` | Wipes element out (clip mask sweep). | Direction: `to-up`, `to-down` (default), `to-left`, `to-right` |
| `split-out` | Splits element closed toward the center. | Orientation: `vertical` (default), `horizontal` |
| `wheel-out` | Contracts element in a clockwise circular mask. | None |
| `bounce-out` | Flies element out with a downward bouncing drop. | None |
| `checkerboard-out` | Disappears element using square grid tiles. | None |
| `random-bars-out` | Disappears element using horizontal stripes. | Orientation: `vertical`, `horizontal` (default) |

---

## 2. Timing Options (Utility Classes)

Control the duration and delay of your animations using custom utility classes:

- **Duration**: Set length of animation in milliseconds:
  - Syntax: `animate-duration-[MS]` (e.g., `animate-duration-[1000]`, `animate-duration-[400]`)
  - Default: `700ms`
- **Delay**: Offset the start of the animation in milliseconds:
  - Syntax: `animate-delay-[MS]` (e.g., `animate-delay-[200]`, `animate-delay-[500]`)
  - Default: `0ms`

---

## 3. Triggers & Flows

Control how slide elements coordinate their playback sequence:

<!-- prettier-ignore -->
| Class | PowerPoint Event | Action |
| :--- | :---: | :--- |
| `animate-trigger-on-click` _(default)_ | `onClick` | Pauses sequence; waits for user mouse click to play. |
| `animate-trigger-with` / `with-previous` | `withPrevious` | Starts simultaneously with the preceding animation card. |
| `animate-trigger-after` / `after-previous` | `afterPrevious` | Starts automatically after the preceding animation completes. |

---

## 4. Text Builds & Splits

Animate text blocks incrementally rather than all at once:

- **Paragraph Build**: Animates paragraphs or list rows one at a time.
  - Syntax: Add `paragraph` (or `animate-build-paragraph`) to the text container.
  - Requirement: Child block elements (like `<p>` tags) should be used inside. _Tip: Style children with `display: inline-block` in CSS so the parent is recognized as a text container._
- **Character / Letter Build**: Animates text letter-by-letter.
  - Syntax: Add `letter` (or `animate-build-letter`) to the text container.

---

## 5. Intelligent Motion Design & Recipes

When animating elements on a slide, apply these best practices to ensure professional quality and visual flow:

1. **Avoid Floating Orphans**: Never animate a slide's title without also animating its body or surrounding items. If any element on the slide is animated, all foreground elements must be animated in
   a coordinated sequence.
2. **Stagger Parallel Items**: When revealing grids, cards, or lists, use parallel stagger patterns.
   - Combine `animate-trigger-with` on secondary elements with incremented delays like `animate-delay-[150]`, `animate-delay-[300]`, etc.
3. **Use the "Typing Effect" for Key Text**:
   - Combine `fade-in` with the `letter` build class and set a duration of `300ms` or `400ms`. This creates a premium typing-style sweep.
   - Example: `<h1 class="fade-in letter animate-duration-[400]">Executive Concept</h1>`
4. **Use Paragraph Builds for Lists**:
   - Set `paragraph` on the parent container to reveal bullet points one click at a time, preventing cognitive overload.

---

## See also

- [SAFE_HTML_TEMPLATE.md](SAFE_HTML_TEMPLATE.md) — a template that only uses ✅ items
- [STYLE_WHITELIST.md](STYLE_WHITELIST.md) — exhaustive allow/block list
- [VALIDATION.md](VALIDATION.md) — a scanner that flags ❌/⚠️ items in your DOM
- [TRANSITIONS_WHITELIST.md](TRANSITIONS_WHITELIST.md) — exhaustive list of whitelisted slide-level transition effects and durations
- [TEMPLATE.md](TEMPLATE.md) — layout patterns using whitelisted features
