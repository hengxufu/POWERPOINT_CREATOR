# dom-to-pptx: System Knowledge Graph

This knowledge graph provides structural, relational, and data-flow mappings of the `dom-to-pptx` ecosystem for autonomous agents and developer tooling.

---

## 1. Domain Entity & Component Graph

```mermaid
graph TD
    subgraph Inputs ["Input Layer"]
        HTML["DOM Tree (Element / Selector / Array)"]
        CSS["Computed Styles / External Stylesheets"]
        Options["Export Options (dimensions, scale, fonts, etc.)"]
    end

    subgraph CoreEngine ["Core Engine (src/index.js)"]
        exportToPptx["exportToPptx() Entry Point"]
        WeakCache["_textContainerCache (WeakMap)"]
        processSlide["processSlide() Traversal Engine"]
        prepareRenderItem["prepareRenderItem() Item Factory"]
        RenderQueue["RenderQueue (Synchronous & Async Tasks)"]
        PptxGenJS["PptxGenJS Pres & Slide Instance"]
    end

    subgraph AnalysisHelpers ["Analysis & Layout (src/utils.js)"]
        isTextContainer["isTextContainer() / isTextContainerCached()"]
        collectTextParts["collectTextParts() Rich Text Parser"]
        getPadding["getPadding(), createShapeMargin() & createTableCellMargin()"]
        parseColor["parseColor() RGB/Alpha Engine"]
        FontDetection["getFontsFromStyleSheets(), parseFontFacesFromCssText(), resolveCssUrl() & parseImportUrlsFromCssText()"]
        SpeakerNotes["extractSpeakerNotesFromElement()"]
    end

    subgraph VectorShapeEngine ["Vector & Shape Processing"]
        SVGGen["generateCustomShapeSVG()"]
        BorderGen["generateCompositeBorderSVG()"]
        CanvasCapture["capturePseudoElementCanvas()"]
    end

    subgraph FontPipeline ["Font Embedding Pipeline (src/font-embedder.js)"]
        AutoDetect["getAutoDetectedFonts()"]
        FontVariant["classifyFontVariant() & detectVariantSlotCollisions()"]
        WasmConverter["fontToEot() via Wasm / opentype.js"]
        ZipFontInjector["PPTXEmbedFonts (ppt/fonts/, [Content_Types].xml)"]
    end

    subgraph NormalizationPipeline ["Post-Processing Normalizer (src/pptx-normalizer.js)"]
        JSZip["JSZip In-Memory Decompressor"]
        ZReorder["Shape Z-Index Sorter (Re-orders <p:sp>)"]
        AnimInject["<p:timing> Animation Tree Injector"]
        TransInject["Slide Transition Injector"]
        ContentTypeScrubber["Dangling <Override> Scrubber"]
    end

    subgraph Outputs ["Output Artifacts"]
        PPTXBlob["PPTX Blob / Buffer (Deflated ZIP Archive)"]
        FileDownload["Browser Triggered Download / CLI Written File"]
    end

    HTML --> exportToPptx
    CSS --> exportToPptx
    Options --> exportToPptx

    exportToPptx --> WeakCache
    exportToPptx --> processSlide
    processSlide --> prepareRenderItem

    prepareRenderItem --> isTextContainer
    prepareRenderItem --> collectTextParts
    prepareRenderItem --> getPadding
    prepareRenderItem --> parseColor
    prepareRenderItem --> SpeakerNotes

    prepareRenderItem --> SVGGen
    prepareRenderItem --> BorderGen
    prepareRenderItem --> CanvasCapture

    prepareRenderItem --> RenderQueue
    RenderQueue --> PptxGenJS

    exportToPptx --> AutoDetect
    AutoDetect --> FontDetection
    FontDetection --> FontVariant
    FontVariant --> WasmConverter
    WasmConverter --> ZipFontInjector

    PptxGenJS --> JSZip
    ZipFontInjector --> JSZip
    JSZip --> NormalizationPipeline
    NormalizationPipeline --> ZReorder
    NormalizationPipeline --> AnimInject
    NormalizationPipeline --> TransInject
    NormalizationPipeline --> ContentTypeScrubber

    NormalizationPipeline --> PPTXBlob
    PPTXBlob --> FileDownload
```

---

## 2. Component Responsibility Matrix

| Component | Primary File | Input | Output | Upstream Dependencies | Downstream Dependents |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Orchestrator** | `src/index.js` | DOM Root(s), `options` | PPTX Blob / Buffer | `pptxgenjs`, `jszip` | External Consumers, CLI |
| **DOM Classifier** | `src/utils.js` | Element, ComputedStyle | Boolean, Insets, TextParts | DOM CSSOM | `prepareRenderItem`, `collect` |
| **Shape Factory** | `src/index.js`, `src/utils.js` | Node, Dimensions, Borders | DrawingML Shape / SVG Data URL | `parseColor`, `getPadding` | `PptxGenJS.Slide.addShape` |
| **Font Detector** | `src/utils.js` | `usedFamilies`, CSSOM | Array of Font Variant Objects | `document.styleSheets`, `fetch` | `font-embedder.js` |
| **Font Transcoder** | `src/font-embedder.js` | TTF/OTF/WOFF Buffers | EOT Data, OpenXML Part XML | `opentype.js`, Wasm converter | `JSZip` archive |
| **Normalizer** | `src/pptx-normalizer.js` | JSZip instance, Slide Metadata | Patched OpenXML Archive | `DOMParser`, `XMLSerializer` | Final PPTX Serialization |
| **Headless CLI** | `src/node-exporter.js` | URL / HTML File, CLI flags | `.pptx` File on Disk | `puppeteer`, Chromium/Edge | CLI Users, Automated CI |

---

## 3. Data Invariant & Execution Contracts

1. **State Isolation**: `exportToPptx` allocates an isolated `_textContainerCache: new WeakMap()` per invocation. No classification state leaks across runs or concurrent exports.
2. **Text Box Inset Array Contract**:
   - `pptxgenjs` text shape `margin`: `[lIns, rIns, bIns, tIns]` (in points).
   - `pptxgenjs` table cell `margin`: `[marT, marR, marB, marL]` (in points).
3. **Font Slot Constraint Contract**:
   - PowerPoint OOXML allows only 4 embedded font variations per family name: `regular`, `bold`, `italic`, `boldItalic`.
   - Any secondary bold weight (e.g. 700 and 900) will overwrite the slot unless split into distinct `font-family` aliases.
4. **DrawingML Sequence Contract**:
   - Inside `<a:pPr>`, elements must follow strict schema order (`lnSpc` -> `spcBef` -> `spcAft` -> `buClr` -> `defRPr`). Out-of-order injection triggers OpenXML corruption repair alerts.
