# Changelog

All notable changes to this project are documented in this file.

## [1.3.0] - 2026-08-18

### Fixed
- Hotkeys assigned via "Assign Hotkey..." were throwing a MEL
  `Line 2.30: Syntax error` when pressed. Maya's hotkey execution path runs
  the bound command through MEL regardless of `nameCommand`'s
  `sourceType="python"` setting, so a raw Python string got parsed as MEL
  and failed. Fixed by registering the command as MEL that explicitly calls
  into Python via `python("...")` -- the standard, reliable pattern for
  Python hotkeys in Maya. Existing assignments made with the old (broken)
  version need to be re-assigned once via the dialog to pick up the fix.

## [1.2.0] - 2026-08-18

### Added
- Right-click menu on the shelf button: **Assign Hotkey - Toggle Side** /
  **Assign Hotkey - Both Sides**. Opens a small dialog to pick modifiers
  and a key, and binds it directly via `nameCommand`/`hotkey` -- shows up
  in Maya's Hotkey Editor too, and warns before overwriting an existing
  binding on that combo.

## [1.1.0] - 2026-08-17

### Changed
- Installer hardened: retry-safe file copying (handles transient file locks
  on Windows), icon copied to both `userBitmapsDir` and `prefs/icons` for
  reliability across Maya versions, automatic shelf-tab creation if no
  shelf is found, and a non-blocking in-viewport install confirmation
  instead of a modal dialog.

## [1.0.0] - 2026-08-17

### Added
- Custom shelf icon (`mirrorIcon.png`), installed automatically to Maya's
  bitmaps folder by the installer.
- Python rewrite of the original `selectMirror.mel`.
- Namespace-aware side detection, including nested namespaces (referenced rigs).
- Side token detected anywhere in the control name (not just the first token).
- Built-in token pairs: `L/R`, `LT/RT`, `Lt/Rt`, `lt/rt`, `Left/Right`,
  `left/right`, `LEFT/RIGHT`.
- `select_mirror_toggle()` - collapses the current selection onto a single
  side (the opposite of the reference side), deduplicated. Fixes the
  original script's bug where the swap direction was computed once from
  the first selected item and applied to the whole selection.
- `select_mirror_both()` - selects the current controls plus their mirrored
  counterparts, regardless of which side(s) were originally selected.
- Compact UI (`selectMirrorUI.py`) with Toggle Side / Both Sides buttons and
  an optional single custom side-token pair (checkbox-gated), including a
  "Guess" button that reads the side token from the current selection.
  Custom token settings persist across Maya sessions via `optionVar`.
- Hotkey-safe wrapper functions (`hotkey_toggle`, `hotkey_both`) that respect
  the saved custom-token setting without requiring the UI to be open.
- Drag-and-drop installer (`drag_and_drop_install.py`) that copies the
  package into the user's Maya scripts folder and creates a shelf button.
