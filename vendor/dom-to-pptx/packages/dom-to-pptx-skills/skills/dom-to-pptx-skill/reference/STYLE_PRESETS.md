# Style Presets for dom-to-pptx

Visual styles adapted for dom-to-pptx compatibility. Each preset provides inline CSS values ready to use.

---

## 1. Bold Signal

**Vibe:** Confident, bold, high-impact corporate

**Colors:**

- Background: `#1a1a1a`
- Gradient: `linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%)`
- Accent: `#FF5722` (orange)
- Text primary: `#ffffff`
- Text on accent: `#1a1a1a`

**Typography:** Arial Black / Arial (fallback-safe)

**Usage:**

```html
<div
  style="width: 1920px; height: 1080px; background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%); position: relative;"
>
  <div
    style="position: absolute; left: 80px; top: 80px; width: 200px; height: 100px; background: #FF5722; border-radius: 12px;"
  ></div>
  <h1 style="font-size: 80px; color: #ffffff; font-family: 'Arial Black', Arial, sans-serif; margin: 0;">
    Bold Statement
  </h1>
</div>
```

**Signature Elements:**

- Orange accent card as focal point
- Large section numbers (01, 02)
- High contrast text

---

## 2. Electric Studio

**Vibe:** Clean, professional, modern corporate

**Colors:**

- Background: `#0a0a0a`
- Card/Panel: `#ffffff`
- Accent: `#4361ee` (blue)
- Text dark: `#0a0a0a`
- Text light: `#ffffff`

**Typography:** Arial / Helvetica (clean sans-serif)

**Usage:**

```html
<div style="width: 1920px; height: 1080px; background: #ffffff; position: relative;">
  <div style="position: absolute; top: 0; left: 0; width: 1920px; height: 400px; background: #0a0a0a;"></div>
  <h1 style="font-size: 64px; color: #ffffff; position: absolute; top: 120px; left: 100px; margin: 0;">Clean & Bold</h1>
  <div style="position: absolute; bottom: 100px; left: 100px; right: 100px; display: flex; gap: 40px;">
    <div style="flex: 1; background: #f5f5f5; padding: 40px; border-radius: 16px;">
      <h3 style="font-size: 32px; color: #0a0a0a; margin: 0 0 20px 0;">Feature One</h3>
      <p style="font-size: 24px; color: #666666; margin: 0;">Description text here</p>
    </div>
  </div>
</div>
```

**Signature Elements:**

- Split layout (dark top, light bottom OR vice versa)
- Accent color bar on edge
- Minimal spacing

---

## 3. Creative Voltage

**Vibe:** Energetic, creative, bold

**Colors:**

- Primary: `#0066ff` (electric blue)
- Dark: `#1a1a2e`
- Accent: `#d4ff00` (neon yellow)
- Text light: `#ffffff`

**Typography:** Arial / Helvetica

**Usage:**

```html
<div style="width: 1920px; height: 1080px; background: #0066ff; position: relative;">
  <div style="position: absolute; left: 0; top: 0; width: 960px; height: 1080px; background: #1a1a2e;"></div>
  <h1 style="font-size: 72px; color: #ffffff; position: absolute; left: 100px; top: 400px; margin: 0;">
    Creative Energy
  </h1>
  <div
    style="position: absolute; right: 200px; top: 450px; background: #d4ff00; padding: 20px 40px; border-radius: 8px;"
  >
    <span style="font-size: 32px; color: #1a1a2e; font-weight: bold;">Get Started</span>
  </div>
</div>
```

**Signature Elements:**

- Electric blue + neon yellow contrast
- Split panel layout

---

## 4. Dark Botanical

**Vibe:** Elegant, sophisticated, premium

**Colors:**

- Background: `#0f0f0f`
- Text primary: `#e8e4df`
- Text secondary: `#9a9590`
- Accent warm: `#d4a574`
- Accent pink: `#e8b4b8`

**Typography:** Georgia / Times New Roman (elegant serif)

**Usage:**

```html
<div style="width: 1920px; height: 1080px; background: #0f0f0f; position: relative; overflow: hidden;">
  <!-- Soft decorative blur (dom-to-pptx: filter: blur() is supported; radial-gradient is not) -->
  <div
    style="position: absolute; right: 100px; top: 100px; width: 600px; height: 600px; border-radius: 50%; background: #d4a574; opacity: 0.3; filter: blur(120px);"
  ></div>
  <h1
    style="font-size: 72px; color: #e8e4df; font-family: Georgia, serif; position: absolute; top: 350px; left: 100px; margin: 0; font-style: italic;"
  >
    Elegant Design
  </h1>
  <p style="font-size: 28px; color: #9a9590; position: absolute; top: 500px; left: 100px; margin: 0;">
    Refined and sophisticated
  </p>
</div>
```

**Signature Elements:**

- Abstract soft gradient circles (blurred)
- Warm accent colors (gold, pink)
- Italic serif typography

---

## 5. Pastel Light

**Vibe:** Friendly, approachable, clean

**Colors:**

- Background: `#f8f6f1` (warm cream)
- Card: `#ffffff`
- Text primary: `#1a1a1a`
- Accent pink: `#f0b4d4`
- Accent mint: `#a8d4c4`
- Accent lavender: `#9b8dc4`

**Typography:** Arial / Helvetica

**Usage:**

```html
<div style="width: 1920px; height: 1080px; background: #f8f6f1; position: relative;">
  <h1 style="font-size: 64px; color: #1a1a1a; position: absolute; top: 300px; left: 100px; margin: 0;">
    Friendly Design
  </h1>
  <div style="position: absolute; top: 500px; left: 100px; display: flex; gap: 30px;">
    <div style="background: #f0b4d4; padding: 16px 32px; border-radius: 24px;">
      <span style="font-size: 24px; color: #1a1a1a;">Pink</span>
    </div>
    <div style="background: #a8d4c4; padding: 16px 32px; border-radius: 24px;">
      <span style="font-size: 24px; color: #1a1a1a;">Mint</span>
    </div>
    <div style="background: #9b8dc4; padding: 16px 32px; border-radius: 24px;">
      <span style="font-size: 24px; color: #ffffff;">Lavender</span>
    </div>
  </div>
</div>
```

**Signature Elements:**

- Pastel color pills/badges
- Rounded corners
- Warm cream background

---

## 6. Corporate Navy

**Vibe:** Professional, trustworthy, enterprise

**Colors:**

- Background: `#1e3a5f` (navy)
- Card: `#ffffff`
- Text light: `#ffffff`
- Text dark: `#1a1a1a`
- Accent: `#0066cc` (blue)

**Typography:** Arial / Helvetica

**Usage:**

```html
<div style="width: 1920px; height: 1080px; background: #1e3a5f; position: relative;">
  <h1 style="font-size: 72px; color: #ffffff; position: absolute; top: 350px; left: 100px; margin: 0;">
    Enterprise Solution
  </h1>
  <p style="font-size: 28px; color: #cccccc; position: absolute; top: 480px; left: 100px; margin: 0;">
    Professional • Reliable • Secure
  </p>
  <div style="position: absolute; bottom: 100px; left: 100px; right: 100px; display: flex; gap: 40px;">
    <div style="flex: 1; background: #ffffff; padding: 40px; border-radius: 12px;">
      <h3 style="font-size: 28px; color: #1a1a1a; margin: 0 0 16px 0;">Scale</h3>
      <p style="font-size: 20px; color: #666666; margin: 0;">Enterprise-grade reliability</p>
    </div>
  </div>
</div>
```

**Signature Elements:**

- Navy blue background
- Clean white cards
- Professional hierarchy

---

## 7. Minimal White

**Vibe:** Clean, minimal, modern

**Colors:**

- Background: `#ffffff`
- Text primary: `#1a1a1a`
- Text secondary: `#666666`
- Accent: `#0066cc`

**Typography:** Arial / Helvetica

**Usage:**

```html
<div style="width: 1920px; height: 1080px; background: #ffffff; position: relative;">
  <div style="position: absolute; top: 350px; left: 50%; transform: translateX(-50%); text-align: center;">
    <h1 style="font-size: 80px; color: #1a1a1a; margin: 0 0 32px 0;">Minimal</h1>
    <p style="font-size: 32px; color: #666666; margin: 0;">Less is more</p>
  </div>
  <div
    style="position: absolute; bottom: 150px; left: 50%; transform: translateX(-50%); width: 200px; height: 4px; background: #0066cc;"
  ></div>
</div>
```

**Signature Elements:**

- Heavy whitespace
- Single accent line
- Centered typography

---

## 8. Gradient Modern

**Vibe:** Contemporary, tech, vibrant

**Colors:**

- Gradient: `linear-gradient(135deg, #667eea 0%, #764ba2 100%)`
- Text light: `#ffffff`
- Card: `#ffffff` with opacity

**Typography:** Arial / Helvetica

**Usage:**

```html
<div
  style="width: 1920px; height: 1080px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); position: relative; overflow: hidden;"
>
  <h1 style="font-size: 80px; color: #ffffff; position: absolute; top: 350px; left: 100px; margin: 0;">
    Modern Gradient
  </h1>
  <div style="position: absolute; bottom: 150px; left: 100px; display: flex; gap: 40px;">
    <!-- Semi-transparent panel (no backdrop-filter — not supported by dom-to-pptx) -->
    <div
      style="background: rgba(255,255,255,0.2); padding: 24px 48px; border-radius: 12px; border: 1px solid rgba(255,255,255,0.3);"
    >
      <span style="font-size: 28px; color: #ffffff;">Explore</span>
    </div>
  </div>
</div>
```

**Signature Elements:**

- Rich gradient background
- Semi-transparent card overlays
- Modern tech feel

---

## 9. Neo-Brutalism

**Vibe:** Raw, anti-design, high-impact trend

**Colors:**

- Background: `#FEF08A` (bright yellow)
- Card: `#FFFFFF`
- Accent: `#FF6B6B` (coral)
- Text Primary: `#000000`
- Text Secondary: `#262626`

**Typography:** 'Roboto Mono', 'Courier New', monospace

**Usage:**

```html
<div style="width: 1920px; height: 1080px; background: #FEF08A; position: relative;">
  <div
    style="position: absolute; left: 100px; top: 100px; width: 800px; padding: 60px; background: #FFFFFF; border: 4px solid #000000; box-shadow: 16px 16px 0px #000000;"
  >
    <h1 style="font-size: 80px; color: #000000; font-family: monospace; margin: 0; text-transform: uppercase;">
      Raw Design
    </h1>
  </div>
</div>
```

**Signature Elements:**

- Thick black borders (4px+)
- Hard, unsoftened shadows (offset, no blur)
- Bright, clashing colors
- Monospace fonts

---

## 10. Soft Pastel

**Vibe:** Calm, dreamy, airy and approachable

**Colors:**

- Background: `#F0F9FF` (soft sky)
- Card: `#FFFFFF`
- Accent: `#FDA4AF` (rose)
- Text Primary: `#1d1d1d`
- Text Secondary: `#6D28D9` (deep violet)

**Typography:** 'Quicksand', 'Nunito', Arial

**Usage:**

```html
<div style="width: 1920px; height: 1080px; background: #F0F9FF; position: relative;">
  <div
    style="position: absolute; left: 100px; top: 100px; width: 600px; height: 400px; background: #FFFFFF; border-radius: 60px; box-shadow: 0 40px 80px rgba(253, 164, 175, 0.2);"
  ></div>
  <h1
    style="font-size: 72px; color: #1d1d1d; font-family: 'Quicksand', sans-serif; position: absolute; top: 200px; left: 160px;"
  >
    Dreamy Spaces
  </h1>
</div>
```

**Signature Elements:**

- Ultra-rounded corners (40px+)
- Soft, colored shadows
- Airy whitespace
- Gentle, playful typography

---

## 11. Swiss Minimalism

**Vibe:** Structured, typographic, and clinical

**Colors:**

- Background: `#FFFFFF`
- Card: `#F4F4F5`
- Accent: `#DC2626` (signal red)
- Text Primary: `#000000`
- Text Secondary: `#3F3F46`

**Typography:** 'Inter', 'Helvetica Neue', Arial

**Usage:**

```html
<div style="width: 1920px; height: 1080px; background: #FFFFFF; position: relative;">
  <div style="position: absolute; left: 120px; top: 80px; width: 80px; height: 8px; background: #DC2626;"></div>
  <h1
    style="font-size: 110px; color: #000000; font-family: 'Inter', sans-serif; font-weight: 900; position: absolute; top: 140px; left: 120px; letter-spacing: -4px;"
  >
    SWISS<br />MODERN
  </h1>
</div>
```

**Signature Elements:**

- Rigid mathematical grid
- Massive typographic hierarchy
- Extreme negative space
- Singular red accent

---

## 12. Nature Eco

**Vibe:** Organic, fresh, and grounded

**Colors:**

- Background: `#F7FEE7` (lime wash)
- Card: `#FFFFFF`
- Accent: `#166534` (forest green)
- Text Primary: `#064E3B`
- Text Secondary: `#374151`

**Typography:** 'Montserrat', 'Source Sans Pro', Arial

**Usage:**

```html
<div style="width: 1920px; height: 1080px; background: #F7FEE7; position: relative;">
  <div
    style="position: absolute; right: 0; top: 0; width: 800px; height: 1080px; background: #166534; border-top-left-radius: 500px; opacity: 0.1;"
  ></div>
  <h1 style="font-size: 72px; color: #064E3B; position: absolute; top: 400px; left: 120px;">Organic Growth</h1>
</div>
```

**Signature Elements:**

- Leaf-like curves
- Forest green and earth tones
- Natural textures (simulated via subtle gradients)
- Breathable layouts

---

## 13. Luxury Noir

**Vibe:** Exclusive, high-fashion, and moody

**Colors:**

- Background: `#0A0A0A` (matte black)
- Card: `#171717`
- Accent: `#D4AF37` (gold)
- Text Primary: `#FFFFFF`
- Text Secondary: `#A3A3A3`

**Typography:** 'Playfair Display', 'Lora', serif

**Usage:**

```html
<div style="width: 1920px; height: 1080px; background: #0A0A0A; position: relative;">
  <div
    style="position: absolute; left: 50%; top: 400px; transform: translateX(-50%); width: 2px; height: 100px; background: #D4AF37;"
  ></div>
  <h1
    style="font-size: 80px; color: #FFFFFF; font-family: serif; position: absolute; top: 540px; width: 100%; text-align: center; letter-spacing: 12px;"
  >
    PREMIUM
  </h1>
</div>
```

**Signature Elements:**

- Matte black surfaces
- Thin gold accents
- Centered, spacious composition
- High-contrast serif typography

---

## 14. Cyberpunk Neon

**Vibe:** High-tech, dystopian, and glowing

**Colors:**

- Background: `#020617` (deep space)
- Card: `#0F172A`
- Accent: `#D946EF` (magenta)
- Secondary Accent: `#22D3EE` (cyan)
- Text Primary: `#22D3EE`

**Typography:** 'Oswald', 'Bebas Neue', Arial

**Usage:**

```html
<div style="width: 1920px; height: 1080px; background: #020617; position: relative;">
  <div
    style="position: absolute; left: 0; top: 500px; width: 1920px; height: 1px; background: #D946EF; box-shadow: 0 0 20px #D946EF;"
  ></div>
  <h1
    style="font-size: 90px; color: #22D3EE; position: absolute; top: 400px; left: 120px; text-shadow: 0 0 10px #22D3EE;"
  >
    SYSTEM READY
  </h1>
</div>
```

**Signature Elements:**

- Glowing borders and lines
- Cyan/Magenta contrast
- Dark technical backgrounds
- Sharp angular geometry

---

---

## 15. Swiss Foundry (Premium)

**Vibe:** 1950s Swiss Modernism. Clinical, authoritative, and clean.

**Design Logic:**

- **Materiality:** Warm, unbleached physical paper.
- **Light Physics:** Flat, no shadows.
- **Spatial Tension:** Rigid mathematical grid with aggressive negative space.

**Colors:**

- [Color 1] BASE (Background): `#F9F9F7`
- [Color 2] SURFACE (Cards): `#FFFFFF`
- [Color 3] ACCENT: `#E63946` (Signal Red)
- [Color 4] TYPE-PRIMARY: `#1A1A1A`
- [Color 5] TYPE-SECONDARY: `#666666`

---

## 16. Linen & Obsidian (Premium)

**Vibe:** High-end architectural minimalism. Tactile and organic.

**Design Logic:**

- **Materiality:** Textured linen and matte ceramic.
- **Light Physics:** Subtle 1px inner borders instead of drop shadows.
- **Spatial Tension:** Airy, breathable, with heavy visual anchors.

**Colors:**

- [Color 1] BASE (Background): `#F2EDE4`
- [Color 2] SURFACE (Cards): `#E5DED1`
- [Color 3] ACCENT: `#2C2C2C` (Matte Obsidian)
- [Color 4] TYPE-PRIMARY: `#121212`
- [Color 5] TYPE-SECONDARY: `#4A4A4A`

---

## 17. Veridian Studio (Premium)

**Vibe:** Serene gallery-like atmosphere. "Soft-Industrial" elegance.

**Design Logic:**

- **Materiality:** Custom-molded clay or high-end tech hardware.
- **Light Physics:** Soft, diffuse lighting with exaggerated rounded corners (32px+).
- **Spatial Tension:** Generous padding and expansive margins.

**Colors:**

- [Color 1] BASE (Background): `#FBFBFA`
- [Color 2] SURFACE (Cards): `#F1F3F0`
- [Color 3] ACCENT: `#2D4C3E` (Oxidized Veridian)
- [Color 4] TYPE-PRIMARY: `#1A1C1B`
- [Color 5] TYPE-SECONDARY: `#5C6360`

---

## Color Palette Quick Reference (Updated)

<!-- prettier-ignore -->
| Style | Background | Surface | Accent | Type 1 | Type 2 |
| --- | --- | --- | --- | --- | --- |
| Swiss Foundry | #F9F9F7 | #FFFFFF | #E63946 | #1A1A1A | #666666 |
| Linen & Obsidian | #F2EDE4 | #E5DED1 | #2C2C2C | #121212 | #4A4A4A |
| Veridian Studio | #FBFBFA | #F1F3F0 | #2D4C3E | #1A1C1B | #5C6360 |
| Luxury Noir | #0A0A0A | #171717 | #D4AF37 | #FFFFFF | #A3A3A3 |
| Swiss Minimalism | #FFFFFF | #F4F4F5 | #DC2626 | #000000 | #3F3F46 |

---

## Font Sizing Guide (dom-to-pptx)

Use these sizes for optimal PowerPoint rendering:

<!-- prettier-ignore -->
| Element | Size |
| --- | --- |
| Main Title | 72-80px |
| Section Title | 48-56px |
| H3 / Card Title | 32-40px |
| Body Text | 24-28px |
| Caption / Label | 18-20px |
| Small Text | 16px |

**Note:** Use px units (not rem/em). Arial and Helvetica are safest for cross-platform rendering. Georgia/Times work well for serif elegance.
