"""
selectMirrorUI.py

Compact UI on top of selectMirror.py.

Usage:
    import selectMirrorUI
    selectMirrorUI.show_ui()
"""

import importlib

import maya.cmds as cmds

import selectMirror
importlib.reload(selectMirror)


OPT_ENABLED = "selectMirror_customEnabled"
OPT_LEFT = "selectMirror_customLeft"
OPT_RIGHT = "selectMirror_customRight"
WINDOW_NAME = "selectMirrorUIWindow"


def _load_state():
    enabled = bool(cmds.optionVar(query=OPT_ENABLED)) if cmds.optionVar(exists=OPT_ENABLED) else False
    left = cmds.optionVar(query=OPT_LEFT) if cmds.optionVar(exists=OPT_LEFT) else ""
    right = cmds.optionVar(query=OPT_RIGHT) if cmds.optionVar(exists=OPT_RIGHT) else ""
    return enabled, left, right


def _save_state(enabled, left, right):
    cmds.optionVar(intValue=(OPT_ENABLED, 1 if enabled else 0))
    cmds.optionVar(stringValue=(OPT_LEFT, left))
    cmds.optionVar(stringValue=(OPT_RIGHT, right))


class SelectMirrorUI(object):

    def __init__(self):
        self.enabled, self.left, self.right = _load_state()
        self._build_ui()

    # -- building -----------------------------------------------------

    def _build_ui(self):
        if cmds.window(WINDOW_NAME, exists=True):
            cmds.deleteUI(WINDOW_NAME)

        cmds.window(WINDOW_NAME, title="Select Mirror", widthHeight=(280, 190), sizeable=False)
        main = cmds.columnLayout(adjustableColumn=True, rowSpacing=5, columnAttach=("both", 8))

        cmds.rowLayout(numberOfColumns=2, columnWidth2=(130, 130),
                        columnAttach2=("both", "both"), parent=main)
        toggle_btn = cmds.button(label="Toggle Side", height=30, command=self._on_toggle)
        both_btn = cmds.button(label="Both Sides", height=30, command=self._on_both)
        cmds.setParent(main)

        cmds.popupMenu(parent=toggle_btn, button=3)
        cmds.menuItem(label="Assign Hotkey...", command=lambda *_a: open_assign_hotkey_dialog("toggle"))
        cmds.popupMenu(parent=both_btn, button=3)
        cmds.menuItem(label="Assign Hotkey...", command=lambda *_a: open_assign_hotkey_dialog("both"))
        cmds.button(toggle_btn, edit=True, annotation="Right-click to assign a hotkey.")
        cmds.button(both_btn, edit=True, annotation="Right-click to assign a hotkey.")

        cmds.separator(height=8, style="in", parent=main)

        self.enable_cb = cmds.checkBox(
            label="Custom side tokens", value=self.enabled,
            changeCommand=self._on_toggle_enabled, parent=main,
        )

        cmds.rowLayout(numberOfColumns=2, columnWidth2=(130, 130),
                        columnAttach2=("both", "both"), parent=main)
        self.left_field = cmds.textField(text=self.left, placeholderText="Left (e.g. Lf)",
                                          enable=self.enabled)
        self.right_field = cmds.textField(text=self.right, placeholderText="Right (e.g. Rt)",
                                           enable=self.enabled)
        cmds.setParent(main)

        cmds.rowLayout(numberOfColumns=2, columnWidth2=(130, 130),
                        columnAttach2=("both", "both"), parent=main)
        self.guess_btn = cmds.button(label="Guess", height=24, command=self._on_guess,
                                      enable=self.enabled)
        self.update_btn = cmds.button(label="Update", height=24, command=self._on_update,
                                       enable=self.enabled)
        cmds.setParent(main)

        self.status_text = cmds.text(label="", align="left", wordWrap=True, height=28, parent=main)

        cmds.showWindow(WINDOW_NAME)

    # -- helpers ------------------------------------------------------

    def _active_pairs(self):
        if not cmds.checkBox(self.enable_cb, query=True, value=True):
            return None
        left = cmds.textField(self.left_field, query=True, text=True).strip()
        right = cmds.textField(self.right_field, query=True, text=True).strip()
        if left and right and left != right:
            return [(left, right)]
        return None

    def _guess_pair(self):
        selection = cmds.ls(selection=True) or []
        if not selection:
            return "", ""
        _ns, base = selectMirror._split_namespace(selection[0])
        side_map = selectMirror._build_side_map()
        match = selectMirror._find_side_token(base, side_map)
        if match is not None:
            _idx, tok, opposite, side = match
            return (tok, opposite) if side == "L" else (opposite, tok)
        for tok in base.split("_"):
            if tok.isalpha() and 1 <= len(tok) <= 4:
                return tok, ""
        return "", ""

    # -- callbacks ------------------------------------------------------

    def _on_toggle_enabled(self, value):
        cmds.textField(self.left_field, edit=True, enable=value)
        cmds.textField(self.right_field, edit=True, enable=value)
        cmds.button(self.guess_btn, edit=True, enable=value)
        cmds.button(self.update_btn, edit=True, enable=value)
        _save_state(value,
                    cmds.textField(self.left_field, query=True, text=True),
                    cmds.textField(self.right_field, query=True, text=True))
        if value:
            self._on_guess()

    def _on_guess(self, *_args):
        left, right = self._guess_pair()
        if not left:
            self._set_status("Select a control first to guess from.")
            return
        cmds.textField(self.left_field, edit=True, text=left)
        cmds.textField(self.right_field, edit=True, text=right)
        if right:
            self._set_status("Guessed: {0} / {1}. Edit if wrong, then Update.".format(left, right))
        else:
            self._set_status("Guessed left: {0}. Enter the right value, then Update.".format(left))

    def _on_update(self, *_args):
        left = cmds.textField(self.left_field, query=True, text=True).strip()
        right = cmds.textField(self.right_field, query=True, text=True).strip()
        if not left or not right:
            self._set_status("Enter both a left and right value first.")
            return
        if left == right:
            self._set_status("Left and right values must be different.")
            return
        _save_state(True, left, right)
        self._set_status("Updated custom pair: {0} / {1}".format(left, right))

    def _on_toggle(self, *_args):
        result = selectMirror.select_mirror_toggle(extra_pairs=self._active_pairs())
        self._report(result)

    def _on_both(self, *_args):
        result = selectMirror.select_mirror_both(extra_pairs=self._active_pairs())
        self._report(result)

    def _report(self, result):
        self._set_status("Selected {0} control(s).".format(len(result)) if result
                          else "Nothing selected / no mirror found.")

    def _set_status(self, message):
        cmds.text(self.status_text, edit=True, label=message)


def show_ui():
    return SelectMirrorUI()


# ---------------------------------------------------------------------------
# Hotkey-safe wrappers.
#
# These read the saved custom-token setting (from the UI's "Update" button)
# directly from optionVars, so a hotkey behaves identically to clicking the
# UI buttons -- even if the UI window has never been opened this session.
# Bind these two to hotkeys rather than the raw selectMirror functions.
# ---------------------------------------------------------------------------

def _active_pairs_from_optionvar():
    enabled = bool(cmds.optionVar(query=OPT_ENABLED)) if cmds.optionVar(exists=OPT_ENABLED) else False
    if not enabled:
        return None
    left = cmds.optionVar(query=OPT_LEFT) if cmds.optionVar(exists=OPT_LEFT) else ""
    right = cmds.optionVar(query=OPT_RIGHT) if cmds.optionVar(exists=OPT_RIGHT) else ""
    if left and right and left != right:
        return [(left, right)]
    return None


def hotkey_toggle():
    """Bind to a hotkey: collapses selection onto the opposite side."""
    return selectMirror.select_mirror_toggle(extra_pairs=_active_pairs_from_optionvar())


def hotkey_both():
    """Bind to a hotkey: selects current controls plus their mirrors."""
    return selectMirror.select_mirror_both(extra_pairs=_active_pairs_from_optionvar())


# ---------------------------------------------------------------------------
# Right-click shelf menu: "Assign Hotkey..."
#
# Lets an artist bind Toggle Side / Both Sides to a key combo directly,
# without opening Maya's full Hotkey Editor. Uses cmds.nameCommand +
# cmds.hotkey, the same mechanism the Hotkey Editor itself uses under the
# hood, so assignments show up there too and persist normally.
# ---------------------------------------------------------------------------

_HOTKEY_INFO = {
    "toggle": ("SelectMirror_ToggleSide", "Select Mirror: Toggle Side",
               "import selectMirrorUI\nselectMirrorUI.hotkey_toggle()\n"),
    "both": ("SelectMirror_BothSides", "Select Mirror: Both Sides",
             "import selectMirrorUI\nselectMirrorUI.hotkey_both()\n"),
}

_HOTKEY_WINDOW = "selectMirrorHotkeyWin"


def _format_combo(key, ctrl, alt, shift):
    parts = []
    if ctrl:
        parts.append("Ctrl")
    if alt:
        parts.append("Alt")
    if shift:
        parts.append("Shift")
    parts.append(key)
    return "+".join(parts)


def open_assign_hotkey_dialog(which):
    """which: 'toggle' or 'both'."""
    if which not in _HOTKEY_INFO:
        return
    label = "Toggle Side" if which == "toggle" else "Both Sides"

    if cmds.window(_HOTKEY_WINDOW, exists=True):
        cmds.deleteUI(_HOTKEY_WINDOW)

    cmds.window(_HOTKEY_WINDOW, title="Hotkey: {0}".format(label),
                widthHeight=(230, 160), sizeable=False)
    col = cmds.columnLayout(adjustableColumn=True, rowSpacing=6, columnAttach=("both", 10))

    cmds.text(label="Assign hotkey for:\n{0}".format(label), align="left")

    cmds.rowLayout(numberOfColumns=3, columnWidth3=(65, 65, 65), parent=col)
    ctrl_cb = cmds.checkBox(label="Ctrl")
    alt_cb = cmds.checkBox(label="Alt")
    shift_cb = cmds.checkBox(label="Shift")
    cmds.setParent(col)

    key_field = cmds.textField(placeholderText="Key (e.g. T, F5)")

    cmds.rowLayout(numberOfColumns=2, columnWidth2=(105, 105), parent=col)
    cmds.button(label="Assign", command=lambda *_a: _do_assign_hotkey(
        which, key_field, ctrl_cb, alt_cb, shift_cb))
    cmds.button(label="Clear", command=lambda *_a: _do_clear_hotkey(
        key_field, ctrl_cb, alt_cb, shift_cb))
    cmds.setParent(col)

    cmds.showWindow(_HOTKEY_WINDOW)


def _do_assign_hotkey(which, key_field, ctrl_cb, alt_cb, shift_cb):
    key = cmds.textField(key_field, query=True, text=True).strip()
    ctrl = cmds.checkBox(ctrl_cb, query=True, value=True)
    alt = cmds.checkBox(alt_cb, query=True, value=True)
    shift = cmds.checkBox(shift_cb, query=True, value=True)

    if not key:
        cmds.warning("Select Mirror: enter a key to assign.")
        return

    name_cmd, annotation, py_command = _HOTKEY_INFO[which]

    existing = cmds.hotkey(keyShortcut=key, ctrlModifier=ctrl, altModifier=alt,
                            shiftModifier=shift, query=True, name=True)
    if existing and existing != name_cmd:
        result = cmds.confirmDialog(
            title="Hotkey In Use",
            message="{0} is already assigned to:\n{1}\n\nOverwrite it?".format(
                _format_combo(key, ctrl, alt, shift), existing),
            button=["Overwrite", "Cancel"], defaultButton="Cancel",
            cancelButton="Cancel", dismissString="Cancel",
        )
        if result != "Overwrite":
            return

    cmds.nameCommand(name_cmd, annotation=annotation, command=py_command, sourceType="python")
    cmds.hotkey(keyShortcut=key, name=name_cmd, ctrlModifier=ctrl, altModifier=alt,
                shiftModifier=shift)

    cmds.inViewMessage(
        amg="Select Mirror: {0} assigned to {1}".format(
            annotation, _format_combo(key, ctrl, alt, shift)),
        pos="topCenter", fade=True, alpha=0.9,
    )
    if cmds.window(_HOTKEY_WINDOW, exists=True):
        cmds.deleteUI(_HOTKEY_WINDOW)


def _do_clear_hotkey(key_field, ctrl_cb, alt_cb, shift_cb):
    key = cmds.textField(key_field, query=True, text=True).strip()
    ctrl = cmds.checkBox(ctrl_cb, query=True, value=True)
    alt = cmds.checkBox(alt_cb, query=True, value=True)
    shift = cmds.checkBox(shift_cb, query=True, value=True)

    if not key:
        cmds.warning("Select Mirror: enter the key combo to clear.")
        return

    cmds.hotkey(keyShortcut=key, name="", ctrlModifier=ctrl, altModifier=alt, shiftModifier=shift)
    cmds.inViewMessage(
        amg="Select Mirror: cleared {0}".format(_format_combo(key, ctrl, alt, shift)),
        pos="topCenter", fade=True, alpha=0.9,
    )


if __name__ == "__main__":
    show_ui()
