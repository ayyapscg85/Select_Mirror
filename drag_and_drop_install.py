"""
drag_and_drop_install.py

Drag this file onto the Maya viewport to install Select Mirror.

Copies selectMirror.py, selectMirrorUI.py, and mirrorIcon.png into your
Maya scripts / icons folders and adds a shelf button that opens the UI.
Once installed, everything runs from your Maya user folder -- you can
delete the folder you dragged this from and it will keep working.
"""

import os
import shutil
import stat
import time

import maya.cmds as cmds
import maya.mel as mel


PACKAGE_FILES = ["selectMirror.py", "selectMirrorUI.py"]
ICON_FILE = "mirrorIcon.png"
SHELF_BUTTON_LABEL = "MirrorSel"
SHELF_TAB_NAME = "SelectMirror"


# ---------------------------------------------------------------------------
# Retry-safe file copy (Windows can transiently lock a .pyc/.py that's still
# referenced by a live Maya session; a couple of retries avoids a hard fail).
# ---------------------------------------------------------------------------

def _copy_file_with_retries(src, dst, retries=5, delay=0.2):
    for i in range(retries):
        try:
            if os.path.exists(dst):
                os.chmod(dst, stat.S_IWRITE)
            shutil.copy2(src, dst)
            return True
        except Exception:
            time.sleep(delay * (i + 1))
    return False


# ---------------------------------------------------------------------------
# Icon install -- copy to every known Maya icon search location so the icon
# resolves regardless of Maya version / OS quirks.
# ---------------------------------------------------------------------------

def _get_icon_dirs():
    dirs = []
    try:
        bitmaps_dir = cmds.internalVar(userBitmapsDir=True)
        if bitmaps_dir:
            dirs.append(bitmaps_dir)
    except Exception:
        pass

    try:
        pref_dir = cmds.internalVar(userPrefDir=True)
        if pref_dir:
            dirs.append(os.path.join(pref_dir, "icons"))
    except Exception:
        pass

    seen = set()
    unique = []
    for d in dirs:
        key = os.path.normcase(os.path.normpath(d))
        if key not in seen:
            seen.add(key)
            unique.append(d)
    return unique


def _copy_icon(src_dir):
    icon_src = os.path.join(src_dir, ICON_FILE)
    if not os.path.isfile(icon_src):
        cmds.warning(
            "Select Mirror: icon not found next to installer (expected at: "
            "{0}). Falling back to the default shelf icon.".format(icon_src)
        )
        return None

    copied_anywhere = False
    copy_errors = []
    for icon_dir in _get_icon_dirs():
        try:
            if not os.path.isdir(icon_dir):
                os.makedirs(icon_dir)
            if _copy_file_with_retries(icon_src, os.path.join(icon_dir, ICON_FILE)):
                copied_anywhere = True
            else:
                copy_errors.append(icon_dir)
        except Exception as exc:
            copy_errors.append("{0} ({1})".format(icon_dir, exc))

    if not copied_anywhere:
        cmds.warning(
            "Select Mirror: found {0} but could not copy it to any icon "
            "folder. Tried: {1}".format(icon_src, ", ".join(copy_errors) or "none")
        )

    return ICON_FILE if copied_anywhere else None


# ---------------------------------------------------------------------------
# Shelf button
# ---------------------------------------------------------------------------

def _get_current_shelf():
    try:
        shelf_top = mel.eval("$tmp = $gShelfTopLevel")
        return cmds.tabLayout(shelf_top, query=True, selectTab=True)
    except Exception:
        return None


def _ensure_shelf_exists():
    shelf = _get_current_shelf()
    if shelf and cmds.shelfLayout(shelf, exists=True):
        return shelf
    # No usable shelf found (rare) -- create a dedicated tab as a fallback.
    try:
        mel.eval('addNewShelfTab("{0}")'.format(SHELF_TAB_NAME))
    except Exception:
        pass
    return _get_current_shelf()


def _create_shelf_button(icon_name):
    shelf = _ensure_shelf_exists()
    if not shelf:
        cmds.warning("Select Mirror: could not find a shelf to add the button to.")
        return

    existing = cmds.shelfLayout(shelf, query=True, childArray=True) or []
    for btn in existing:
        try:
            if cmds.shelfButton(btn, query=True, label=True) == SHELF_BUTTON_LABEL:
                cmds.deleteUI(btn)
        except Exception:
            pass

    kwargs = dict(
        parent=shelf,
        label=SHELF_BUTTON_LABEL,
        annotation="Select Mirror - select mirrored / both-side controls",
        command="import selectMirrorUI; selectMirrorUI.show_ui()",
        sourceType="python",
    )
    if icon_name:
        kwargs["image1"] = icon_name

    cmds.shelfButton(**kwargs)


# ---------------------------------------------------------------------------
# Install
# ---------------------------------------------------------------------------

def install():
    src_dir = os.path.dirname(os.path.abspath(__file__))
    dest_dir = cmds.internalVar(userScriptDir=True)

    missing = []
    failed = []
    for filename in PACKAGE_FILES:
        src = os.path.join(src_dir, filename)
        if not os.path.isfile(src):
            missing.append(filename)
            continue
        if not _copy_file_with_retries(src, os.path.join(dest_dir, filename)):
            failed.append(filename)

    if missing or failed:
        problems = []
        if missing:
            problems.append("Missing next to the installer: {0}".format(", ".join(missing)))
        if failed:
            problems.append("Could not copy (file may be locked): {0}".format(", ".join(failed)))
        cmds.confirmDialog(
            title="Select Mirror - Install Failed",
            message="\n".join(problems),
            button=["OK"],
        )
        return

    icon_name = _copy_icon(src_dir)
    _create_shelf_button(icon_name or "commandButton.png")

    icon_note = "" if icon_name else "<br><span style=\"color:#ffaa00\">Icon not found -- using default icon.</span>"
    cmds.inViewMessage(
        amg="Select Mirror installed to:<br>{0}{1}".format(dest_dir, icon_note),
        pos="topCenter",
        fade=True,
        alpha=0.9,
    )


def onMayaDroppedPythonFile(*_args):
    """Called automatically by Maya when this file is dropped into the viewport."""
    install()


if __name__ == "__main__":
    install()
