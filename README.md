# From Procedural to SOLID

Beckhoff TwinCAT 3 workshop — *From Procedural to SOLID: Object-Oriented PLC Design in TwinCAT 3* (NEM 2026).

Students build the same 4-station filling line three ways (procedural → inheritance → composition) and apply the same three change requests at each stage to compare blast radius. The branches and the diffs between them are the workshop scoreboard.

## Where to start

- **Workshop docs** — `docs/getting-started.md` covers prerequisites, cloning, and running the docs site locally on Windows or Linux/macOS via `serve-docs.cmd` / `serve-docs.sh`. Browse the full site at <https://mark-code-cowboys.github.io/NEM_Workshop/>.
- **Repo conventions** — `CLAUDE.md` for project layout, branch map, library reference policy, and editing rules for `.TcPOU` / `.TcDUT` / `.TcGVL` files.
- **Workshop deck** — `presentation/` builds `NEM2026_workshop.pptx` from `presentation/build_deck.py` on top of the Beckhoff SPT template; see `presentation/README.md` for rebuild and theme notes.
