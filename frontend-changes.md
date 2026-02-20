# Frontend Changes

## Quality Tooling

Added code quality tooling to enforce consistent formatting and catch common JavaScript issues automatically.

### New Files Added

#### `frontend/package.json`
Defines the frontend project and its dev tooling dependencies:
- **prettier** `^3.3.3` — automatic code formatter
- **eslint** `^8.57.0` — JavaScript linter

Includes four npm scripts:
| Script | Command | Purpose |
|---|---|---|
| `format` | `prettier --write "**/*.{js,css,html}"` | Format all frontend files in-place |
| `format:check` | `prettier --check "**/*.{js,css,html}"` | Verify formatting without changes (CI use) |
| `lint` | `eslint .` | Run ESLint on all JS files |
| `quality` | `npm run format:check && npm run lint` | Full quality gate (format + lint) |

#### `frontend/.prettierrc`
Prettier configuration:
```json
{
  "singleQuote": true,
  "semi": true,
  "tabWidth": 2,
  "printWidth": 80,
  "trailingComma": "es5"
}
```

#### `frontend/.eslintrc.json`
ESLint configuration for a vanilla JS browser environment:
- **env**: `browser: true`, `es6: true`
- **globals**: `marked` (readonly — loaded from CDN)
- **rules**: `no-unused-vars` (warn), `no-console` (warn), `eqeqeq` (error), `no-undef` (error), `prefer-const` (warn), `no-var` (error)

### How to Use

```bash
cd frontend && npm install  # first time only
npm run format              # format all files
npm run format:check        # check formatting (CI)
npm run lint                # lint JavaScript
npm run quality             # full quality check
```

---

## Feature: Dark/Light Mode Toggle

Added a floating icon-based toggle button (sun/moon) that lets users switch between dark and light themes.

### `frontend/index.html`

1. **Inline `<head>` script** — reads `localStorage.getItem('theme')` and sets `data-theme` on `<html>` before the stylesheet renders, preventing flash of wrong theme.
2. **Toggle button markup** — `<button id="themeToggle" class="theme-toggle">` placed at the end of `<body>` with `position: fixed`. Contains two overlapping SVG icons (`.icon-sun` / `.icon-moon`) with `aria-hidden="true"`; the button `aria-label` updates dynamically via JS.

### `frontend/style.css`

- **`:root`** — Added new semantic CSS variables: `--code-bg`, `--assistant-border`, `--error-bg/text/border`, `--success-bg/text/border`.
- **`[data-theme="light"]`** — Full light theme with WCAG AA contrast ratios verified.
- **`.theme-toggle`** — `position: fixed; top: 1rem; right: 1rem`, 44×44 px circle, hover/focus/active states, animated icon swap.

### `frontend/script.js`

- **`toggleTheme()`** — flips `data-theme` on `<html>`, persists to `localStorage`.
- **`initTheme()`** — called on `DOMContentLoaded` to sync button label with the already-applied theme.
- Click listener wired in `setupEventListeners()`.

### Accessibility

- All text/background combinations meet WCAG AA
- Focus rings visible on keyboard navigation only (`focus-visible`)
- `aria-label` describes the *next action*, not the current state
- Theme preference persists via `localStorage`, defaults to dark
