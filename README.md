# From Procedural to SOLID

Beckhoff TwinCAT 3 workshop — *From Procedural to SOLID: Object-Oriented PLC Design in TwinCAT 3* (NEM 2026).

Students build the same 4-station filling line three ways (procedural → inheritance → composition) and apply the same three change requests at each stage to compare blast radius. The branches and the diffs between them are the workshop scoreboard.

## Where to start

- **Workshop docs** — `docs/getting-started.md` covers prerequisites, cloning, and branch navigation. The published site lives at <https://beckhoff-usa-community.github.io/Procedural_To_SOLID/>; the *Run the docs site locally* section below covers the offline path.
- **Repo conventions** — `CLAUDE.md` for project layout, branch map, library reference policy, and editing rules for `.TcPOU` / `.TcDUT` / `.TcGVL` files.
- **Workshop deck** — `presentation/` builds `NEM2026_workshop.pptx` from `presentation/build_deck.py` on top of the Beckhoff SPT template; see `presentation/README.md` for rebuild and theme notes.

## Run the docs site locally

The repo ships launcher scripts that create a Python venv on first run, install MkDocs + Material + plugins, and serve the site at <http://localhost:8000/Procedural_To_SOLID/> with hot-reload on save.

**Linux / macOS:**
```sh
./serve-docs.sh                 # serve at http://localhost:8000
./serve-docs.sh build           # one-shot static build to ./site/
./serve-docs.sh --dev-addr 127.0.0.1:9000   # custom port
```

**Windows (cmd or PowerShell):**
```cmd
serve-docs.cmd
serve-docs.cmd build
```

**Manual setup** (if you'd rather drive `mkdocs` yourself):
```sh
python3 -m venv .venv-docs
source .venv-docs/bin/activate          # bash/zsh
# .venv-docs/bin/activate.fish          # fish
pip install -r requirements-docs.txt
mkdocs serve
```

Requires Python 3.9+ on `PATH`. The first run takes ~30 s while pip resolves dependencies; subsequent runs start in under a second.

## Credits

Workshop material © Beckhoff Automation LLC. The framework libraries used at each stage — **TwinCAT 3**, **SPT-Libraries** (`SPT Base Types`, `SPT Components`, `SPT Diagnostic`, `SPT Event Logger`, `SPT Utilities`), and the internal Beckhoff USA **Core** / **CoreComponents** libraries that the SPT layer is built on top of — are © Beckhoff Automation. The SPT design conventions used in `FillingLine_Inheritance` follow the public Beckhoff USA Community style guide at <https://beckhoff-usa-community.github.io/SPT-Libraries/>.
