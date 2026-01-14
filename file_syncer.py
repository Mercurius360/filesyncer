import os
import sys
import ctypes
import subprocess
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

APP_TITLE = "File Syncer"

def is_admin() -> bool:
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False

def relaunch_as_admin():
    # Relaunch this script with UAC prompt
    params = " ".join([f'"{arg}"' for arg in sys.argv])
    rc = ctypes.windll.shell32.ShellExecuteW(
        None, "runas", sys.executable, params, None, 1
    )
    # If rc <= 32 it failed; otherwise new process launched
    if rc <= 32:
        raise RuntimeError("Elevation (runas) failed or was cancelled.")

def path_is_dir(p: str) -> bool:
    return os.path.isdir(p)

def path_is_file(p: str) -> bool:
    return os.path.isfile(p)

def safe_join(folder: str, name: str) -> str:
    # Prevent weird absolute paths in name
    name = name.strip().strip("\\/")  # disallow leading slashes
    if not name:
        raise ValueError("Link name is empty.")
    if any(x in name for x in ['"', "<", ">", "|"]):
        raise ValueError('Link name contains invalid characters: ", <, >, |')
    # Windows also dislikes ':' in filenames except after drive letter, keep it simple:
    if ":" in name:
        raise ValueError("Link name cannot contain ':'.")
    return os.path.join(folder, name)

def run_cmd(cmd: list[str]) -> tuple[int, str]:
    # Run command and capture output
    p = subprocess.run(cmd, capture_output=True, text=True, shell=False)
    out = (p.stdout or "") + (p.stderr or "")
    return p.returncode, out.strip()

class FileLinkerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("900x560")
        self.minsize(900, 560)

        self.source_folder = tk.StringVar()
        self.link_name = tk.StringVar()
        self.target_path = tk.StringVar()
        self.link_type = tk.StringVar(value="Symlink (Auto: File/Folder)")

        self._build_ui()

    def _build_ui(self):
        pad = {"padx": 10, "pady": 8}

        header = ttk.Frame(self)
        header.pack(fill="x", **pad)

        title = ttk.Label(header, text=APP_TITLE, font=("Segoe UI", 16, "bold"))
        title.pack(side="left")

        admin_badge = "Admin: YES" if is_admin() else "Admin: NO"
        admin_lbl = ttk.Label(header, text=admin_badge)
        admin_lbl.pack(side="right")

        main = ttk.Frame(self)
        main.pack(fill="both", expand=True, **pad)

        # Source location (where link will be created)
        src_box = ttk.LabelFrame(main, text="1) Source location (where the link will be created)")
        src_box.pack(fill="x", **pad)

        src_row = ttk.Frame(src_box)
        src_row.pack(fill="x", padx=10, pady=10)

        src_entry = ttk.Entry(src_row, textvariable=self.source_folder)
        src_entry.pack(side="left", fill="x", expand=True)

        ttk.Button(src_row, text="Browse…", command=self.browse_source_folder).pack(side="left", padx=8)

        # Link name (user-provided “source name”)
        name_box = ttk.LabelFrame(main, text="2) Link name (this is what users type; include extension if syncing a file)")
        name_box.pack(fill="x", **pad)

        name_row = ttk.Frame(name_box)
        name_row.pack(fill="x", padx=10, pady=10)

        name_entry = ttk.Entry(name_row, textvariable=self.link_name)
        name_entry.pack(side="left", fill="x", expand=True)

        ttk.Label(name_row, text="Example: live_streams.sii  OR  live_streams").pack(side="left", padx=10)

        # Target (destination)
        dst_box = ttk.LabelFrame(main, text="3) Destination target (file/folder you want to sync it TO)")
        dst_box.pack(fill="x", **pad)

        dst_row = ttk.Frame(dst_box)
        dst_row.pack(fill="x", padx=10, pady=10)

        dst_entry = ttk.Entry(dst_row, textvariable=self.target_path)
        dst_entry.pack(side="left", fill="x", expand=True)

        ttk.Button(dst_row, text="Pick File…", command=self.pick_target_file).pack(side="left", padx=6)
        ttk.Button(dst_row, text="Pick Folder…", command=self.pick_target_folder).pack(side="left", padx=6)

        # Link type
        type_box = ttk.LabelFrame(main, text="4) Link type")
        type_box.pack(fill="x", **pad)

        type_row = ttk.Frame(type_box)
        type_row.pack(fill="x", padx=10, pady=10)

        choices = [
            "Symlink (Auto: File/Folder)",
            "Symlink (File)",
            "Symlink (Folder)",
            "Hardlink (File only)",
            "Junction (Folder only)",
        ]
        type_menu = ttk.Combobox(type_row, textvariable=self.link_type, values=choices, state="readonly")
        type_menu.pack(side="left")

        ttk.Label(type_row, text="Tip: Junction is often best for folders on same drive.").pack(side="left", padx=12)

        # Actions
        action_row = ttk.Frame(main)
        action_row.pack(fill="x", **pad)

        ttk.Button(action_row, text="Create Sync", command=self.create_link).pack(side="left")
        ttk.Button(action_row, text="Open Source Folder", command=self.open_source_folder).pack(side="left", padx=8)
        ttk.Button(action_row, text="Open Target Location", command=self.open_target_location).pack(side="left", padx=8)
        ttk.Button(action_row, text="Clear Log", command=self.clear_log).pack(side="right")

        # Log
        log_box = ttk.LabelFrame(main, text="Log")
        log_box.pack(fill="both", expand=True, **pad)

        self.log = tk.Text(log_box, wrap="word", height=12)
        self.log.pack(fill="both", expand=True, padx=10, pady=10)
        self.log.configure(state="disabled")

        self._log_line("Ready.")

    def _log_line(self, msg: str):
        self.log.configure(state="normal")
        self.log.insert("end", msg + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def clear_log(self):
        self.log.configure(state="normal")
        self.log.delete("1.0", "end")
        self.log.configure(state="disabled")
        self._log_line("Log cleared.")

    def browse_source_folder(self):
        folder = filedialog.askdirectory(title="Select SOURCE folder (link will be created here)")
        if folder:
            self.source_folder.set(folder)

    def pick_target_file(self):
        f = filedialog.askopenfilename(title="Select DESTINATION target file")
        if f:
            self.target_path.set(f)

    def pick_target_folder(self):
        folder = filedialog.askdirectory(title="Select DESTINATION target folder")
        if folder:
            self.target_path.set(folder)

    def open_source_folder(self):
        folder = self.source_folder.get().strip()
        if folder and os.path.isdir(folder):
            subprocess.run(["explorer", folder])
        else:
            messagebox.showerror("Error", "Source folder is not set or does not exist.")

    def open_target_location(self):
        target = self.target_path.get().strip()
        if not target:
            messagebox.showerror("Error", "Target path is not set.")
            return
        if os.path.exists(target):
            # If file, open its parent folder and select it
            if os.path.isfile(target):
                subprocess.run(["explorer", "/select,", target])
            else:
                subprocess.run(["explorer", target])
        else:
            messagebox.showerror("Error", "Target path does not exist.")

    def create_link(self):
        src_folder = self.source_folder.get().strip()
        name = self.link_name.get().strip()
        target = self.target_path.get().strip()
        mode = self.link_type.get().strip()

        try:
            if not src_folder or not os.path.isdir(src_folder):
                raise ValueError("Source folder is not set or does not exist.")

            if not target or not os.path.exists(target):
                raise ValueError("Destination target does not exist.")

            link_path = safe_join(src_folder, name)

            # If link already exists, block (keeps behavior predictable)
            if os.path.lexists(link_path):
                raise FileExistsError(f"Link path already exists: {link_path}")

            target_is_file = path_is_file(target)
            target_is_dir = path_is_dir(target)

            self._log_line(f"Creating link:")
            self._log_line(f"  Link will be created at: {link_path}")
            self._log_line(f"  Target points to:        {target}")
            self._log_line(f"  Selected type:           {mode}")

            if mode == "Hardlink (File only)":
                if not target_is_file:
                    raise ValueError("Hardlink only works with files. Pick a file target.")
                # Hardlinks must be on same volume/drive
                if os.path.splitdrive(link_path)[0].lower() != os.path.splitdrive(target)[0].lower():
                    raise ValueError("Hardlink requires link and target to be on the same drive.")
                os.link(target, link_path)
                self._log_line("✅ Hardlink created successfully.")
                return

            if mode == "Junction (Folder only)":
                if not target_is_dir:
                    raise ValueError("Junction only works with folders. Pick a folder target.")
                # mklink /J "link" "target"
                rc, out = run_cmd(["cmd", "/c", "mklink", "/J", link_path, target])
                self._log_line(out if out else f"(mklink exited {rc})")
                if rc != 0:
                    raise RuntimeError("mklink /J failed.")
                self._log_line("✅ Junction created successfully.")
                return

            # Symlink types (mklink)
            if mode in ("Symlink (File)", "Symlink (Folder)", "Symlink (Auto: File/Folder)"):
                if mode == "Symlink (File)" and not target_is_file:
                    raise ValueError("Symlink (File) selected but target is not a file.")
                if mode == "Symlink (Folder)" and not target_is_dir:
                    raise ValueError("Symlink (Folder) selected but target is not a folder.")

                # mklink:
                #   file symlink: mklink "link" "target"
                #   dir symlink:  mklink /D "link" "target"
                use_dir_flag = target_is_dir
                if mode == "Symlink (File)":
                    use_dir_flag = False
                if mode == "Symlink (Folder)":
                    use_dir_flag = True

                cmd = ["cmd", "/c", "mklink"]
                if use_dir_flag:
                    cmd.append("/D")
                cmd.extend([link_path, target])

                rc, out = run_cmd(cmd)
                self._log_line(out if out else f"(mklink exited {rc})")
                if rc != 0:
                    raise RuntimeError("mklink failed.")
                self._log_line("✅ Symlink created successfully.")
                return

            raise ValueError("Unknown link type selected.")

        except Exception as e:
            self._log_line(f"❌ Error: {e}")
            messagebox.showerror("Link Creation Failed", str(e))

def main():
    # Force admin at startup (as you requested)
    if not is_admin():
        try:
            relaunch_as_admin()
        except Exception as e:
            # User cancelled or it failed; exit cleanly
            messagebox.showerror(APP_TITLE, f"This tool requires admin privileges.\n\n{e}")
        return

    app = FileLinkerApp()
    app.mainloop()

if __name__ == "__main__":
    # Tk messagebox requires a root; if admin prompt fails, create minimal root
    try:
        main()
    except tk.TclError:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(APP_TITLE, "Failed to start the UI.")
