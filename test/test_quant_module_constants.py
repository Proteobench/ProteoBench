import os

import pytest

from proteobench.modules.quant.quant_base.constants import MODULE_SETTINGS_DIRS


@pytest.mark.parametrize(
    "module_id",
    list(MODULE_SETTINGS_DIRS.keys()),
)
def test_MODULE_SETTINGS_DIRS(module_id):
    assert os.path.exists(MODULE_SETTINGS_DIRS[module_id])
