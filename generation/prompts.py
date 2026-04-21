"""
Prompt templates for web generation tasks.
"""

TEXT_TO_WEB_PROMPT = '''You are a highly skilled professional front-end engineer.

Your task: Based on the web design document below, generate a complete runnable web project repository.

Hard output contract (MUST follow):
1) Your entire response MUST be pure Markdown text.
2) ABSOLUTELY NO explanations, no extra commentary, no preface, no trailing notes.
3) Every file MUST be emitted using the following format:

# path/to/file.ext
```ext
<full file content>
```

4) The heading line MUST start with '# ' followed by the file path (relative path).
5) The code fence language MUST match the file type when possible (html/css/js/json/md/txt).
6) Include all necessary files (HTML, CSS, JS, etc.) so the project can run.
7) Do NOT nest triple backticks inside code blocks.
8) Use HTML, CSS, and JavaScript only. No frameworks or build tools required.

Few-shot examples:

# index.html
```html
<!doctype html>
<html>
    <head>
        <meta charset="utf-8" />
        <title>Demo</title>
        <link rel="stylesheet" href="styles.css" />
    </head>
    <body>
        Hello
        <script type="module" src="main.js"></script>
    </body>
</html>
```

# styles.css
```css
body {{ font-family: system-ui; }}
```

# main.js
```js
console.log('ok')
```

Web design document:
---
{document}
---
'''


IMAGE_TO_WEB_PROMPT = '''You are a highly skilled professional front-end engineer.

Your task: Based on the web design document and the reference screenshots provided, generate a complete runnable web project repository.
The screenshots represent the target UI and function. The generated site should match the screenshots as closely as possible.

Hard output contract (MUST follow):
1) Your entire response MUST be pure Markdown text.
2) ABSOLUTELY NO explanations, no extra commentary, no preface, no trailing notes.
3) Every file MUST be emitted using the following format:

# path/to/file.ext
```ext
<full file content>
```

4) The heading line MUST start with '# ' followed by the file path (relative path).
5) The code fence language MUST match the file type when possible (html/css/js/json/md/txt).
6) Include all necessary files (HTML, CSS, JS, etc.) so the project can run.
7) Do NOT nest triple backticks inside code blocks.

Startup requirements:
- MUST include a README.md with the simplest way to run locally.
- MUST be runnable via a static server (no backend). Prefer Vite or plain static files.

Web design document:
---
{document}
---
'''


VIDEO_TO_WEB_PROMPT = """You are a world-class front-end engineer with expertise in creating pixel-perfect web reproductions. Your task is to analyze these video frames and create a complete, production-ready web project repository that exactly replicates the demonstrated interface with professional-grade quality.

🎯 MISSION: Create a flawless HTML reproduction that matches the video demonstration in every detail, achieving 95%+ quality score.

📋 COMPREHENSIVE ANALYSIS PROTOCOL:

1. TEMPORAL SEQUENCE ANALYSIS:
   - Study frame progression to understand user interactions
   - Identify animation sequences, timing, and easing patterns
   - Map state transitions and user feedback mechanisms
   - Recognize loading states, hover effects, and micro-interactions
   - Document exact timing and duration of animations

2. VISUAL DESIGN EXTRACTION:
   - Extract precise color values (prefer hex codes: #RRGGBB)
   - Identify typography: font families, sizes, weights, line heights, letter-spacing
   - Measure spacing: margins, padding, gaps between elements (use rem/em units)
   - Analyze shadows: box-shadow values, blur radius, spread, inset shadows
   - Document border radius, opacity levels, and gradient effects
   - Note z-index layering and stacking contexts
   - Capture exact dimensions and proportions

3. LAYOUT & STRUCTURE ANALYSIS:
   - Identify layout systems: Flexbox, CSS Grid, or positioning
   - Map responsive breakpoints and mobile adaptations
   - Document component hierarchy and nesting structure
   - Analyze alignment, distribution, and spacing patterns
   - Ensure proper semantic HTML structure

4. INTERACTION PATTERN RECOGNITION:
   - Button states: normal, hover, active, focus, disabled
   - Animation triggers: click, hover, scroll, load events
   - State management: data flow and component updates
   - User feedback: visual confirmations and error states
   - Keyboard navigation patterns

🛠️ TECHNICAL IMPLEMENTATION REQUIREMENTS:

HTML5 STRUCTURE (MANDATORY):
- Use semantic HTML5 elements (main, section, article, nav, header, footer)
- Include proper meta tags: charset, viewport, description, keywords
- Implement accessibility features: ARIA labels, alt text, focus management, role attributes
- Optimize for SEO and performance
- Ensure valid HTML5 markup

CSS IMPLEMENTATION (MANDATORY):
- Use CSS custom properties (--variables) for maintainability and theming
- Implement modern layout: Flexbox and CSS Grid
- Create smooth animations with proper easing functions (cubic-bezier)
- Use transform3d for hardware acceleration
- Implement responsive design with mobile-first approach (@media queries)
- Ensure cross-browser compatibility (Chrome, Firefox, Safari, Edge)
- Optimize for performance: avoid layout thrashing, use will-change property
- Include CSS reset/normalize for consistency
- Use modern CSS features: clamp(), min(), max(), calc()

JAVASCRIPT FUNCTIONALITY (MANDATORY):
- Write modern ES6+ JavaScript with proper error handling (try/catch)
- Implement event-driven architecture with clean separation of concerns
- Use requestAnimationFrame for smooth animations
- Implement proper state management for complex interactions
- Add performance optimizations: debouncing, throttling
- Ensure accessibility: keyboard navigation, screen reader support
- Use modern JavaScript features: arrow functions, destructuring, async/await
- Implement proper event delegation and cleanup

🎨 ANIMATION & INTERACTION STANDARDS (MANDATORY):
- Use CSS transforms for performance (translate3d, scale, rotate)
- Implement 60fps smooth animations with proper timing functions
- Add appropriate transition durations (typically 200-500ms)
- Create natural easing curves: ease-out for entrances, ease-in for exits
- Implement hover states with subtle feedback (scale, color, shadow changes)
- Add loading states and skeleton screens where appropriate
- Use CSS animations for complex sequences
- Implement proper animation cleanup and performance monitoring

🔍 QUALITY ASSURANCE CHECKLIST (MANDATORY - MUST ACHIEVE 95%+):
✓ Pixel-perfect visual reproduction (colors, spacing, typography)
✓ Smooth, professional animations matching video timing
✓ Responsive design working on all screen sizes (mobile, tablet, desktop)
✓ Accessible keyboard navigation and screen reader support (ARIA, roles, alt text)
✓ Cross-browser compatibility (modern browsers)
✓ Performance optimized (fast loading, smooth interactions, will-change, transform3d)
✓ Clean, maintainable, well-structured code with proper comments
✓ No console errors or warnings
✓ Proper semantic HTML structure with semantic elements
✓ SEO-friendly implementation with meta tags and structured data

📤 OUTPUT SPECIFICATIONS (CRITICAL):
- Your entire response MUST be pure Markdown text.
- ABSOLUTELY NO explanations, no extra commentary, no preface, no trailing notes.
- Every file MUST be emitted using the following format:

# path/to/file.ext
```ext
<full file content>
```

- The heading line MUST start with '# ' followed by the file path (relative path).
- The code fence language MUST match the file type when possible (html/css/js/json/md/txt).
- Include all necessary files (HTML, CSS, JS, etc.) so the project can run.
- Do NOT nest triple backticks inside code blocks.
- Keep assets inline or generate all files needed; avoid external dependencies.

🎖️ SUCCESS CRITERIA (TARGET: 95%+ QUALITY SCORE):
- Visual output is indistinguishable from the video demonstration
- All animations and interactions work smoothly and naturally
- Code quality meets professional development standards
- Performance is optimized for real-world usage
- Accessibility standards are met or exceeded (WCAG 2.1 AA)
- Responsive design works flawlessly across all devices
- Code is maintainable and well-documented
- No errors or warnings in browser console
- Semantic HTML structure is properly implemented
- Modern CSS and JavaScript best practices are followed

Begin your comprehensive analysis and create the ultimate HTML reproduction that achieves 95%+ quality score:"""
