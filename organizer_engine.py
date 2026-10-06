from pathlib import Path
import shutil
import json
from datetime import datetime
from typing import Any
import sys


if getattr(sys, "frozen", False):
    APP_FOLDER = Path(sys.executable).resolve().parent
else:
    APP_FOLDER = Path(__file__).resolve().parent


HISTORY_FILE = APP_FOLDER / "file_organizer_history.json"
CONFIG_FILE = APP_FOLDER / "file_organizer_config.json"
DEFAULT_CATEGORY = "Other"


# ============================================================
# CONFIGURATION
# ============================================================

def validate_config(config: Any) -> bool:
    if not isinstance(config, dict):
        print("Configuration must be a dictionary.")
        return False

    if "settings" not in config:
        print("Configuration is missing 'settings'.")
        return False

    if "categories" not in config:
        print("Configuration is missing 'categories'.")
        return False

    settings = config["settings"]
    categories = config["categories"]

    if not isinstance(settings, dict):
        print("'settings' must be a dictionary.")
        return False

    if not isinstance(categories, dict):
        print("'categories' must be a dictionary.")
        return False

    excluded_folders = settings.get("excluded_folders", [])
    excluded_files = settings.get("excluded_files", [])

    if not isinstance(excluded_folders, list):
        print("'excluded_folders' must be a list.")
        return False

    if not isinstance(excluded_files, list):
        print("'excluded_files' must be a list.")
        return False

    seen_extensions: set[str] = set()

    for category, extensions in categories.items():

        if not isinstance(category, str):
            print("Category names must be text.")
            return False

        if not category.strip():
            print("Category names cannot be empty.")
            return False

        if not isinstance(extensions, list):
            print(
                f"Category '{category}' must contain "
                f"a list of extensions."
            )
            return False

        for extension in extensions:

            if not isinstance(extension, str):
                print(
                    f"Extensions in '{category}' "
                    f"must be text."
                )
                return False

            extension = extension.strip().lower()

            if not extension:
                print(
                    f"Category '{category}' contains "
                    f"an empty extension."
                )
                return False

            if not extension.startswith("."):
                print(
                    f"Invalid extension '{extension}' "
                    f"in '{category}'."
                )
                print("Extensions must begin with a period.")
                return False

            if extension in seen_extensions:
                print(
                    f"Duplicate extension found: "
                    f"{extension}"
                )
                return False

            seen_extensions.add(extension)

    for folder in excluded_folders:
        if not isinstance(folder, str):
            print("Excluded folder names must be text.")
            return False

        if not folder.strip():
            print("Excluded folder names cannot be empty.")
            return False

    for filename in excluded_files:
        if not isinstance(filename, str):
            print("Excluded file names must be text.")
            return False

        if not filename.strip():
            print("Excluded file names cannot be empty.")
            return False

    return True


def load_config() -> dict[str, Any] | None:
    if not CONFIG_FILE.exists():
        print("Configuration file not found.")
        return None

    try:
        with open(
            CONFIG_FILE,
            "r",
            encoding="utf-8"
        ) as file:
            config = json.load(file)

        if not validate_config(config):
            print("Configuration is invalid.")
            return None

        # Normalize category extensions.
        for category, extensions in config["categories"].items():
            config["categories"][category] = [
                extension.strip().lower()
                for extension in extensions
            ]

        # Normalize exclusions for Windows-style
        # case-insensitive behavior.
        config["settings"]["excluded_folders"] = [
            folder.strip().lower()
            for folder in config["settings"]["excluded_folders"]
        ]

        config["settings"]["excluded_files"] = [
            filename.strip().lower()
            for filename in config["settings"]["excluded_files"]
        ]

        return config

    except json.JSONDecodeError as error:
        print(
            f"Configuration contains invalid JSON: {error}"
        )
        return None

    except OSError as error:
        print(
            f"Could not access configuration file: {error}"
        )
        return None


_config = load_config()

if _config is None:
    print(
        "Program stopped because the configuration "
        "is invalid or unavailable."
    )
    raise SystemExit

CONFIG: dict[str, Any] = _config

FILE_CATEGORIES: dict[str, list[str]] = CONFIG["categories"]

EXCLUDED_FOLDERS: set[str] = set(
    CONFIG["settings"]["excluded_folders"]
)

EXCLUDED_FILES: set[str] = set(
    CONFIG["settings"]["excluded_files"]
)


# ============================================================
# FILE DISCOVERY
# ============================================================

def get_files_to_organize(folder: Path) -> list[Path]:
    files: list[Path] = []

    for item in folder.rglob("*"):
        relative_parts = item.relative_to(folder).parts

        if not relative_parts:
            continue

        # Skip excluded folders anywhere in the
        # recursive path.
        if any(
            part.lower() in EXCLUDED_FOLDERS
            for part in relative_parts[:-1]
        ):
            continue

        # Skip explicitly excluded files.
        if (
            item.is_file()
            and item.name.lower() in EXCLUDED_FILES
        ):
            continue

        if item.is_file():
            files.append(item)

    return files


# ============================================================
# CLASSIFICATION
# ============================================================

def get_file_categories(file: Path) -> str:
    extension = file.suffix.lower()

    for category, extensions in FILE_CATEGORIES.items():
        if extension in extensions:
            return category

    return DEFAULT_CATEGORY


# ============================================================
# DESTINATION / CONFLICT HANDLING
# ============================================================

def get_unique_destination(
    destination: Path,
    reserved_destinations: set[Path]
) -> Path:

    if (
        not destination.exists()
        and destination not in reserved_destinations
    ):
        return destination

    counter = 1

    while True:
        new_name = (
            f"{destination.stem} "
            f"({counter})"
            f"{destination.suffix}"
        )

        new_destination = destination.with_name(new_name)

        if (
            not new_destination.exists()
            and new_destination not in reserved_destinations
        ):
            return new_destination

        counter += 1


def plan_file(
    file: Path,
    folder: Path,
    reserved_destinations: set[Path]
) -> tuple[str, Path, Path]:

    category = get_file_categories(file)

    destination_folder = folder / category
    destination_file = destination_folder / file.name

    destination_file = get_unique_destination(
        destination_file,
        reserved_destinations
    )

    reserved_destinations.add(destination_file)

    return (
        category,
        destination_folder,
        destination_file
    )


# ============================================================
# ORGANIZATION PLANNING
# ============================================================

def build_organization_plan(
    folder: Path
) -> list[dict[str, Any]]:

    folder = Path(folder)

    files = get_files_to_organize(folder)

    reserved_destinations: set[Path] = set()
    plan: list[dict[str, Any]] = []

    for file in files:
        (
            category,
            destination_folder,
            destination_file
        ) = plan_file(
            file,
            folder,
            reserved_destinations
        )

        plan.append({
            "source": file,
            "category": category,
            "destination_folder": destination_folder,
            "destination": destination_file
        })

    return plan


def validate_plan(
    plan: list[dict[str, Any]]
) -> bool:

    if not plan:
        print("There are no files to organize.")
        return False

    planned_destinations: set[Path] = set()

    for operation in plan:
        source = operation["source"]
        destination = operation["destination"]

        if not source.exists():
            print(
                f"Source file no longer exists: "
                f"{source}"
            )
            return False

        if not source.is_file():
            print(
                f"Source is not a file: "
                f"{source}"
            )
            return False

        if source == destination:
            print(
                f"Source and destination are identical: "
                f"{source}"
            )
            return False

        if destination.exists():
            print(
                f"Destination became occupied: "
                f"{destination}"
            )
            return False

        if destination in planned_destinations:
            print(
                f"Duplicate destination in plan: "
                f"{destination}"
            )
            return False

        planned_destinations.add(destination)

    return True


# ============================================================
# OPERATION IDs
# ============================================================

def create_operation_id() -> str:
    return datetime.now().strftime(
        "%Y%m%d-%H%M%S-%f"
    )


# ============================================================
# HISTORY
# ============================================================

def save_history(
    folder: Path,
    history: list[dict[str, Any]]
) -> bool:

    data: dict[str, Any] = {
        "version": 1,
        "operation_id": (
            history[0]["operation_id"]
            if history
            else None
        ),
        "folder": str(folder),
        "timestamp": datetime.now().isoformat(
            timespec="seconds"
        ),
        "operations": []
    }

    for operation in history:
        data["operations"].append({
            "operation_id": operation["operation_id"],
            "original": str(operation["original"]),
            "destination": str(operation["destination"]),
            "category": operation["category"],
        })

    try:
        with open(
            HISTORY_FILE,
            "w",
            encoding="utf-8"
        ) as file:
            json.dump(
                data,
                file,
                indent=4
            )

        print(
            f"\nHistory saved to "
            f"{HISTORY_FILE}"
        )

        return True

    except OSError as error:
        print(
            f"Could not save history: {error}"
        )
        return False


def load_history() -> list[dict[str, Any]] | None:
    if not HISTORY_FILE.exists():
        print("No saved history found.")
        return None

    try:
        with open(
            HISTORY_FILE,
            "r",
            encoding="utf-8"
        ) as file:
            data = json.load(file)

        if not isinstance(data, dict):
            print("Saved history has an invalid format.")
            return None

        if "operations" not in data:
            print("Saved history is missing 'operations'.")
            return None

        if not isinstance(data["operations"], list):
            print("'operations' in history must be a list.")
            return None

        history: list[dict[str, Any]] = []

        for operation in data["operations"]:

            if not isinstance(operation, dict):
                print(
                    "History contains an invalid operation."
                )
                return None

            required_fields = {
                "operation_id",
                "original",
                "destination",
                "category"
            }

            if not required_fields.issubset(operation):
                print(
                    "History operation is missing "
                    "required information."
                )
                return None

            history.append({
                "operation_id": operation["operation_id"],
                "original": Path(
                    operation["original"]
                ),
                "destination": Path(
                    operation["destination"]
                ),
                "category": operation["category"]
            })

        print("\nSaved history loaded.")

        if "folder" in data:
            print(f"Folder: {data['folder']}")

        if "timestamp" in data:
            print(f"Time: {data['timestamp']}")

        print(
            f"Operations: {len(history)}"
        )

        return history

    except json.JSONDecodeError as error:
        print(
            f"History contains invalid JSON: {error}"
        )
        return None

    except (OSError, TypeError, KeyError) as error:
        print(
            f"Could not load history: {error}"
        )
        return None


def validate_history(
    history: list[dict[str, Any]]
) -> bool:

    if not history:
        print(
            "There is no history to validate."
        )
        return False

    valid = True

    print("\nValidating history...")
    print("-" * 60)

    for operation in history:
        original = operation["original"]
        destination = operation["destination"]

        if not destination.exists():
            print(
                f"Missing destination: "
                f"{destination}"
            )
            valid = False

        elif original.exists():
            print(
                f"Original already exists: "
                f"{original}"
            )
            valid = False

    return valid


# ============================================================
# EXECUTION
# ============================================================

def execute_organization_plan(
    plan: list[dict[str, Any]]
) -> list[dict[str, Any]] | None:

    if not validate_plan(plan):
        print(
            "Organization cancelled "
            "because the plan was invalid."
        )
        return None

    operation_id = create_operation_id()

    print(
        "\nExecuting organization plan..."
    )
    print(
        f"Operation ID: {operation_id}"
    )
    print("-" * 60)

    moved_count = 0
    failed_count = 0

    move_history: list[dict[str, Any]] = []

    for operation in plan:
        file = operation["source"]
        category = operation["category"]
        destination_folder = operation[
            "destination_folder"
        ]
        destination_file = operation["destination"]

        try:
            destination_folder.mkdir(
                exist_ok=True
            )

            shutil.move(
                str(file),
                str(destination_file)
            )

            move_history.append({
                "operation_id": operation_id,
                "original": file,
                "destination": destination_file,
                "category": category
            })

            moved_count += 1

            if destination_file.name != file.name:
                print(
                    f"Moved: {file.name} -> "
                    f"{destination_file.name} "
                    f"(renamed)"
                )
            else:
                print(
                    f"Moved: {file.name} -> "
                    f"{destination_file.name}"
                )

        except OSError as error:
            failed_count += 1

            print(
                f"Could not move "
                f"{file.name}: {error}"
            )

    print("\nOrganization complete.")
    print(f"Files found: {len(plan)}")
    print(f"Files moved: {moved_count}")
    print(f"Files failed: {failed_count}")

    return move_history


def organize_folder(
    folder_path: Path
) -> list[dict[str, Any]] | None:

    folder = Path(folder_path)

    if not folder.exists():
        print(
            "This folder does not exist."
        )
        return None

    if not folder.is_dir():
        print(
            "This path is not a folder."
        )
        return None

    print(
        f"\nPreparing organization: "
        f"{folder}"
    )
    print("-" * 60)

    plan = build_organization_plan(
        folder
    )

    if not plan:
        print(
            "There are no files to organize."
        )
        return None

    return execute_organization_plan(
        plan
    )


# ============================================================
# UNDO
# ============================================================

def undo_moves(
    history: list[dict[str, Any]]
) -> tuple[int, int]:

    if not history:
        print(
            "There are no moves to undo."
        )
        return 0, 0

    print("\nUndoing last organization...")
    print("-" * 60)

    undone_count = 0
    failed_count = 0

    for operation in reversed(history):
        original = operation["original"]
        destination = operation["destination"]

        try:
            if not destination.exists():
                print(
                    f"Could not undo: "
                    f"{destination.name} "
                    f"no longer exists."
                )
                failed_count += 1
                continue

            if original.exists():
                print(
                    f"Could not undo: "
                    f"{original.name} "
                    f"already exists."
                )
                failed_count += 1
                continue

            shutil.move(
                str(destination),
                str(original)
            )

            print(
                f"Restored: "
                f"{destination.name} -> "
                f"{original}"
            )

            undone_count += 1

        except OSError as error:
            failed_count += 1

            print(
                f"Could not undo "
                f"{destination.name}: {error}"
            )

    print("\nUndo complete.")
    print(
        f"Files in history: "
        f"{len(history)}"
    )
    print(
        f"Files restored: "
        f"{undone_count}"
    )
    print(
        f"Files failed: "
        f"{failed_count}"
    )

    return undone_count, failed_count