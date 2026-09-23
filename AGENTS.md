# Octypst working notes

- In the Octypst source repository, the canonical remote is `github.com/gvrooyen/octypst`; it may also have an Amp remote. Check both branches before pushing changes to that repository.
- In the source repository, use `make check` for both branded sample PDFs and the table alignment regression. `bin/new-report <destination>` creates a standalone copy; compile its `report.typ` as well when changing generation or template paths. In a generated project, compile `report.typ` directly.
- The live preview is declared in `.amp/services.yaml`. Run `amp orb services ensure` from the project root and use its printed portal URL. Do not run the watcher as an unsupervised background process. In the Octypst source repository it defaults to `sample_report.typ`; in a generated project it defaults to `report.typ`. Set `OCTYPST_PREVIEW_SOURCE` in the service environment or pass `--source` in the service command to switch reports; restart the service after changing its configuration.
- The viewer renders PNG pages and preserves its scroll position on successful rebuilds. **Open PDF** serves the separately compiled, selectable PDF. Inspect representative rendered pages (cover, body, and affected non-default states such as wrapped tables) after visual changes, not just build output. Check `/api/version` and `amp orb service logs pdf-preview` when builds fail; the last good preview should remain visible.
- Generated PDFs and `.amp/preview/` and `.amp/portals/` are ignored. Keep source files and brand assets tracked; don't commit preview output.

## Report writing style

- Write for an intelligent non-technical reader in simple, clear, professional language. Prefer concrete facts, actions, and decisions to abstract consulting jargon.
- Use short, direct sentences. Explain technical terms when they are needed.
- Avoid pompous claims and stock AI-sounding contrasts such as “it is X, not Y”, “not just X but Y”, and “rather than X, Y”.
- Do not use em-dashes. Prefer punctuation or separate sentences; use an en-dash only when a dash is necessary.
- Keep British or South African spelling consistent where appropriate.
- In proposals, state deliverables, limits, fees, assumptions, and approval steps explicitly. Simplify language without changing commitments or presenting rough estimates as promises.
