// src/animations/css-parser.js

/**
 * Known animation names recognized as entrance or exit animations.
 * Used to both detect if an element has an animation AND infer direction.
 */
const ENTRANCE_NAMES = new Set([
  'fade-in',
  'appear',
  'zoom-in',
  'fly-in',
  'wipe-in',
  'split-in',
  'wheel',
  'bounce-in',
  'checkerboard-in',
  'random-bars-in',
  'rise-up',
  'swivel-in',
  'drop-in',
  'fly-in-left',
  'fly-in-right',
  'fly-in-top',
  'fly-in-bottom',
]);

const EXIT_NAMES = new Set([
  'fade-out',
  'disappear',
  'zoom-out',
  'fly-out',
  'wipe-out',
  'split-out',
  'wheel-out',
  'bounce-out',
  'checkerboard-out',
  'random-bars-out',
  'swivel-out',
  'drop-out',
  'fly-out-left',
  'fly-out-right',
  'fly-out-top',
  'fly-out-bottom',
]);

/**
 * Parses time string (e.g. "1.5s", "500ms") into milliseconds.
 */
function parseTimeMs(val, defaultVal = 0) {
  if (!val) return defaultVal;
  const str = val.trim().toLowerCase();
  if (str.endsWith('ms')) {
    const n = parseFloat(str);
    return isNaN(n) ? defaultVal : n;
  }
  if (str.endsWith('s')) {
    const n = parseFloat(str);
    return isNaN(n) ? defaultVal : n * 1000;
  }
  const parsed = parseFloat(str);
  return isNaN(parsed) ? defaultVal : parsed;
}

/**
 * Parses duration/delay encoded in utility class names.
 * e.g. "animate-duration-[700]" → 700 (ms)
 *      "animate-delay-[150]"    → 150 (ms)
 */
function parseUtilityClass(classList) {
  let duration = null;
  let delay = null;
  for (const cls of classList) {
    const durMatch = cls.match(/^animate-duration-\[(\d+)\]$/);
    if (durMatch) duration = parseInt(durMatch[1], 10);
    const delayMatch = cls.match(/^animate-delay-\[(\d+)\]$/);
    if (delayMatch) delay = parseInt(delayMatch[1], 10);
  }
  return { duration, delay };
}

/**
 * Extracts animation config from a DOM node and its computed styles.
 * Returns null if no recognized animation is defined.
 *
 * Priority order for animation name:
 *   1. data-pptx-animation dataset attribute
 *   2. --pptx-animation CSS custom property
 *   3. CSS animation-name (set by our animations.css classes)
 *   4. className scan (fallback for when computed animationName is "none")
 *
 * Priority order for duration/delay:
 *   1. data-pptx-animation-duration / data-pptx-animation-delay
 *   2. --pptx-duration / --pptx-delay custom properties
 *   3. animate-duration-[X] / animate-delay-[X] utility classes
 *   4. CSS animation-duration / animation-delay
 *
 * @param {HTMLElement} node
 * @param {CSSStyleDeclaration} style
 * @returns {Object|null}
 */
export function parseAnimation(node, style) {
  if (!node || node.nodeType !== 1) return null;

  // ── 1. Resolve animation name ────────────────────────────────────────────
  let name =
    (node.dataset?.pptxAnimation || node.dataset?.pptxAnimationType || '').trim().toLowerCase() ||
    (style?.getPropertyValue('--pptx-animation-name') || style?.getPropertyValue('--pptx-animation') || '')
      .trim()
      .toLowerCase();

  if (!name || name === 'none') {
    // Try computed CSS animation-name (set by our .fade-in, .zoom-in classes etc.)
    const cssName = style?.animationName?.trim().toLowerCase();
    if (cssName && cssName !== 'none' && cssName !== '') {
      // It may be a comma-separated list; take first
      name = cssName.split(',')[0].trim();
    }
  }

  if (!name || name === 'none' || name === '') {
    // Last resort: scan className list for a known animation name.
    // Use classList rather than className.split() because SVG elements
    // expose className as an SVGAnimatedString, not a string; calling
    // .split() on it throws and aborts the whole PPTX export.
    const classNames = Array.from(node.classList || []);
    for (const cls of classNames) {
      if (ENTRANCE_NAMES.has(cls) || EXIT_NAMES.has(cls)) {
        name = cls;
        break;
      }
    }
  }

  if (!name || name === 'none') return null;

  // ── 2. Determine class (entrance vs exit) ────────────────────────────────
  let animClass = (node.dataset?.pptxAnimationClass || style?.getPropertyValue('--pptx-animation-class') || '')
    .trim()
    .toLowerCase();

  if (!animClass) {
    if (EXIT_NAMES.has(name) || name.endsWith('-out') || name.includes('disappear') || name.includes('exit')) {
      animClass = 'exit';
    } else {
      animClass = 'entr';
    }
  } else {
    animClass = animClass.includes('exit') || animClass.includes('out') ? 'exit' : 'entr';
  }

  // ── 3. Resolve duration ──────────────────────────────────────────────────
  // classList is safe on both HTML and SVG elements; className.split() is not
  // (SVG className is an SVGAnimatedString, not a string).
  const classList = Array.from(node.classList || []);
  const { duration: utilDuration, delay: utilDelay } = parseUtilityClass(classList);

  let durationStr =
    node.dataset?.pptxAnimationDuration ||
    style?.getPropertyValue('--pptx-animation-duration') ||
    style?.getPropertyValue('--pptx-duration');

  let duration;
  if (durationStr) {
    duration = parseTimeMs(durationStr, 1000);
  } else if (utilDuration !== null) {
    duration = utilDuration; // already in ms from utility class
  } else {
    const cssDur = style?.animationDuration;
    duration = cssDur ? parseTimeMs(cssDur, 1000) : 1000;
  }

  // ── 4. Resolve delay ─────────────────────────────────────────────────────
  let delayStr =
    node.dataset?.pptxAnimationDelay ||
    style?.getPropertyValue('--pptx-animation-delay') ||
    style?.getPropertyValue('--pptx-delay');

  let delay;
  if (delayStr) {
    delay = parseTimeMs(delayStr, 0);
  } else if (utilDelay !== null) {
    delay = utilDelay;
  } else {
    const cssDelay = style?.animationDelay;
    delay = cssDelay ? parseTimeMs(cssDelay, 0) : 0;
  }

  // ── 5. Resolve start trigger ─────────────────────────────────────────────
  let start = (
    node.dataset?.pptxAnimationStart ||
    style?.getPropertyValue('--pptx-animation-start') ||
    style?.getPropertyValue('--pptx-start') ||
    ''
  )
    .trim()
    .toLowerCase();

  if (!start) {
    // Check utility trigger classes
    const classSet = new Set(classList);
    if (classSet.has('animate-trigger-with') || classSet.has('with-previous')) {
      start = 'with';
    } else if (classSet.has('animate-trigger-after') || classSet.has('after-previous')) {
      start = 'after';
    } else {
      start = 'click';
    }
  } else {
    if (start.includes('with')) start = 'with';
    else if (start.includes('after')) start = 'after';
    else start = 'click';
  }

  // ── 6. Subtype ────────────────────────────────────────────────────────────
  const subtype =
    (
      node.dataset?.pptxAnimationSubtype ||
      style?.getPropertyValue('--pptx-animation-subtype') ||
      style?.getPropertyValue('--pptx-subtype') ||
      ''
    ).trim() || null;

  // ── 7. Build Type (all at once, paragraph, letter) ───────────────────────
  let build = (
    node.dataset?.pptxAnimationBuild ||
    node.dataset?.pptxBuild ||
    style?.getPropertyValue('--pptx-animation-build') ||
    style?.getPropertyValue('--pptx-build') ||
    ''
  )
    .trim()
    .toLowerCase();

  if (!build) {
    const classSet = new Set(classList);
    if (classSet.has('paragraph') || classSet.has('animate-build-paragraph')) {
      build = 'paragraph';
    } else if (classSet.has('letter') || classSet.has('animate-build-letter')) {
      build = 'letter';
    } else if (classSet.has('all-at-once') || classSet.has('all-once') || classSet.has('animate-build-all')) {
      build = 'all';
    } else {
      build = 'all';
    }
  } else {
    if (build.includes('paragraph') || build === 'p') build = 'paragraph';
    else if (build.includes('letter') || build === 'l' || build === 'character') build = 'letter';
    else build = 'all';
  }

  // ── 8. Direction (to-up, to-down, to-left, to-right) ──────────────────────
  let direction = (
    node.dataset?.pptxAnimationDirection ||
    node.dataset?.pptxDirection ||
    style?.getPropertyValue('--pptx-animation-direction') ||
    style?.getPropertyValue('--pptx-direction') ||
    ''
  )
    .trim()
    .toLowerCase();

  if (!direction) {
    const classSet = new Set(classList);
    if (
      classSet.has('to-up') ||
      classSet.has('fly-in-bottom') ||
      classSet.has('fly-out-top') ||
      name === 'fly-in-bottom' ||
      name === 'fly-out-top'
    ) {
      direction = 'up';
    } else if (
      classSet.has('to-down') ||
      classSet.has('fly-in-top') ||
      classSet.has('fly-out-bottom') ||
      name === 'fly-in-top' ||
      name === 'fly-out-bottom'
    ) {
      direction = 'down';
    } else if (
      classSet.has('to-left') ||
      classSet.has('fly-in-left') ||
      classSet.has('fly-out-left') ||
      name === 'fly-in-left' ||
      name === 'fly-out-left'
    ) {
      direction = 'left';
    } else if (
      classSet.has('to-right') ||
      classSet.has('fly-in-right') ||
      classSet.has('fly-out-right') ||
      name === 'fly-in-right' ||
      name === 'fly-out-right'
    ) {
      direction = 'right';
    } else {
      direction = null;
    }
  } else {
    if (direction.includes('up')) direction = 'up';
    else if (direction.includes('down')) direction = 'down';
    else if (direction.includes('left')) direction = 'left';
    else if (direction.includes('right')) direction = 'right';
    else direction = null;
  }

  // ── 9. Orientation (vertical, horizontal) ─────────────────────────────────
  let orientation = (
    node.dataset?.pptxAnimationOrientation ||
    node.dataset?.pptxOrientation ||
    style?.getPropertyValue('--pptx-animation-orientation') ||
    style?.getPropertyValue('--pptx-orientation') ||
    ''
  )
    .trim()
    .toLowerCase();

  if (!orientation) {
    const classSet = new Set(classList);
    if (classSet.has('vertical')) {
      orientation = 'vertical';
    } else if (classSet.has('horizontal')) {
      orientation = 'horizontal';
    } else {
      orientation = null;
    }
  } else {
    if (orientation.includes('vert')) orientation = 'vertical';
    else if (orientation.includes('horz') || orientation.includes('hori')) orientation = 'horizontal';
    else orientation = null;
  }

  // ── 10. Validate and Sanitise Invalid Combinations ────────────────────────
  const isExit = animClass === 'exit';

  if (name.includes('fly')) {
    // Fly supports direction, ignores orientation
    if (!direction) {
      direction = isExit ? 'down' : 'up';
    }
    orientation = null;
  } else if (name.includes('wipe')) {
    // Wipe supports direction, ignores orientation
    if (!direction) {
      direction = 'down';
    }
    orientation = null;
  } else if (name.includes('split')) {
    // Split supports orientation, ignores direction
    if (!orientation) {
      orientation = 'vertical';
    }
    direction = null;
  } else if (name.includes('random-bars') || name.includes('randombar')) {
    // Random Bars supports orientation, ignores direction
    if (!orientation) {
      orientation = 'horizontal';
    }
    direction = null;
  } else {
    // Other animations do not support direction or orientation
    direction = null;
    orientation = null;
  }

  return {
    name,
    class: animClass,
    duration,
    delay,
    start,
    subtype,
    build,
    direction,
    orientation,
  };
}
