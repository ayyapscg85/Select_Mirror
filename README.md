# Select Mirror

A Maya tool for selecting mirrored (Left/Right) rig controls, namespace-aware
for referenced rigs. Rewritten in Python from an original MEL script.

## Install

1. Download / clone this repo.
2. Drag `drag_and_drop_install.py` into the Maya viewport.
3. A shelf button named **MirrorSel** is added to your current shelf.

## Use

Click the shelf button, or run:

```python
import selectMirrorUI
selectMirrorUI.show_ui()
```

- **Toggle Side** - collapses the current selection onto the opposite side
  entirely (works even from a mixed left+right selection).
- **Both Sides** - selects the current controls plus their mirrored
  counterparts, regardless of which side you started with.

### Custom side tokens

Built-in tokens: `L/R`, `LT/RT`, `Lt/Rt`, `lt/rt`, `Left/Right`,
`left/right`, `LEFT/RIGHT` - matched anywhere in the control name.

If a rig uses something else, tick **Custom side tokens**, select a control,
hit **Guess** (it reads the side from the selected control's name), correct
it if needed, then hit **Update**. This is remembered across Maya sessions.

## Hotkeys

**Quick way (right-click any button):**

Right-click **Toggle Side** or **Both Sides** in the UI window itself (or
the **MirrorSel** shelf button), choose **Assign Hotkey...**, tick any
modifiers (Ctrl/Alt/Shift), type a key (e.g. `T`, `F5`), and hit **Assign**.
Done -- no need to open the Hotkey Editor. **Clear** removes a binding the
same way. If the combo is already in use, you'll be asked before it's
overwritten.

**Manual way (Hotkey Editor):**

To bind Toggle / Both Sides via **Windows > Settings/Preferences > Hotkey
Editor** instead, use the wrapper functions below rather than the raw
`selectMirror` functions -- these respect your saved custom-token setting
even if the UI has never been opened this session.

1. **Windows > Settings/Preferences > Hotkey Editor**
2. Click the **+** to add a new runtime command.
3. Create a command for Toggle:
   - Name: `selectMirrorToggle`
   - Category: `Custom Scripts` (or your preference)
   - Command Language: `Python`
   - Command:
     ```python
     import selectMirrorUI
     selectMirrorUI.hotkey_toggle()
     ```
4. Create a second command for Both Sides:
   - Name: `selectMirrorBoth`
   - Command Language: `Python`
   - Command:
     ```python
     import selectMirrorUI
     selectMirrorUI.hotkey_both()
     ```
5. Assign your preferred key combo to each in the hotkey list, then **Save**.

## Files

| File | Purpose |
|---|---|
| `selectMirror.py` | Core selection logic, no UI dependency |
| `selectMirrorUI.py` | UI + hotkey-safe wrapper functions |
| `drag_and_drop_install.py` | Installer, drag into Maya to install |
| `mirrorIcon.png` | Shelf button icon (installed automatically) |
| `LICENSE` | MIT License |
| `CHANGELOG.md` | Version history |

## License

MIT - see [LICENSE](LICENSE).
