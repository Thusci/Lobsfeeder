from pathlib import Path

from app.core.config_store import ConfigStore


def test_config_store_roundtrip(tmp_path: Path) -> None:
    db_path = tmp_path / "router.db"
    store = ConfigStore(str(db_path))
    payload = {"server": {"config_source": "db"}}
    store.set_config(payload)

    stored = store.get_config()
    assert stored is not None
    assert stored.payload == payload
