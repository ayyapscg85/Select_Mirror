"""
selectMirror.py

Python rewrite of selectMirror.mel for Maya.

Fixes / improvements over the MEL version:
  1. Works with referenced rigs (namespaces), including nested namespaces
     like "char:body:L_arm_ctrl".
  2. The side token ("L"/"R", "LT"/"RT", "Left"/"Right", etc.) is found
     ANYWHERE in the underscore-separated name, not just the first token.
     e.g. "arm_L_ctrl" and "L_arm_ctrl" both work.
  3. Ships with a sensible set of default token pairs (L/R, LT/RT, Left/Right,
     lt/rt, etc.) but you can pass your own pairs in at call time -- no need
     to edit the script.
  4. Each selected object is mirrored independently, based on whichever side
     token IT contains -- not based on the first item in the selection.
     (The old MEL script computed the swap direction once from $select[0]
     and applied it to everything, which is why it "toggled" the wrong way
     depending on what happened to be first in your selection.)
  5. Two selection modes:
       - "toggle": select only the mirrored (opposite side) controls.
       - "both":   select the original selection PLUS their mirrored
                   counterparts, regardless of whether you started on the
                   left or the right (e.g. select an arm control on either
                   side and get both arms).
  6. Controls with no recognizable side token (centre controls, etc.) are
     left alone / skipped, same as the original script, and are reported
     via a warning so you know what was skipped.

Usage in Maya's Script Editor (Python tab):

    import selectMirror
    selectMirror.select_mirror_toggle()          # old toggle behaviour, fixed
    selectMirror.select_mirror_both()             # new: select both sides

    # Adding your own token pairs (checked before the built-in defaults):
    selectMirror.select_mirror_both(extra_pairs=[("Lf", "Rt"), ("F", "B")])

You can also wire these up to shelf buttons:
    python("import selectMirror; selectMirror.select_mirror_toggle()")
    python("import selectMirror; selectMirror.select_mirror_both()")
"""

import maya.cmds as cmds


# ---------------------------------------------------------------------------
# Default side-token pairs. Order matters a little: earlier pairs are matched
# before later ones if there is ever an ambiguous collision, but in practice
# these are all distinct strings so it rarely matters.
# Add/remove pairs here if you want to change studio-wide defaults, or pass
# extra_pairs= at call time for a one-off / per-rig override instead.
# ---------------------------------------------------------------------------
DEFAULT_SIDE_PAIRS = [
    ("Left", "Right"),
    ("left", "right"),
    ("LEFT", "RIGHT"),
    ("LT", "RT"),
    ("Lt", "Rt"),
    ("lt", "rt"),
    ("L", "R"),
]


def _build_side_map(extra_pairs=None):
    """
    Build a lookup dict: token -> (opposite_token, side_letter)

    extra_pairs, if given, is a list of (left_token, right_token) tuples
    supplied by the caller. These take priority over the built-in defaults
    if the same token appears in both.
    """
    pairs = list(extra_pairs) + DEFAULT_SIDE_PAIRS if extra_pairs else list(DEFAULT_SIDE_PAIRS)

    side_map = {}
    for left_tok, right_tok in pairs:
        # first-seen wins, so user-supplied pairs (listed first) take priority
        if left_tok not in side_map:
            side_map[left_tok] = (right_tok, "L")
        if right_tok not in side_map:
            side_map[right_tok] = (left_tok, "R")
    return side_map


def _split_namespace(name):
    """
    Split off the namespace from a node name, handling nested namespaces.
    "char:body:L_arm_ctrl" -> ("char:body:", "L_arm_ctrl")
    "L_arm_ctrl"           -> ("", "L_arm_ctrl")
    """
    if ":" in name:
        ns, base = name.rsplit(":", 1)
        return ns + ":", base
    return "", name


def _find_side_token(base_name, side_map):
    """
    Search every underscore-separated token in base_name for a side match,
    regardless of its position. Returns (index, token, opposite, side) for
    the first match found, or None if no token matches.
    """
    tokens = base_name.split("_")
    for i, tok in enumerate(tokens):
        if tok in side_map:
            opposite, side = side_map[tok]
            return i, tok, opposite, side
    return None


def get_mirror_name(name, side_map):
    """
    Return the mirrored node name for `name`, or None if no recognizable
    side token is present anywhere in the name.
    """
    namespace, base = _split_namespace(name)
    match = _find_side_token(base, side_map)
    if match is None:
        return None

    idx, _tok, opposite, _side = match
    tokens = base.split("_")
    tokens[idx] = opposite
    return namespace + "_".join(tokens)


def _analyze_selection(selection, side_map):
    """
    For each object in `selection`, work out which side token it contains.
    Returns (analyzed, skipped) where analyzed is a list of (obj, side)
    tuples (side is 'L' or 'R') for objects with a recognizable side token,
    and skipped is a list of objects that had none.
    """
    analyzed = []
    skipped = []
    for obj in selection:
        _ns, base = _split_namespace(obj)
        match = _find_side_token(base, side_map)
        if match is None:
            skipped.append(obj)
        else:
            _idx, _tok, _opposite, side = match
            analyzed.append((obj, side))
    return analyzed, skipped


def select_mirror_toggle(extra_pairs=None):
    """
    Collapse the current selection onto a single side, entirely.

    The reference side is taken from the first (side-having) object in the
    selection; every object -- whether it's already on that side or on the
    opposite side -- ends up mapped to the OPPOSITE of that reference side,
    deduplicated. This means:
      - a pure left selection -> becomes a pure right selection (and vice
        versa), same as a classic toggle.
      - a mixed left+right selection (e.g. straight after select_mirror_both)
        -> collapses entirely onto one side instead of staying mixed.
      - running it twice in a row toggles back and forth between sides.
    """
    side_map = _build_side_map(extra_pairs)
    selection = cmds.ls(selection=True) or []

    if not selection:
        cmds.warning("selectMirror: nothing selected.")
        return []

    analyzed, skipped = _analyze_selection(selection, side_map)

    if skipped:
        cmds.warning(
            "selectMirror: skipped (no side token found): {0}".format(
                ", ".join(skipped)
            )
        )

    if not analyzed:
        cmds.warning("selectMirror: no side-recognizable controls in selection.")
        cmds.select(clear=True)
        return []

    ref_side = analyzed[0][1]
    target_side = "R" if ref_side == "L" else "L"

    result = []
    seen = set()
    missing = []

    for obj, side in analyzed:
        final = obj if side == target_side else get_mirror_name(obj, side_map)
        if final in seen:
            continue
        if cmds.objExists(final):
            seen.add(final)
            result.append(final)
        else:
            missing.append(final)

    if missing:
        cmds.warning(
            "selectMirror: mirrored control(s) not found in scene: {0}".format(
                ", ".join(missing)
            )
        )

    if result:
        cmds.select(result, replace=True)
    else:
        cmds.select(clear=True)

    return result


def select_mirror_both(extra_pairs=None):
    """
    Select the current selection PLUS its opposite-side counterparts, so
    you end up with both left and right, no matter which side (or mix of
    sides) you started with.
    """
    side_map = _build_side_map(extra_pairs)
    selection = cmds.ls(selection=True) or []

    if not selection:
        cmds.warning("selectMirror: nothing selected.")
        return []

    analyzed, skipped = _analyze_selection(selection, side_map)

    if skipped:
        cmds.warning(
            "selectMirror: skipped (no side token found): {0}".format(
                ", ".join(skipped)
            )
        )

    result = []
    seen = set()
    missing = []

    def _add(node):
        if node not in seen:
            seen.add(node)
            result.append(node)

    for obj, _side in analyzed:
        _add(obj)
        mirrored = get_mirror_name(obj, side_map)
        if cmds.objExists(mirrored):
            _add(mirrored)
        else:
            missing.append(mirrored)

    if missing:
        cmds.warning(
            "selectMirror: mirrored control(s) not found in scene: {0}".format(
                ", ".join(missing)
            )
        )

    if result:
        cmds.select(result, replace=True)
    else:
        cmds.select(clear=True)

    return result
