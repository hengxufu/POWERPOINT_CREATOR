# Safe HTML Template for dom-to-pptx

A minimal, copy-paste starting template that respects **every** dom-to-pptx compatibility constraint. Use this as the skeleton for any new deck — every rule below is enforced by the scanner in
[VALIDATION.md](VALIDATION.md).

## Why "safe"?

dom-to-pptx converts DOM → native PPTX shapes by reading `getBoundingClientRect()` and computed styles. It ignores animations, fails silently on non-CORS images, and has partial support for a handful
of CSS properties (see [STYLE_WHITELIST.md](STYLE_WHITELIST.md)). This template sticks to the **intersection** of what dom-to-pptx reliably converts and what looks good in PowerPoint after export.

## The template

```html
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <title>Presentation</title>

    <!-- Fonts MUST have crossorigin="anonymous" for auto-embedding -->
    <link rel="preconnect" href="https://fonts.googleapis.com" />
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
    <link
      href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap"
      rel="stylesheet"
      crossorigin="anonymous"
    />
    <!-- Animations & transitions stylesheets (required for browser previews of element animations; note: slide transitions are not previewed in-browser) -->
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/dom-to-pptx@latest/dist/animations.css" />
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/dom-to-pptx@latest/dist/transitions.css" />

    <style>
      /* Only page chrome lives here. Slide content uses INLINE styles. */
      html,
      body {
        margin: 0;
        padding: 0;
        background: #222;
      }
      body {
        font-family: 'Inter', Arial, Helvetica, sans-serif;
      }
      .slide-stage {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 24px;
        padding: 40px 0;
      }
    </style>
  </head>
  <body>
    <div class="slide-stage">
      <!--
    ========================================================================
    SLIDE RULES (enforced by validator)
    ------------------------------------------------------------------------
    1.  Every slide is .slide with width: 1920px; height: 1080px (fixed px).
    2.  position: relative on the slide; children use position: absolute
        with explicit left/top/width/height in px — NO transform: translate/scale.
    3.  All visual styles live inline on the element. No class-based styling
        for slide content (the <style> block above is for page chrome only).
    4.  Images: full https:// URL (Unsplash / Cloudinary / picsum / your own
        CORS-enabled CDN). NEVER relative paths, NEVER file://.
    5.  Gradients: linear-gradient() only. No radial/conic.
    6.  No: backdrop-filter, text-shadow, mix-blend-mode, filter (except
        filter: blur() — partial support).
    7.  Animations & Slide Transitions: Supported ONLY via whitelisted CSS
        classes (e.g. fade-in, slide-transition-fade). No custom @keyframes. Note: only slide element animations are previewed in-browser; slide-to-slide transitions are not previewed in-browser.
    8.  Fonts: px units only. Arial / Helvetica / Georgia / a CORS-loaded
        Google Font. No rem/em/vw on slide content.
    9.  Speaker Notes: Optionally use data-pptx-notes="..." on .slide to automatically
        populate presenter speaker notes in PowerPoint.
    ========================================================================
  -->

      <!-- ┌─ SLIDE 1 — Title (Fades in on slide entry) ──────────────────────┐ -->
      <div
        class="slide slide-transition-fade"
        data-pptx-notes="Welcome executives. Key takeaways: Q3 growth, strategic roadmap, and operational milestones."
        style="
    width: 1920px; height: 1080px;
    position: relative; overflow: hidden;
    background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%);
  "
      >
        <div style="position: absolute; left: 120px; top: 420px; width: 1400px;">
          <!-- Animated title (Triggers on click) -->
          <h1
            class="fade-in animate-duration-[1000]"
            style="
        margin: 0;
        font-family: 'Inter', Arial, sans-serif;
        font-size: 88px; font-weight: 700; line-height: 1.05;
        color: #ffffff;
        letter-spacing: -1px;
      "
          >
            Presentation Title
          </h1>
          <!-- Animated subtitle (Triggers after the title animates) -->
          <p
            class="fly-in to-up animate-duration-[800] animate-delay-[200] animate-trigger-after"
            style="
        margin: 28px 0 0 0;
        font-size: 32px; font-weight: 400;
        color: #cccccc;
      "
          >
            Subtitle or tagline goes here
          </p>
        </div>

        <!-- Accent bar (Animates with the title) -->
        <div
          class="fade-in animate-duration-[1000] animate-trigger-with"
          style="
      position: absolute; left: 120px; top: 380px;
      width: 120px; height: 6px;
      background: #FF5722;
      border-radius: 3px;
    "
        ></div>
      </div>

      <!-- ┌─ SLIDE 2 — Content with bullets ───────────────────────────────┐ -->
      <div
        class="slide"
        style="
    width: 1920px; height: 1080px;
    position: relative; overflow: hidden;
    background: #ffffff;
  "
      >
        <h2
          style="
      position: absolute; left: 120px; top: 100px;
      margin: 0;
      font-family: 'Inter', Arial, sans-serif;
      font-size: 56px; font-weight: 700; color: #1a1a1a;
    "
        >
          Section Heading
        </h2>

        <ul
          style="
      position: absolute; left: 120px; top: 240px; width: 1200px;
      margin: 0; padding-left: 40px;
      list-style: disc;
    "
        >
          <li style="font-size: 30px; color: #333333; line-height: 1.5; margin-bottom: 24px;">
            First key point stated clearly and concisely.
          </li>
          <li style="font-size: 30px; color: #333333; line-height: 1.5; margin-bottom: 24px;">
            Second point that builds on the first.
          </li>
          <li style="font-size: 30px; color: #333333; line-height: 1.5; margin-bottom: 24px;">
            Third point supporting the argument.
          </li>
          <li style="font-size: 30px; color: #333333; line-height: 1.5;">Closing thought or takeaway.</li>
        </ul>
      </div>

      <!-- ┌─ SLIDE 3 — Two-column (text + image) ──────────────────────────┐ -->
      <div
        class="slide"
        style="
    width: 1920px; height: 1080px;
    position: relative; overflow: hidden;
    background: #f8f6f1;
  "
      >
        <!-- Left column -->
        <div style="position: absolute; left: 120px; top: 160px; width: 720px;">
          <h2 style="margin: 0; font-size: 52px; font-weight: 700; color: #1a1a1a; line-height: 1.1;">
            Why this matters
          </h2>
          <p style="margin: 32px 0 0 0; font-size: 26px; line-height: 1.6; color: #555555;">
            A short paragraph explaining the idea. Keep it tight — one clear thought, two or three sentences maximum.
          </p>
        </div>
        <!-- Right column: image -->
        <img
          src="https://images.unsplash.com/photo-1557683316-973673baf926?w=1200&auto=format&fit=crop"
          alt="decorative"
          style="
        position: absolute; right: 120px; top: 120px;
        width: 840px; height: 840px;
        object-fit: cover;
        border-radius: 16px;
        box-shadow: 0 20px 60px rgba(0,0,0,0.2);
      "
        />
      </div>
    </div>

    <!-- Preview/animation script (Optional: for browser previewing only) -->
    <script src="https://cdn.jsdelivr.net/npm/dom-to-pptx@latest/dist/dom-to-pptx.bundle.js"></script>
    <script>
      // Apply browser preview properties on load
      if (window.domToPptx && window.domToPptx.applyBrowserAnimations) {
        window.domToPptx.applyBrowserAnimations(document.body);
      }
    </script>
  </body>
</html>
```

## Using the template

1. **Copy it verbatim** as `presentation.html`.
2. **Duplicate** the `<!-- ┌─ SLIDE N ─┐ -->` block for each new slide.
3. **Keep edits inline** — don't move layout styles into a `<style>` block or external CSS.
4. **Swap the font** by changing the `<link>` href AND the `font-family` on each slide root. Always keep `crossorigin="anonymous"`.
5. **Compile to PowerPoint**:
   Run the headless exporter directly from your command line:

   ```bash
   # Compile all slides in the deck
   npx dom-to-pptx-exporter presentation.html -o presentation.pptx

   # Compile a single slide only (e.g., Slide 2)
   npx dom-to-pptx-exporter presentation.html -s "#slide-2" -o slide2-only.pptx
   ```

6. **Preview in browser**: Open `presentation.html` in Chrome/Edge. Firefox has stricter CORS behavior that sometimes breaks Unsplash images.

## What NOT to add to this template

<!-- prettier-ignore -->
| Don't | Why |
| --- | --- |
| Tailwind / Bootstrap CDN | Classes are fine (computed styles are read), but it encourages utilities that translate poorly (`backdrop-blur`). If you want Tailwind, keep it to layout/color utilities. For motion, use whitelisted transition/animation classes. |
| `<style>` blocks for slide content | dom-to-pptx reads computed styles so it _works_, but inline styles are the safest round-trip and make debugging layouts trivial. |
| `transform: translate(-50%, -50%)` centering tricks | `transform: translate` isn't respected by the converter. Use `left:` + `width:` math, or `display: flex; justify-content: center; align-items: center;` on the parent. |
| `vh`, `vw`, `rem`, `em`, `clamp()` on slide content | Fixed `px` is the only unit that round-trips predictably. |
| Lazy-loaded images (`loading="lazy"`) | The DOM is measured synchronously — a lazy image may not have loaded when export fires. |
| Fonts loaded via `@font-face` pointing at relative `url(./fonts/...)` | Relative font paths won't embed. Use a CORS-serving CDN or Google Fonts. |

## See also

- [STYLE_WHITELIST.md](STYLE_WHITELIST.md) — exhaustive allow/block list
- [VALIDATION.md](VALIDATION.md) — pre-export scanner
- [ANIMATIONS_WHITELIST.md](ANIMATIONS_WHITELIST.md) — exhaustive list of whitelisted element-level animations, triggers, and text builds
- [TRANSITIONS_WHITELIST.md](TRANSITIONS_WHITELIST.md) — exhaustive list of whitelisted slide-level transition effects and durations
- [SAMPLE_PROMPTS.md](SAMPLE_PROMPTS.md) — prompts for common layouts
- [TEMPLATE.md](TEMPLATE.md) — layout pattern library (card grids, stats, steps…)
- [STYLE_PRESETS.md](STYLE_PRESETS.md) — color/typography presets
