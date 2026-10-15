# PhishForge Console — Design Direction

## Point of view

A calm, dense, confident security/ML-evaluation console — closer to a SOC dashboard or an eval
harness than a generic "AI app." The hero moments are the live pipeline stepper and the
convergence chart; everything else stays quiet on purpose. Deliberately avoids: warm
cream+serif, near-black+neon-accent, identical rounded SaaS cards with a uniform drop shadow,
tracked-out ALL-CAPS eyebrows, middle-dot metadata strings, `→` on buttons.

## Color

Design tokens live in `web/src/styles/tokens.css` as CSS custom properties, consumed identically
by Tailwind utility classes (`style={{ color: 'var(--color-...)' }}`) and by Recharts (axis,
grid, and series colors all reference the same variables), so light/dark stay coherent
everywhere including inside charts.

**Core palette** (named, light → dark):

| Role | Light | Dark | Used for |
|---|---|---|---|
| Page plane | `#F2F4F7` | `#0E1420` | app background — cool slate, not warm cream, not flat black |
| Surface | `#FFFFFF` | `#161D2B` | cards, panels |
| Primary ink | `#121A24` | `#EDEFF3` | body text |
| Secondary ink | `#4B5563` | `#A7AFBD` | supporting text |
| Muted | `#8A94A3` | `#6B7585` | axis labels, hints |
| Signal (brand accent) | `#3E5FD9` | `#5B7CF0` | buttons, links, active nav, focus ring, default chart line — deliberately not reused by any status color |
| Forge (decorative only) | `#B8702E` | `#D98A4A` | the second series color in two-condition charts, About diagram accents — never interactive/semantic |

**Status palette** (fixed, colorblind-safe, validated with the dataviz skill's
`scripts/validate_palette.js`): `PASS` (green `#0ca30c`), `REVISE` (amber `#fab219`), `FAIL`
(coral `#ec835a`), `REJECTED_UNSAFE` (red `#d03b3b`), `FAILED_TO_CONVERGE` (violet `#9B4FC9` /
`#b47adf` dark), `GENERATION_FAILURE` (teal `#0892A8` / `#2fb0c7` dark). The four PASS/REVISE/
FAIL/REJECTED_UNSAFE steps are the dataviz skill's own reference `good/warning/serious/critical`
set, reassigned to match PhishForge's semantics (REJECTED_UNSAFE = `critical`, since a safety
violation is the single most severe outcome). The two added hues (violet, teal) were chosen and
validated specifically so they introduce **no new failing pairs** beyond what the reference
4-color set already accepts by design (red vs. green and amber vs. orange both sit in the
6–8 ΔE "legal only with secondary encoding" band in the upstream reference too — mitigated the
same way here: every status rendering is icon + label + color together, in `StateBadge.tsx`,
never color alone).

## Type

**IBM Plex Sans** (UI text and headings — one weight scale, no separate display face) + **IBM
Plex Mono** (run IDs, timestamps, Q scores, the raw-JSON toggle — anything tabular or
identifier-like), loaded from Google Fonts in `index.html`. A technical, slightly engineered
character that fits an evaluation console without defaulting to Inter or a cliché serif+cream
pairing.

## Layout

Left-rail navigation (Studio / Runs / Dashboard / Settings & About) + content area, collapsing to
a horizontal top bar below `lg`. Studio is two-column on desktop (scenario builder on the left,
the live run view as the hero on the right); stacks on tablet. Dashboard is a KPI-row-then-
chart-grid layout. Text is left-aligned throughout — this is a working tool, not a landing page.
8px spacing scale (`--space-1` … `--space-8`).

## Motion

Purposeful only, all gated behind `prefers-reduced-motion` (global CSS rule in `tokens.css`):
pipeline-stepper stage dots transition color/icon on state change; the convergence chart's line
and points use Recharts' built-in draw-in animation; score bars animate width on data change;
panel reveals are a plain conditional render (no scroll-triggered fade-ins scattered everywhere).

## Data visualization

Every chart (`ConvergenceView`, Dashboard's terminal-state/leakage/quality/histogram charts) is
Recharts themed entirely off the same CSS variables — no separate Recharts-only palette.

- **Convergence chart**: Signal-blue line, Q on 0–100, dashed reference lines at the real
  `pass_threshold`/`revise_threshold` read from `/api/config` (never hardcoded 80/60), each point
  tooltipped, a single-point run shown as "converged on first attempt," a `REJECTED_UNSAFE` run
  shown as an explicit "no score — the gate stopped this run before scoring" state rather than an
  empty chart.
- **Dimension breakdown**: small multiples (one card per iteration) rather than one cluttered
  grouped bar, with per-dimension delta labels (e.g. "+34") echoing the paper's own worked-example
  framing.
- **Two-condition charts** (terminal-state distribution, quality-by-condition): Signal vs. Forge
  — a categorical pair encoding *condition identity*, intentionally not the status palette (status
  colors are reserved for state, never reused as "series 2").
- **Safety-leakage chart**: uses the rejected-unsafe red specifically, since it *is* charting a
  safety-violation rate, with an explicit "descriptive only, N=…" caption per the paper's own
  stance on inference from small N.

## The "SIMULATION" treatment

`EmailCard.tsx` renders a persistent amber ribbon ("SIMULATION — training content only. Not a
real email.") above every generated email preview, using the REVISE status color (not a
one-off color) so it reads as part of the same system rather than a bolted-on warning banner.
Sender and any links/domains are always plain text — no `<a>`, no `dangerouslySetInnerHTML` —
enforced by construction, not by a lint rule.

## Accessibility

Visible focus ring (`:focus-visible` in `index.css`), semantic landmarks (`<nav>`, `<main>`,
skip-to-content link), `role="img"` + descriptive `aria-label` on the convergence chart, every
status rendering pairs an icon with its label text (never color alone), form fields use real
`<label>` elements, the pipeline stepper is a `role="group"` with per-stage `aria-label`s.
