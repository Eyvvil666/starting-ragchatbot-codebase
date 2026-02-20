# Frontend Quality Tool Changes

## Overview

Added code quality tooling to the frontend to enforce consistent formatting and catch common JavaScript issues automatically.

## New Files Added

### `frontend/package.json`
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

### `frontend/.prettierrc`
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

### `frontend/.eslintrc.json`
ESLint configuration for a vanilla JS browser environment:
- **env**: `browser: true`, `es6: true`
- **globals**: `marked` (readonly — loaded from CDN)
- **rules**:
  - `no-unused-vars` — warn
  - `no-console` — warn
  - `eqeqeq` — error (enforce `===`)
  - `no-undef` — error
  - `prefer-const` — warn
  - `no-var` — error

### `frontend/.prettierignore`
Excludes `node_modules/` from formatting.

## Files Reformatted

All three frontend source files were reformatted to match Prettier's output (2-space indentation, single quotes in JS, consistent spacing):

### `frontend/script.js`
- 4-space → 2-space indentation throughout
- Double quotes → single quotes for all string literals
- Trailing commas added in multi-line object/array literals (`es5` style)
- Arrow function parameters wrapped in parentheses: `s =>` → `(s) =>`
- Template literal indentation aligned to 2-space style
- Removed debug `console.log` calls (would trigger ESLint `no-console` warnings)
- Long `addMessage(...)` call broken across multiple lines to stay within 80-char print width

### `frontend/index.html`
- 4-space → 2-space indentation throughout
- `DOCTYPE` lowercased to `<!doctype html>` (Prettier standard)
- Void elements self-closed (`<meta ... />`, `<link ... />`, `<input ... />`)
- Long `data-question` attributes placed on their own lines for readability
- SVG attributes line-wrapped to fit within 80-char print width

### `frontend/style.css`
- 4-space → 2-space indentation throughout
- Single-property shorthand selectors expanded: `h1 { font-size: 1.5rem; }` → multi-line block
- Comma-separated selectors (`.no-courses, .loading, .error`) split onto separate lines
- `@keyframes bounce` selector group `0%, 80%, 100%` kept on one line (Prettier default)
- Long `font-family` value broken across two lines to stay within print width

## How to Use

```bash
# Install dependencies (first time only)
cd frontend
npm install

# Format all files
npm run format

# Check formatting (no changes — for CI)
npm run format:check

# Lint JavaScript
npm run lint

# Run full quality check
npm run quality
```
