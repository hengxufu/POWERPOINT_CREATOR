# HTML Template & Patterns for dom-to-pptx

Reference architecture for generating dom-to-pptx-compatible HTML presentations.

## Base HTML Structure

```html
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <title>Presentation Title</title>
    <!-- Google Fonts with crossorigin for dom-to-pptx -->
    <link
      href="https://fonts.googleapis.com/css2?family=Roboto:wght@400;700&display=swap"
      rel="stylesheet"
      crossorigin="anonymous"
    />
  </head>
  <body style="margin: 0; padding: 0; background: #cccccc;">
    <!-- Slide 1: Title Slide -->
    <div
      class="slide"
      style="width: 1920px; height: 1080px; position: relative; overflow: hidden; background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%);"
    >
      <div style="position: absolute; left: 120px; top: 400px;">
        <h1 style="font-size: 72px; color: #ffffff; font-family: Arial, sans-serif; margin: 0;">Presentation Title</h1>
        <p style="font-size: 32px; color: #cccccc; margin-top: 24px;">Subtitle or description</p>
      </div>
    </div>

    <!-- Slide 2: Content with Bullets -->
    <div
      class="slide"
      style="width: 1920px; height: 1080px; position: relative; overflow: hidden; background: #ffffff;"
    >
      <h2 style="font-size: 48px; color: #1a1a1a; position: absolute; top: 80px; left: 120px; margin: 0;">
        Section Title
      </h2>
      <ul
        style="position: absolute; top: 200px; left: 120px; width: 800px; margin: 0; padding-left: 40px; list-style: disc;"
      >
        <li style="font-size: 28px; color: #333333; margin-bottom: 24px;">First key point</li>
        <li style="font-size: 28px; color: #333333; margin-bottom: 24px;">Second key point</li>
        <li style="font-size: 28px; color: #333333; margin-bottom: 24px;">Third key point</li>
      </ul>
    </div>

    <!-- Slide 3: Two Column Layout -->
    <div
      class="slide"
      style="width: 1920px; height: 1080px; position: relative; overflow: hidden; background: #f8f6f1;"
    >
      <!-- Left column: Text -->
      <div
        style="position: absolute; left: 0; top: 0; width: 960px; height: 1080px; padding: 80px; background: #1a1a1a;"
      >
        <h2 style="font-size: 48px; color: #ffffff; margin: 0 0 40px 0;">Left Column Title</h2>
        <p style="font-size: 24px; color: #cccccc; line-height: 1.6; margin: 0;">
          Description text goes here with multiple lines of content.
        </p>
      </div>
      <!-- Right column: Image placeholder -->
      <div
        style="position: absolute; right: 0; top: 0; width: 960px; height: 1080px; display: flex; align-items: center; justify-content: center; background: #f0f0f0;"
      >
        <img
          src="https://images.unsplash.com/photo-xxx?w=800"
          style="width: 700px; height: 500px; object-fit: cover; border-radius: 16px;"
          alt="Description"
        />
      </div>
    </div>

    <!-- Slide 4: Stats/Numbers -->
    <div
      class="slide"
      style="width: 1920px; height: 1080px; position: relative; overflow: hidden; background: #ffffff;"
    >
      <h2
        style="font-size: 48px; color: #1a1a1a; position: absolute; top: 80px; left: 50%; transform: translateX(-50%); margin: 0;"
      >
        Key Metrics
      </h2>
      <!-- Stats row -->
      <div
        style="position: absolute; top: 300px; left: 120px; right: 120px; display: flex; justify-content: space-around;"
      >
        <div style="text-align: center;">
          <div style="font-size: 96px; color: #FF5722; font-weight: bold; margin: 0;">85%</div>
          <div style="font-size: 24px; color: #666666; margin-top: 16px;">Efficiency</div>
        </div>
        <div style="text-align: center;">
          <div style="font-size: 96px; color: #4361ee; font-weight: bold; margin: 0;">2x</div>
          <div style="font-size: 24px; color: #666666; margin-top: 16px;">Faster</div>
        </div>
        <div style="text-align: center;">
          <div style="font-size: 96px; color: #667eea; font-weight: bold; margin: 0;">$1.2M</div>
          <div style="font-size: 24px; color: #666666; margin-top: 16px;">Savings</div>
        </div>
      </div>
    </div>

    <!-- Slide 5: Quote -->
    <div
      class="slide"
      style="width: 1920px; height: 1080px; position: relative; overflow: hidden; background: #0f0f0f;"
    >
      <div style="position: absolute; top: 300px; left: 200px; right: 200px; text-align: center;">
        <p
          style="font-size: 48px; color: #e8e4df; font-family: Georgia, serif; font-style: italic; line-height: 1.5; margin: 0 0 40px 0;"
        >
          "Quote text goes here about the main topic."
        </p>
        <p style="font-size: 24px; color: #9a9590; margin: 0;">— Attribution or Source</p>
      </div>
    </div>

    <!-- Export Button (add anywhere, fixed position) -->
    <script src="https://cdn.jsdelivr.net/npm/dom-to-pptx@latest/dist/dom-to-pptx.bundle.js"></script>
    <script>
      document.getElementById('exportBtn').addEventListener('click', async () => {
        const slides = document.querySelectorAll('.slide');
        await domToPptx.exportToPptx(Array.from(slides), {
          fileName: 'presentation.pptx',
        });
      });
    </script>
    <button
      id="exportBtn"
      style="position: fixed; top: 20px; right: 20px; padding: 16px 32px; background: #4361ee; color: white; border: none; border-radius: 8px; cursor: pointer; font-size: 18px; z-index: 9999; box-shadow: 0 4px 12px rgba(0,0,0,0.3);"
    >
      Export PPTX
    </button>
  </body>
</html>
```

---

## Common Layout Patterns

### Full-bleed Background Image

```html
<div style="width: 1920px; height: 1080px; position: relative; overflow: hidden;">
  <img
    src="https://images.unsplash.com/photo-xxx?w=1920"
    style="position: absolute; top: 0; left: 0; width: 1920px; height: 1080px; object-fit: cover;"
  />
  <div style="position: absolute; top: 0; left: 0; width: 1920px; height: 1080px; background: rgba(0,0,0,0.5);"></div>
  <h1 style="position: absolute; top: 400px; left: 120px; font-size: 72px; color: #ffffff; margin: 0;">
    Title on Image
  </h1>
</div>
```

### Card Grid (2x2)

```html
<div style="display: flex; flex-wrap: wrap; position: absolute; top: 200px; left: 120px; width: 1680px;">
  <!-- Card 1 -->
  <div
    style="width: 800px; height: 320px; background: #ffffff; border-radius: 16px; padding: 40px; margin: 0 20px 40px 0; box-shadow: 0 8px 32px rgba(0,0,0,0.1);"
  >
    <h3 style="font-size: 32px; color: #1a1a1a; margin: 0 0 16px 0;">Card Title</h3>
    <p style="font-size: 20px; color: #666666; margin: 0;">Card content description.</p>
  </div>
  <!-- Card 2 -->
  <div
    style="width: 800px; height: 320px; background: #ffffff; border-radius: 16px; padding: 40px; margin: 0 0 40px 0; box-shadow: 0 8px 32px rgba(0,0,0,0.1);"
  >
    <h3 style="font-size: 32px; color: #1a1a1a; margin: 0 0 16px 0;">Card Title</h3>
    <p style="font-size: 20px; color: #666666; margin: 0;">Card content description.</p>
  </div>
  <!-- Card 3 -->
  <div
    style="width: 800px; height: 320px; background: #ffffff; border-radius: 16px; padding: 40px; margin: 0 20px 0 0; box-shadow: 0 8px 32px rgba(0,0,0,0.1);"
  >
    <h3 style="font-size: 32px; color: #1a1a1a; margin: 0 0 16px 0;">Card Title</h3>
    <p style="font-size: 20px; color: #666666; margin: 0;">Card content description.</p>
  </div>
  <!-- Card 4 -->
  <div
    style="width: 800px; height: 320px; background: #ffffff; border-radius: 16px; padding: 40px; margin: 0; box-shadow: 0 8px 32px rgba(0,0,0,0.1);"
  >
    <h3 style="font-size: 32px; color: #1a1a1a; margin: 0 0 16px 0;">Card Title</h3>
    <p style="font-size: 20px; color: #666666; margin: 0;">Card content description.</p>
  </div>
</div>
```

### Sidebar Layout

```html
<div style="width: 1920px; height: 1080px; position: relative; overflow: hidden; background: #ffffff;">
  <!-- Left sidebar -->
  <div
    style="position: absolute; left: 0; top: 0; width: 400px; height: 1080px; background: #1a1a1a; padding: 60px 40px;"
  >
    <div style="width: 80px; height: 80px; background: #FF5722; border-radius: 12px; margin-bottom: 40px;"></div>
    <h3 style="font-size: 28px; color: #ffffff; margin: 0 0 16px 0;">Brand</h3>
    <p style="font-size: 18px; color: #999999; margin: 0;">Company tagline</p>
  </div>
  <!-- Main content -->
  <div style="position: absolute; left: 500px; top: 100px; right: 100px;">
    <h2 style="font-size: 48px; color: #1a1a1a; margin: 0 0 40px 0;">Main Content Title</h2>
    <p style="font-size: 24px; color: #666666; line-height: 1.6; margin: 0 0 32px 0;">
      Main body text content goes here with multiple lines to fill the space nicely.
    </p>
    <ul style="list-style: disc; padding-left: 32px; margin: 0;">
      <li style="font-size: 22px; color: #333333; margin-bottom: 16px;">Bullet point one</li>
      <li style="font-size: 22px; color: #333333; margin-bottom: 16px;">Bullet point two</li>
    </ul>
  </div>
</div>
```

### Image with Caption

```html
<div style="width: 1920px; height: 1080px; position: relative; overflow: hidden; background: #f8f6f1;">
  <img
    src="https://images.unsplash.com/photo-xxx?w=1200"
    style="position: absolute; top: 100px; left: 50%; transform: translateX(-50%); width: 1400px; height: 700px; object-fit: cover; border-radius: 16px;"
    alt="Main image"
  />
  <p
    style="position: absolute; bottom: 80px; left: 50%; transform: translateX(-50%); font-size: 20px; color: #666666; margin: 0; text-align: center;"
  >
    Image caption or source attribution
  </p>
</div>
```

### Numbered Steps

```html
<div style="position: absolute; top: 200px; left: 120px; right: 120px;">
  <!-- Step 1 -->
  <div style="display: flex; align-items: flex-start; margin-bottom: 60px;">
    <div
      style="width: 80px; height: 80px; background: #4361ee; border-radius: 50%; display: flex; align-items: center; justify-content: center; flex-shrink: 0;"
    >
      <span style="font-size: 36px; color: #ffffff; font-weight: bold;">1</span>
    </div>
    <div style="margin-left: 40px; padding-top: 10px;">
      <h3 style="font-size: 32px; color: #1a1a1a; margin: 0 0 12px 0;">First Step Title</h3>
      <p style="font-size: 22px; color: #666666; margin: 0;">Description of the first step.</p>
    </div>
  </div>
  <!-- Step 2 -->
  <div style="display: flex; align-items: flex-start; margin-bottom: 60px;">
    <div
      style="width: 80px; height: 80px; background: #4361ee; border-radius: 50%; display: flex; align-items: center; justify-content: center; flex-shrink: 0;"
    >
      <span style="font-size: 36px; color: #ffffff; font-weight: bold;">2</span>
    </div>
    <div style="margin-left: 40px; padding-top: 10px;">
      <h3 style="font-size: 32px; color: #1a1a1a; margin: 0 0 12px 0;">Second Step Title</h3>
      <p style="font-size: 22px; color: #666666; margin: 0;">Description of the second step.</p>
    </div>
  </div>
  <!-- Step 3 -->
  <div style="display: flex; align-items: flex-start;">
    <div
      style="width: 80px; height: 80px; background: #4361ee; border-radius: 50%; display: flex; align-items: center; justify-content: center; flex-shrink: 0;"
    >
      <span style="font-size: 36px; color: #ffffff; font-weight: bold;">3</span>
    </div>
    <div style="margin-left: 40px; padding-top: 10px;">
      <h3 style="font-size: 32px; color: #1a1a1a; margin: 0 0 12px 0;">Third Step Title</h3>
      <p style="font-size: 22px; color: #666666; margin: 0;">Description of the third step.</p>
    </div>
  </div>
</div>
```

---

## Image Guidelines

### Image Sources (CORS-compatible)

```html
<!-- Unsplash (recommended) -->
<img src="https://images.unsplash.com/photo-xxx?w=800&auto=format" />

<!-- Picsum -->
<img src="https://picsum.photos/800/600" />

<!-- Placeholder services -->
<img src="https://via.placeholder.com/800x600.png?text=Image" />
```

### Image Sizing

```html
<!-- Hero/background: Full slide -->
<img src="https://..." style="width: 1920px; height: 1080px; object-fit: cover;" />

<!-- Content image: Fixed size -->
<img src="https://..." style="width: 600px; height: 400px; object-fit: cover; border-radius: 12px;" />

<!-- Thumbnail: Small fixed -->
<img src="https://..." style="width: 120px; height: 120px; object-fit: cover; border-radius: 50%;" />
```

---

## Color Values for dom-to-pptx

### Standard Colors (Safe)

```css
/* Whites */
#ffffff, #f8f6f1, #f5f5f5, #eeeeee

/* Blacks/Greys */
#000000, #1a1a1a, #333333, #666666, #999999, #cccccc

/* Brand Colors (most reliable) */
#FF5722  /* Orange */
#4361ee  /* Blue */
#667eea  /* Purple-blue */
#764ba2  /* Purple */
#1e3a5f  /* Navy */
#d4a574  /* Gold/tan */
#e8b4b8  /* Pink */
#a8d4c4  /* Mint */
```

### Gradients (Linear only)

```css
/* Two-color diagonal */
background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);

/* Dark overlay */
background: linear-gradient(180deg, rgba(0, 0, 0, 0) 0%, rgba(0, 0, 0, 0.8) 100%);

/* Light overlay */
background: linear-gradient(180deg, rgba(255, 255, 255, 0.3) 0%, rgba(255, 255, 255, 0) 100%);
```

---

### Complete Export Snippet

```html
<!DOCTYPE html>
<html>
  <head>
    <title>Presentation</title>
    <link
      href="https://fonts.googleapis.com/css2?family=Roboto:wght@400;700&display=swap"
      rel="stylesheet"
      crossorigin="anonymous"
    />
    <style>
      body {
        margin: 0;
        padding: 0;
        background: #333;
      }
      .slide {
        display: block;
      }
    </style>
  </head>
  <body>
    <!-- Slides go here -->
    <div class="slide" id="slide-1" style="width: 1920px; height: 1080px; position: relative; background: #ffffff;">
      <h1 style="position: absolute; left: 100px; top: 100px; font-size: 54px; margin: 0;">Slide 1</h1>
    </div>

    <!-- Preview/animation script (Optional: for browser previewing only) -->
    <script src="https://cdn.jsdelivr.net/npm/dom-to-pptx@latest/dist/dom-to-pptx.bundle.js"></script>
    <script>
      if (window.domToPptx && window.domToPptx.applyBrowserAnimations) {
        window.domToPptx.applyBrowserAnimations(document.body);
      }
    </script>
  </body>
</html>
```

### Headless Compilation Instructions

To convert this presentation to a PowerPoint file, run the exporter utility on the command line:

```bash
# Compile all elements with the class '.slide' (default)
npx dom-to-pptx-exporter presentation.html -o presentation.pptx

# Compile a specific slide only
npx dom-to-pptx-exporter presentation.html -s "#slide-1" -o slide1-only.pptx
```

### Slide with Transitions & Animations

This layout is a content slide that enters with a **Push Left** transition, fades the title in, and flys in three info cards from the bottom.

```html
<!-- Slide with Push Left transition -->
<div
  class="slide slide-transition-push transition-dir-l"
  style="width: 1920px; height: 1080px; position: relative; overflow: hidden; background: #ffffff;"
>
  <!-- Animated Title (Fades in on click) -->
  <h2
    class="fade-in animate-duration-[800]"
    style="position: absolute; left: 120px; top: 100px; margin: 0; font-family: 'Inter', Arial, sans-serif; font-size: 56px; font-weight: 700; color: #1a1a1a;"
  >
    Animated Feature Deck
  </h2>

  <!-- Card Grid (Cards fly in sequentially) -->
  <div style="position: absolute; top: 260px; left: 120px; right: 120px; display: flex; gap: 40px;">
    <!-- Card 1 (Flys in after the title) -->
    <div
      class="fly-in to-up animate-duration-[700] animate-trigger-after"
      style="flex: 1; height: 450px; background: #f8f9fa; border: 1px solid #e9ecef; border-radius: 24px; padding: 40px; box-shadow: 0 10px 30px rgba(0,0,0,0.05);"
    >
      <h3 style="font-size: 32px; color: #333333; margin: 0 0 16px 0;">01</h3>
      <p style="font-size: 20px; color: #666666; margin: 0; line-height: 1.5;">Card content animated sequentially.</p>
    </div>

    <!-- Card 2 (Flys in simultaneously with Card 1 but delayed by 150ms) -->
    <div
      class="fly-in to-up animate-duration-[700] animate-delay-[150] animate-trigger-with"
      style="flex: 1; height: 450px; background: #f8f9fa; border: 1px solid #e9ecef; border-radius: 24px; padding: 40px; box-shadow: 0 10px 30px rgba(0,0,0,0.05);"
    >
      <h3 style="font-size: 32px; color: #333333; margin: 0 0 16px 0;">02</h3>
      <p style="font-size: 20px; color: #666666; margin: 0; line-height: 1.5;">Card content animated sequentially.</p>
    </div>

    <!-- Card 3 (Flys in simultaneously with Card 1 but delayed by 300ms) -->
    <div
      class="fly-in to-up animate-duration-[700] animate-delay-[300] animate-trigger-with"
      style="flex: 1; height: 450px; background: #f8f9fa; border: 1px solid #e9ecef; border-radius: 24px; padding: 40px; box-shadow: 0 10px 30px rgba(0,0,0,0.05);"
    >
      <h3 style="font-size: 32px; color: #333333; margin: 0 0 16px 0;">03</h3>
      <p style="font-size: 20px; color: #666666; margin: 0; line-height: 1.5;">Card content animated sequentially.</p>
    </div>
  </div>
</div>
```

---

## Troubleshooting

<!-- prettier-ignore -->
| Issue | Solution |
| --- | --- |
| Text misaligned | Use absolute positioning with explicit left/top values |
| Font wrong | Use web-safe fonts (Arial, Helvetica, Georgia) |
| Image not showing | Ensure HTTPS URL and CORS-accessible |
| Colors off | Use hex codes directly, avoid CSS variables |
| Gradient fails | Use simple 2-color linear-gradient |
| Shadow missing | Use box-shadow inline with explicit values |
| Border radius | Works but may need explicit px values |
| Text truncated | Increase container width or reduce font size |
