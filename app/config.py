import json
import os
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional


def _default_data_dir() -> Path:
    env = os.environ.get("SIMONETTO_DATA_DIR")
    if env:
        return Path(env)
    local_appdata = os.environ.get("LOCALAPPDATA", str(Path.home() / "AppData" / "Local"))
    return Path(local_appdata) / "SimonettoDevolucoes"


@dataclass
class Config:
    data_dir: Path
    backup_folder: Path
    backup_retention: int = 30
    backup_frequency: str = "on_close"  # on_close | daily | weekly | manual
    sidebar_collapsed: bool = False

    @property
    def db_path(self) -> Path:
        return self.data_dir / "dados.db"

    @property
    def anexos_dir(self) -> Path:
        return self.data_dir / "anexos"

    @property
    def backups_dir(self) -> Path:
        return self.data_dir / "backups"

    @property
    def config_file(self) -> Path:
        return self.data_dir / "config.json"

    @classmethod
    def load(cls) -> "Config":
        data_dir = _default_data_dir()
        data_dir.mkdir(parents=True, exist_ok=True)
        (data_dir / "anexos").mkdir(exist_ok=True)
        (data_dir / "backups").mkdir(exist_ok=True)

        config_file = data_dir / "config.json"
        defaults = {
            "backup_folder": str(data_dir / "backups"),
            "backup_retention": 30,
            "backup_frequency": "on_close",
            "sidebar_collapsed": False,
        }
        if config_file.exists():
            defaults.update(json.loads(config_file.read_text(encoding="utf-8")))

        return cls(
            data_dir=data_dir,
            backup_folder=Path(defaults["backup_folder"]),
            backup_retention=defaults["backup_retention"],
            backup_frequency=defaults["backup_frequency"],
            sidebar_collapsed=defaults["sidebar_collapsed"],
        )

    def save(self) -> None:
        payload = {
            "backup_folder": str(self.backup_folder),
            "backup_retention": self.backup_retention,
            "backup_frequency": self.backup_frequency,
            "sidebar_collapsed": self.sidebar_collapsed,
        }
        self.config_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")
