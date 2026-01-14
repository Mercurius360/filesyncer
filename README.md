# File Syncer
<img width="902" height="592" alt="Image" src="https://github.com/user-attachments/assets/94003917-5c27-441c-924f-f2e84653056c" />

File Syncer is a lightweight Windows GUI tool for creating file/folder links between locations (Hardlink, Symlink, Junction) using a simple “pick source folder + name the link + pick target” workflow.

It’s designed for cases where you want two apps/games/folders to reference the same underlying file/folder without manually copying data.

## Features

- Windows GUI (Tkinter)
- Runs with admin privileges (UAC)
- Create links inside a chosen **Source folder** using a user-typed **Link Name**
- Supports:
  - **Hardlink** (files only, same drive)
  - **Symlink** (files or folders)
  - **Junction** (folders only)
- Built-in log window for debugging and error messages

## How it works (workflow)

1. Select the **Source folder** (this is where the link will be created)
2. Type the **Link Name** (example: `live_streams.sii` or `profiles`)
3. Select the **Target** file/folder (this is what the link points to)
4. Choose link type and click **Create Sync**

## Requirements

- Windows 10/11
- Python 3.10+ recommended

## Run from source

```bash
python file_syncer.py
