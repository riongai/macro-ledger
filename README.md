# Macro Ledger

Daily macro and training tracker. One HTML file, no dependencies, works offline,
installs to the iOS home screen.

**Live: https://riongai.github.io/macro-ledger/**

- 645-food library weighted to Malaysian and wider Asian cooking, plus franchise
  menus, with calories, protein, carbs, fat and sugar
- 56 exercises with MET-based burn, custom entries and circuits
- Targets from Mifflin-St Jeor BMR, adjusted for activity and goal
- Everything stored in your own browser — nothing is sent anywhere

## Working on it

Edit **`macro-ledger.html`**, then:

```bash
python3 build.py
```

`index.html` is generated — don't edit it. Bump `CACHE` in `sw.js` before
pushing, or installed phones keep serving the cached copy.

See [CLAUDE.md](CLAUDE.md) for the full layout and conventions.

## Nutrition data

Whole foods use published composition data. Restaurant and franchise dishes are
estimates derived from their components, because those chains do not publish
full macros — the app says so wherever those figures appear. Treat them as ±15%
and overwrite any you can check against a label.

Not medical advice.
