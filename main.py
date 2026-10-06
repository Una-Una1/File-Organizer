from pathlib import Path

from organizer_engine import (
    preview_organization,
    organize_folder,
    undo_moves,
    validate_history,
    save_history
)


folder_to_scan = input("Enter folder to scan: ")

preview_organization(folder_to_scan)

choice = input(
    "\nWould you like to organize these files? (y/n): "
)

if choice.lower() == "y":
    history = organize_folder(folder_to_scan)

    if history:
        save_history(Path(folder_to_scan), history)

        undo_choice = input(
            "\nWould you like to undo this organization? (y/n): "
        )

        if undo_choice.lower() == "y":
            if validate_history(history):
                undo_moves(history)
        else:
            print("Organization kept.")

    else:
        print("No files were organized.")

else:
    print("Organization cancelled.")