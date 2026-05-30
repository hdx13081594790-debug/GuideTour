from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory


def test_alembic_has_initial_revision():
    config = Config("alembic.ini")
    script = ScriptDirectory.from_config(config)
    heads = script.get_heads()

    assert heads == ["20260530_0001"]
    assert Path("alembic/versions/20260530_0001_initial_schema.py").exists()
