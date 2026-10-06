from pathlib import Path
import json
import re
import shutil
from datetime import datetime
from typing import Any


APP_FOLDER = Path(__file__).resolve().parent
PRO_CONFIG_FILE = APP_FOLDER / "file_organizer_pro.json"
PRO_HISTORY_FILE = APP_FOLDER / "file_organizer_pro_history.json"


def validate_pro_config(config: Any) -> bool:
    """Validate the basic shape of the Pro profile/rule configuration."""
    if not isinstance(config, dict):
        return False

    profiles = config.get("profiles")
    if not isinstance(profiles, dict) or not profiles:
        return False

    for profile_name, profile in profiles.items():
        if not isinstance(profile_name, str) or not profile_name.strip():
            return False
        if not isinstance(profile, dict):
            return False

        rules = profile.get("rules")
        if not isinstance(rules, list):
            return False

        for rule in rules:
            if not isinstance(rule, dict):
                return False

            if not isinstance(rule.get("name"), str) or not rule["name"].strip():
                return False

            if not isinstance(rule.get("enabled", True), bool):
                return False

            if rule.get("match", "all") not in {"all", "any"}:
                return False

            conditions = rule.get("conditions", {})
            action = rule.get("action", {})

            if not isinstance(conditions, dict):
                return False

            if not isinstance(action, dict):
                return False

            if action.get("type") not in {"move", "copy"}:
                return False

            destination = action.get("destination")

            if not isinstance(destination, str) or not destination.strip():
                return False

    return True


def load_pro_config() -> dict[str, Any]:
    """Load and validate the Pro configuration."""
    if not PRO_CONFIG_FILE.exists():
        raise FileNotFoundError(
            f"Missing Pro configuration: {PRO_CONFIG_FILE}"
        )

    with open(
        PRO_CONFIG_FILE,
        "r",
        encoding="utf-8"
    ) as file:
        config = json.load(file)

    if not validate_pro_config(config):
        raise ValueError("Pro configuration is invalid.")

    return config


def get_files_to_scan(folder: Path) -> list[Path]:
    """Return files from a folder and its subfolders."""
    return [
        item
        for item in folder.rglob("*")
        if item.is_file()
    ]


def _extension_matches(
    file: Path,
    expected: list[str]
) -> bool:
    if not expected:
        return False

    extension = file.suffix.lower()

    return extension in {
        value.strip().lower()
        for value in expected
    }


def _name_contains_matches(
    file: Path,
    values: list[str]
) -> bool:
    if not values:
        return False

    filename = file.name.lower()

    return any(
        value.strip().lower() in filename
        for value in values
    )


def _size_matches(
    file: Path,
    minimum_mb: float | None,
    maximum_mb: float | None
) -> bool:
    size_mb = file.stat().st_size / (1024 * 1024)

    if minimum_mb is not None and size_mb < minimum_mb:
        return False

    if maximum_mb is not None and size_mb > maximum_mb:
        return False

    return True


def _regex_matches(
    file: Path,
    pattern: str | None
) -> bool:
    if not pattern:
        return False

    try:
        return re.search(
            pattern,
            file.name,
            flags=re.IGNORECASE
        ) is not None
    except re.error:
        return False


def rule_matches(
    file: Path,
    rule: dict[str, Any]
) -> bool:
    """Evaluate all configured conditions for one file."""
    conditions = rule.get("conditions", {})
    checks: list[bool] = []

    extensions = conditions.get("extensions", [])

    if extensions:
        checks.append(
            _extension_matches(
                file,
                extensions
            )
        )

    name_contains = conditions.get(
        "name_contains",
        []
    )

    if name_contains:
        checks.append(
            _name_contains_matches(
                file,
                name_contains
            )
        )

    name_regex = conditions.get("name_regex")

    if name_regex:
        checks.append(
            _regex_matches(
                file,
                name_regex
            )
        )

    minimum_mb = conditions.get("min_size_mb")
    maximum_mb = conditions.get("max_size_mb")

    if (
        minimum_mb is not None
        or maximum_mb is not None
    ):
        try:
            checks.append(
                _size_matches(
                    file,
                    minimum_mb,
                    maximum_mb
                )
            )
        except OSError:
            checks.append(False)

    # A rule with no conditions should never
    # accidentally match every file.
    if not checks:
        return False

    if rule.get("match", "all") == "any":
        return any(checks)

    return all(checks)


def _unique_destination(
    destination: Path,
    reserved: set[Path]
) -> Path:
    if (
        not destination.exists()
        and destination not in reserved
    ):
        return destination

    counter = 1

    while True:
        candidate = destination.with_name(
            f"{destination.stem} "
            f"({counter})"
            f"{destination.suffix}"
        )

        if (
            not candidate.exists()
            and candidate not in reserved
        ):
            return candidate

        counter += 1


def build_pro_plan(
    folder: Path,
    profile_name: str
) -> list[dict[str, Any]]:
    """Build a safe preview plan from the selected Pro profile."""
    folder = folder.resolve()
    config = load_pro_config()
    profiles = config["profiles"]

    if profile_name not in profiles:
        raise ValueError(
            f"Unknown Pro profile: {profile_name}"
        )

    rules = profiles[profile_name]["rules"]
    files = get_files_to_scan(folder)

    reserved_destinations: set[Path] = set()
    plan: list[dict[str, Any]] = []

    for file in files:
        matched_rule = None

        for rule in rules:
            if (
                rule.get("enabled", True)
                and rule_matches(file, rule)
            ):
                matched_rule = rule
                break

        if matched_rule is None:
            continue

        action = matched_rule["action"]["type"]

        destination_root = Path(
            matched_rule["action"]["destination"]
        )

        if not destination_root.is_absolute():
            destination_root = (
                folder / destination_root
            )

        destination = _unique_destination(
            destination_root / file.name,
            reserved_destinations
        )

        reserved_destinations.add(destination)

        plan.append({
            "source": file,
            "destination": destination,
            "action": action,
            "rule": matched_rule["name"],
        })

    return plan


def validate_pro_plan(
    plan: list[dict[str, Any]]
) -> bool:
    """Validate that the planned operations are safe."""
    if not plan:
        return False

    destinations: set[Path] = set()

    for operation in plan:
        source = Path(operation["source"])
        destination = Path(
            operation["destination"]
        )

        if not source.exists() or not source.is_file():
            return False

        if source.resolve() == destination.resolve():
            return False

        if destination.exists():
            return False

        if destination in destinations:
            return False

        destinations.add(destination)

    return True


def create_operation_id() -> str:
    return datetime.now().strftime(
        "%Y%m%d-%H%M%S-%f"
    )


def execute_pro_plan(
    plan: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Execute a validated Pro plan."""
    if not validate_pro_plan(plan):
        raise ValueError(
            "The Pro plan is no longer valid. "
            "Preview again before organizing."
        )

    operation_id = create_operation_id()
    history: list[dict[str, Any]] = []

    for operation in plan:
        source = Path(operation["source"])
        destination = Path(
            operation["destination"]
        )
        action = operation["action"]

        destination.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        if action == "move":
            shutil.move(
                str(source),
                str(destination)
            )

        elif action == "copy":
            shutil.copy2(
                str(source),
                str(destination)
            )

        else:
            raise ValueError(
                f"Unsupported Pro action: {action}"
            )

        history.append({
            "operation_id": operation_id,
            "source": str(source),
            "destination": str(destination),
            "action": action,
            "rule": operation["rule"],
        })

    return history


def save_pro_history(
    history: list[dict[str, Any]]
) -> None:
    """Persist the most recent Pro operation history."""
    data = {
        "version": 1,
        "timestamp": datetime.now().isoformat(
            timespec="seconds"
        ),
        "operations": history,
    }

    with open(
        PRO_HISTORY_FILE,
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(
            data,
            file,
            indent=4
        )
