# Changelog

All notable changes to this project are documented in this file.

## \[1.2.0] - 2026-08-18

### Added

* Right-click "Assign Hotkey..." menu on the **Toggle Side** and **Both
Sides** buttons inside the UI window itself, not just the shelf button --
matches the convenience of tools like Morgan Loomis's ml\_tools
(`ButtonWithPopup`). Uses the same hotkey-assign dialog added in 1.2.0.

## \[1.1.0] - 2026-08-17

### Changed

* Installer hardened: retry-safe file copying (handles transient file locks
on Windows), icon copied to both `userBitmapsDir` and `prefs/icons` for
reliability across Maya versions, automatic shelf-tab creation if no
shelf is found, and a non-blocking in-viewport install confirmation
instead of a modal dialog.

## \[1.0.0] - 2026-08-17

### Added

* Custom shelf icon (`mirrorIcon.png`), installed automatically to Maya's
bitmaps folder by the installer.
* Python rewrite of the original `selectMirror.mel`.
* Namespace-aware side detection, including nested namespaces (referenced rigs).
* Side token detected anywhere in the control name (not just the first token).
* Built-in token pairs: `L/R`, `LT/RT`, `Lt/Rt`, `lt/rt`, `Left/Right`,
`left/right`, `LEFT/RIGHT`.
* `select\_mirror\_toggle()` - collapses the current selection onto a single
side (the opposite of the reference side), deduplicated. Fixes the
original script's bug where the swap direction was computed once from
the first selected item and applied to the whole selection.
* `select\_mirror\_both()` - selects the current controls plus their mirrored
counterparts, regardless of which side(s) were originally selected.
* Compact UI (`selectMirrorUI.py`) with Toggle Side / Both Sides buttons and
an optional single custom side-token pair (checkbox-gated), including a
"Guess" button that reads the side token from the current selection.
Custom token settings persist across Maya sessions via `optionVar`.
* Hotkey-safe wrapper functions (`hotkey\_toggle`, `hotkey\_both`) that respect
the saved custom-token setting without requiring the UI to be open.
* Drag-and-drop installer (`drag\_and\_drop\_install.py`) that copies the
package into the user's Maya scripts folder and creates a shelf button.

