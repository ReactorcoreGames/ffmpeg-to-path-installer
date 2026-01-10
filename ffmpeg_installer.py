import os
import sys
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


class FFmpegInstaller:
    def __init__(self):
        self.root = ttk.Window(themename="superhero")
        self.root.title("FFmpeg PATH Installer")
        self.root.geometry("600x500")
        self.root.resizable(True, True)
        
        # Center the window
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (600 // 2)
        y = (self.root.winfo_screenheight() // 2) - (500 // 2)
        self.root.geometry(f"600x500+{x}+{y}")
        
        self.setup_ui()
        
    def setup_ui(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding=20)
        main_frame.pack(fill=BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(
            main_frame,
            text="FFmpeg PATH Installer",
            font=("Helvetica", 24, "bold")
        )
        title_label.pack(pady=(0, 20))
        
        # Description
        desc_text = (
            "This tool will download and install FFmpeg to your system PATH,\n"
            "making it available to all applications that need video/audio processing.\n\n"
            "FFmpeg will be installed to: C:\\ffmpeg\n"
            "And automatically added to your Windows PATH environment variable."
        )
        desc_label = ttk.Label(
            main_frame,
            text=desc_text,
            font=("Helvetica", 11),
            justify=CENTER
        )
        desc_label.pack(pady=(0, 30))
        
        # Status frame
        self.status_frame = ttk.Frame(main_frame)
        self.status_frame.pack(fill=X, pady=(0, 20))
        
        self.status_label = ttk.Label(
            self.status_frame,
            text="Ready to install FFmpeg",
            font=("Helvetica", 10)
        )
        self.status_label.pack()
        
        # Progress bar
        self.progress = ttk.Progressbar(
            main_frame,
            mode='indeterminate',
            style="success.Horizontal.TProgressbar"
        )
        self.progress.pack(fill=X, pady=(0, 30))
        
        # Buttons frame
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.pack(fill=X, pady=(0, 20))
        
        # Install button
        self.install_btn = ttk.Button(
            buttons_frame,
            text="Install FFmpeg to PATH",
            command=self.start_installation,
            style="success.TButton",
            width=25
        )
        self.install_btn.pack(side=LEFT, padx=(0, 10))
        
        # Check installation button
        self.check_btn = ttk.Button(
            buttons_frame,
            text="Check Installation",
            command=self.check_installation,
            style="info.TButton",
            width=20
        )
        self.check_btn.pack(side=LEFT, padx=(0, 10))
        
        # Uninstall button
        self.uninstall_btn = ttk.Button(
            buttons_frame,
            text="Uninstall",
            command=self.uninstall_ffmpeg,
            style="danger.TButton",
            width=15
        )
        self.uninstall_btn.pack(side=LEFT)
        
        # Instructions frame
        instructions_frame = ttk.LabelFrame(main_frame, text="Instructions", padding=15)
        instructions_frame.pack(fill=BOTH, expand=True, pady=(20, 0))
        
        instructions_text = (
            "1. Click 'Install FFmpeg to PATH' to download and install FFmpeg\n"
            "2. The installation will add FFmpeg to your Windows PATH\n"
            "3. You may need to restart applications to use FFmpeg\n"
            "4. Use 'Check Installation' to verify FFmpeg is working\n"
            "5. Use 'Uninstall' to remove FFmpeg if needed"
        )
        
        instructions_label = ttk.Label(
            instructions_frame,
            text=instructions_text,
            font=("Helvetica", 10),
            justify=LEFT
        )
        instructions_label.pack(anchor=W)
        
        # Footer
        footer_frame = ttk.Frame(self.root)
        footer_frame.pack(side=BOTTOM, fill=X, padx=20, pady=10)
        
        footer_label = ttk.Label(
            footer_frame,
            text="Made by Reactorcore",
            font=("Helvetica", 8),
            foreground="gray",
            cursor="hand2"
        )
        footer_label.pack(side=RIGHT)
        footer_label.bind("<Button-1>", lambda e: webbrowser.open("https://reactorcore.itch.io/"))
        
    def update_status(self, message, progress_mode=None):
        """Update status label and progress bar"""
        self.status_label.config(text=message)
        if progress_mode == "start":
            self.progress.start()
        elif progress_mode == "stop":
            self.progress.stop()
        self.root.update()
        
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
            extracted_folders = [f for f in os.listdir(temp_dir) if os.path.isdir(os.path.join(temp_dir, f))]
            if not extracted_folders:
                raise Exception("No folder found in extracted zip")
            
            ffmpeg_folder = os.path.join(temp_dir, extracted_folders[0])
            bin_folder = os.path.join(ffmpeg_folder, "bin")
            
            if not os.path.exists(bin_folder):
                raise Exception("FFmpeg bin folder not found in extracted files")
            
            # Install to C:\\ffmpeg
            install_path = "C:\\ffmpeg"
            if os.path.exists(install_path):
                import shutil
                shutil.rmtree(install_path)
            
            self.update_status("Installing FFmpeg to C:\\ffmpeg...")
            import shutil
            shutil.copytree(ffmpeg_folder, install_path)
            
            return install_path
            
        except Exception as e:
            raise Exception(f"Installation failed: {str(e)}")
            
    def add_to_path(self, install_path):
        """Add FFmpeg to Windows PATH"""
        try:
            self.update_status("Adding FFmpeg to PATH...")
            
            bin_path = os.path.join(install_path, "bin")
            
            # Use setx command to add to PATH permanently
            cmd = f'setx PATH "%PATH%;{bin_path}"'
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            if result.returncode != 0:
                # Try alternative method using reg command
                cmd_check = f'reg query "HKCU\\Environment" /v PATH'
                result_check = subprocess.run(cmd_check, shell=True, capture_output=True, text=True)
                
                if result_check.returncode == 0:
                    # Get current PATH
                    current_path = ""
                    for line in result_check.stdout.split('\n'):
                        if 'PATH' in line and 'REG_' in line:
                            current_path = line.split('REG_')[1].split(' ', 1)[1].strip()
                            break
                    
                    # Add new path if not already present
                    if bin_path.lower() not in current_path.lower():
                        new_path = f"{current_path};{bin_path}" if current_path else bin_path
                        cmd_reg = f'reg add "HKCU\\Environment" /v PATH /t REG_EXPAND_SZ /d "{new_path}" /f'
                        subprocess.run(cmd_reg, shell=True)
                
        except Exception as e:
            raise Exception(f"Failed to add to PATH: {str(e)}")
            
    def start_installation(self):
        """Start the installation process in a separate thread"""
        def install():
            try:
                self.install_btn.config(state="disabled")
                self.check_btn.config(state="disabled")
                self.uninstall_btn.config(state="disabled")
                
                # Download
                zip_path, temp_dir = self.download_ffmpeg()
                
                # Extract and install
                install_path = self.extract_and_install(zip_path, temp_dir)
                
                # Add to PATH
                self.add_to_path(install_path)
                
                # Cleanup
                import shutil
                shutil.rmtree(temp_dir)
                
                self.update_status("FFmpeg installed successfully! Restart applications to use FFmpeg.", "stop")
                messagebox.showinfo("Success", 
                    "FFmpeg has been installed successfully!\n\n"
                    "You may need to restart applications or your computer\n"
                    "for the PATH changes to take effect.")
                
            except Exception as e:
                self.update_status(f"Installation failed: {str(e)}", "stop")
                messagebox.showerror("Error", f"Installation failed:\n{str(e)}")
                
            finally:
                self.install_btn.config(state="normal")
                self.check_btn.config(state="normal")
                self.uninstall_btn.config(state="normal")
        
        threading.Thread(target=install, daemon=True).start()
        
    def check_installation(self):
        """Check if FFmpeg is properly installed"""
        try:
            result = subprocess.run(['ffmpeg', '-version'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                version_line = result.stdout.split('\n')[0]
                self.update_status("FFmpeg is installed and working!")
                messagebox.showinfo("Installation Check", 
                    f"FFmpeg is properly installed!\n\n{version_line}")
            else:
                self.update_status("FFmpeg not found in PATH")
                messagebox.showwarning("Installation Check", 
                    "FFmpeg is not found in PATH.\nPlease install or restart your applications.")
        except subprocess.TimeoutExpired:
            self.update_status("FFmpeg check timed out")
            messagebox.showerror("Error", "FFmpeg check timed out.")
        except FileNotFoundError:
            self.update_status("FFmpeg not found in PATH")
            messagebox.showwarning("Installation Check", 
                "FFmpeg is not found in PATH.\nPlease install or restart your applications.")
        except Exception as e:
            self.update_status(f"Check failed: {str(e)}")
            messagebox.showerror("Error", f"Check failed: {str(e)}")
            
    def uninstall_ffmpeg(self):
        """Uninstall FFmpeg"""
        try:
            result = messagebox.askyesno("Uninstall FFmpeg", 
                "Are you sure you want to uninstall FFmpeg?\n\n"
                "This will remove FFmpeg from C:\\ffmpeg and update PATH.")
            
            if not result:
                return
                
            self.update_status("Uninstalling FFmpeg...", "start")
            
            # Remove from PATH
            try:
                cmd_check = f'reg query "HKCU\\Environment" /v PATH'
                result_check = subprocess.run(cmd_check, shell=True, capture_output=True, text=True)
                
                if result_check.returncode == 0:
                    current_path = ""
                    for line in result_check.stdout.split('\n'):
                        if 'PATH' in line and 'REG_' in line:
                            current_path = line.split('REG_')[1].split(' ', 1)[1].strip()
                            break
                    
                    # Remove ffmpeg paths
                    path_parts = current_path.split(';')
                    new_path_parts = [part for part in path_parts if 'ffmpeg' not in part.lower()]
                    new_path = ';'.join(new_path_parts)
                    
                    if new_path != current_path:
                        cmd_reg = f'reg add "HKCU\\Environment" /v PATH /t REG_EXPAND_SZ /d "{new_path}" /f'
                        subprocess.run(cmd_reg, shell=True)
            except:
                pass  # Continue even if PATH removal fails
            
            # Remove directory
            import shutil
            install_path = "C:\\ffmpeg"
            if os.path.exists(install_path):
                shutil.rmtree(install_path)
            
            self.update_status("FFmpeg uninstalled successfully!", "stop")
            messagebox.showinfo("Success", "FFmpeg has been uninstalled successfully!")
            
        except Exception as e:
            self.update_status(f"Uninstall failed: {str(e)}", "stop")
            messagebox.showerror("Error", f"Uninstall failed: {str(e)}")
            
    def run(self):
        """Start the application"""
        self.root.mainloop()


if __name__ == "__main__":
    app = FFmpegInstaller()
    app.run()