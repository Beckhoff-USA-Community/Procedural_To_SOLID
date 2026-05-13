# From Procedural to SOLID

Beckhoff TwinCAT 3 workshop — *From Procedural to SOLID: Object-Oriented PLC Design in TwinCAT 3* (NEM 2026).

See `CLAUDE.md` for project layout, branch map, and editing conventions.

## Serving the documentation locally

The docs source (`mkdocs.yml`, `docs/`) lives on `main`. The published HTML lives on the `gh-pages` branch (built by `mkdocs gh-deploy`). Pick whichever fits:

### Option 1 — preview the built site (any branch)

Use a worktree so your current branch stays put:

```bash
git worktree add /tmp/nem-docs-site gh-pages
python3 -m http.server 8000 --directory /tmp/nem-docs-site
# browse http://localhost:8000/
```

Cleanup:

```bash
kill $(lsof -ti:8000)
git worktree remove /tmp/nem-docs-site
```

### Option 2 — live-reload dev server (from `main`)

```bash
git switch main
source .venv-docs/bin/activate   # or: python3 -m venv .venv-docs && pip install mkdocs-material
mkdocs serve                     # http://127.0.0.1:8000/ with live reload
```
