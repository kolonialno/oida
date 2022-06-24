from pathlib import Path

import libcst as cst

from ..config_generator import collect_violations, update_component_config
from ..utils import run_black


def generate_config(project_root: Path) -> None:
    """
    Auto-generate config files for the given component.
    """

    all_volations = collect_violations(project_root)

    for component_path, violations in all_volations.items():
        config_path = component_path / "confcomponent.py"
        if not config_path.exists():
            if not violations:
                continue
            config = cst.Module(body=[])
        else:
            with open(config_path) as f:
                config = cst.parse_module(f.read())

        updated_config = update_component_config(config, allowed_imports=violations)

        with open(config_path, "w") as f:
            action = "Updating" if config_path.exists() else "Creating"
            print(f"{action} component config: {config_path}")
            f.write(run_black(updated_config.code))
