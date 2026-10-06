import tkinter as tk
from tkinter import filedialog, messagebox
from pathlib import Path

from organizer_engine import (
    build_organization_plan,
    execute_organization_plan,
    save_history,
    validate_plan,
    undo_moves,
    validate_history
)


# -----------------------------
# Application State
# -----------------------------

last_history = None
last_plan = None
last_plan_folder = None


# -----------------------------
# Helper Functions
# -----------------------------

def get_selected_folder():
    folder_text = folder_entry.get().strip()

    if not folder_text:
        messagebox.showerror(
            "No Folder",
            "Please select a folder first."
        )
        return None

    folder = Path(folder_text)

    if not folder.exists():
        messagebox.showerror(
            "Invalid Folder",
            "The selected folder does not exist."
        )
        return None

    if not folder.is_dir():
        messagebox.showerror(
            "Invalid Folder",
            "The selected path is not a folder."
        )
        return None

    return folder


def clear_plan():
    global last_plan, last_plan_folder

    last_plan = None
    last_plan_folder = None

    organizer_button.config(state="disabled")


# -----------------------------
# Preview
# -----------------------------

def preview():
    global last_plan, last_plan_folder

    status_text.set("Building preview...")

    folder = get_selected_folder()

    if folder is None:
        status_text.set("Invalid folder.")
        clear_plan()
        return

    folder = folder.resolve()

    plan = build_organization_plan(folder)

    results.delete("1.0", tk.END)

    if not plan:
        results.insert(
            tk.END,
            "No files found.\n"
        )

        status_text.set("No files found.")
        clear_plan()
        return

    last_plan = plan
    last_plan_folder = folder

    for operation in plan:
        source = operation["source"]
        category = operation["category"]
        destination = operation["destination"]

        results.insert(
            tk.END,
            f"{source.name}\n"
            f"    Category: {category}\n"
            f"    Destination: {destination}\n\n"
        )

    category_counts = {}

    for planned_operation in plan:
        category = planned_operation["category"]

        if category not in category_counts:
            category_counts[category] = 0

        category_counts[category] += 1

    results.insert(
        tk.END,
        "\n" + "=" * 60 + "\n"
    )

    results.insert(
        tk.END,
        "Summary\n"
    )

    results.insert(
        tk.END,
        "=" * 60 + "\n"
    )

    for category, count in category_counts.items():
        results.insert(
            tk.END,
            f"{category}: {count}\n"
        )

    organizer_button.config(state="normal")

    status_text.set("Preview ready.")


# -----------------------------
# Clear
# -----------------------------

def clear_results():
    results.delete("1.0", tk.END)

    clear_plan()

    status_text.set("Ready.")


# -----------------------------
# Organize
# -----------------------------

def organize():
    global last_history

    status_text.set("Preparing organization...")

    folder = get_selected_folder()

    if folder is None:
        status_text.set("Invalid folder.")
        return

    folder = folder.resolve()

    if last_plan is None:
        messagebox.showinfo(
            "Preview Required",
            "Please preview the folder before organizing."
        )
        status_text.set("Preview required.")
        return

    if last_plan_folder != folder:
        messagebox.showerror(
            "Plan Changed",
            "The selected folder changed after the preview was created.\n\n"
            "Please preview the new folder before organizing."
        )

        clear_plan()
        status_text.set("Plan is no longer valid.")
        return

    if not validate_plan(last_plan):
        messagebox.showerror(
            "Plan Changed",
            "The folder changed after the preview was created.\n\n"
            "Please preview the folder again before organizing."
        )

        clear_plan()
        status_text.set("Plan is no longer valid.")
        return

    confirmation = messagebox.askyesno(
        "Confirm Organization",
        f"{len(last_plan)} files are ready to be organized.\n\n"
        "Do you want to continue?"
    )

    if not confirmation:
        status_text.set("Organization cancelled.")
        return

    status_text.set("Organizing files...")

    history = execute_organization_plan(last_plan)

    organizer_button.config(state="disabled")

    if history:
        save_history(folder, history)

        last_history = history

        results.delete("1.0", tk.END)

        results.insert(
            tk.END,
            "Organization Complete.\n\n"
        )

        results.insert(
            tk.END,
            f"Successfully moved: {len(history)} files.\n\n"
        )

        results.insert(
            tk.END,
            "Undo is available for this operation."
        )

        clear_plan()

        undo_button.config(state="normal")

        status_text.set("Organization complete.")

    else:
        results.delete("1.0", tk.END)

        results.insert(
            tk.END,
            "No files were moved."
        )

        status_text.set("No files were moved.")


# -----------------------------
# Undo
# -----------------------------

def undo():
    global last_history

    if not last_history:
        messagebox.showinfo(
            "Nothing to Undo",
            "There is no organization to undo in this session."
        )
        return

    if not validate_history(last_history):
        messagebox.showerror(
            "Undo Cancelled",
            "The previous organization can no longer be safely undone."
        )
        return

    confirmation = messagebox.askyesno(
        "Confirm Undo",
        "Undo the last organization?"
    )

    if not confirmation:
        return

    status_text.set("Undoing organization...")

    restored_count, failed_count = undo_moves(last_history)

    results.delete("1.0", tk.END)

    if failed_count == 0:
        results.insert(
            tk.END,
            "The last organization was completely undone.\n\n"
            f"Files restored: {restored_count}"
        )

        last_history = None
        undo_button.config(state="disabled")
        status_text.set("Undo complete.")

    else:
        results.insert(
            tk.END,
            "Undo was only partially completed.\n\n"
            f"Files restored: {restored_count}\n"
            f"Files failed: {failed_count}\n\n"
            "The remaining history has been kept."
        )

        status_text.set("Undo partially completed.")


# -----------------------------
# Folder Selection
# -----------------------------

def choose_folder():
    folder = filedialog.askdirectory()

    if folder:
        folder_entry.delete(0, tk.END)
        folder_entry.insert(0, folder)

        clear_plan()

        status_text.set("Folder selected.")


# -----------------------------
# Main Window
# -----------------------------

window = tk.Tk()

window.title("File Organizer")
window.geometry("800x600")


title_label = tk.Label(
    window,
    text="File Organizer",
    font=("Segoe UI", 20, "bold")
)
title_label.pack(
    pady=(15, 5)
)


subtitle_label = tk.Label(
    window,
    text="Organize your files safely and quickly",
    font=("Segoe UI", 10)
)
subtitle_label.pack(
    pady=(0, 15)
)


folder_label = tk.Label(
    window,
    text="Folder to organize:",
    font=("Segoe UI", 10, "bold")
)
folder_label.pack(
    anchor="w",
    padx=20
)


folder_frame = tk.Frame(window)
folder_frame.pack(
    fill="x",
    padx=20,
    pady=8
)


folder_entry = tk.Entry(
    folder_frame
)
folder_entry.pack(
    side="left",
    fill="x",
    expand=True
)


browse_button = tk.Button(
    folder_frame,
    text="Browse",
    command=choose_folder
)
browse_button.pack(
    side="left",
    padx=(8, 0)
)


button_frame = tk.Frame(window)
button_frame.pack(
    pady=10
)


preview_button = tk.Button(
    button_frame,
    text="Preview",
    command=preview
)
preview_button.pack(
    side="left",
    padx=5
)


organizer_button = tk.Button(
    button_frame,
    text="Organize",
    command=organize,
    state="disabled"
)
organizer_button.pack(
    side="left",
    padx=5
)


undo_button = tk.Button(
    button_frame,
    text="Undo Last Organization",
    command=undo,
    state="disabled"
)
undo_button.pack(
    side="left",
    padx=5
)


clear_button = tk.Button(
    button_frame,
    text="Clear",
    command=clear_results
)
clear_button.pack(
    side="left",
    padx=5
)


results_frame = tk.Frame(window)
results_frame.pack(
    padx=20,
    pady=10,
    fill="both",
    expand=True
)


results = tk.Text(
    results_frame,
    width=90,
    height=25
)
results.pack(
    side="left",
    fill="both",
    expand=True
)


results_scrollbar = tk.Scrollbar(
    results_frame,
    command=results.yview
)
results_scrollbar.pack(
    side="right",
    fill="y"
)


results.config(
    yscrollcommand=results_scrollbar.set
)


status_text = tk.StringVar()
status_text.set("Ready")


status_label = tk.Label(
    window,
    textvariable=status_text,
    anchor="w"
)
status_label.pack(
    fill="x",
    padx=20,
    pady=(0, 10)
)


window.mainloop()