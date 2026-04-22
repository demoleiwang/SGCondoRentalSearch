import os
import pytest

if os.environ.get("CRITICS") != "1":
    pytest.skip(
        "critics tests require CRITICS=1 env var",
        allow_module_level=True,
    )
