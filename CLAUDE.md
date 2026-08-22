# Macro Ledger

A single-page macro tracker. Static site, no build tooling beyond
one Python script, no dependencies, no framework.

Live: https://riongai.github.io/macro-ledger/

## Which file to edit

**`macro-ledger.html` is the source of truth. Edit that one.**

`index.html` is generated output — it is `macro-ledger.html` wrapped in a
`<head>`. Editing it directly works until the next build silently discards your
change. It carries a DO-NOT-EDIT banner at the top for this reason.

| File | Role |
|---|---|
| `macro-ledger.html` | **Source. All app changes go here.** |
| `build.py` | Wraps the source into `index.html` |
| `index.html` | Generated. Deployed. Do not edit |
| `sw.js` | Service worker. Bump `CACHE` on every deploy |
| `manifest.webmanifest` | PWA manifest |
| `icon-*.png` | Home-screen icons |
| `make-icons.py` | Regenerates the icons (pure stdlib, no Pillow) |
| `add-sugar.py` | One-off tool that added sugar to every food row. Kept as the record of how those values were derived |

## Deploy

```bash
python3 build.py
# bump CACHE in sw.js: macro-ledger-v4 -> v5
git add -A && git commit -m "..." && git push
```

GitHub Pages redeploys automatically, usually inside two minutes.

**Bumping `CACHE` is not optional.** The service worker is cache-first, so
phones with the app installed keep serving the old copy until the cache name
changes. Skip it and the deploy appears to do nothing.

Check the deploy:

```bash
gh api repos/riongai/macro-ledger/pages/builds/latest --jq '{status,error:.error.message}'
```

`gh` is at `~/.local/bin/gh`, which is in `.zshrc` but not on the PATH of
non-interactive shells — prefix with `export PATH="$HOME/.local/bin:$PATH"`.

## How the app is structured

One file, three sections: `<style>`, then markup, then `<script>`. Inside the
script:

- `FOODS` — 645 rows, `[name, unit, basis, kcal, protein, carbs, fat, sugar, cuisine]`.
  `basis` is the amount the numbers describe: `100` for per-100g ingredients,
  `1` with unit `"ea"` for a whole serve. `LIB` maps these to objects.
- `targets(dayKey)` — Mifflin-St Jeor BMR × activity, adjusted for goal.
  Protein and fat are set per kg bodyweight; carbs take the remainder; the
  sugar cap is 10% of calories. If `dayKey` is marked drinking, fat switches to
  `profile.drinkFat` and `profile.drinkKcal` is reserved before carbs take what
  is left — the calorie ceiling does not move, only the split beneath it.
- `render()` — the single entry point. Every state change calls `save()` then
  `render()`. There is no framework and no virtual DOM; render functions
  rewrite their own `innerHTML`.
- State lives in `S`, persisted to `localStorage` under `macroLedger.v1`.
- `dayType[dateKey]` — `"drinking"`, or absent for dry. Dry is the absence of a
  mark rather than a stored value, so existing data needs no migration.
- `PREGNANCY` — additional kcal and protein per trimester, FAO/WHO/UNU 2004
  (+85 / +285 / +475 kcal, +1 / +10 / +31 g protein). When `profile.pregnant`
  is set, `targets()` adds `pregKcal` and `pregProt` and clamps the goal at
  maintenance. Both increments are editable so a clinician's figure wins.

## Conventions that matter

- **No personal data in the source.** Profile defaults are neutral placeholders
  (75 kg / 175 cm / 30) with a `configured: false` flag; the first-run prompt
  collects the real values, which stay in the browser. The repo is public —
  keep it that way.
- **Self-contained.** No CDN, no external fonts, no network calls at runtime.
  The service worker caches everything, so the app must work offline.
- **Theme-aware.** Three states: `:root` light tokens, a
  `prefers-color-scheme: dark` block guarded with `:not([data-theme="light"])`,
  and a `[data-theme="dark"]` block. Never define a colour only inside one of
  them.
- **Estimates are labelled as estimates.** Franchise and composite-dish figures
  are derived, not published, and the app says so where they are used. Do not
  quietly present a derived number as sourced.
- **Sugar never exceeds carbohydrate.** Enforced in `addEntry` and in the
  manual-entry form. Preserve that invariant.
- **No weight-loss preset while pregnant.** `targets()` clamps the goal to
  maintenance rather than rewriting `profile.goal`, so unticking the box
  restores whatever the user had. Restriction in pregnancy is a clinical
  decision; the app must not offer it as a preset.
- **Verify with `read_console_messages` on a fresh load.** A listener attached
  from inside a test script runs after load and misses load-time errors — a
  dangling call once shipped that broke the whole app, and an in-page listener
  reported no errors.
- **Alcohol is reserved, not logged, by the day-type toggle.** Ethanol is
  7.1 kcal/g and is no macro at all, so its calories belong to none of the three
  bars. The drinking preset holds them back before carbs take the remainder; the
  drink itself is still logged as an ordinary entry. Reserving *and* omitting the
  entry would understate the day; logging without reserving leaves a carb target
  that cannot be reached.

## Testing

There is no test suite. Verify in a browser against a real HTTP origin —
`file://` blocks both `localStorage` and service workers, so it will report
false failures.

```bash
python3 -m http.server 8731 --directory .
```

Then check: the food count is 645, all five gauges render, storage reports
"Working" in *Backup & data*, and a logged entry survives a reload.
