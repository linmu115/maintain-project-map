# Archify native runtime

Source: https://github.com/tt-a1i/archify

Pinned commit: `d673e8300df60a5c8166abe78787fdc78f6b8000`

License: MIT, reproduced unchanged in [LICENSE](LICENSE). Additional bundled
third-party attribution is retained in [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
The JetBrains Mono font license is also retained in
[assets/JetBrainsMono-OFL.txt](assets/JetBrainsMono-OFL.txt) and inside the viewer.

## Included upstream code

This directory contains the original five typed diagram renderers, JSON schemas,
compiled validators and brand catalogue, standalone viewer, native CLI,
validation and atomic delivery pipeline, architecture comparison, workflow
schema migration, optional native live preview, command guidance, and JSON
examples. The inline viewer retains upstream Node Finder, focus and relationship
navigation, Semantic Passport, reachability, Route Probe, and export behavior.

`PIN.json` records every included original file, its upstream path, SHA-256, and
byte count. Files were copied from Git blobs at the pinned commit, preserving
original bytes without checkout line-ending conversion. `PIN.json` and this
attribution document are downstream packaging metadata.

No upstream SKILL instructions, update checker, updater workflow, development
generators, test suite, generated example HTML collection, or npm dependency
installation is included. Node.js 18 or newer is required. The bundled compiled
validators make ordinary rendering and validation independent of npm packages.

## Integration boundary

The host Skill adapts its reading pages around this runtime. Native diagram JSON
keeps the upstream schema and stable graph identities; project identity,
Markdown records, long-conversation sources, and record lifecycle management are
host capabilities. Upstream `lifecycle` means a state-machine diagram, and
`migrate` means workflow schema migration, not project-record retirement.

The downstream adapter may add a fixed light, low-saturation style and host
navigation to a separate embedded copy. Such a copy is distinct from the original
HTML and SHA-256 produced by native `deliver`. Licensing and original sources are
preserved here so that future updates can be reviewed file by file.

The generated copy also supports an opt-in camera extension: pointer-anchored
wheel zoom, blank-space panning, fit-to-window sizing and a wider zoom range.
Version-checked patches extend the existing Archify.view state, not a second
camera. The host reader separately gates input behind click-to-select; inactive
inline diagrams let the document scroll, and clicking outside deselects them.
Neither adaptation edits the original files enumerated in PIN.json.

The native preview command is optional and watches one explicit diagram JSON.
The host's A/B/C documentation service remains a separate integration capability.
Browser-based checks and optional brand URL capture require their own runtime
capabilities; their presence in this package is not evidence that they ran.
