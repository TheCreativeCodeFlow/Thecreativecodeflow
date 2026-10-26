# Design System Tokens & Specification

## Visual Direction
**Style:** Premium Engineering Dashboard + Editorial Portfolio + Subtle Terminal Aesthetics  
**Repository:** `TheCreativeCodeFlow/Thecreativecodeflow`  
**Engineer:** Rahul Seervi

---

## 1. Color Palette Tokens

| Token Name | Hex Code | RGB | Role / Usage |
|---|---|---|---|
| **Midnight Navy** | `#061D30` | `rgb(6, 29, 48)` | Primary canvas & root background |
| **Deep Teal** | `#042F40` | `rgb(4, 47, 64)` | Secondary panel fills, card containers, inset modules |
| **Ocean Blue** | `#064663` | `rgb(6, 70, 99)` | Architectural lines, structural borders, active states |
| **Electric Teal** | `#00C9B7` | `rgb(0, 201, 183)` | Live status beacons, active telemetry, data flows |
| **Champagne Gold** | `#F0B45F` | `rgb(240, 180, 95)` | Milestone tags, credentials, featured highlights |
| **Soft White** | `#EAF2F5` | `rgb(234, 242, 245)` | Primary headings, prominent data metrics, high-contrast text |
| **Muted Slate** | `#8FA7B5` | `rgb(143, 167, 181)` | Secondary labels, node descriptions, metadata text |

### Auxiliary / Structural Accents
| Token Name | Hex Code | Role / Usage |
|---|---|---|
| Border Dark | `#0A354E` | Subtle inner borders between cards and panels |
| Grid Dot Accent | `#0B3854` | Faint coordinate grid pattern (16x16 / 20x20) |
| Dark Glow / Gradient Stop | `#021422` | Deep contrast gradient baseline |
| Highlight Wash | `rgba(0, 201, 183, 0.08)` | Electric Teal fill wash for selected cards |
| Gold Wash | `rgba(240, 180, 95, 0.12)` | Champagne Gold fill wash for milestone badges |

---

## 2. Typography Rules

### Font Families
- **Monospace Stack (Labels, Telemetry, Code, Subheadings):**  
  `ui-monospace, SFMono-Regular, "JetBrains Mono", Menlo, Consolas, "Liberation Mono", monospace`
- **Sans-Serif Stack (Headings, Display Titles, Hero):**  
  `-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif`

### Type Scale (SVG Standard Context)
| Level | Font Size | Weight | Line Height / Letter Spacing | Color |
|---|---|---|---|---|
| **Hero Title** | 26px - 32px | 700 / Bold | `letter-spacing: 1.5px` | `#EAF2F5` |
| **Section Header** | 12px - 14px | 700 / Bold | `letter-spacing: 2px; text-transform: uppercase` | `#00C9B7` |
| **Panel Title** | 11px - 12px | 700 / Bold | `letter-spacing: 1px` | `#EAF2F5` |
| **Metric Value** | 16px - 22px | 700 / 800 | `letter-spacing: 0.5px` | `#00C9B7` or `#F0B45F` |
| **Body / Description** | 9.5px - 10.5px | 400 / 500 | `letter-spacing: 0.2px` | `#8FA7B5` |
| **Monospace Tag / HUD** | 8px - 8.5px | 600 / 700 | `letter-spacing: 0.8px` | `#8FA7B5` / `#00C9B7` |

---

## 3. SVG Grid & Layout Dimensions

All primary SVG assets follow standard coordinate bounds optimized for responsive desktop and tablet rendering on GitHub:

- **Profile Hero (`assets/profile_hero.svg`):**
  - Dimensions: `viewBox="0 0 900 240"`, `width="100%"`, `height="auto"`
  - Layout: Left hero branding + engineering discipline, right HUD micro-metrics + architectural node topology.
- **System Architecture (`assets/system_architecture.svg`):**
  - Dimensions: `viewBox="0 0 900 300"`, `width="100%"`, `height="auto"`
  - Layout: 4 core horizontal runtime tiers (Client View -> Gateway API -> Distributed Daemons -> Persistence & AI) with explicit routing channels.
- **Scheduler Architecture (`assets/scheduler_architecture.svg`):**
  - Dimensions: `viewBox="0 0 900 260"`, `width="100%"`, `height="auto"`
  - Layout: Queue pipeline flow (Client Task Submission -> Scheduler Daemon & Partitioning -> State / Mutex Store -> Worker Cluster -> SSE Telemetry Stream).
- **Technology Stack (`assets/technology_stack.svg`):**
  - Dimensions: `viewBox="0 0 900 320"`, `width="100%"`, `height="auto"`
  - Layout: 6 organized domain clusters (Languages, Frontend, Backend & APIs, Distributed Systems, Data & AI, Infrastructure & Tooling).
- **System Diagnostics / Telemetry (`assets/system_diagnostics.svg` & `assets/github_telemetry.svg`):**
  - Dimensions: `viewBox="0 0 900 240"`, `width="100%"`, `height="auto"`
  - Layout: 3 coordinated columns (System Metrics, Active Streaks & Telemetry, Language Distribution).
- **Profile Footer (`assets/profile_footer.svg`):**
  - Dimensions: `viewBox="0 0 900 70"`, `width="100%"`, `height="auto"`
  - Layout: Minimal horizontal engineering signature with coordinate badges and subtle borders.

---

## 4. Visual Conventions & Constraints

1. **No High-Saturation Neon:** Replace fluorescent lime and cyan with calibrated `#00C9B7` (Electric Teal) and `#064663` (Ocean Blue).
2. **Strict Contrast:** Backgrounds must be `#061D30` with `#042F40` container panels. Secondary text `#8FA7B5` meets WCAG AA contrast against both panel and background tones.
3. **Restrained Animation:** Subtle pulse/fade indicators only on live status beacons (`dur="2s"`, `opacity="0.4;1;0.4"`). No intrusive bouncing or flashy effects.
4. **Clean Borders:** All container panels use `stroke="#064663"` with `stroke-width="1"` or `1.5` and `rx="6"` to `rx="8"` border radius.
5. **Precision Dividers:** Thin lines (`stroke="#064663"`, `opacity="0.6"`) between data rows and columns.
