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
        cmds.button(label="Toggle Side", height=30, command=self._on_toggle)
        cmds.button(label="Both Sides", height=30, command=self._on_both)
        cmds.setParent(main)

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


if __name__ == "__main__":
    show_ui()
