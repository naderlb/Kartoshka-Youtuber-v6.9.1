#!/usr/bin/env python3
"""
Kartoshka Youtuber GUI
Modern GUI frontend for YouTube downloading
Created by NaderB - https://www.naderb.org
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import subprocess
import json
import threading
import os
import sys
from pathlib import Path
import webbrowser

class KartoshkaYoutuberGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Kartoshka Youtuber v6.9.1")
        self.root.geometry("900x700")
        self.root.minsize(700, 500)
        self.root.configure(bg='#f8f9fa')
        
        # Professional color scheme
        bg_color = '#f8f9fa'  # Light gray background
        fg_color = '#212529'  # Dark text
        accent_color = '#007bff'  # Blue accent
        border_color = '#dee2e6'  # Light border
        
        self.root.option_add('*background', bg_color)
        self.root.option_add('*TFrame*background', bg_color)
        self.root.option_add('*TLabelFrame*background', bg_color)
        self.root.option_add('*TLabel*background', bg_color)
        self.root.option_add('*TButton*background', bg_color)
        self.root.option_add('*TEntry*background', bg_color)
        self.root.option_add('*TCombobox*background', bg_color)
        self.root.option_add('*TScrollbar*background', bg_color)
        self.root.option_add('*Frame*background', bg_color)
        self.root.option_add('*Label*background', bg_color)
        self.root.option_add('*Button*background', bg_color)
        self.root.option_add('*Entry*background', bg_color)
        self.root.option_add('*Canvas*background', bg_color)
        self.root.option_add('*Scrollbar*background', bg_color)
        
        # Set professional colors for all widget types
        self.root.option_add('*activeBackground', '#e9ecef')
        self.root.option_add('*selectBackground', accent_color)
        self.root.option_add('*highlightBackground', accent_color)
        self.root.option_add('*troughColor', border_color)
        self.root.option_add('*fieldBackground', '#ffffff')
        self.root.option_add('*foreground', fg_color)
        
        # Set window icon if available
        try:
            self.root.iconbitmap("icon.ico")
        except:
            pass
        
        # Variables
        self.url_var = tk.StringVar()
        self.quality_var = tk.StringVar(value="best")
        self.selected_quality = "best"  # Store the actually selected quality
        self.format_var = tk.StringVar(value="mp4")
        # Set default download path to 'download' folder in the same directory as the app
        if getattr(sys, 'frozen', False):
            # Running as compiled exe
            app_dir = Path(sys.executable).parent
        else:
            # Running as script
            app_dir = Path(__file__).parent
        download_dir = app_dir / "download"
        self.download_path_var = tk.StringVar(value=str(download_dir))
        self.is_downloading = False
        self.video_info = None
        self.playlist_info = None
        self.playlist_videos = []
        self.playlist_checkboxes = []
        
        # Backend path - look for backend exe in the same directory as the app
        if getattr(sys, 'frozen', False):
            # Running as compiled exe
            backend_name = "kartoshka-backend.exe" if os.name == 'nt' else "./kartoshka-backend"
            self.backend_path = str(app_dir / backend_name)
        else:
            # Running as script - use the new backend
            backend_name = "kartoshka-backend.exe" if os.name == 'nt' else "./kartoshka-backend"
            self.backend_path = str(app_dir / backend_name)
        
        self.setup_ui()
        self.setup_styles()
        
        # Bind window close event
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def setup_styles(self):
        """Setup professional styling"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Professional color scheme
        bg_color = '#f8f9fa'
        fg_color = '#212529'
        accent_color = '#007bff'
        border_color = '#dee2e6'
        success_color = '#28a745'
        error_color = '#dc3545'
        
        # Configure colors
        style.configure('Title.TLabel', font=('Segoe UI', 18, 'bold'), foreground=accent_color, background=bg_color)
        style.configure('Heading.TLabel', font=('Segoe UI', 11, 'bold'), foreground=fg_color, background=bg_color)
        style.configure('Success.TLabel', foreground=success_color, background=bg_color)
        style.configure('Error.TLabel', foreground=error_color, background=bg_color)
        
        # Configure frame background
        style.configure('TFrame', background=bg_color, relief='flat')
        style.configure('TLabelFrame', background=bg_color, relief='flat', borderwidth=1)
        style.configure('TLabelFrame.Label', background=bg_color, foreground=fg_color)
        style.configure('TLabel', background=bg_color, foreground=fg_color)
        style.configure('TButton', background=bg_color, foreground=fg_color, relief='flat')
        style.configure('TEntry', background='#ffffff', fieldbackground='#ffffff', foreground=fg_color, borderwidth=1)
        style.configure('TCombobox', background='#ffffff', fieldbackground='#ffffff', foreground=fg_color, borderwidth=1)
        style.configure('TProgressbar', background=bg_color, troughcolor=border_color, borderwidth=0)
        style.configure('TScrollbar', background=bg_color, troughcolor=border_color, borderwidth=0)
        
        # Map properties for better visual feedback
        style.map('TFrame', background=[('active', bg_color), ('!active', bg_color)])
        style.map('TLabelFrame', background=[('active', bg_color), ('!active', bg_color)])
        style.map('TLabelFrame.Label', background=[('active', bg_color), ('!active', bg_color)])
        style.map('TLabel', background=[('active', bg_color), ('!active', bg_color)])
        style.map('TButton', background=[('active', '#e9ecef'), ('!active', bg_color)], 
                 foreground=[('active', fg_color), ('!active', fg_color)])
        style.map('TEntry', background=[('active', '#ffffff'), ('!active', '#ffffff')], 
                 fieldbackground=[('active', '#ffffff'), ('!active', '#ffffff')])
        style.map('TCombobox', background=[('active', '#ffffff'), ('!active', '#ffffff')], 
                 fieldbackground=[('active', '#ffffff'), ('!active', '#ffffff')],
                 selectbackground=[('active', accent_color), ('!active', accent_color)],
                 selectforeground=[('active', '#ffffff'), ('!active', '#ffffff')])
        style.map('TScrollbar', background=[('active', bg_color), ('!active', bg_color)], 
                 troughcolor=[('active', border_color), ('!active', border_color)])
    
    def apply_background_color(self, widget):
        """Recursively apply background color to all widgets"""
        try:
            # Try to configure background for ttk widgets
            if hasattr(widget, 'configure'):
                try:
                    widget.configure(background='#f0f0f0')
                except:
                    pass
                try:
                    widget.configure(style='TFrame')
                except:
                    pass
        except:
            pass
        
        # Apply to all children
        for child in widget.winfo_children():
            self.apply_background_color(child)
    
    def force_background_update(self):
        """Force background color update on all widgets"""
        try:
            # Update all ttk styles
            style = ttk.Style()
            for widget_class in ['TFrame', 'TLabelFrame', 'TLabel', 'TButton', 'TEntry', 'TCombobox', 'TScrollbar']:
                try:
                    style.configure(widget_class, background='#f0f0f0')
                except:
                    pass
            
            # Force update of all widgets
            self.root.update_idletasks()
        except:
            pass
        
    def setup_ui(self):
        """Setup the user interface"""
        # Create main canvas and scrollbar for scrolling
        canvas = tk.Canvas(self.root, bg='#f8f9fa', highlightthickness=0, relief='flat', bd=0)
        scrollbar = tk.Scrollbar(self.root, orient="vertical", command=canvas.yview, bg='#f8f9fa', highlightthickness=0)
        scrollable_frame = tk.Frame(canvas, bg='#f8f9fa')
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set, scrollregion=canvas.bbox("all"))
        
        # Main container
        main_frame = tk.Frame(scrollable_frame, bg='#f8f9fa', padx=20, pady=20)
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Apply background color to all widgets recursively
        self.apply_background_color(main_frame)
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Bind mousewheel to canvas
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        # Store canvas reference for cleanup
        self.canvas = canvas
        
        # Force background update after UI is created
        self.root.after(100, self.force_background_update)
        
        # Title
        title_label = ttk.Label(main_frame, text="Kartoshka Youtuber v6.9", style='Title.TLabel')
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 10))
        
        subtitle_label = ttk.Label(main_frame, text="Created by NaderB - https://www.naderb.org", 
                                 foreground='gray')
        subtitle_label.grid(row=1, column=0, columnspan=3, pady=(0, 5))
        
        # Copyright warning
        warning_label = ttk.Label(main_frame, text="IMPORTANT: Only download content you own or have permission to download. Respect copyright laws.", 
                                foreground='red', font=('Arial', 9, 'bold'), wraplength=800)
        warning_label.grid(row=2, column=0, columnspan=3, pady=(0, 20))
        
        # URL Input Section
        url_frame = ttk.LabelFrame(main_frame, text="YouTube URL", padding="10")
        url_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        url_frame.columnconfigure(1, weight=1)
        
        ttk.Label(url_frame, text="URL:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        url_entry = ttk.Entry(url_frame, textvariable=self.url_var, width=50)
        url_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 10))
        
        ttk.Button(url_frame, text="Paste", command=self.paste_url).grid(row=0, column=2, padx=(0, 5))
        ttk.Button(url_frame, text="Get Info", command=self.get_video_info).grid(row=0, column=3)
        
        # Quality and Format Selection
        options_frame = ttk.LabelFrame(main_frame, text="Download Options", padding="10")
        options_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        options_frame.columnconfigure(1, weight=1)
        options_frame.columnconfigure(3, weight=1)
        
        # Quality selection
        ttk.Label(options_frame, text="Quality:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        self.quality_label = ttk.Label(options_frame, text="Select from available qualities below", 
                                     foreground='gray', font=('Arial', 9))
        self.quality_label.grid(row=0, column=1, sticky=tk.W, padx=(0, 20))
        
        # Format selection
        ttk.Label(options_frame, text="Format:").grid(row=0, column=2, sticky=tk.W, padx=(0, 10))
        format_combo = ttk.Combobox(options_frame, textvariable=self.format_var,
                                  values=["mp4", "mp3"], 
                                  state="readonly", width=15)
        format_combo.grid(row=0, column=3, sticky=tk.W)
        
        # Download path
        path_frame = ttk.Frame(options_frame)
        path_frame.grid(row=1, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=(10, 0))
        path_frame.columnconfigure(1, weight=1)
        
        ttk.Label(path_frame, text="Download to:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        path_entry = ttk.Entry(path_frame, textvariable=self.download_path_var)
        path_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 10))
        ttk.Button(path_frame, text="Browse", command=self.browse_folder).grid(row=0, column=2)
        
        # Video Information Display
        self.info_frame = ttk.LabelFrame(main_frame, text="Video Information", padding="10")
        self.info_frame.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        self.info_frame.columnconfigure(1, weight=1)
        
        # Initially hide info frame
        self.info_frame.grid_remove()
        
        # Available Qualities Display
        self.qualities_frame = ttk.LabelFrame(main_frame, text="Available Qualities", padding="10")
        self.qualities_frame.grid(row=6, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        self.qualities_frame.columnconfigure(0, weight=1)
        
        # Initially hide qualities frame
        self.qualities_frame.grid_remove()
        
        # Control Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=7, column=0, columnspan=3, pady=(0, 10))
        
        self.download_btn = ttk.Button(button_frame, text="Download", 
                                     command=self.start_download, style='Accent.TButton')
        self.download_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(button_frame, text="Refresh", command=self.get_video_info).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="Settings", command=self.show_settings).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="Clear", command=self.clear_all).pack(side=tk.LEFT)
        
        # Progress Section
        self.progress_frame = ttk.LabelFrame(main_frame, text="Download Progress", padding="10")
        self.progress_frame.grid(row=8, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        self.progress_frame.columnconfigure(0, weight=1)
        
        # Initially hide progress frame
        self.progress_frame.grid_remove()
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(self.progress_frame, variable=self.progress_var, 
                                          maximum=100, length=400)
        self.progress_bar.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
        
        self.status_label = ttk.Label(self.progress_frame, text="Ready to download")
        self.status_label.grid(row=1, column=0, sticky=tk.W)
        
        self.speed_label = ttk.Label(self.progress_frame, text="")
        self.speed_label.grid(row=2, column=0, sticky=tk.W)
        
        # Status Section
        self.status_frame = ttk.LabelFrame(main_frame, text="Status", padding="10")
        self.status_frame.grid(row=9, column=0, columnspan=3, sticky=(tk.W, tk.E))
        self.status_frame.columnconfigure(0, weight=1)
        
        self.status_text = tk.Text(self.status_frame, height=6, wrap=tk.WORD)
        self.status_text.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        # Scrollbar for status text
        scrollbar = ttk.Scrollbar(self.status_frame, orient=tk.VERTICAL, command=self.status_text.yview)
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.status_text.configure(yscrollcommand=scrollbar.set)
        
        # Bind Enter key to URL entry
        url_entry.bind('<Return>', lambda e: self.get_video_info())
        
    def log_message(self, message):
        """Add message to status log"""
        self.status_text.insert(tk.END, f"{message}\n")
        self.status_text.see(tk.END)
        self.root.update_idletasks()
        
    def paste_url(self):
        """Paste URL from clipboard"""
        try:
            clipboard_content = self.root.clipboard_get()
            if clipboard_content and ('youtube.com' in clipboard_content or 'youtu.be' in clipboard_content):
                self.url_var.set(clipboard_content.strip())
                self.log_message("URL pasted from clipboard")
            else:
                self.log_message("Clipboard doesn't contain a valid YouTube URL")
        except tk.TclError:
            self.log_message("Clipboard is empty or contains invalid data")
        
    def browse_folder(self):
        """Browse for download folder"""
        folder = filedialog.askdirectory(initialdir=self.download_path_var.get())
        if folder:
            self.download_path_var.set(folder)
            
    def get_video_info(self):
        """Get video information from backend"""
        url = self.url_var.get().strip()
        if not url:
            messagebox.showerror("Error", "Please enter a YouTube URL")
            return
            
        self.log_message(f"Getting video information for: {url}")
        
        def get_info_thread():
            try:
                # Call backend to get video info
                cmd = [
                    self.backend_path,
                    "--command", "info",
                    "--url", url
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30, 
                                      creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
                
                if result.returncode == 0:
                    info = json.loads(result.stdout)
                    if 'error' in info:
                        self.root.after(0, lambda: self.log_message(f"Error: {info['error']}"))
                    else:
                        self.root.after(0, lambda: self.display_video_info(info))
                else:
                    error_msg = result.stderr or "Unknown error occurred"
                    self.root.after(0, lambda: self.log_message(f"Backend error: {error_msg}"))
                    
            except subprocess.TimeoutExpired:
                self.root.after(0, lambda: self.log_message("Timeout: Backend took too long to respond"))
            except Exception as e:
                self.root.after(0, lambda: self.log_message(f"Error calling backend: {str(e)}"))
        
        threading.Thread(target=get_info_thread, daemon=True).start()
        
    def display_video_info(self, info):
        """Display video information in the UI"""
        self.video_info = info
        
        # Clear existing info
        for widget in self.info_frame.winfo_children():
            widget.destroy()
            
        # Show info frame
        self.info_frame.grid()
        
        # Check if it's a playlist
        if info.get('type') == 'playlist':
            self.display_playlist_info(info)
            return
        
        # Title
        ttk.Label(self.info_frame, text="Title:", style='Heading.TLabel').grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        title_text = info.get('title', 'Unknown')[:80] + "..." if len(info.get('title', '')) > 80 else info.get('title', 'Unknown')
        ttk.Label(self.info_frame, text=title_text).grid(row=0, column=1, sticky=tk.W)
        
        # Duration
        duration = info.get('duration', 0)
        duration_str = f"{duration // 60}:{duration % 60:02d}" if duration > 0 else "Unknown"
        ttk.Label(self.info_frame, text="Duration:", style='Heading.TLabel').grid(row=1, column=0, sticky=tk.W, padx=(0, 10))
        ttk.Label(self.info_frame, text=duration_str).grid(row=1, column=1, sticky=tk.W)
        
        # Uploader
        ttk.Label(self.info_frame, text="Uploader:", style='Heading.TLabel').grid(row=2, column=0, sticky=tk.W, padx=(0, 10))
        ttk.Label(self.info_frame, text=info.get('uploader', 'Unknown')).grid(row=2, column=1, sticky=tk.W)
        
        # Views
        views = info.get('view_count', 0)
        views_str = f"{views:,}" if views > 0 else "Unknown"
        ttk.Label(self.info_frame, text="Views:", style='Heading.TLabel').grid(row=3, column=0, sticky=tk.W, padx=(0, 10))
        ttk.Label(self.info_frame, text=views_str).grid(row=3, column=1, sticky=tk.W)
        
        # Display available qualities
        self.display_available_qualities(info.get('formats', []))
        
        self.log_message("Video information retrieved successfully")
        
    def display_available_qualities(self, formats):
        """Display available video qualities"""
        # Clear existing qualities
        for widget in self.qualities_frame.winfo_children():
            widget.destroy()
            
        if not formats:
            ttk.Label(self.qualities_frame, text="No quality information available").pack(anchor=tk.W)
            return
            
        # Show qualities frame
        self.qualities_frame.grid()
        
        # Extract unique resolutions
        resolutions = set()
        for fmt in formats:
            resolution = fmt.get('resolution', '')
            if resolution and resolution != 'audio only':
                resolutions.add(resolution)
        
        # Sort resolutions by quality (highest first)
        sorted_resolutions = sorted(resolutions, key=lambda x: int(x.split('x')[1]) if 'x' in x else 0, reverse=True)
        
        # Create quality buttons
        quality_frame = ttk.Frame(self.qualities_frame)
        quality_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(quality_frame, text="Available Qualities:", style='Heading.TLabel').pack(anchor=tk.W)
        
        buttons_frame = ttk.Frame(quality_frame)
        buttons_frame.pack(fill=tk.X, pady=(5, 0))
        
        for i, resolution in enumerate(sorted_resolutions[:8]):  # Show max 8 qualities
            btn = ttk.Button(buttons_frame, text=resolution, 
                           command=lambda r=resolution: self.set_quality(r))
            btn.grid(row=i//4, column=i%4, padx=(0, 10), pady=2, sticky=tk.W)
        
        # Update quality label to show selected quality
        if sorted_resolutions:
            self.quality_label.config(text="Click a quality button above to select")
        else:
            self.quality_label.config(text="No quality information available")
        
    def show_quality_selector(self):
        """Show quality selection popup"""
        if not self.video_info or 'formats' not in self.video_info:
            messagebox.showwarning("No Video Info", "Please get video information first.")
            return
            
        # Create popup window
        popup = tk.Toplevel(self.root)
        popup.title("Select Quality")
        popup.geometry("500x400")
        popup.resizable(False, False)
        popup.configure(bg='#e0e0e0')
        
        # Center the popup
        popup.transient(self.root)
        popup.grab_set()
        
        # Main frame
        main_frame = tk.Frame(popup, bg='#e0e0e0', padx=20, pady=20)
        main_frame.pack(fill="both", expand=True)
        
        # Title
        title_label = ttk.Label(main_frame, text="Select Video Quality", style='Heading.TLabel')
        title_label.pack(pady=(0, 20))
        
        # Available qualities
        formats = self.video_info['formats']
        resolutions = set()
        for fmt in formats:
            resolution = fmt.get('resolution', '')
            if resolution and resolution != 'audio only':
                resolutions.add(resolution)
        
        resolutions = sorted(resolutions, key=lambda x: int(x.split('x')[1]) if 'x' in x else 0, reverse=True)
        
        # Create quality buttons
        quality_frame = tk.Frame(main_frame, bg='#e0e0e0')
        quality_frame.pack(fill="both", expand=True)
        
        ttk.Label(quality_frame, text="Available Qualities:", style='Heading.TLabel').pack(anchor=tk.W, pady=(0, 10))
        
        buttons_frame = tk.Frame(quality_frame, bg='#e0e0e0')
        buttons_frame.pack(fill="x")
        
        # Add "Best" and "Worst" options
        ttk.Button(buttons_frame, text="Best Quality", 
                  command=lambda: self.set_quality("best", popup)).pack(side=tk.LEFT, padx=(0, 10), pady=5)
        ttk.Button(buttons_frame, text="Worst Quality", 
                  command=lambda: self.set_quality("worst", popup)).pack(side=tk.LEFT, padx=(0, 10), pady=5)
        
        # Add resolution buttons
        for i, resolution in enumerate(resolutions):
            if i % 3 == 0:
                row_frame = tk.Frame(quality_frame, bg='#e0e0e0')
                row_frame.pack(fill="x", pady=2)
            
            ttk.Button(row_frame, text=resolution, 
                      command=lambda r=resolution: self.set_quality(r, popup)).pack(side=tk.LEFT, padx=(0, 10), pady=2)
        
        # Close button
        ttk.Button(main_frame, text="Close", command=popup.destroy).pack(pady=(20, 0))
    
    def set_quality(self, quality):
        """Set the selected quality"""
        self.selected_quality = quality
        self.quality_label.config(text=f"Selected: {quality}")
        self.log_message(f"Quality set to: {quality}")
        
    def start_download(self):
        """Start video download"""
        if self.is_downloading:
            messagebox.showwarning("Warning", "Download already in progress")
            return
            
        url = self.url_var.get().strip()
        if not url:
            messagebox.showerror("Error", "Please enter a YouTube URL")
            return
            
        self.is_downloading = True
        self.download_btn.config(state='disabled', text="Downloading...")
        
        # Show progress frame
        self.progress_frame.grid()
        self.progress_var.set(0)
        self.status_label.config(text="Starting download...")
        self.speed_label.config(text="")
        
        self.log_message(f"Starting download: {url}")
        
        def download_thread():
            try:
                # Call backend to download video
                cmd = [
                    self.backend_path,
                    "--command", "download",
                    "--url", url,
                    "--quality", self.selected_quality,
                    "--format", self.format_var.get(),
                    "--path", self.download_path_var.get()
                ]
                
                process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, 
                                         text=True, bufsize=1, universal_newlines=True,
                                         creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
                
                while True:
                    output = process.stdout.readline()
                    if output == '' and process.poll() is not None:
                        break
                    if output:
                        try:
                            data = json.loads(output.strip())
                            if data.get('type') == 'progress':
                                self.root.after(0, lambda p=data: self.update_progress(p))
                            else:
                                self.root.after(0, lambda: self.log_message(f"Backend: {output.strip()}"))
                        except json.JSONDecodeError:
                            self.root.after(0, lambda: self.log_message(output.strip()))
                
                # Check final result
                return_code = process.poll()
                if return_code == 0:
                    self.root.after(0, lambda: self.download_completed(True, "Download completed successfully!"))
                else:
                    error_output = process.stderr.read()
                    self.root.after(0, lambda: self.download_completed(False, f"Download failed: {error_output}"))
                    
            except Exception as e:
                self.root.after(0, lambda: self.download_completed(False, f"Error: {str(e)}"))
        
        threading.Thread(target=download_thread, daemon=True).start()
        
    def update_progress(self, data):
        """Update download progress"""
        percent = data.get('percent', 0)
        speed = data.get('speed', 0)
        eta = data.get('eta', 0)
        
        self.progress_var.set(percent)
        
        speed_str = f"{speed / 1024 / 1024:.1f} MB/s" if speed > 0 else ""
        eta_str = f"ETA: {eta}s" if eta > 0 else ""
        
        self.speed_label.config(text=f"{speed_str} {eta_str}")
        self.status_label.config(text=f"Downloading... {percent:.1f}%")
        
    def download_completed(self, success, message):
        """Handle download completion"""
        self.is_downloading = False
        self.download_btn.config(state='normal', text="Download")
        
        if success:
            self.progress_var.set(100)
            self.status_label.config(text="Download completed!", style='Success.TLabel')
            self.log_message(message)
            messagebox.showinfo("Success", message)
        else:
            self.status_label.config(text="Download failed!", style='Error.TLabel')
            self.log_message(message)
            messagebox.showerror("Error", message)
            
    def show_settings(self):
        """Show settings dialog"""
        settings_window = tk.Toplevel(self.root)
        settings_window.title("Settings")
        settings_window.geometry("500x450")
        settings_window.resizable(False, False)
        
        # Center the window
        settings_window.transient(self.root)
        settings_window.grab_set()
        
        # Settings content
        ttk.Label(settings_window, text="Settings", style='Title.TLabel').pack(pady=10)
        
        # Default download path
        path_frame = ttk.Frame(settings_window)
        path_frame.pack(fill=tk.X, padx=20, pady=10)
        
        ttk.Label(path_frame, text="Default Download Path:").pack(anchor=tk.W)
        path_entry = ttk.Entry(path_frame, textvariable=self.download_path_var)
        path_entry.pack(fill=tk.X, pady=(5, 0))
        
        # Default quality
        quality_frame = ttk.Frame(settings_window)
        quality_frame.pack(fill=tk.X, padx=20, pady=10)
        
        ttk.Label(quality_frame, text="Default Quality:").pack(anchor=tk.W)
        quality_combo = ttk.Combobox(quality_frame, textvariable=self.quality_var,
                                   values=["best", "worst", "720p", "480p", "360p"],
                                   state="readonly")
        quality_combo.pack(fill=tk.X, pady=(5, 0))
        
        # Default format
        format_frame = ttk.Frame(settings_window)
        format_frame.pack(fill=tk.X, padx=20, pady=10)
        
        ttk.Label(format_frame, text="Default Format:").pack(anchor=tk.W)
        format_combo = ttk.Combobox(format_frame, textvariable=self.format_var,
                                  values=["mp4", "mp3"],
                                  state="readonly")
        format_combo.pack(fill=tk.X, pady=(5, 0))
        
        # Buttons
        button_frame = ttk.Frame(settings_window)
        button_frame.pack(fill=tk.X, padx=20, pady=20)
        
        ttk.Button(button_frame, text="Save", command=settings_window.destroy).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(button_frame, text="Cancel", command=settings_window.destroy).pack(side=tk.RIGHT)
        
    def display_playlist_info(self, playlist_info):
        """Display playlist information in main interface"""
        self.playlist_info = playlist_info
        self.playlist_videos = playlist_info.get('videos', [])
        is_from_single_video = playlist_info.get('is_from_single_video', False)
        
        # Playlist title
        ttk.Label(self.info_frame, text="Playlist:", style='Heading.TLabel').grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        title_text = playlist_info.get('title', 'Unknown Playlist')[:80] + "..." if len(playlist_info.get('title', '')) > 80 else playlist_info.get('title', 'Unknown Playlist')
        ttk.Label(self.info_frame, text=title_text).grid(row=0, column=1, sticky=tk.W)
        
        # Uploader
        ttk.Label(self.info_frame, text="Uploader:", style='Heading.TLabel').grid(row=1, column=0, sticky=tk.W, padx=(0, 10))
        ttk.Label(self.info_frame, text=playlist_info.get('uploader', 'Unknown')).grid(row=1, column=1, sticky=tk.W)
        
        # Video count
        ttk.Label(self.info_frame, text="Videos:", style='Heading.TLabel').grid(row=2, column=0, sticky=tk.W, padx=(0, 10))
        ttk.Label(self.info_frame, text=str(playlist_info.get('playlist_count', 0))).grid(row=2, column=1, sticky=tk.W)
        
        # Playlist indicator and options
        playlist_frame = ttk.Frame(self.info_frame)
        playlist_frame.grid(row=3, column=0, columnspan=2, sticky=tk.W+tk.E, pady=(10, 0))
        
        # Playlist indicator
        if is_from_single_video:
            ttk.Label(playlist_frame, text="[VIDEO FROM PLAYLIST DETECTED]", 
                     style='Heading.TLabel', foreground='#28a745').pack(side=tk.LEFT, padx=(0, 10))
        else:
            ttk.Label(playlist_frame, text="[PLAYLIST DETECTED]", 
                     style='Heading.TLabel', foreground='#007bff').pack(side=tk.LEFT, padx=(0, 10))
        
        # Options frame
        options_frame = ttk.Frame(self.info_frame)
        options_frame.grid(row=4, column=0, columnspan=2, sticky=tk.W+tk.E, pady=(10, 0))
        
        if is_from_single_video:
            # Show options for single video from playlist
            ttk.Label(options_frame, text="Choose download option:", style='Heading.TLabel').pack(anchor=tk.W)
            
            button_frame = ttk.Frame(options_frame)
            button_frame.pack(fill=tk.X, pady=(5, 0))
            
            ttk.Button(button_frame, text="Download This Video Only", 
                      command=self.download_current_video).pack(side=tk.LEFT, padx=(0, 10))
            ttk.Button(button_frame, text="Select from Playlist", 
                      command=self.open_playlist_selection).pack(side=tk.LEFT)
        else:
            # Show option for full playlist
            ttk.Button(options_frame, text="Select Videos to Download", 
                      command=self.open_playlist_selection).pack(side=tk.LEFT)
        
        self.log_message(f"Playlist detected: {playlist_info.get('playlist_count', 0)} videos found")
        
    def download_current_video(self):
        """Download just the current video from playlist"""
        if not self.playlist_info:
            messagebox.showerror("Error", "No playlist information available")
            return
            
        # Find the current video
        current_video_id = self.playlist_info.get('current_video_id')
        current_video = None
        
        for video in self.playlist_videos:
            if video.get('id') == current_video_id:
                current_video = video
                break
                
        if not current_video:
            messagebox.showerror("Error", "Current video not found in playlist")
            return
            
        # Download the single video
        self.start_single_video_download(current_video['url'])
        
    def start_single_video_download(self, video_url):
        """Start downloading a single video"""
        if self.is_downloading:
            messagebox.showwarning("Warning", "A download is already in progress.")
            return
            
        self.is_downloading = True
        self.download_btn.config(state='disabled', text="Downloading...")
        
        # Show progress frame
        self.progress_frame.grid()
        self.progress_var.set(0)
        self.status_label.config(text="Starting download...")
        
        def download_thread():
            try:
                # Call backend to download single video
                cmd = [
                    self.backend_path,
                    "--command", "download",
                    "--url", video_url,
                    "--quality", self.selected_quality,
                    "--format", self.format_var.get(),
                    "--path", self.download_path_var.get()
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=300,
                                      creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
                
                if result.returncode == 0:
                    response = json.loads(result.stdout)
                    if response.get('success'):
                        self.root.after(0, lambda: self.download_completed(True, response.get('message', 'Download completed!')))
                    else:
                        self.root.after(0, lambda: self.download_completed(False, response.get('error', 'Unknown error')))
                else:
                    error_msg = result.stderr or "Unknown error occurred"
                    self.root.after(0, lambda: self.download_completed(False, f"Backend error: {error_msg}"))
                    
            except subprocess.TimeoutExpired:
                self.root.after(0, lambda: self.download_completed(False, "Timeout: Download took too long"))
            except Exception as e:
                self.root.after(0, lambda: self.download_completed(False, f"Error: {str(e)}"))
        
        threading.Thread(target=download_thread, daemon=True).start()
        
    def open_playlist_selection(self):
        """Open the playlist selection window"""
        if not self.playlist_info:
            messagebox.showerror("Error", "No playlist information available")
            return
        self.create_playlist_selection()
        
    def create_playlist_selection(self):
        """Create scrollable playlist selection interface"""
        # Create a new window for playlist selection
        self.playlist_window = tk.Toplevel(self.root)
        self.playlist_window.title("Select Videos to Download")
        self.playlist_window.geometry("800x600")
        self.playlist_window.configure(bg='#f8f9fa')
        
        # Make it modal
        self.playlist_window.transient(self.root)
        self.playlist_window.grab_set()
        
        # Main frame
        main_frame = ttk.Frame(self.playlist_window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Title
        ttk.Label(main_frame, text=f"Select Videos from: {self.playlist_info.get('title', 'Playlist')}", 
                 style='Title.TLabel').pack(pady=(0, 10))
        
        # Create canvas and scrollbar for video list
        canvas = tk.Canvas(main_frame, bg='#f8f9fa')
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Create video selection checkboxes
        self.playlist_checkboxes = []
        for i, video in enumerate(self.playlist_videos):
            self.create_video_checkbox(scrollable_frame, video, i)
        
        # Control buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(button_frame, text="Select All", command=self.select_all_videos).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Deselect All", command=self.deselect_all_videos).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Download Selected", command=self.download_selected_videos).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(button_frame, text="Cancel", command=self.playlist_window.destroy).pack(side=tk.RIGHT, padx=(0, 5))
        
        # Bind mousewheel to canvas
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        # Store canvas for cleanup
        self.playlist_canvas = canvas
        
    def create_video_checkbox(self, parent, video, index):
        """Create a checkbox for a video in the playlist"""
        video_frame = ttk.Frame(parent)
        video_frame.pack(fill=tk.X, pady=2)
        
        # Checkbox
        var = tk.BooleanVar(value=video.get('selected', True))
        checkbox = ttk.Checkbutton(video_frame, variable=var)
        checkbox.pack(side=tk.LEFT, padx=(0, 10))
        
        # Video info
        info_frame = ttk.Frame(video_frame)
        info_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Title
        title_text = video.get('title', 'Unknown')[:60] + "..." if len(video.get('title', '')) > 60 else video.get('title', 'Unknown')
        ttk.Label(info_frame, text=title_text, font=('Segoe UI', 9, 'bold')).pack(anchor=tk.W)
        
        # Duration and uploader
        duration = video.get('duration', 0)
        duration_str = f"{duration//60}:{duration%60:02d}" if duration > 0 else "Unknown"
        uploader = video.get('uploader', 'Unknown')
        info_text = f"Duration: {duration_str} | Uploader: {uploader}"
        ttk.Label(info_frame, text=info_text, font=('Segoe UI', 8)).pack(anchor=tk.W)
        
        # Store reference
        self.playlist_checkboxes.append({
            'var': var,
            'video': video,
            'index': index
        })
        
    def select_all_videos(self):
        """Select all videos in the playlist"""
        for checkbox in self.playlist_checkboxes:
            checkbox['var'].set(True)
            
    def deselect_all_videos(self):
        """Deselect all videos in the playlist"""
        for checkbox in self.playlist_checkboxes:
            checkbox['var'].set(False)
            
    def download_selected_videos(self):
        """Download selected videos from playlist"""
        selected_videos = []
        for checkbox in self.playlist_checkboxes:
            if checkbox['var'].get():
                video = checkbox['video'].copy()
                video['selected'] = True
                selected_videos.append(video)
        
        if not selected_videos:
            messagebox.showwarning("Warning", "Please select at least one video to download.")
            return
            
        # Close playlist window
        self.playlist_window.destroy()
        
        # Start download
        self.start_playlist_download(selected_videos)
        
    def start_playlist_download(self, selected_videos):
        """Start downloading selected videos from playlist"""
        if self.is_downloading:
            messagebox.showwarning("Warning", "A download is already in progress.")
            return
            
        url = self.url_var.get().strip()
        if not url:
            messagebox.showerror("Error", "Please enter a YouTube URL")
            return
            
        self.is_downloading = True
        self.download_btn.config(state='disabled', text="Downloading...")
        
        # Show progress frame
        self.progress_frame.grid()
        self.progress_var.set(0)
        self.status_label.config(text="Starting playlist download...")
        
        def download_thread():
            try:
                # Prepare playlist data
                playlist_data = {
                    'videos': selected_videos
                }
                
                # Call backend to download playlist
                cmd = [
                    self.backend_path,
                    "--command", "download_playlist",
                    "--url", url,
                    "--quality", self.selected_quality,
                    "--format", self.format_var.get(),
                    "--path", self.download_path_var.get(),
                    "--playlist-data", json.dumps(playlist_data)
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=300,
                                      creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
                
                if result.returncode == 0:
                    response = json.loads(result.stdout)
                    if response.get('success'):
                        self.root.after(0, lambda: self.download_completed(True, response.get('message', 'Playlist download completed!')))
                    else:
                        self.root.after(0, lambda: self.download_completed(False, response.get('error', 'Unknown error')))
                else:
                    error_msg = result.stderr or "Unknown error occurred"
                    self.root.after(0, lambda: self.download_completed(False, f"Backend error: {error_msg}"))
                    
            except subprocess.TimeoutExpired:
                self.root.after(0, lambda: self.download_completed(False, "Timeout: Download took too long"))
            except Exception as e:
                self.root.after(0, lambda: self.download_completed(False, f"Error: {str(e)}"))
        
        threading.Thread(target=download_thread, daemon=True).start()

    def clear_all(self):
        """Clear all inputs and status"""
        self.url_var.set("")
        self.video_info = None
        self.playlist_info = None
        self.playlist_videos = []
        self.info_frame.grid_remove()
        self.qualities_frame.grid_remove()
        self.progress_frame.grid_remove()
        self.progress_var.set(0)
        self.status_text.delete(1.0, tk.END)
        self.quality_label.config(text="Select from available qualities below")
        self.log_message("Cleared all data")
        
    def on_closing(self):
        """Handle window closing"""
        if hasattr(self, 'canvas'):
            self.canvas.unbind_all("<MouseWheel>")
        self.root.destroy()

def main():
    """Main function"""
    root = tk.Tk()
    app = KartoshkaYoutuberGUI(root)
    
    # Check if backend exists
    if getattr(sys, 'frozen', False):
        # Running as compiled exe
        app_dir = Path(sys.executable).parent
        backend_name = "kartoshka-backend.exe" if os.name == 'nt' else "./kartoshka-backend"
        backend_path = str(app_dir / backend_name)
    else:
        # Running as script - use the new backend
        app_dir = Path(__file__).parent
        backend_name = "kartoshka-backend.exe" if os.name == 'nt' else "./kartoshka-backend"
        backend_path = str(app_dir / backend_name)
    
    if not os.path.exists(backend_path):
        messagebox.showerror("Error", f"Backend application not found!\nPlease ensure {backend_path} is in the same directory.")
        return
    
    # Start the application
    root.mainloop()

if __name__ == "__main__":
    main()
