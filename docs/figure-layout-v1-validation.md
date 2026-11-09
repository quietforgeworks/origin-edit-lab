# Figure Layout V1 source sync validation

Validated on macOS on 2026-11-09 in an isolated checkout. The installed skill was not modified.

- The 123-file installed V1 source manifest matches all copied source bytes.
- Six skill Python suites: 354 tests discovered. Optimized mode passed 353 with one expected Inkscape-dependent skip; normal mode initially skipped two Node-dependent tests as well, which passed with Node on PATH in optimized mode.
- Node interaction suites: 17 tests passed.
- No binary research inputs, private figures, session state, fonts or credentials were added.
- Repository-wide run_tests.py was attempted but stopped in the unchanged native atomic-output suite: its no-overwrite publication implementation is intentionally Linux-only. This is not a full repository pass on macOS.
- Origin/PowerPoint native reopen, visual quality for a real figure and end-to-end application lifecycle remain unvalidated by these synthetic tests.
- V1 is a source synchronization, not a new binary release or a universal Origin writer.
