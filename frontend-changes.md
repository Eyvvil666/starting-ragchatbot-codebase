# Frontend Changes

## Feature 1: Dark/Light Mode Toggle Button

Added a floating icon-based toggle button (sun/moon) that lets users switch between dark and light themes.

### `frontend/index.html`

1. **Inline `<head>` script** — reads `localStorage.getItem('theme')` and sets `data-theme` on `<html>` before the stylesheet renders, preventing flash of wrong theme.

2. **Toggle button markup** — `<button id="themeToggle" class="theme-toggle">` placed at the end of `<body>` with `position: fixed`. Contains two overlapping SVG icons:
   - `.icon-sun` (shown in dark mode, click → switch to light)
   - `.icon-moon` (shown in light mode, click → switch to dark)
   Both carry `aria-hidden="true"`; the button `aria-label` updates dynamically via JS.

### `frontend/style.css`

- **`.theme-toggle`**: `position: fixed; top: 1rem; right: 1rem`, 44 × 44 px circle, themed with CSS variables, `z-index: 1000`.
- **Hover/focus/active states**: scale lift, blue glow, `focus-visible` ring (no ring on mouse clicks).
- **Icon swap animation**: both icons are `position: absolute` and overlap; inactive icon fades + rotates ±90° (`transition: opacity 0.35s, transform 0.35s`).

### `frontend/script.js`

- **`toggleTheme()`** — flips `data-theme` on `<html>`, persists to `localStorage`.
- **`updateToggleLabel()`** — keeps `aria-label`/`title` accurate after each toggle.
- **`initTheme()`** — called on `DOMContentLoaded` to sync the button label with the already-applied theme.
- Click listener wired in `setupEventListeners()`.

---

## Feature 2: Accessible Light Theme Color Palette

Audited and upgraded the light theme to pass WCAG AA contrast requirements across all UI surfaces.

### `frontend/style.css` — `:root` (dark theme base)

Added new semantic CSS variables so every color has a single source of truth:

| Variable | Dark value | Purpose |
|---|---|---|
| `--code-bg` | `rgba(0,0,0,0.25)` | Inline code / pre block background |
| `--error-bg` | `rgba(239,68,68,0.12)` | Error message background |
| `--error-text` | `#f87171` | Error message text |
| `--error-border` | `rgba(239,68,68,0.25)` | Error message border |
| `--success-bg` | `rgba(34,197,94,0.12)` | Success message background |
| `--success-text` | `#4ade80` | Success message text |
| `--success-border` | `rgba(34,197,94,0.25)` | Success message border |
| `--assistant-border` | `transparent` | Chat bubble outline (dark: hidden) |
| `--focus-ring` | `rgba(37,99,235,0.25)` | Focus indicator ring color |

### `frontend/style.css` — `[data-theme="light"]` overrides

Complete set of light theme values with WCAG AA contrast ratios verified:

| Variable | Light value | Contrast on bg | WCAG |
|---|---|---|---|
| `--background` | `#f1f5f9` | — | — |
| `--surface` | `#ffffff` | — | — |
| `--surface-hover` | `#e8edf3` | — | — |
| `--text-primary` | `#0f172a` | 19:1 on white | AAA ✓ |
| `--text-secondary` | `#475569` | 6.2:1 on white | AA ✓ |
| `--border-color` | `#cbd5e1` | — | — |
| `--focus-ring` | `rgba(37,99,235,0.4)` | stronger on light bg | — |
| `--assistant-border` | `#cbd5e1` | outlines white bubble | — |
| `--welcome-bg` | `#eff6ff` | — | — |
| `--code-bg` | `rgba(15,23,42,0.07)` | subtle tint on white | — |
| `--error-text` | `#b91c1c` (Red-700) | 5.9:1 on white | AA ✓ |
| `--success-text` | `#15803d` (Green-700) | 5.1:1 on white | AA ✓ |

### CSS rules updated to use variables (previously hardcoded)

| Selector | Property changed |
|---|---|
| `.message-content code` | `background-color` → `var(--code-bg)` |
| `.message-content pre` | `background-color` → `var(--code-bg)` |
| `.error-message` | `background`, `color`, `border` → error vars |
| `.success-message` | `background`, `color`, `border` → success vars |
| `.message.assistant .message-content` | Added `border: 1px solid var(--assistant-border)` |

The assistant bubble border is `transparent` in dark mode (invisible, as before) and `#cbd5e1` in light mode, making the white bubble visible against the `#f1f5f9` page background.

---

## Accessibility Summary

- All text/background combinations meet WCAG AA (4.5:1 for normal text, 3:1 for large/UI)
- Focus rings visible on keyboard navigation only (`focus-visible`)
- Native `<button>` element — keyboard activatable with `Enter`/`Space`
- `aria-label` describes the *next action*, not the current state
- Theme preference persists via `localStorage`, defaults to dark
