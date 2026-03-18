import os
import re
import sys
import ctypes
import winreg
import tkinter as tk
from tkinter import messagebox
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import requests
import zipfile
import tempfile
import subprocess
import threading
import webbrowser
from pathlib import Path

INSTALL_PATH = "C:\\ffmpeg"
BIN_PATH = "C:\\ffmpeg\\bin"
FFMPEG_EXE = "C:\\ffmpeg\\bin\\ffmpeg.exe"
MIN_VERSION_WARN = (6, 0)   # Below this: show recommendation warning
MIN_VERSION_ERROR = (4, 0)  # Below this: missing core filters, show strong warning


class FFmpegInstaller:
    def __init__(self):
        self.root = ttk.Window(themename="darkly")
        self.root.title("FFmpeg PATH Installer")
        self.root.geometry("800x600")
        self.root.resizable(True, True)

        # Set window icon (titlebar + taskbar). Path works both from source and PyInstaller exe.
        _base = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        icon_path = os.path.join(_base, "ffmpeg.ico")
        if os.path.exists(icon_path):
            self.root.iconbitmap(icon_path)

        # Center the window
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (680 // 2)
        y = (self.root.winfo_screenheight() // 2) - (620 // 2)
        self.root.geometry(f"800x600+{x}+{y}")

        self.setup_ui()

    def setup_ui(self):
        MONO = "Courier New"

        # Footer (packed first so it anchors to bottom before main_frame expands)
        footer_frame = ttk.Frame(self.root)
        footer_frame.pack(side=BOTTOM, fill=X, padx=20, pady=10)
        footer_label = ttk.Label(
            footer_frame,
            text="Made by Reactorcore",
            font=(MONO, 8),
            foreground="#6c757d",
            cursor="hand2"
        )
        footer_label.pack(side=RIGHT)
        footer_label.bind("<Button-1>", lambda e: webbrowser.open("https://reactorcore.itch.io/"))

        # Main frame
        main_frame = ttk.Frame(self.root, padding=24)
        main_frame.pack(fill=BOTH, expand=True)

        # Title
        ttk.Label(
            main_frame,
            text="🎬  FFmpeg PATH Installer  🔊",
            font=(MONO, 22, "bold"),
            anchor=CENTER
        ).pack(fill=X, pady=(0, 4))

        # Subtitle
        ttk.Label(
            main_frame,
            text="Downloads from gyan.dev  ·  Installs to C:\\ffmpeg  ·  Adds to user PATH",
            font=(MONO, 9),
            foreground="#6c757d",
            anchor=CENTER
        ).pack(fill=X, pady=(0, 10))

        ttk.Separator(main_frame, orient='horizontal').pack(fill=X, pady=(0, 14))

        # Description
        ttk.Label(
            main_frame,
            text=(
                "This tool downloads and installs FFmpeg, making it available\n"
                "to any application that needs audio or video processing."
            ),
            font=(MONO, 10),
            justify=CENTER,
            anchor=CENTER
        ).pack(fill=X, pady=(0, 10))

        ttk.Separator(main_frame, orient='horizontal').pack(fill=X, pady=(0, 12))

        # Status area
        self.status_frame = ttk.Frame(main_frame)
        self.status_frame.pack(pady=(0, 4))

        self.status_label = ttk.Label(
            self.status_frame,
            text="Ready to install FFmpeg",
            font=(MONO, 10),
            anchor=CENTER
        )
        self.status_label.pack()

        # Conflict warning label (amber, hidden until needed)
        self.conflict_label = ttk.Label(
            self.status_frame,
            text="",
            font=(MONO, 9),
            foreground="#FFD43B",
            anchor=CENTER
        )
        self.conflict_label.pack()

        # Progress bar
        self.progress = ttk.Progressbar(
            main_frame,
            mode='indeterminate',
            style="success.Horizontal.TProgressbar"
        )
        self.progress.pack(fill=X, pady=(8, 20))

        # Buttons — centered via outer/inner frame pair
        btn_outer = ttk.Frame(main_frame)
        btn_outer.pack(pady=(0, 20))
        btn_inner = ttk.Frame(btn_outer)
        btn_inner.pack()

        self.install_btn = ttk.Button(
            btn_inner,
            text="Install FFmpeg to PATH",
            command=self.start_installation,
            style="success.TButton",
            width=26
        )
        self.install_btn.pack(side=LEFT, padx=(0, 8))

        self.check_btn = ttk.Button(
            btn_inner,
            text="Check Installation",
            command=self.check_installation,
            style="info.TButton",
            width=21
        )
        self.check_btn.pack(side=LEFT, padx=(0, 8))

        self.uninstall_btn = ttk.Button(
            btn_inner,
            text="Uninstall",
            command=self.uninstall_ffmpeg,
            style="danger.TButton",
            width=16
        )
        self.uninstall_btn.pack(side=LEFT)

        # Instructions frame
        instructions_frame = ttk.LabelFrame(main_frame, text="Instructions")
        instructions_frame.pack(fill=BOTH, expand=True, pady=(4, 0))
        instructions_inner = ttk.Frame(instructions_frame, padding=15)
        instructions_inner.pack(fill=BOTH, expand=True)

        ttk.Label(
            instructions_inner,
            text=(
                "1. Click 'Install FFmpeg to PATH' to download and install FFmpeg.\n"
                "2. The installation adds C:\\ffmpeg\\bin to the front of your user PATH.\n"
                "3. Use 'Check Installation' to verify the installation."
            ),
            font=(MONO, 10),
            justify=LEFT
        ).pack(anchor=W)

    def update_status(self, message, progress_mode=None):
        """Update status label and progress bar"""
        self.status_label.config(text=message)
        if progress_mode == "start":
            self.progress.start()
        elif progress_mode == "stop":
            self.progress.stop()
        self.root.update()

    def set_conflict_warning(self, message):
        """Show or clear the persistent amber conflict warning label."""
        self.conflict_label.config(text=message)
        self.root.update()

    # ── Registry helpers ──────────────────────────────────────────────────────

    def _read_registry_path(self):
        """Read HKCU\\Environment\\PATH via winreg. Returns '' if key absent."""
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment", 0, winreg.KEY_READ)
            value, _ = winreg.QueryValueEx(key, "PATH")
            winreg.CloseKey(key)
            return value
        except FileNotFoundError:
            return ""
        except Exception as e:
            raise Exception(f"Cannot read registry PATH: {e}")

    def _write_registry_path(self, new_path):
        """Write HKCU\\Environment\\PATH as REG_EXPAND_SZ and broadcast WM_SETTINGCHANGE."""
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment", 0, winreg.KEY_WRITE)
            winreg.SetValueEx(key, "PATH", 0, winreg.REG_EXPAND_SZ, new_path)
            winreg.CloseKey(key)
        except Exception as e:
            raise Exception(f"Cannot write registry PATH: {e}")
        # Notify running processes so the new PATH takes effect without a full reboot
        ctypes.windll.user32.SendMessageTimeoutW(0xFFFF, 0x001A, 0, "Environment", 2, 5000, None)

    # ── Version parsing ───────────────────────────────────────────────────────

    def _parse_ffmpeg_version(self, version_output):
        """
        Parse (major, minor) from ffmpeg -version output.
        Returns (major, minor) tuple or None if unparseable.
        Example first line: 'ffmpeg version 7.1-essentials_build-www.gyan.dev ...'
        """
        first_line = version_output.split('\n')[0]
        match = re.search(r'version\s+(\d+)\.(\d+)', first_line)
        if match:
            return (int(match.group(1)), int(match.group(2)))
        return None

    def _version_warning(self, ver):
        """
        Return a warning string if ver is below minimum recommendations, else ''.
        ver is (major, minor) tuple or None.
        """
        if ver is None:
            return ""
        if ver < MIN_VERSION_ERROR:
            return (
                f"\u26a0 Version {ver[0]}.{ver[1]} is too old and may not work correctly\n"
                "with modern applications.\n\n"
                "Please click Uninstall, then Install again to get the current version."
            )
        if ver < MIN_VERSION_WARN:
            return (
                f"Note: Version {ver[0]}.{ver[1]} may be missing some features.\n"
                "Version 6.0 or newer is recommended."
            )
        return ""

    # ── Conflict detection ────────────────────────────────────────────────────

    def _find_other_ffmpeg_on_path(self):
        """
        Return list of ffmpeg.exe paths found via 'where ffmpeg',
        excluding C:\\ffmpeg\\bin\\ffmpeg.exe (our install).
        Non-critical — returns [] on any error.
        """
        try:
            result = subprocess.run(['where', 'ffmpeg'],
                                    capture_output=True, text=True, timeout=5)
            if result.returncode != 0:
                return []
            paths = [p.strip() for p in result.stdout.strip().split('\n') if p.strip()]
            canonical = FFMPEG_EXE.lower()
            return [p for p in paths if p.lower() != canonical]
        except Exception:
            return []

    # ── Download / extract / install ──────────────────────────────────────────

    def download_ffmpeg(self):
        """Download FFmpeg from official source"""
        try:
            self.update_status("Downloading FFmpeg...", "start")

            # FFmpeg download URL (Windows 64-bit)
            url = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"

            # Create temp directory
            temp_dir = tempfile.mkdtemp()
            zip_path = os.path.join(temp_dir, "ffmpeg.zip")

            # Download with progress
            response = requests.get(url, stream=True)
            response.raise_for_status()

            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0

            with open(zip_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            progress = (downloaded / total_size) * 100
                            self.update_status(f"Downloading FFmpeg... {progress:.1f}%")

            return zip_path, temp_dir

        except Exception as e:
            raise Exception(f"Download failed: {str(e)}")

    def extract_and_install(self, zip_path, temp_dir):
        """Extract and install FFmpeg to C:\\ffmpeg"""
        try:
            self.update_status("Extracting FFmpeg...")

            # Extract zip
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)

            # Find the extracted folder
            extracted_folders = [f for f in os.listdir(temp_dir)
                                  if os.path.isdir(os.path.join(temp_dir, f))]
            if not extracted_folders:
                raise Exception("No folder found in extracted zip")

            ffmpeg_folder = os.path.join(temp_dir, extracted_folders[0])
            bin_folder = os.path.join(ffmpeg_folder, "bin")

            if not os.path.exists(bin_folder):
                raise Exception("FFmpeg bin folder not found in extracted files")

            # Install to C:\\ffmpeg
            if os.path.exists(INSTALL_PATH):
                import shutil
                shutil.rmtree(INSTALL_PATH)

            self.update_status("Installing FFmpeg to C:\\ffmpeg...")
            import shutil
            shutil.copytree(ffmpeg_folder, INSTALL_PATH)

            return INSTALL_PATH

        except PermissionError:
            raise Exception(
                "Permission denied writing to C:\\ffmpeg.\n"
                "Try running this installer as Administrator."
            )
        except Exception as e:
            raise Exception(f"Installation failed: {str(e)}")

    def add_to_path(self, install_path):
        """
        Add C:\\ffmpeg\\bin to the front of HKCU\\Environment\\PATH via winreg.
        Prepending ensures our FFmpeg takes priority over any pre-existing version.
        Removes duplicate entries if present (idempotent on repeated installs).
        """
        self.update_status("Adding FFmpeg to PATH...")

        bin_path = os.path.join(install_path, "bin")  # C:\ffmpeg\bin

        current_path = self._read_registry_path()

        # Split, strip blanks, remove any pre-existing entries for our bin_path
        parts = [p for p in current_path.split(';') if p.strip()]
        parts = [p for p in parts if p.lower() != bin_path.lower()]

        # Prepend so our install takes priority
        new_path = ';'.join([bin_path] + parts)

        self._write_registry_path(new_path)  # raises on failure

    # ── Main actions ──────────────────────────────────────────────────────────

    def start_installation(self):
        """Start the installation process in a separate thread"""
        def install():
            try:
                self.install_btn.config(state="disabled")
                self.check_btn.config(state="disabled")
                self.uninstall_btn.config(state="disabled")
                self.set_conflict_warning("")

                # Download
                zip_path, temp_dir = self.download_ffmpeg()

                # Extract and install
                install_path = self.extract_and_install(zip_path, temp_dir)

                # Add to PATH (prepend, idempotent)
                self.add_to_path(install_path)

                # Cleanup temp files
                import shutil
                shutil.rmtree(temp_dir, ignore_errors=True)

                # ── Post-install verification ──────────────────────────────
                self.update_status("Verifying installation...")

                # Verify the installed binary directly (full path, not PATH resolution)
                if not os.path.exists(FFMPEG_EXE):
                    raise Exception(
                        "FFmpeg could not be written to C:\\ffmpeg\\bin.\n\n"
                        "Try right-clicking the installer and choosing 'Run as administrator'."
                    )

                ver_result = subprocess.run(
                    [FFMPEG_EXE, '-version'],
                    capture_output=True, text=True, timeout=10
                )
                if ver_result.returncode != 0:
                    raise Exception(
                        "FFmpeg was installed but failed to start correctly.\n\n"
                        "The download may have been incomplete — please try installing again."
                    )

                installed_ver = self._parse_ffmpeg_version(ver_result.stdout)
                ver_str = f"{installed_ver[0]}.{installed_ver[1]}" if installed_ver else "unknown"
                ver_warn = self._version_warning(installed_ver)

                # Scan for conflicting older FFmpeg elsewhere on PATH
                conflicts = self._find_other_ffmpeg_on_path()
                conflict_warn = ""
                conflict_short = ""
                if conflicts:
                    conflict_list = "\n".join(f"  \u2022 {p}" for p in conflicts)
                    conflict_warn = (
                        f"\n\n\u26a0 Another FFmpeg was found on your computer:\n"
                        f"{conflict_list}\n\n"
                        "FFmpeg has been installed and set as the priority version.\n"
                        "If your applications still have issues, try restarting them.\n"
                        "If problems persist, the other installation may need to be removed."
                    )
                    conflict_short = f"\u26a0 Another FFmpeg found at {conflicts[0]}"
                    self.set_conflict_warning(conflict_short)

                # Build success message
                msg_parts = [
                    f"FFmpeg {ver_str} installed successfully to C:\\ffmpeg\\bin.",
                ]
                if ver_warn:
                    msg_parts.append(f"\n{ver_warn}")
                if conflict_warn:
                    msg_parts.append(conflict_warn)
                msg_parts.append("\nRestart your applications to apply.")

                self.update_status(f"FFmpeg {ver_str} installed successfully!", "stop")
                messagebox.showinfo("Success", "\n".join(msg_parts))

            except Exception as e:
                self.update_status(f"Installation failed: {str(e)}", "stop")
                messagebox.showerror("Error", f"Installation failed:\n{str(e)}")

            finally:
                self.install_btn.config(state="normal")
                self.check_btn.config(state="normal")
                self.uninstall_btn.config(state="normal")

        threading.Thread(target=install, daemon=True).start()

    def check_installation(self):
        """
        Check FFmpeg installation status.
        Check A: verify C:\\ffmpeg\\bin\\ffmpeg.exe directly (authoritative).
        Check B: check what 'ffmpeg' resolves to on PATH (may differ).
        Report both and flag any conflict.
        """
        self.set_conflict_warning("")
        lines = []
        conflict = False

        # ── Check A: direct binary ────────────────────────────────────────────
        installed_ver = None
        if os.path.exists(FFMPEG_EXE):
            try:
                result = subprocess.run([FFMPEG_EXE, '-version'],
                                        capture_output=True, text=True, timeout=10)
                installed_ver = self._parse_ffmpeg_version(result.stdout)
                ver_str = f"{installed_ver[0]}.{installed_ver[1]}" if installed_ver else "unknown"
                lines.append(f"\u2705 FFmpeg {ver_str} is installed and ready to use.")
                lines.append(f"   Location: {FFMPEG_EXE}")
                ver_warn = self._version_warning(installed_ver)
                if ver_warn:
                    lines.append("")
                    lines.append(ver_warn)
            except Exception as e:
                lines.append(f"\u26a0 FFmpeg is installed but could not be started. ({e})")
        else:
            lines.append("\u274c FFmpeg is not installed.")
            lines.append("Click 'Install FFmpeg to PATH' to install it.")

        lines.append("")

        # ── Check B: PATH resolution ──────────────────────────────────────────
        try:
            where_result = subprocess.run(['where', 'ffmpeg'],
                                          capture_output=True, text=True, timeout=5)
            resolved_paths = [p.strip() for p in where_result.stdout.strip().split('\n')
                               if p.strip()] if where_result.returncode == 0 else []
            first_resolved = resolved_paths[0] if resolved_paths else None
        except Exception:
            first_resolved = None
            resolved_paths = []

        try:
            path_result = subprocess.run(['ffmpeg', '-version'],
                                         capture_output=True, text=True, timeout=10)
            if path_result.returncode == 0:
                # Conflict: Windows is running a different FFmpeg than our install
                if first_resolved and first_resolved.lower() != FFMPEG_EXE.lower():
                    conflict = True
                    path_ver = self._parse_ffmpeg_version(path_result.stdout)
                    path_ver_str = f"{path_ver[0]}.{path_ver[1]}" if path_ver else "unknown"
                    lines.append(
                        f"\u26a0 Windows is currently using a different FFmpeg\n"
                        f"   from another program on your computer:\n"
                        f"   {first_resolved}  (version {path_ver_str})\n\n"
                        "This may cause issues with your applications.\n"
                        "Try restarting them — if problems persist, the other\n"
                        "FFmpeg installation may need to be removed."
                    )
            else:
                if os.path.exists(FFMPEG_EXE):
                    lines.append(
                        "FFmpeg is installed but not yet active in this session.\n"
                        "Restart Script-to-Voice Generator to apply."
                    )
        except FileNotFoundError:
            if os.path.exists(FFMPEG_EXE):
                lines.append(
                    "FFmpeg is installed but not yet active in this session.\n"
                    "Restart your applications to apply."
                )
            # else: already reported not installed above
        except subprocess.TimeoutExpired:
            lines.append("Could not check FFmpeg status — the check timed out.")
        except Exception as e:
            lines.append(f"Could not check FFmpeg status. ({e})")

        msg = "\n".join(lines)

        if conflict:
            self.update_status("Check complete — another FFmpeg may interfere (see details)")
            self.set_conflict_warning(f"\u26a0 Another FFmpeg found: {first_resolved}")
            messagebox.showwarning("Installation Check", msg)
        elif os.path.exists(FFMPEG_EXE):
            self.update_status("Check complete — FFmpeg is installed correctly")
            messagebox.showinfo("Installation Check", msg)
        else:
            self.update_status("Check complete — FFmpeg is not installed")
            messagebox.showwarning("Installation Check", msg)

    def uninstall_ffmpeg(self):
        """Uninstall FFmpeg: remove C:\\ffmpeg and remove C:\\ffmpeg\\bin from user PATH."""
        confirmed = messagebox.askyesno(
            "Uninstall FFmpeg",
            "Are you sure you want to uninstall FFmpeg?\n\n"
            "This will remove FFmpeg from C:\\ffmpeg and update your user PATH."
        )
        if not confirmed:
            return

        self.update_status("Uninstalling FFmpeg...", "start")
        path_error = None

        # Remove C:\ffmpeg\bin from user PATH
        try:
            current_path = self._read_registry_path()
            parts = [p for p in current_path.split(';') if p.strip()]
            new_parts = [p for p in parts if p.lower() != BIN_PATH.lower()]
            if len(new_parts) != len(parts):
                self._write_registry_path(';'.join(new_parts))
        except Exception as e:
            path_error = str(e)

        # Remove C:\ffmpeg directory
        import shutil
        dir_error = None
        if os.path.exists(INSTALL_PATH):
            try:
                shutil.rmtree(INSTALL_PATH)
            except Exception as e:
                dir_error = str(e)

        self.update_status("Uninstall complete.", "stop")
        self.set_conflict_warning("")

        if path_error or dir_error:
            details = []
            if dir_error:
                if "permission" in dir_error.lower() or "access" in dir_error.lower():
                    details.append(
                        "Could not delete C:\\ffmpeg — a program may currently be\n"
                        "using FFmpeg. Close any apps that use audio or video and try again.\n"
                        "If that doesn't help, try right-clicking the installer and\n"
                        "choosing 'Run as administrator'."
                    )
                else:
                    details.append(f"Could not delete C:\\ffmpeg:\n  {dir_error}")
            if path_error:
                details.append(f"Could not update PATH:\n  {path_error}")
            messagebox.showwarning(
                "Uninstall — Partial",
                "Uninstall completed with errors:\n\n" + "\n\n".join(details)
            )
        else:
            messagebox.showinfo("Success", "FFmpeg has been uninstalled successfully!")

    def run(self):
        """Start the application"""
        self.root.mainloop()


if __name__ == "__main__":
    app = FFmpegInstaller()
    app.run()
