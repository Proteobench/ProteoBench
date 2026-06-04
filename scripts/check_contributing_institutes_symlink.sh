#!/usr/bin/env bash
# Checks that the contributing-institutes logo in the webinterface is a symlink
# pointing to the canonical copy in docs/_static/img/.
# The canonical file to edit is: docs/_static/img/proteobench-contributing-institutes.png

SYMLINK="webinterface/logos/logo_participants/proteobench-contributing-institutes.png"
EXPECTED_TARGET="../../../docs/_static/img/proteobench-contributing-institutes.png"

if [ ! -L "$SYMLINK" ]; then
    echo ""
    echo "WARNING: $SYMLINK is not a symlink."
    echo "  It should be a symlink pointing to $EXPECTED_TARGET"
    echo "  (canonical file: docs/_static/img/proteobench-contributing-institutes.png)"
    echo ""
    echo "  To fix, run:"
    echo "    cd webinterface/logos/logo_participants"
    echo "    rm proteobench-contributing-institutes.png"
    echo "    ln -s ../../../docs/_static/img/proteobench-contributing-institutes.png proteobench-contributing-institutes.png"
    echo ""
    echo "  If you intended to update the figure, move your new file to"
    echo "  docs/_static/img/proteobench-contributing-institutes.png instead."
    echo ""
    exit 1
fi

RESOLVED=$(readlink "$SYMLINK")
if [ "$RESOLVED" != "$EXPECTED_TARGET" ]; then
    echo ""
    echo "WARNING: $SYMLINK points to '$RESOLVED'"
    echo "  Expected: $EXPECTED_TARGET"
    echo ""
    exit 1
fi
