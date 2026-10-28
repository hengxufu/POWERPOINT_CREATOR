// src/animations/xml-templates.js
//
// Generates native PowerPoint <p:timing> XML from animation metadata.
// Structure derived from real PowerPoint-exported PPTX files (fixed reference XMLs).
//
// KEY STRUCTURAL RULES:
//
//  ENTRANCE animations:
//    1. <p:set style.visibility="visible"> FIRST (delay=0)
//    2. Then the actual effect (animEffect / p:anim motion)
//
//  EXIT animations:
//    1. The actual effect FIRST
//    2. Then <p:set style.visibility="hidden"> at the END (delay=duration-1)
//
//  Click-group structure (identical for entrance/exit):
//  <p:par>  ← outer click-group (delay=indefinite → numbered animation, not ⚡)
//    <p:cTn fill="hold">
//      <p:stCondLst><p:cond delay="indefinite"/></p:stCondLst>
//      <p:childTnLst>
//        <p:par>  ← inner wrapper (delay=0 or cumulative ms)
//          <p:cTn fill="hold">
//            <p:stCondLst><p:cond delay="N"/></p:stCondLst>
//            <p:childTnLst>
//              <p:par><p:cTn nodeType="clickEffect">...</p:cTn></p:par>
//              <p:par><p:cTn nodeType="withEffect">...</p:cTn></p:par>  ← SIBLING
//            </p:childTnLst>
//          </p:cTn>
//        </p:par>
//        <p:par>  ← separate inner wrapper for each afterEffect
//          ...
//        </p:par>
//      </p:childTnLst>
//    </p:cTn>
//  </p:par>
//
//  prevCondLst / nextCondLst MUST target <p:sldTgt/> for numbered animations.
//  bldLst entries MUST include animBg="1".

// ─────────────────────────────────────────────────────────────────────────────
// Preset definitions keyed by canonical name.
// "type" drives which XML builder to use in buildEffectChildren().
// ─────────────────────────────────────────────────────────────────────────────
const PRESETS = {
  // ── Entrance (10) ──────────────────────────────────────────────────────────
  'fade-in': {
    presetId: '10',
    presetSubtype: '0',
    class: 'entr',
    type: 'filter',
    filter: 'fade',
  },
  appear: {
    presetId: '1',
    presetSubtype: '0',
    class: 'entr',
    type: 'set',
  },
  'zoom-in': {
    // presetID=23 (Grow & Turn entrance), subtype=16
    // Animates ppt_w/ppt_h from 0 → #ppt_w/#ppt_h
    presetId: '23',
    presetSubtype: '16',
    class: 'entr',
    type: 'zoom',
  },
  'fly-in': {
    // presetID=2 (Fly In), subtype=4 (from bottom)
    // Entrance uses #ppt_x / #ppt_y (with # prefix)
    presetId: '2',
    presetSubtype: '4',
    class: 'entr',
    type: 'fly-entr',
  },
  'wipe-in': {
    presetId: '22',
    presetSubtype: '4',
    class: 'entr',
    type: 'filter',
    filter: 'wipe(down)',
  },
  'split-in': {
    presetId: '16',
    presetSubtype: '21',
    class: 'entr',
    type: 'filter',
    filter: 'barn(inVertical)',
  },
  wheel: {
    presetId: '21',
    presetSubtype: '4',
    class: 'entr',
    type: 'filter',
    filter: 'wheel(4)',
  },
  'bounce-in': {
    // presetID=26, subtype=0. Complex multi-keyframe y + animScale (bounce effect).
    presetId: '26',
    presetSubtype: '0',
    class: 'entr',
    type: 'bounce',
  },
  'checkerboard-in': {
    presetId: '7',
    presetSubtype: '0',
    class: 'entr',
    type: 'filter',
    filter: 'checkerboard(across)',
  },
  'random-bars-in': {
    // presetID=14, subtype=10. Filter is "randombar(horizontal)" NOT "randombar(horz)".
    presetId: '14',
    presetSubtype: '10',
    class: 'entr',
    type: 'filter',
    filter: 'randombar(horizontal)',
  },

  // ── Exit (10) ──────────────────────────────────────────────────────────────
  'fade-out': {
    presetId: '10',
    presetSubtype: '0',
    class: 'exit',
    type: 'filter',
    filter: 'fade',
  },
  disappear: {
    presetId: '1',
    presetSubtype: '0',
    class: 'exit',
    type: 'set',
  },
  'zoom-out': {
    // presetID=53, subtype=32. Animates ppt_w/ppt_h from ppt_w/ppt_h → 0 + fade filter.
    presetId: '53',
    presetSubtype: '32',
    class: 'exit',
    type: 'zoom',
  },
  'fly-out': {
    // Exit uses plain ppt_x / ppt_y (NO # prefix)
    presetId: '2',
    presetSubtype: '4',
    class: 'exit',
    type: 'fly-exit',
  },
  'wipe-out': {
    presetId: '22',
    presetSubtype: '4',
    class: 'exit',
    type: 'filter',
    filter: 'wipe(down)',
  },
  'split-out': {
    presetId: '16',
    presetSubtype: '21',
    class: 'exit',
    type: 'filter',
    filter: 'barn(outVertical)',
  },
  'wheel-out': {
    presetId: '21',
    presetSubtype: '4',
    class: 'exit',
    type: 'filter',
    filter: 'wheel(4)',
  },
  'bounce-out': {
    // presetID=26, subtype=0. Complex multi-keyframe bounce exit.
    presetId: '26',
    presetSubtype: '0',
    class: 'exit',
    type: 'bounce',
  },
  'checkerboard-out': {
    // presetID=5 (NOT 7), subtype=10.
    presetId: '5',
    presetSubtype: '10',
    class: 'exit',
    type: 'filter',
    filter: 'checkerboard(across)',
  },
  'random-bars-out': {
    // presetID=14, subtype=10.
    presetId: '14',
    presetSubtype: '10',
    class: 'exit',
    type: 'filter',
    filter: 'randombar(horizontal)',
  },
};

export function getPreset(name, animClass, options = {}) {
  const cls = animClass === 'exit' ? 'exit' : 'entr';
  let n = name.toLowerCase().replace(/^ppt-/, '');

  // Map known aliases to base 10+10 presets
  if (n.startsWith('fly-in')) n = 'fly-in';
  if (n.startsWith('fly-out')) n = 'fly-out';

  let presetObj;
  if (PRESETS[n]) {
    presetObj = { ...PRESETS[n], class: cls };
  } else {
    const withSuffix = cls === 'exit' ? n.replace(/(-in)?$/, '-out') : n.replace(/(-out)?$/, '-in');
    if (PRESETS[withSuffix]) {
      presetObj = { ...PRESETS[withSuffix], class: cls };
    } else {
      const base = n.replace(/-in$|-out$/, '');
      const targetKey = cls === 'exit' ? `${base}-out` : `${base}-in`;
      if (PRESETS[targetKey]) {
        presetObj = { ...PRESETS[targetKey], class: cls };
      } else {
        presetObj = { ...PRESETS[cls === 'exit' ? 'fade-out' : 'fade-in'], class: cls };
      }
    }
  }

  // Resolve direction/orientation dynamically
  const { direction, orientation } = options;
  if (n.includes('fly')) {
    presetObj.direction = direction || (cls === 'exit' ? 'down' : 'up');
    if (cls === 'exit') {
      presetObj.presetSubtype =
        presetObj.direction === 'up'
          ? '8'
          : presetObj.direction === 'down'
            ? '4'
            : presetObj.direction === 'left'
              ? '1'
              : presetObj.direction === 'right'
                ? '2'
                : '4';
    } else {
      presetObj.presetSubtype =
        presetObj.direction === 'up'
          ? '4'
          : presetObj.direction === 'down'
            ? '8'
            : presetObj.direction === 'left'
              ? '2'
              : presetObj.direction === 'right'
                ? '1'
                : '4';
    }
  } else if (n.includes('wipe')) {
    presetObj.direction = direction || 'down';
    presetObj.presetSubtype =
      presetObj.direction === 'left'
        ? '1'
        : presetObj.direction === 'right'
          ? '2'
          : presetObj.direction === 'down'
            ? '4'
            : presetObj.direction === 'up'
              ? '8'
              : '4';
    presetObj.filter = `wipe(${presetObj.direction})`;
  } else if (n.includes('split')) {
    presetObj.orientation = orientation || 'vertical';
    if (cls === 'exit') {
      if (presetObj.orientation === 'horizontal') {
        presetObj.presetSubtype = '6';
        presetObj.filter = 'barn(outHorizontal)';
      } else {
        presetObj.presetSubtype = '22';
        presetObj.filter = 'barn(outVertical)';
      }
    } else {
      if (presetObj.orientation === 'horizontal') {
        presetObj.presetSubtype = '5';
        presetObj.filter = 'barn(inHorizontal)';
      } else {
        presetObj.presetSubtype = '21';
        presetObj.filter = 'barn(inVertical)';
      }
    }
  } else if (n.includes('random-bars') || n.includes('randombar')) {
    presetObj.orientation = orientation || 'horizontal';
    presetObj.presetSubtype = presetObj.orientation === 'vertical' ? '9' : '10';
    presetObj.filter = `randombar(${presetObj.orientation})`;
  }

  return presetObj;
}

// ─────────────────────────────────────────────────────────────────────────────
// ID counter (reset before each buildTimingXml call)
// ─────────────────────────────────────────────────────────────────────────────
let _id = 1;
const nextId = () => _id++;

// ─────────────────────────────────────────────────────────────────────────────
// Primitive XML builders
// ─────────────────────────────────────────────────────────────────────────────

function buildTargetEl(spid, paragraphIndex, build) {
  if (build === 'paragraph' && paragraphIndex === 'bg') {
    return `<p:tgtEl><p:spTgt spid="${spid}"><p:bg/></p:spTgt></p:tgtEl>`;
  }
  if (build === 'paragraph' && typeof paragraphIndex === 'number') {
    return `<p:tgtEl><p:spTgt spid="${spid}"><p:txEl><p:pRg st="${paragraphIndex}" end="${paragraphIndex}"/></p:txEl></p:spTgt></p:tgtEl>`;
  }
  return `<p:tgtEl><p:spTgt spid="${spid}"/></p:tgtEl>`;
}

/** Visibility set — entrance: sets visible at start; exit: sets hidden at end */
function buildVisibilitySet(spid, animClass, delay, paragraphIndex, build) {
  const id = nextId();
  const val = animClass === 'exit' ? 'hidden' : 'visible';
  const delayAttr = delay != null ? ` delay="${delay}"` : '';
  const targetEl = buildTargetEl(spid, paragraphIndex, build);
  return (
    '<p:set>' +
    '<p:cBhvr>' +
    `<p:cTn id="${id}" dur="1" fill="hold"><p:stCondLst><p:cond${delayAttr}/></p:stCondLst></p:cTn>` +
    targetEl +
    '<p:attrNameLst><p:attrName>style.visibility</p:attrName></p:attrNameLst>' +
    '</p:cBhvr>' +
    `<p:to><p:strVal val="${val}"/></p:to>` +
    '</p:set>'
  );
}

function buildAnimEffect(spid, duration, transition, filter, paragraphIndex, build) {
  const id = nextId();
  const targetEl = buildTargetEl(spid, paragraphIndex, build);
  return (
    `<p:animEffect transition="${transition}" filter="${filter}">` +
    `<p:cBhvr><p:cTn id="${id}" dur="${duration}"/>` +
    targetEl +
    '</p:cBhvr>' +
    '</p:animEffect>'
  );
}

/** Motion anim for fly-in (entrance): uses #ppt_x / #ppt_y notation */
function buildMotionAxisEntrance(spid, duration, attr, fromVal, toVal, paragraphIndex, build) {
  const id = nextId();
  const targetEl = buildTargetEl(spid, paragraphIndex, build);
  return (
    `<p:anim calcMode="lin" valueType="num">` +
    `<p:cBhvr additive="base">` +
    `<p:cTn id="${id}" dur="${duration}" fill="hold"/>` +
    targetEl +
    `<p:attrNameLst><p:attrName>${attr}</p:attrName></p:attrNameLst>` +
    `</p:cBhvr>` +
    `<p:tavLst>` +
    `<p:tav tm="0"><p:val><p:strVal val="${fromVal}"/></p:val></p:tav>` +
    `<p:tav tm="100000"><p:val><p:strVal val="${toVal}"/></p:val></p:tav>` +
    `</p:tavLst>` +
    `</p:anim>`
  );
}

/** Motion anim for fly-out (exit): uses plain ppt_x / ppt_y (no # prefix) */
function buildMotionAxisExit(spid, duration, attr, fromVal, toVal, paragraphIndex, build) {
  const id = nextId();
  const targetEl = buildTargetEl(spid, paragraphIndex, build);
  return (
    `<p:anim calcMode="lin" valueType="num">` +
    `<p:cBhvr additive="base">` +
    `<p:cTn id="${id}" dur="${duration}"/>` +
    targetEl +
    `<p:attrNameLst><p:attrName>${attr}</p:attrName></p:attrNameLst>` +
    `</p:cBhvr>` +
    `<p:tavLst>` +
    `<p:tav tm="0"><p:val><p:strVal val="${fromVal}"/></p:val></p:tav>` +
    `<p:tav tm="100000"><p:val><p:strVal val="${toVal}"/></p:val></p:tav>` +
    `</p:tavLst>` +
    `</p:anim>`
  );
}

/** Zoom anim: animates ppt_w and ppt_h */
function buildZoomAxis(spid, duration, attr, fromVal, toVal, paragraphIndex, build) {
  const id = nextId();
  const fromNode = typeof fromVal === 'number' ? `<p:fltVal val="${fromVal}"/>` : `<p:strVal val="${fromVal}"/>`;
  const toNode = typeof toVal === 'number' ? `<p:fltVal val="${toVal}"/>` : `<p:strVal val="${toVal}"/>`;
  const targetEl = buildTargetEl(spid, paragraphIndex, build);
  return (
    `<p:anim calcMode="lin" valueType="num">` +
    `<p:cBhvr>` +
    `<p:cTn id="${id}" dur="${duration}" fill="hold"/>` +
    targetEl +
    `<p:attrNameLst><p:attrName>${attr}</p:attrName></p:attrNameLst>` +
    `</p:cBhvr>` +
    `<p:tavLst>` +
    `<p:tav tm="0"><p:val>${fromNode}</p:val></p:tav>` +
    `<p:tav tm="100000"><p:val>${toNode}</p:val></p:tav>` +
    `</p:tavLst>` +
    `</p:anim>`
  );
}

/**
 * Builds the bounce-in entrance effect children.
 * Based on exact XML from PowerPoint reference (slide1.xml).
 * Uses multi-keyframe ppt_y animation + animScale blocks for the
 * classic PowerPoint "Bounce" entrance effect.
 */
function buildBounceEntranceChildren(spid, duration, paragraphIndex, build) {
  // The bounce-in (presetID=26) uses a wipe filter (down) for the entrance reveal,
  // combined with a complex ppt_y (sin-formula keyframes) and ppt_x slide,
  // plus a series of animScale to simulate the vertical bounces.
  // Duration breakdown: total ~1820ms. We scale relative to `duration`.
  const scale = duration / 1820;
  const d1 = Math.round(1822 * scale);
  const d2 = Math.round(664 * scale);
  const d3 = Math.round(664 * scale);
  const d4 = Math.round(332 * scale);
  const d5 = Math.round(164 * scale);

  const id1 = nextId();
  const id2 = nextId();
  const id3 = nextId();
  const id4 = nextId();
  const id5 = nextId();
  const id6 = nextId();
  const id7 = nextId();
  const id8 = nextId();
  const id9 = nextId();
  const id10 = nextId();
  const id11 = nextId();
  const id12 = nextId();
  const id13 = nextId();
  const id14 = nextId();

  const filterDur = Math.round(580 * scale);
  const aniScale1Delay = Math.round(650 * scale);
  const aniScale2Delay = Math.round(676 * scale);
  const aniScale3Delay = Math.round(1312 * scale);
  const aniScale4Delay = Math.round(1338 * scale);
  const aniScale5Delay = Math.round(1642 * scale);
  const aniScale6Delay = Math.round(1668 * scale);
  const aniScale7Delay = Math.round(1808 * scale);
  const aniScale8Delay = Math.round(1834 * scale);
  const d2delay = Math.round(664 * scale);
  const d3delay = Math.round(1324 * scale);
  const d4delay = Math.round(1656 * scale);

  const targetEl = buildTargetEl(spid, paragraphIndex, build);

  return (
    buildVisibilitySet(spid, 'entr', 0, paragraphIndex, build) +
    `<p:animEffect transition="in" filter="wipe(down)"><p:cBhvr><p:cTn id="${id1}" dur="${filterDur}"><p:stCondLst><p:cond delay="0"/></p:stCondLst></p:cTn>${targetEl}</p:cBhvr></p:animEffect>` +
    // ppt_x slide (bouncing in from left with deceleration)
    `<p:anim calcMode="lin" valueType="num"><p:cBhvr><p:cTn id="${id2}" dur="${d1}" tmFilter="0,0; 0.14,0.36; 0.43,0.73; 0.71,0.91; 1.0,1.0"><p:stCondLst><p:cond delay="0"/></p:stCondLst></p:cTn>${targetEl}<p:attrNameLst><p:attrName>ppt_x</p:attrName></p:attrNameLst></p:cBhvr><p:tavLst><p:tav tm="0"><p:val><p:strVal val="#ppt_x-0.25"/></p:val></p:tav><p:tav tm="100000"><p:val><p:strVal val="#ppt_x"/></p:val></p:tav></p:tavLst></p:anim>` +
    // ppt_y bounce phases
    `<p:anim calcMode="lin" valueType="num"><p:cBhvr><p:cTn id="${id3}" dur="${d2}" tmFilter="0.0,0.0; 0.25,0.07; 0.50,0.2; 0.75,0.467; 1.0,1.0"><p:stCondLst><p:cond delay="0"/></p:stCondLst></p:cTn>${targetEl}<p:attrNameLst><p:attrName>ppt_y</p:attrName></p:attrNameLst></p:cBhvr><p:tavLst><p:tav tm="0" fmla="#ppt_y-sin(pi*$)/3"><p:val><p:fltVal val="0.5"/></p:val></p:tav><p:tav tm="100000"><p:val><p:fltVal val="1"/></p:val></p:tav></p:tavLst></p:anim>` +
    `<p:anim calcMode="lin" valueType="num"><p:cBhvr><p:cTn id="${id4}" dur="${d3}" tmFilter="0, 0; 0.125,0.2665; 0.25,0.4; 0.375,0.465; 0.5,0.5;  0.625,0.535; 0.75,0.6; 0.875,0.7335; 1,1"><p:stCondLst><p:cond delay="${d2delay}"/></p:stCondLst></p:cTn>${targetEl}<p:attrNameLst><p:attrName>ppt_y</p:attrName></p:attrNameLst></p:cBhvr><p:tavLst><p:tav tm="0" fmla="#ppt_y-sin(pi*$)/9"><p:val><p:fltVal val="0"/></p:val></p:tav><p:tav tm="100000"><p:val><p:fltVal val="1"/></p:val></p:tav></p:tavLst></p:anim>` +
    `<p:anim calcMode="lin" valueType="num"><p:cBhvr><p:cTn id="${id5}" dur="${d4}" tmFilter="0, 0; 0.125,0.2665; 0.25,0.4; 0.375,0.465; 0.5,0.5;  0.625,0.535; 0.75,0.6; 0.875,0.7335; 1,1"><p:stCondLst><p:cond delay="${d3delay}"/></p:stCondLst></p:cTn>${targetEl}<p:attrNameLst><p:attrName>ppt_y</p:attrName></p:attrNameLst></p:cBhvr><p:tavLst><p:tav tm="0" fmla="#ppt_y-sin(pi*$)/27"><p:val><p:fltVal val="0"/></p:val></p:tav><p:tav tm="100000"><p:val><p:fltVal val="1"/></p:val></p:tav></p:tavLst></p:anim>` +
    `<p:anim calcMode="lin" valueType="num"><p:cBhvr><p:cTn id="${id6}" dur="${d5}" tmFilter="0, 0; 0.125,0.2665; 0.25,0.4; 0.375,0.465; 0.5,0.5;  0.625,0.535; 0.75,0.6; 0.875,0.7335; 1,1"><p:stCondLst><p:cond delay="${d4delay}"/></p:stCondLst></p:cTn>${targetEl}<p:attrNameLst><p:attrName>ppt_y</p:attrName></p:attrNameLst></p:cBhvr><p:tavLst><p:tav tm="0" fmla="#ppt_y-sin(pi*$)/81"><p:val><p:fltVal val="0"/></p:val></p:tav><p:tav tm="100000"><p:val><p:fltVal val="1"/></p:val></p:tav></p:tavLst></p:anim>` +
    // animScale blocks
    `<p:animScale><p:cBhvr><p:cTn id="${id7}" dur="26"><p:stCondLst><p:cond delay="${aniScale1Delay}"/></p:stCondLst></p:cTn>${targetEl}</p:cBhvr><p:to x="100000" y="60000"/></p:animScale>` +
    `<p:animScale><p:cBhvr><p:cTn id="${id8}" dur="166" decel="50000"><p:stCondLst><p:cond delay="${aniScale2Delay}"/></p:stCondLst></p:cTn>${targetEl}</p:cBhvr><p:to x="100000" y="100000"/></p:animScale>` +
    `<p:animScale><p:cBhvr><p:cTn id="${id9}" dur="26"><p:stCondLst><p:cond delay="${aniScale3Delay}"/></p:stCondLst></p:cTn>${targetEl}</p:cBhvr><p:to x="100000" y="80000"/></p:animScale>` +
    `<p:animScale><p:cBhvr><p:cTn id="${id10}" dur="166" decel="50000"><p:stCondLst><p:cond delay="${aniScale4Delay}"/></p:stCondLst></p:cTn>${targetEl}</p:cBhvr><p:to x="100000" y="100000"/></p:animScale>` +
    `<p:animScale><p:cBhvr><p:cTn id="${id11}" dur="26"><p:stCondLst><p:cond delay="${aniScale5Delay}"/></p:stCondLst></p:cTn>${targetEl}</p:cBhvr><p:to x="100000" y="90000"/></p:animScale>` +
    `<p:animScale><p:cBhvr><p:cTn id="${id12}" dur="166" decel="50000"><p:stCondLst><p:cond delay="${aniScale6Delay}"/></p:stCondLst></p:cTn>${targetEl}</p:cBhvr><p:to x="100000" y="100000"/></p:animScale>` +
    `<p:animScale><p:cBhvr><p:cTn id="${id13}" dur="26"><p:stCondLst><p:cond delay="${aniScale7Delay}"/></p:stCondLst></p:cTn>${targetEl}</p:cBhvr><p:to x="100000" y="95000"/></p:animScale>` +
    `<p:animScale><p:cBhvr><p:cTn id="${id14}" dur="166" decel="50000"><p:stCondLst><p:cond delay="${aniScale8Delay}"/></p:stCondLst></p:cTn>${targetEl}</p:cBhvr><p:to x="100000" y="100000"/></p:animScale>`
  );
}

/**
 * Builds the bounce-out exit effect children.
 * Based on exact XML from PowerPoint reference (slide2.xml, presetID=26 exit).
 * Uses multi-keyframe ppt_y (sinusoidal) + horizontal drift + wipe filter at end.
 */
function buildBounceExitChildren(spid, duration, paragraphIndex, build) {
  const scale = duration / 2000;
  const totalDur = Math.round(2000 * scale);

  // ID pool
  const ids = [];
  for (let i = 0; i < 20; i++) ids.push(nextId());

  const d1 = Math.round(1822 * scale);
  const d2 = Math.round(664 * scale);
  const d3 = Math.round(664 * scale);

  const d5 = Math.round(164 * scale);
  const wipeDelay = Math.round(1820 * scale);
  const wipeDur = Math.round(180 * scale);
  const d2delay = Math.round(664 * scale);
  const d3delay = Math.round(1324 * scale);
  const d4delay = Math.round(1656 * scale);
  const xDur2 = Math.round(178 * scale);
  const xDelay2 = Math.round(1822 * scale);
  const hidDelay = totalDur - 1;

  const targetEl = buildTargetEl(spid, paragraphIndex, build);

  return (
    // wipe out at end (after bounces are done)
    `<p:animEffect transition="out" filter="wipe(down)"><p:cBhvr><p:cTn id="${ids[0]}" dur="${wipeDur}" accel="50000"><p:stCondLst><p:cond delay="${wipeDelay}"/></p:stCondLst></p:cTn>${targetEl}</p:cBhvr></p:animEffect>` +
    // ppt_x drift (element drifts to right while bouncing)
    `<p:anim calcMode="lin" valueType="num"><p:cBhvr><p:cTn id="${ids[1]}" dur="${d1}" tmFilter="0,0; 0.14,0.31; 0.43,0.73; 0.71,0.91; 1.0,1.0"><p:stCondLst><p:cond delay="0"/></p:stCondLst></p:cTn>${targetEl}<p:attrNameLst><p:attrName>ppt_x</p:attrName></p:attrNameLst></p:cBhvr><p:tavLst><p:tav tm="0"><p:val><p:strVal val="ppt_x"/></p:val></p:tav><p:tav tm="100000"><p:val><p:strVal val="#ppt_x+0.25"/></p:val></p:tav></p:tavLst></p:anim>` +
    `<p:anim calcMode="lin" valueType="num"><p:cBhvr><p:cTn id="${ids[2]}" dur="${xDur2}"><p:stCondLst><p:cond delay="${xDelay2}"/></p:stCondLst></p:cTn>${targetEl}<p:attrNameLst><p:attrName>ppt_x</p:attrName></p:attrNameLst></p:cBhvr><p:tavLst><p:tav tm="0"><p:val><p:strVal val="ppt_x"/></p:val></p:tav><p:tav tm="100000"><p:val><p:strVal val="ppt_x"/></p:val></p:tav></p:tavLst></p:anim>` +
    // ppt_y bounce phases (downward bounces before flying off)
    `<p:anim calcMode="lin" valueType="num"><p:cBhvr><p:cTn id="${ids[3]}" dur="${d2}" tmFilter="0.0,0.0;0.25,0.07;0.50,0.2;0.75,0.467;1.0,1.0"><p:stCondLst><p:cond delay="0"/></p:stCondLst></p:cTn>${targetEl}<p:attrNameLst><p:attrName>ppt_y</p:attrName></p:attrNameLst></p:cBhvr><p:tavLst><p:tav tm="0"><p:val><p:strVal val="ppt_y"/></p:val></p:tav><p:tav tm="5000"><p:val><p:strVal val="ppt_y+0.026"/></p:val></p:tav><p:tav tm="10000"><p:val><p:strVal val="ppt_y+0.052"/></p:val></p:tav><p:tav tm="15000"><p:val><p:strVal val="ppt_y+0.078"/></p:val></p:tav><p:tav tm="20000"><p:val><p:strVal val="ppt_y+0.103"/></p:val></p:tav><p:tav tm="30000"><p:val><p:strVal val="ppt_y+0.151"/></p:val></p:tav><p:tav tm="40000"><p:val><p:strVal val="ppt_y+0.196"/></p:val></p:tav><p:tav tm="50000"><p:val><p:strVal val="ppt_y+0.236"/></p:val></p:tav><p:tav tm="60000"><p:val><p:strVal val="ppt_y+0.270"/></p:val></p:tav><p:tav tm="70000"><p:val><p:strVal val="ppt_y+0.297"/></p:val></p:tav><p:tav tm="80000"><p:val><p:strVal val="ppt_y+0.317"/></p:val></p:tav><p:tav tm="90000"><p:val><p:strVal val="ppt_y+0.329"/></p:val></p:tav><p:tav tm="100000"><p:val><p:strVal val="ppt_y+0.333"/></p:val></p:tav></p:tavLst></p:anim>` +
    `<p:anim calcMode="lin" valueType="num"><p:cBhvr><p:cTn id="${ids[4]}" dur="${d3}" tmFilter="0, 0; 0.125,0.2665; 0.25,0.4; 0.375,0.465; 0.5,0.5;  0.625,0.535; 0.75,0.6; 0.875,0.7335; 1,1"><p:stCondLst><p:cond delay="${d2delay}"/></p:stCondLst></p:cTn>${targetEl}<p:attrNameLst><p:attrName>ppt_y</p:attrName></p:attrNameLst></p:cBhvr><p:tavLst><p:tav tm="0"><p:val><p:strVal val="ppt_y"/></p:val></p:tav><p:tav tm="10000"><p:val><p:strVal val="ppt_y-0.034"/></p:val></p:tav><p:tav tm="20000"><p:val><p:strVal val="ppt_y-0.065"/></p:val></p:tav><p:tav tm="30000"><p:val><p:strVal val="ppt_y-0.090"/></p:val></p:tav><p:tav tm="40000"><p:val><p:strVal val="ppt_y-0.106"/></p:val></p:tav><p:tav tm="50000"><p:val><p:strVal val="ppt_y-0.111"/></p:val></p:tav><p:tav tm="60000"><p:val><p:strVal val="ppt_y-0.106"/></p:val></p:tav><p:tav tm="70000"><p:val><p:strVal val="ppt_y-0.090"/></p:val></p:tav><p:tav tm="80000"><p:val><p:strVal val="ppt_y-0.065"/></p:val></p:tav><p:tav tm="90000"><p:val><p:strVal val="ppt_y-0.034"/></p:val></p:tav><p:tav tm="100000"><p:val><p:strVal val="ppt_y"/></p:val></p:tav></p:tavLst></p:anim>` +
    `<p:anim calcMode="lin" valueType="num"><p:cBhvr><p:cTn id="${ids[5]}" dur="${d5}" tmFilter="0, 0; 0.125,0.2665; 0.25,0.4; 0.375,0.465; 0.5,0.5;  0.625,0.535; 0.75,0.6; 0.875,0.7335; 1,1"><p:stCondLst><p:cond delay="${d3delay}"/></p:stCondLst></p:cTn>${targetEl}<p:attrNameLst><p:attrName>ppt_y</p:attrName></p:attrNameLst></p:cBhvr><p:tavLst><p:tav tm="0"><p:val><p:strVal val="ppt_y"/></p:val></p:tav><p:tav tm="10000"><p:val><p:strVal val="ppt_y-0.011"/></p:val></p:tav><p:tav tm="20000"><p:val><p:strVal val="ppt_y-0.022"/></p:val></p:tav><p:tav tm="30000"><p:val><p:strVal val="ppt_y-0.030"/></p:val></p:tav><p:tav tm="40000"><p:val><p:strVal val="ppt_y-0.035"/></p:val></p:tav><p:tav tm="50000"><p:val><p:strVal val="ppt_y-0.037"/></p:val></p:tav><p:tav tm="60000"><p:val><p:strVal val="ppt_y-0.035"/></p:val></p:tav><p:tav tm="70000"><p:val><p:strVal val="ppt_y-0.030"/></p:val></p:tav><p:tav tm="80000"><p:val><p:strVal val="ppt_y-0.022"/></p:val></p:tav><p:tav tm="90000"><p:val><p:strVal val="ppt_y-0.011"/></p:val></p:tav><p:tav tm="100000"><p:val><p:strVal val="ppt_y"/></p:val></p:tav></p:tavLst></p:anim>` +
    `<p:anim calcMode="lin" valueType="num"><p:cBhvr><p:cTn id="${ids[6]}" dur="${d5}" tmFilter="0, 0; 0.125,0.2665; 0.25,0.4; 0.375,0.465; 0.5,0.5;  0.625,0.535; 0.75,0.6; 0.875,0.7335; 1,1"><p:stCondLst><p:cond delay="${d4delay}"/></p:stCondLst></p:cTn>${targetEl}<p:attrNameLst><p:attrName>ppt_y</p:attrName></p:attrNameLst></p:cBhvr><p:tavLst><p:tav tm="0"><p:val><p:strVal val="ppt_y"/></p:val></p:tav><p:tav tm="10000"><p:val><p:strVal val="ppt_y-0.004"/></p:val></p:tav><p:tav tm="20000"><p:val><p:strVal val="ppt_y-0.007"/></p:val></p:tav><p:tav tm="30000"><p:val><p:strVal val="ppt_y-0.010"/></p:val></p:tav><p:tav tm="40000"><p:val><p:strVal val="ppt_y-0.012"/></p:val></p:tav><p:tav tm="50000"><p:val><p:strVal val="ppt_y-0.0123"/></p:val></p:tav><p:tav tm="60000"><p:val><p:strVal val="ppt_y-0.012"/></p:val></p:tav><p:tav tm="70000"><p:val><p:strVal val="ppt_y-0.010"/></p:val></p:tav><p:tav tm="80000"><p:val><p:strVal val="ppt_y-0.007"/></p:val></p:tav><p:tav tm="90000"><p:val><p:strVal val="ppt_y-0.004"/></p:val></p:tav><p:tav tm="100000"><p:val><p:strVal val="ppt_y"/></p:val></p:tav></p:tavLst></p:anim>` +
    // final acceleration y
    `<p:anim calcMode="lin" valueType="num"><p:cBhvr><p:cTn id="${ids[7]}" dur="${wipeDur}" accel="50000"><p:stCondLst><p:cond delay="${wipeDelay}"/></p:stCondLst></p:cTn>${targetEl}<p:attrNameLst><p:attrName>ppt_y</p:attrName></p:attrNameLst></p:cBhvr><p:tavLst><p:tav tm="0"><p:val><p:strVal val="ppt_y"/></p:val></p:tav><p:tav tm="100000"><p:val><p:strVal val="1+ppt_h/2"/></p:val></p:tav></p:tavLst></p:anim>` +
    // visibility hide at the very end
    buildVisibilitySet(spid, 'exit', hidDelay, paragraphIndex, build)
  );
}

/**
 * Builds the effect children for a single shape animation.
 * Entrance: visibility-visible first, then effect.
 * Exit: effect first, then visibility-hidden at end.
 */
function buildEffectChildren(spid, preset, duration, animClass, paragraphIndex, build) {
  const isExit = animClass === 'exit';

  if (preset.type === 'set') {
    // Appear/Disappear: just a visibility set
    return buildVisibilitySet(spid, animClass, 0, paragraphIndex, build);
  }

  if (preset.type === 'bounce') {
    if (isExit) return buildBounceExitChildren(spid, duration, paragraphIndex, build);
    else return buildBounceEntranceChildren(spid, duration, paragraphIndex, build);
  }

  if (preset.type === 'filter') {
    const transition = isExit ? 'out' : 'in';
    if (isExit) {
      // Exit filter: effect first, then hide
      return (
        buildAnimEffect(spid, duration, transition, preset.filter, paragraphIndex, build) +
        buildVisibilitySet(spid, 'exit', duration - 1, paragraphIndex, build)
      );
    } else {
      // Entrance filter: show first, then effect
      return (
        buildVisibilitySet(spid, 'entr', 0, paragraphIndex, build) +
        buildAnimEffect(spid, duration, transition, preset.filter, paragraphIndex, build)
      );
    }
  }

  if (preset.type === 'zoom') {
    if (isExit) {
      // zoom-out: presetID=53. Animate w/h from current to 0 + fade filter + hide at end
      return (
        buildZoomAxis(spid, duration, 'ppt_w', 'ppt_w', 0, paragraphIndex, build) +
        buildZoomAxis(spid, duration, 'ppt_h', 'ppt_h', 0, paragraphIndex, build) +
        buildAnimEffect(spid, duration, 'out', 'fade', paragraphIndex, build) +
        buildVisibilitySet(spid, 'exit', duration - 1, paragraphIndex, build)
      );
    } else {
      // zoom-in: presetID=23. Animate w/h from 0 to #ppt_w/#ppt_h
      return (
        buildVisibilitySet(spid, 'entr', 0, paragraphIndex, build) +
        buildZoomAxis(spid, duration, 'ppt_w', 0, '#ppt_w', paragraphIndex, build) +
        buildZoomAxis(spid, duration, 'ppt_h', 0, '#ppt_h', paragraphIndex, build)
      );
    }
  }

  if (preset.type === 'fly-entr') {
    const dir = preset.direction || 'up';
    let fromX = '#ppt_x',
      toX = '#ppt_x';
    let fromY = '#ppt_y',
      toY = '#ppt_y';

    if (dir === 'up') {
      fromY = '1+#ppt_h/2';
    } else if (dir === 'down') {
      fromY = '-#ppt_h/2';
    } else if (dir === 'left') {
      fromX = '1+#ppt_w/2';
    } else if (dir === 'right') {
      fromX = '-#ppt_w/2';
    }

    return (
      buildVisibilitySet(spid, 'entr', 0, paragraphIndex, build) +
      buildMotionAxisEntrance(spid, duration, 'ppt_x', fromX, toX, paragraphIndex, build) +
      buildMotionAxisEntrance(spid, duration, 'ppt_y', fromY, toY, paragraphIndex, build)
    );
  }

  if (preset.type === 'fly-exit') {
    const dir = preset.direction || 'down';
    let fromX = 'ppt_x',
      toX = 'ppt_x';
    let fromY = 'ppt_y',
      toY = 'ppt_y';

    if (dir === 'up') {
      toY = '-ppt_h/2';
    } else if (dir === 'down') {
      toY = '1+ppt_h/2';
    } else if (dir === 'left') {
      toX = '-ppt_w/2';
    } else if (dir === 'right') {
      toX = '1+ppt_w/2';
    }

    return (
      buildMotionAxisExit(spid, duration, 'ppt_x', fromX, toX, paragraphIndex, build) +
      buildMotionAxisExit(spid, duration, 'ppt_y', fromY, toY, paragraphIndex, build) +
      buildVisibilitySet(spid, 'exit', duration - 1, paragraphIndex, build)
    );
  }

  // Default fallback for simple effects (fade, wipe, etc)
  const transition = animClass === 'entr' ? 'in' : 'out';
  const filter = preset.filter || 'fade';

  if (animClass === 'exit') {
    return (
      buildAnimEffect(spid, duration, transition, filter, paragraphIndex, build) +
      buildVisibilitySet(spid, 'exit', duration - 1, paragraphIndex, build)
    );
  } else {
    return (
      buildVisibilitySet(spid, 'entr', 0, paragraphIndex, build) +
      buildAnimEffect(spid, duration, transition, filter, paragraphIndex, build)
    );
  }
}

/**
 * Builds ONE effect-level <p:par> (the innermost).
 * nodeType is "clickEffect", "withEffect", or "afterEffect".
 */
function buildEffectPar(spid, preset, duration, animClass, nodeType, paragraphIndex, build) {
  const id = nextId();

  // PowerPoint requires grpId="0" for all standard sequence animations to prevent the ⚡ trigger symbol
  const grpAttr = ' grpId="0"';

  // For zero-duration effects (appear/disappear), PowerPoint expects an absolute delay between letters (tmAbs).
  // Using tmPct on a zero-duration effect causes PPTX corruption.
  const isZeroDuration = preset.type === 'set';
  const iterateXml =
    build === 'letter'
      ? isZeroDuration
        ? '<p:iterate type="lt"><p:tmAbs val="500"/></p:iterate>'
        : '<p:iterate type="lt"><p:tmPct val="10000"/></p:iterate>'
      : '';

  return (
    '<p:par>' +
    `<p:cTn id="${id}" presetID="${preset.presetId}" presetClass="${animClass}" ` +
    `presetSubtype="${preset.presetSubtype}" fill="hold"${grpAttr} nodeType="${nodeType}">` +
    '<p:stCondLst><p:cond delay="0"/></p:stCondLst>' +
    iterateXml +
    `<p:childTnLst>${buildEffectChildren(spid, preset, duration, animClass, paragraphIndex, build)}</p:childTnLst>` +
    '</p:cTn>' +
    '</p:par>'
  );
}

/**
 * Builds the full <p:timing> XML (including <p:bldLst>) for a slide.
 *
 * Grouping rules:
 *  start="click"  → new outer click-group + new inner wrapper (delay=0)
 *  start="with"   → joins the CURRENT inner wrapper as a sibling withEffect
 *  start="after"  → new inner wrapper in current outer, delay=cumulative ms
 *
 * @param {Array<Object>} animations   - animation metadata collected during traversal
 * @param {Map<number,string[]>} domToSpIdMap
 * @returns {string}
 */
export function buildTimingXml(animations, domToSpIdMap, textBoxSpIds) {
  if (!animations || animations.length === 0) return '';

  // ── 1. Resolve animations to shape IDs ──────────────────────────────────
  const resolved = [];
  const shapeBuilds = new Map(); // spid -> buildType

  for (const anim of animations) {
    const spIds = domToSpIdMap.get(anim.domOrder);
    if (!spIds || spIds.length === 0) continue;

    const preset = getPreset(anim.name, anim.class, {
      direction: anim.direction,
      orientation: anim.orientation,
    });
    const animClass = preset.class;
    const build = anim.build || 'all';
    const numParagraphs = anim.numParagraphs || 1;

    for (const spid of spIds) {
      // Non-textbox shapes (like pictures or empty shapes) cannot have paragraph/letter builds
      const isTextBox = !textBoxSpIds || textBoxSpIds.has(spid);
      const actualBuild = isTextBox ? build : 'all';

      if (actualBuild === 'paragraph') {
        shapeBuilds.set(spid, 'p');

        // 1. Add background step (required by PowerPoint for timeline consistency when animBg="1")
        resolved.push({
          spid,
          preset,
          duration: anim.duration,
          animClass,
          start: anim.start,
          selfDelay: anim.delay || 0,
          paragraphIndex: 'bg',
          build: actualBuild,
        });

        // 2. Expand to one step per paragraph
        for (let pIdx = 0; pIdx < numParagraphs; pIdx++) {
          const pStart = pIdx === 0 ? 'with' : anim.start === 'with' ? 'with' : 'after';
          const pDelay = 0;
          resolved.push({
            spid,
            preset,
            duration: anim.duration,
            animClass,
            start: pStart,
            selfDelay: pDelay,
            paragraphIndex: pIdx,
            build: actualBuild,
          });
        }
      } else {
        shapeBuilds.set(spid, 'all');
        resolved.push({
          spid,
          preset,
          duration: anim.duration,
          animClass,
          start: anim.start,
          selfDelay: anim.delay || 0,
          paragraphIndex: null,
          build: actualBuild,
        });
      }
    }
  }
  if (resolved.length === 0) return '';

  // ── 2. Group into click-groups ───────────────────────────────────────────
  const clickGroups = [];
  let currentOuter = null;
  let currentInner = null;
  let groupTime = 0;
  let lastDuration = 0;

  for (const e of resolved) {
    if (e.start === 'click' || currentOuter === null) {
      currentInner = [{ ...e, nodeType: 'clickEffect', innerDelay: 0 }];
      currentOuter = [currentInner];
      clickGroups.push(currentOuter);
      groupTime = 0;
      lastDuration = e.duration;
    } else if (e.start === 'with') {
      currentInner.push({ ...e, nodeType: 'withEffect', innerDelay: currentInner[0].innerDelay });
    } else if (e.start === 'after') {
      groupTime += lastDuration + e.selfDelay;
      lastDuration = e.duration;
      currentInner = [{ ...e, nodeType: 'afterEffect', innerDelay: groupTime }];
      currentOuter.push(currentInner);
    }
  }

  // ── 3. Build XML with STRICTLY Monotonically Increasing Top-Down IDs ───
  // PowerPoint's rendering engine requires p:cTn IDs to be sequentially increasing
  // in document order. If child nodes have lower IDs than their parents (bottom-up),
  // PowerPoint struggles to resolve the timeline and drops the frame rate to ~5fps
  // (causing the stop-motion/buffering effect).
  _id = 1;
  const rootId = nextId(); // 1
  const mainSeqId = nextId(); // 2

  let allClickGroupXml = '';
  for (const innerWrappers of clickGroups) {
    const outerId = nextId();
    allClickGroupXml += `<p:par><p:cTn id="${outerId}" fill="hold"><p:stCondLst><p:cond delay="indefinite"/></p:stCondLst><p:childTnLst>`;

    for (const effects of innerWrappers) {
      const innerId = nextId();
      const delay = effects[0].innerDelay;
      allClickGroupXml += `<p:par><p:cTn id="${innerId}" fill="hold"><p:stCondLst><p:cond delay="${delay}"/></p:stCondLst><p:childTnLst>`;

      for (const e of effects) {
        allClickGroupXml += buildEffectPar(
          e.spid,
          e.preset,
          e.duration,
          e.animClass,
          e.nodeType,
          e.paragraphIndex,
          e.build
        );
      }

      allClickGroupXml += `</p:childTnLst></p:cTn></p:par>`;
    }

    allClickGroupXml += `</p:childTnLst></p:cTn></p:par>`;
  }

  // ── 4. Build p:bldLst (animBg="1" restored because PowerPoint requires it for compliance) ───
  const animatedSpids = [];
  const seen = new Set();
  for (const group of clickGroups) {
    for (const wrapper of group) {
      for (const e of wrapper) {
        if (!seen.has(e.spid)) {
          seen.add(e.spid);
          animatedSpids.push(e.spid);
        }
      }
    }
  }
  const bldLst =
    animatedSpids.length > 0
      ? `<p:bldLst>${animatedSpids
          .map((s) => {
            const buildType = shapeBuilds.get(s);
            if (buildType === 'p') {
              return `<p:bldP spid="${s}" grpId="0" build="p" animBg="1"/>`;
            }
            // animBg="1" is required for all animated shapes in bldLst —
            // this matches how PowerPoint's own export always formats bldP entries.
            return `<p:bldP spid="${s}" grpId="0" animBg="1"/>`;
          })
          .join('')}</p:bldLst>`
      : '';

  return (
    '<p:timing xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">' +
    '<p:tnLst>' +
    '<p:par>' +
    `<p:cTn id="${rootId}" dur="indefinite" restart="never" nodeType="tmRoot">` +
    '<p:childTnLst>' +
    '<p:seq concurrent="1" nextAc="seek">' +
    `<p:cTn id="${mainSeqId}" dur="indefinite" nodeType="mainSeq">` +
    `<p:childTnLst>${allClickGroupXml}</p:childTnLst>` +
    '</p:cTn>' +
    // CRITICAL: <p:sldTgt/> for numbered animations (not ⚡)
    '<p:prevCondLst><p:cond evt="onPrev" delay="0"><p:tgtEl><p:sldTgt/></p:tgtEl></p:cond></p:prevCondLst>' +
    '<p:nextCondLst><p:cond evt="onNext" delay="0"><p:tgtEl><p:sldTgt/></p:tgtEl></p:cond></p:nextCondLst>' +
    '</p:seq>' +
    '</p:childTnLst>' +
    '</p:cTn>' +
    '</p:par>' +
    '</p:tnLst>' +
    bldLst +
    '</p:timing>'
  );
}
