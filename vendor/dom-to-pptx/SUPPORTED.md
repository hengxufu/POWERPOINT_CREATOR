# Supported CSS & HTML

This document lists the common CSS features, Tailwind-like utility classes, and HTML elements that dom-to-pptx understands and maps to PowerPoint shapes/text.

Note: The library measures computed layout from the browser (getBoundingClientRect) and maps positions/sizes precisely to PPTX inches. If a CSS feature is not listed below it may still work because the browser computes layout and visual styles — the mapping focuses on visual fidelity.

## Supported HTML elements

- div, span, p, h1-h6
- img, svg
- ul, ol, li
- a
- button
- section, article, header, footer
- input (text), textarea (simple text extraction)
- figure, figcaption

## Supported CSS properties (rendered visually)

- background-color, background-image (linear-gradient)
- background-position, background-size (basic handling in gradients)
- color, opacity
- border, border-_-color, border-_-width, border-radius (per-corner)
- box-shadow (outer shadows mapped to PPTX outer shadows)
- filter: blur() (soft-edge rendering via SVG)
- backdrop-filter: blur() (simulated via html2canvas snapshot)
- transform: rotate() (extraction of rotation angle)
- display, position, width, height, padding, margin
- text-align, vertical-align, text-transform
- white-space (`normal`/`nowrap` collapse whitespace; `pre`/`pre-wrap`/`pre-line` preserve author line breaks, and `pre`/`pre-wrap` also preserve indentation/spaces)
- font-family, font-size, font-weight, font-style, line-height
- animations & transitions (20+ entrance/exit animations like `fade-in`, `zoom-in`, `fly-in`, `wipe-in`; 70+ slide transitions; custom delays, durations, trigger sequencing, and character/paragraph reveals)

## Common utility/Tailwind-like classes (recognized by visual result)

These classes are examples; dom-to-pptx reads computed styles, so any combination that results in the same computed value will be supported.

- `rounded`, `rounded-sm`, `rounded-md`, `rounded-lg`, `rounded-xl`, `rounded-full`, `rounded-tr-*`, `rounded-bl-full`, etc.
- `bg-white`, `bg-slate-50`, `bg-indigo-50`, `bg-gradient-to-r`, `from-indigo-400`, `to-cyan-400`, etc. (linear-gradients are parsed)
- `shadow`, `shadow-md`, `shadow-lg`, `shadow-2xl` (box-shadow)
- `flex`, `grid`, `items-center`, `justify-center`, `gap-*`
- `p-4`, `px-6`, `py-2`, `m-4`
- `w-*`, `h-*` (fixed pixel/percentage/wrappers — computed width/height are used)
- `text-xs`, `text-sm`, `text-lg`, `font-bold`, `uppercase`, `italic`, `tracking-wide`
- `fade-in`, `fly-in`, `wipe-out`, `animate-duration-[500]`, `animate-delay-[200]`, `animate-trigger-after` (animation utility classes)
- `slide-transition-fade`, `slide-transition-push`, `transition-dur-[1000]` (transition utility classes)

## Limitations

- Infinite-loop, interaction-triggered, or non-whitelisted CSS animations/transitions are not exported. Only the whitelisted 20+ slide element animations and 70+ slide transitions are translated into PowerPoint motion effects; all others will fallback to their static computed layout.
- Some advanced CSS features (CSS variables used as colors, filters beyond blur) may not map 1:1.
- For images to be processed via canvas (rounded images), the source must be CORS-accessible (`Access-Control-Allow-Origin` header) or the image will be skipped or rendered as-is.

### Recommended Patterns & Best Practices

To achieve the highest fidelity and most reliable rendering in PowerPoint, consider adopting these HTML/CSS patterns:

- **Layouts (Tables vs. Grid/Flex):** While native HTML `<table>` elements are supported (mapping to PptxGenJS native tables), native tables in PowerPoint can be structurally rigid. For absolute layout control, perfect border-radius, and guaranteed visual consistency, **prefer utilizing a `div` structure with `display: grid` or `display: flex`**. These containers dynamically transform into crisp, independent PowerPoint shapes.
- **Images and Backgrounds:**
  - `<img src="...">` tags are fully supported and mapped perfectly, taking `object-fit` and `object-position` into consideration.
  - CSS `background-image: url(...)` is also natively parsed. It correctly handles `background-size` (cover/contain) and translates them into matching image crop parameters in PPTX.
  - CSS `background-image: linear-gradient(...)` transforms into pure vector SVG gradients without requiring rasterization.
- **Writing Modes:** Modern CSS `writing-mode` (`vertical-rl`, `vertical-lr`) properties are supported. Combine them with `text-orientation: upright` to natively tap into PowerPoint's Stacked Vertical Text engine, or leave defaults to map to standard East-Asian rotated text layouts.

If a style or element is critical and you find it not behaving as expected, open an issue with a minimal repro and I'll add support or provide a workaround.
