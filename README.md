# File Organizer

A configurable Windows file-organization utility built with Python.

File Organizer scans a selected folder, identifies files by extension, builds a complete organization plan, and safely moves files into categorized folders. It supports recursive scanning, configurable categories, duplicate-name protection, operation validation, persistent history, and undo functionality.

The project was built from the ground up as a learning project while developing practical Python, file-system automation, GUI, debugging, and software architecture skills.

---

## Features

- **Automatic file classification**
    
    - Images
        
    - Documents
        
    - Spreadsheets
        
    - Presentations
        
    - Fonts
        
    - Videos
        
    - Music
        
    - Archives
        
    - Programs
        
    - Code
        
    - Other
        
- **Recursive folder scanning**
    
    - Searches through subfolders for files to organize.
        
- **Configurable file categories**
    
    - File extensions are controlled through `file_organizer_config.json`.
        
    - Categories can be modified without changing the Python source code.
        
- **Preview mode**
    
    - Shows where files will be moved before anything is changed.
        
- **Safe organization planning**
    
    - The application builds a complete plan before executing file operations.
        
    - The plan is validated before files are moved.
        
- **Duplicate filename protection**
    
    - Existing files are never blindly overwritten.
        
    - Conflicting names are automatically changed:
        
        - `photo.png`
            
        - `photo (1).png`
            
        - `photo (2).png`
            
- **Recursive exclusion system**
    
    - Specific folders and files can be excluded through the configuration file.
        
- **Error handling**
    
    - Individual file failures are reported without unnecessarily stopping the entire operation.
        
- **Operation history**
    
    - Successful file movements are recorded with their original and destination paths.
        
- **Undo**
    
    - The most recent organization operation can be reversed when the recorded file state is still valid.
        
- **Persistent history**
    
    - Operation information can be saved to JSON for later use.
        
- **Windows GUI**
    
    - Folder selection
        
    - Preview
        
    - Organize
        
    - Undo
        
    - Clear results
        
    - Status feedback
        
    - Scrollable results
        
- **Command-line interface**
    
    - The original terminal interface is still available alongside the GUI.
        
- **Standalone executable**
    
    - The application can be packaged as a Windows `.exe` using PyInstaller.
        

---

## Example

Before organization:

```text
Downloads/
├── photo.png
├── resume.pdf
├── spreadsheet.xlsx
├── song.mp3
├── video.mp4
├── game.zip
└── script.py
```

After organization:

```text
Downloads/
├── Images/
│   └── photo.png
├── Documents/
│   └── resume.pdf
├── Spreadsheets/
│   └── spreadsheet.xlsx
├── Music/
│   └── song.mp3
├── Videos/
│   └── video.mp4
├── Archives/
│   └── game.zip
└── Code/
    └── script.py
```

---

## How It Works

The application is built around a separation between planning and execution.

```text
Folder
  ↓
File Discovery
  ↓
File Classification
  ↓
Destination Planning
  ↓
Conflict Detection
  ↓
Complete Organization Plan
  ↓
Plan Validation
  ↓
File Movement
  ↓
Operation History
  ↓
Undo
```

This architecture allows the GUI and command-line interface to use the same underlying organization engine.

---

## Project Structure

```text
File Organizer/
│
├── organizer_engine.py
│   └── Core file organization engine
│
├── gui.py
│   └── Windows graphical interface
│
├── main.py
│   └── Command-line interface
│
├── file_organizer_config.json
│   └── File categories and settings
│
└── README.md
    └── Project documentation
```

---

## Configuration

File categories are controlled through:

```text
file_organizer_config.json
```

Example:

```json
{
    "settings": {
        "excluded_folders": [
            "Images",
            "Documents"
        ],
        "excluded_files": [
            "file_organizer_config.json",
        ]
    },

    "categories": {
        "Images": [
            ".jpg",
            ".jpeg",
            ".png",
            ".gif"
        ],

        "Documents": [
            ".pdf",
            ".docx",
            ".txt"
        ]
    }
}
```

This allows the organizer to be customized without modifying the source code.

---

## Safety Features

Because the application modifies the user's filesystem, safety was treated as a core requirement rather than an afterthought.

The organizer:

1. Builds a complete plan before moving files.
    
2. Validates the plan before execution.
    
3. Detects destination conflicts.
    
4. Avoids blindly overwriting files.
    
5. Supports configurable exclusions.
    
6. Records successful file movements.
    
7. Validates recorded history before attempting Undo.
    
8. Handles individual movement failures without unnecessarily terminating the entire operation.
    

The Preview function is intended to let users inspect the planned operation before committing changes.

---

## Technology

The project was built using:

- **Python**
    
- `pathlib`
    
- `shutil`
    
- `json`
    
- `datetime`
    
- `tkinter`
    
- PyInstaller
    

### Python Concepts Practiced

This project was also used as a practical learning exercise covering:

- Functions
    
- Dictionaries
    
- Lists
    
- Sets
    
- Loops
    
- Conditional logic
    
- Exception handling
    
- File and directory manipulation
    
- `pathlib`
    
- JSON serialization and deserialization
    
- Configuration management
    
- State management
    
- GUI programming
    
- Event-driven programming
    
- Modular program architecture
    
- Type hints
    
- Debugging
    
- Application packaging
    

---

## Development Approach

The project was intentionally developed incrementally rather than beginning with a finished application.

The development path was approximately:

```text
File scanning
      ↓
Extension classification
      ↓
Destination planning
      ↓
File movement
      ↓
Duplicate handling
      ↓
Error handling
      ↓
Statistics
      ↓
Undo
      ↓
Persistent history
      ↓
Configuration
      ↓
Recursive scanning
      ↓
Validation
      ↓
GUI
      ↓
Executable packaging
```

Each stage introduced a new programming or software-engineering concept while extending the usefulness of the application.

---

## Version 1.0

**Current Status: Complete**

File Organizer v1.0 represents the first complete release of the project, including:

- Functional file organization engine
    
- Recursive scanning
    
- Configurable categories
    
- Exclusion rules
    
- Duplicate protection
    
- Plan validation
    
- Error handling
    
- Operation history
    
- Undo support
    
- Windows GUI
    
- Command-line interface
    
- Standalone Windows executable
    

---

## Future Ideas

Potential future improvements include:

- Multiple saved organization profiles
    
- More advanced conflict-resolution modes
    
- Full multi-operation history
    
- Scheduled automatic organization
    
- File type detection beyond extensions
    
- File-size and date-based rules
    
- Custom user-defined sorting rules
    
- Drag-and-drop support
    
- Dark/light interface themes
    
- Installer packaging
    
- Improved logging and diagnostics
    
- Background organization mode
    
- More advanced file analysis
    

These features are intentionally outside the scope of the current v1.0 release.

---

## What I Learned

Building File Organizer taught me that writing a program is more than making the code work once.

The project required thinking about:

- What happens when input is invalid?
    
- What happens when a destination already exists?
    
- What happens when a file cannot be moved?
    
- What happens when the filesystem changes after a preview?
    
- What information needs to be remembered?
    
- How can an operation be reversed safely?
    
- How should the program separate its engine from its interface?
    
- How can configuration be changed without modifying source code?
    
- How can a Python project become a usable Windows application?
    

The project ultimately became a practical introduction to building software as a collection of cooperating components rather than as one large script.

---

## License

This project is currently intended as a personal learning and portfolio project.