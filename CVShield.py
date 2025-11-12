import tkinter as tk
from tkinter import ttk, messagebox
import time
import random
import json
import os
from datetime import timedelta
from PIL import Image, ImageTk, ImageDraw
import pystray
import threading


class CVShield:
    SETTINGS_FILE = "cvshield_settings.json"
    # Default colors to ensure good contrast in light/dark modes
    DEFAULT_BG = "#f0f4f8"
    DEFAULT_BREAK_BG = "#ebf8ff"
    DEFAULT_TEXT = "#1a202c"
    
    @staticmethod
    def create_blank_icon():
        # Create a small blank icon
        icon_size = (32, 32)
        # Try to load a `logo.png` located next to this script
        try:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            logo_path = os.path.join(base_dir, 'logo.png')
            if os.path.exists(logo_path):
                img = Image.open(logo_path).convert('RGBA')
                # Resize while keeping aspect ratio, then paste on transparent background
                img = img.resize(icon_size, Image.LANCZOS)
                return img
        except Exception:
            # If any error, fall back to generated icon
            pass

        # Fallback icon (simple square)
        icon_image = Image.new('RGBA', icon_size, color=(255, 255, 255, 0))
        draw = ImageDraw.Draw(icon_image)
        draw.rectangle([8, 8, 24, 24], fill='black')
        return icon_image

    def __init__(self):
        # Initialize variables first
        self.start_time = None
        self.is_timer_running = False
        self.sent_notification = False
        self.break_interval = 0
        self.break_duration = 0
        self.is_paused = False
        self.pause_time = None
        self.remaining_time = 0
        self.custom_pause_message = "Please take a short break!"  # Default pause message
        self.current_exercise = 0
        self.timer_id = None
        self.icon = None
        self.break_frame = None
        self.main_frame = None
        
        # Initialize Tkinter window
        self.root = tk.Tk()
        self.root.title("CVShield")
        
        # Configure window properties
        window_width = 600
        window_height = 500
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        # Create container frame
        self.container = ttk.Frame(self.root)
        self.container.pack(fill='both', expand=True)
        
        # Ensure proper window closure
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # Eye exercises list (one exercise for each break)
        self.eye_exercises = [
            "Blink 20 times.",
            "Roll your eyes in a clockwise circle 10 times, then in a counterclockwise circle 10 times.",
            "Hold your thumb in front of you at arm's length. Shift focus from your thumb to a distant object and back. Repeat 15 times.",
            "Close your eyes tightly for 5 seconds, then open them wide. Repeat 10 times.",
            "Draw the infinity symbol (a sideways figure-eight) with your eyes. Repeat the motion 10 times.",
            "Focus on an object about 6 inches away, then switch to an object farther away. Repeat this focusing exercise 15 times.",
            "Rapidly shift your gaze between two objects placed at least 10 feet apart. Repeat 20 times.",
            "Sit up straight with your back against the chair.",
            "Keep your feet flat on the floor.",
            "Keep your knees at a 90-degree angle.",
            "Keep your wrists straight when typing.",
            "Stretch your back and neck."
        ]
        
        try:
            # Use the already-created root & container. Set close behavior to minimize to tray.
            self.root.protocol("WM_DELETE_WINDOW", self.minimize_to_tray)

            # Initialize system tray icon with deferred menu creation
            def create_menu():
                return pystray.Menu(
                    pystray.MenuItem("Show", lambda: self.root.after(0, self.show_window)),
                    pystray.MenuItem("Start Timer", lambda: self.root.after(0, self.start_timer)),
                    pystray.MenuItem("Edit Preferences", lambda: self.root.after(0, self.edit_preferences)),
                    pystray.MenuItem("Reset Preferences", lambda: self.root.after(0, self.reset_preferences)),
                    pystray.MenuItem("Quit", lambda: self.root.after(0, self.quit_application))
                )

            self.icon = pystray.Icon(
                "CVShield",
                self.create_blank_icon()
            )
            self.icon.menu = create_menu()

            # Ensure settings exist at startup
            self.ensure_settings_exist()

            # Create main window elements (single call)
            self.setup_gui()

            # Set Tk window icon to logo.png if available (use same image as tray)
            try:
                pil_icon = self.create_blank_icon()
                # Keep a reference to avoid GC
                self._tk_icon_image = ImageTk.PhotoImage(pil_icon)
                try:
                    self.root.iconphoto(False, self._tk_icon_image)
                except Exception:
                    # Some platforms may not support iconphoto; ignore
                    pass
            except Exception:
                pass

            # Show the window immediately after setup
            self.root.deiconify()
            self.root.lift()
            self.root.focus_force()

        except Exception as e:
            messagebox.showerror("Error", f"Failed to initialize application: {str(e)}")
            if self.root:
                try:
                    self.root.destroy()
                except:
                    pass
            if self.icon:
                try:
                    self.icon.stop()
                except:
                    pass
            raise

    def on_close(self):
        """Handle window closing."""
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            if self.icon:
                try:
                    self.icon.stop()
                except:
                    pass
            self.root.quit()
        
    def setup_gui(self):
        """Set up the main GUI window with consistent, high-contrast styling."""
        style = ttk.Style()
        try:
            style.theme_use('clam')
        except Exception:
            pass

        # Basic colors
        bg = self.DEFAULT_BG
        text = self.DEFAULT_TEXT

        style.configure("Main.TFrame", background=bg)
        style.configure("Timer.TLabel", font=("Arial", 14, "bold"), foreground=text, background=bg)
        style.configure("Settings.TLabelframe", background=bg, foreground=text)
        style.configure("Settings.TLabel", background=bg, foreground=text)

        # Button styles
        style.configure("Primary.TButton", background="#4299e1", foreground="white", padding=8,
                        font=("Arial", 10, "bold"))
        style.configure("Secondary.TButton", background="#718096", foreground="white", padding=8)
        style.map("Primary.TButton",
                  foreground=[('active', 'white'), ('pressed', 'white')],
                  background=[('active', '#2b6cb0'), ('pressed', '#2c5282')])
        style.map("Secondary.TButton",
                  foreground=[('active', 'white'), ('pressed', 'white')],
                  background=[('active', '#4a5568'), ('pressed', '#2d3748')])

        # Create main frame
        self.main_frame = ttk.Frame(self.container, padding="10", style="Main.TFrame")
        self.main_frame.pack(fill='both', expand=True)

        # Timer display
        self.timer_label = ttk.Label(self.main_frame, text="CVShield - Inactive", style="Timer.TLabel")
        self.timer_label.pack(pady=10)

        # Button frame and buttons
        self.button_frame = ttk.Frame(self.main_frame)
        self.button_frame.pack(pady=5)

        self.start_button = ttk.Button(self.button_frame, text="Start Timer", command=self.start_timer,
                                       style="Primary.TButton")
        self.start_button.pack(pady=6, padx=10, fill='x')

        self.edit_pref_button = ttk.Button(self.button_frame, text="Edit Preferences",
                                           command=self.edit_preferences, style="Secondary.TButton")
        self.edit_pref_button.pack(pady=6, padx=10, fill='x')

        self.reset_pref_button = ttk.Button(self.button_frame, text="Reset Preferences",
                                            command=self.reset_preferences, style="Secondary.TButton")
        self.reset_pref_button.pack(pady=6, padx=10, fill='x')

        # Buttons that appear during timer (not packed initially)
        self.pause_button = ttk.Button(self.button_frame, text="Pause Timer", command=self.toggle_pause_timer)
        self.stop_button = ttk.Button(self.button_frame, text="Stop Timer", command=self.stop_timer)
        self.edit_break_button = ttk.Button(self.button_frame, text="Edit Break", command=self.edit_break)

        # Settings display
        self.settings_frame = ttk.LabelFrame(self.main_frame, text="Current Settings",
                                             padding="10", style="Settings.TLabelframe")
        self.settings_frame.pack(pady=15, fill='x', padx=5)

        self.interval_label = ttk.Label(self.settings_frame, text="Interval: Not set", style="Settings.TLabel")
        self.interval_label.pack(anchor='w', padx=8, pady=3)

        self.duration_label = ttk.Label(self.settings_frame, text="Duration: Not set", style="Settings.TLabel")
        self.duration_label.pack(anchor='w', padx=8, pady=3)

        self.message_label = ttk.Label(self.settings_frame, text=f"Message: {self.custom_pause_message}",
                                       style="Settings.TLabel")
        self.message_label.pack(anchor='w', padx=8, pady=3)

        # Create additional frames
        self.setup_break_frame()
        self.setup_preferences_frame()

        # Update display
        self.update_preferences_display()

    def setup_system_tray(self):
        """Set up the system tray icon and menu."""
        pass  # This is now handled in __init__

    def show_window(self):
        """Show the main window."""
        if self.root:
            self.root.after(0, self.root.deiconify)
            self.root.after(100, self.root.lift)
            self.root.after(200, self.root.focus_force)

    def minimize_to_tray(self):
        """Minimize the window to system tray."""
        if self.root:
            self.root.withdraw()

    def quit_application(self):
        """Quit the application."""
        try:
            if self.icon:
                self.icon.stop()
            if self.root:
                self.root.quit()
        except Exception:
            # Ensure the application exits even if there's an error
            os._exit(0)

    def start_timer(self, _=None):
        """Start the timer and update the GUI."""
        if self.break_interval == 0 or self.break_duration == 0:
            self.set_initial_break_settings()

        # Save settings in case they were just configured
        self.save_settings()

        # Update buttons (hide main buttons)
        self.start_button.pack_forget()
        self.edit_pref_button.pack_forget()
        self.reset_pref_button.pack_forget()

        # Show pause, stop, and edit break buttons
        self.pause_button.pack(pady=5, padx=5, fill='x')
        self.stop_button.pack(pady=5, padx=5, fill='x')
        self.edit_break_button.pack(pady=5, padx=5, fill='x')

        self.start_time = time.time()
        self.is_timer_running = True
        self.sent_notification = False
        # Show initial time immediately
        self.track_time()  # This will schedule the next update
        if self.icon:
            self.icon.title = "CVShield - Timer Running"

    def stop_timer(self, _=None):
        """Stop the timer and reset the GUI."""
        self.is_timer_running = False
        if self.timer_id:
            self.root.after_cancel(self.timer_id)
            self.timer_id = None
        self.timer_label.config(text="😎 CVShield - Inactive")
        if self.icon:
            self.icon.title = "CVShield - Inactive"

        # Hide pause, stop, and edit break buttons
        self.pause_button.pack_forget()
        self.stop_button.pack_forget()
        self.edit_break_button.pack_forget()

        # Show start and preference buttons
        self.start_button.pack(pady=5, padx=5, fill='x')
        self.edit_pref_button.pack(pady=5, padx=5, fill='x')
        self.reset_pref_button.pack(pady=5, padx=5, fill='x')

        self.update_preferences_display()

    def toggle_pause_timer(self, _=None):
        """Pause or resume the timer."""
        if self.is_paused:
            paused_duration = time.time() - self.pause_time
            self.start_time += paused_duration
            self.is_paused = False
            self.timer_label.config(text="😎 CVShield - Timer Running")
            self.pause_button.config(text="Pause Timer")
            if self.icon:
                self.icon.title = "CVShield - Timer Running"
            self.timer_id = self.root.after(1000, self.track_time)
        else:
            self.is_paused = True
            self.pause_time = time.time()
            if self.timer_id:
                self.root.after_cancel(self.timer_id)
                self.timer_id = None
            self.remaining_time = self.break_interval - (self.pause_time - self.start_time)
            minutes = int(self.remaining_time // 60)
            seconds = int(self.remaining_time % 60)
            pause_text = f"⏸️ {minutes}m {seconds}s remaining"
            self.timer_label.config(text=pause_text)
            self.pause_button.config(text="Resume Timer")
            if self.icon:
                self.icon.title = f"CVShield - Paused: {minutes}m {seconds}s"

    def track_time(self):
        """Track elapsed time and handle notifications or break initiation."""
        if not self.is_timer_running or self.is_paused:
            return

        # Calculate elapsed and remaining time
        elapsed_time = time.time() - self.start_time
        remaining_time = self.break_interval - elapsed_time

        # If the timer hits zero, start the break
        if remaining_time <= 0:
            self.start_break()
            return

        # Calculate remaining minutes and seconds
        minutes, seconds = divmod(int(remaining_time), 60)

        # Handle singular/plural for seconds and format the time
        if minutes > 0:
            if minutes == 1:
                if seconds == 1:
                    timer_text = "Time until break: 1 minute 1 second"
                else:
                    timer_text = f"Time until break: 1 minute {seconds} seconds"
            else:
                if seconds == 1:
                    timer_text = f"Time until break: {minutes} minutes 1 second"
                else:
                    timer_text = f"Time until break: {minutes} minutes {seconds} seconds"
        else:
            if seconds == 1:
                timer_text = "Time until break: 1 second"
            else:
                timer_text = f"Time until break: {seconds} seconds"

        # Update timer label and system tray icon
        self.timer_label.config(text=f"😎 {timer_text}")
        if self.icon:
            self.icon.title = f"CVShield - {timer_text}"

        # Schedule next update
        self.timer_id = self.root.after(1000, self.track_time)

    def start_break(self):
        """Start a break."""
        # Stop the main timer updates
        if self.timer_id:
            try:
                self.root.after_cancel(self.timer_id)
            except Exception:
                pass
            self.timer_id = None

        # Update UI to show break state
        self.timer_label.config(text="😎 CVShield - Break!")
        if self.icon:
            self.icon.title = "CVShield - Break!"

        # Pause the main timer during break
        self.is_timer_running = False

        # Define callback to run after break finishes
        def on_break_end():
            # Reset the main timer starting point so it counts a full interval after break
            self.start_time = time.time()
            self.is_timer_running = True
            self.timer_id = self.root.after(1000, self.track_time)
            self.timer_label.config(text="😎 CVShield - Timer Running")
            if self.icon:
                self.icon.title = "CVShield - Timer Running"

        # Start the break and pass the callback
        self.block_screen_for_break(self.break_duration, on_complete=on_break_end)

    def setup_break_frame(self):
        """Create the break frame (initially hidden)."""
        # Use a frame for the break UI. We'll place a background label into
        # this frame at runtime when entering the break.
        self.break_frame = ttk.Frame(self.container, padding="20")
        
        # Configure styles for break frame
        style = ttk.Style()
        style.configure("Break.TFrame", background='#ebf8ff')
        # Make break text much larger so it's obvious during fullscreen breaks
        style.configure("BreakTimer.TLabel",
                       font=("Arial", 72, "bold"),
                       foreground="#2b6cb0",
                       background="#ebf8ff")
        style.configure("Exercise.TLabel",
                       font=("Arial", 36),
                       foreground="#2d3748",
                       background="#ebf8ff",
                       wraplength=1000)
        style.configure("Horizontal.TProgressbar",
                       background="#4299e1",
                       troughcolor="#e2e8f0")
        
        self.break_frame.configure(style="Break.TFrame")
        
        # Timer label with styling
        self.break_timer_label = ttk.Label(
            self.break_frame,
            text="",
            style="BreakTimer.TLabel"
        )
        self.break_timer_label.pack(pady=25)
        
        # Exercise label with styling
        self.exercise_label = ttk.Label(
            self.break_frame,
            text="",
            style="Exercise.TLabel"
        )
        self.exercise_label.pack(pady=25)
        
        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            self.break_frame,
            length=600,
            mode='determinate',
            variable=self.progress_var
        )
        self.progress_bar.pack(pady=20)

        # Placeholders for optional scenery background used during breaks
        # These are created/destroyed at break time so we don't hold image
        # references when not needed.
        self._break_bg_image = None
        self._break_bg_label = None
        # Store previous window state so we can restore after fullscreen break
        self._prev_geometry = None
        self._was_fullscreen = False

    def setup_preferences_frame(self):
        """Create the preferences frame for editing settings inside the main window."""
        style = ttk.Style()
        style.configure("Pref.TFrame",
                       background="#f7fafc")
        style.configure("PrefLabel.TLabel",
                       font=("Arial", 11),
                       foreground="#4a5568",
                       background="#f7fafc")
        style.configure("PrefEntry.TEntry",
                       fieldbackground="white",
                       borderwidth=1,
                       relief="solid")
        
        self.pref_frame = ttk.Frame(self.container, padding="20", style="Pref.TFrame")

        ttk.Label(self.pref_frame, 
                 text="Break Interval (minutes):",
                 style="PrefLabel.TLabel").pack(anchor='w', pady=(0,4))
        self.pref_interval_var = tk.StringVar()
        self.pref_interval_entry = ttk.Entry(self.pref_frame,
                                           textvariable=self.pref_interval_var,
                                           style="PrefEntry.TEntry")
        self.pref_interval_entry.pack(fill='x', pady=(0,12))

        ttk.Label(self.pref_frame,
                 text="Break Duration (seconds):",
                 style="PrefLabel.TLabel").pack(anchor='w', pady=(0,4))
        self.pref_duration_var = tk.StringVar()
        self.pref_duration_entry = ttk.Entry(self.pref_frame,
                                           textvariable=self.pref_duration_var,
                                           style="PrefEntry.TEntry")
        self.pref_duration_entry.pack(fill='x', pady=(0,12))

        ttk.Label(self.pref_frame,
                 text="Custom Pause Message:",
                 style="PrefLabel.TLabel").pack(anchor='w', pady=(0,4))
        self.pref_message_var = tk.StringVar()
        self.pref_message_entry = ttk.Entry(self.pref_frame,
                                          textvariable=self.pref_message_var,
                                          style="PrefEntry.TEntry")
        self.pref_message_entry.pack(fill='x', pady=(0,12))

        btn_frame = ttk.Frame(self.pref_frame)
        btn_frame.pack(pady=10)

        self.pref_save_btn = ttk.Button(btn_frame, text="Save", command=self._on_pref_save)
        self.pref_save_btn.pack(side='left', padx=5)
        self.pref_cancel_btn = ttk.Button(btn_frame, text="Cancel", command=self._on_pref_cancel)
        self.pref_cancel_btn.pack(side='left', padx=5)

        # Bind Enter key to save
        self.pref_interval_entry.bind('<Return>', lambda e: self._on_pref_save())
        self.pref_duration_entry.bind('<Return>', lambda e: self._on_pref_save())
        self.pref_message_entry.bind('<Return>', lambda e: self._on_pref_save())

        # Variable used to wait for save/cancel
        self._pref_result_var = None

    def _on_pref_save(self):
        """Validate and save preferences from the pref_frame."""
        # Basic validation
        try:
            minutes = int(self.pref_interval_var.get())
            seconds = int(self.pref_duration_var.get())
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter valid numbers for interval and duration.")
            return

        if not (1 <= minutes <= 60):
            messagebox.showerror("Invalid Interval", "Interval must be between 1 and 60 minutes.")
            return
        if not (5 <= seconds <= 3600):
            messagebox.showerror("Invalid Duration", "Duration must be between 5 and 3600 seconds.")
            return

        # Save values
        self.break_interval = minutes * 60
        self.break_duration = seconds
        msg = self.pref_message_var.get().strip()
        self.custom_pause_message = msg if msg else "Please take a short break!"

        # Signal waiting caller and return to main frame
        if isinstance(self._pref_result_var, tk.Variable):
            try:
                self._pref_result_var.set(True)
            except Exception:
                pass

        # Hide preferences and show main
        self.pref_frame.pack_forget()
        self.main_frame.pack(fill='both', expand=True)
        self.update_preferences_display()

    def _on_pref_cancel(self):
        """Cancel preferences editing."""
        if isinstance(self._pref_result_var, tk.Variable):
            try:
                self._pref_result_var.set(False)
            except Exception:
                pass
        # Hide preferences and show main
        self.pref_frame.pack_forget()
        self.main_frame.pack(fill='both', expand=True)
        
    def block_screen_for_break(self, break_duration, on_complete=None):
        """Switch to break screen and start break timer.

        on_complete: optional callback invoked (in the GUI thread) after the break finishes.
        """
        # Store and change window state to fullscreen so the break is prominent.
        try:
            # Save geometry and fullscreen/state so we can restore later
            prev_geom = None
            try:
                prev_geom = self.root.geometry()
            except Exception:
                prev_geom = None
            prev_state = None
            try:
                prev_state = self.root.state()
            except Exception:
                prev_state = None
            prev_fullscreen = False
            try:
                prev_fullscreen = bool(self.root.attributes("-fullscreen"))
            except Exception:
                prev_fullscreen = False

            self._prev_state = {
                'geometry': prev_geom,
                'state': prev_state,
                'fullscreen': prev_fullscreen,
            }

            # Enter fullscreen
            try:
                self.root.attributes("-fullscreen", True)
            except Exception:
                # Fallback: maximize the window if fullscreen isn't supported
                try:
                    self.root.state('zoomed')
                except Exception:
                    pass
        except Exception:
            # If any issue, continue without blocking (we'll still show break_frame)
            self._prev_state = {'geometry': None, 'state': None, 'fullscreen': False}

        # Hide main frame and show break frame
        self.main_frame.pack_forget()
        self.break_frame.pack(fill='both', expand=True)
        
        # Update exercise text
        exercise_text = random.choice(self.eye_exercises)
        self.exercise_label.config(text=exercise_text)
        
        # Reset progress bar
        self.progress_var.set(0)
        
        # Try to place the scenic background image (scenery.jpg) stretched to screen
        try:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            # Prefer images/scenery.jpg inside the repository
            scenery_path = os.path.join(base_dir, 'images', 'scenery.jpg')
            if os.path.exists(scenery_path):
                # Resize to current screen size
                screen_w = self.root.winfo_screenwidth()
                screen_h = self.root.winfo_screenheight()
                img = Image.open(scenery_path).convert('RGBA')
                img = img.resize((screen_w, screen_h), Image.LANCZOS)
                self._break_bg_image = ImageTk.PhotoImage(img)
                # If an existing label exists, replace its image; otherwise create one
                if self._break_bg_label:
                    try:
                        self._break_bg_label.config(image=self._break_bg_image)
                    except Exception:
                        self._break_bg_label = tk.Label(self.break_frame, image=self._break_bg_image)
                        self._break_bg_label.place(x=0, y=0, relwidth=1, relheight=1)
                else:
                    self._break_bg_label = tk.Label(self.break_frame, image=self._break_bg_image)
                    self._break_bg_label.place(x=0, y=0, relwidth=1, relheight=1)
                # Ensure UI elements are on top of the background
                try:
                    self.break_timer_label.lift()
                    self.exercise_label.lift()
                    self.progress_bar.lift()
                except Exception:
                    pass
        except Exception:
            # If background load fails for any reason, ignore and continue
            self._break_bg_image = None
            self._break_bg_label = None

        start_time = time.time()
        
        def update_break_timer():
            elapsed_time = time.time() - start_time
            remaining_time = max(0, break_duration - elapsed_time)
            
            if remaining_time <= 0:
                # Remove scenic background label if it exists and clear image refs
                try:
                    if self._break_bg_label:
                        # Clear image first to avoid platform-specific issues
                        try:
                            self._break_bg_label.config(image='')
                        except Exception:
                            pass
                        try:
                            self._break_bg_label.destroy()
                        except Exception:
                            try:
                                self._break_bg_label.place_forget()
                            except Exception:
                                pass
                        self._break_bg_label = None
                        self._break_bg_image = None
                except Exception:
                    pass

                self.break_frame.pack_forget()
                self.main_frame.pack(fill='both', expand=True)

                # Restore previous window state (exit fullscreen and restore geometry/state)
                try:
                    # First, explicitly turn off fullscreen (safer across platforms)
                    try:
                        self.root.attributes("-fullscreen", False)
                    except Exception:
                        pass
                    # Restore window state if it was changed (e.g., zoomed)
                    try:
                        if isinstance(self._prev_state, dict):
                            prev_state = self._prev_state.get('state')
                            prev_geom = self._prev_state.get('geometry')
                            if prev_state and prev_state != 'normal':
                                try:
                                    self.root.state(prev_state)
                                except Exception:
                                    try:
                                        self.root.state('normal')
                                    except Exception:
                                        pass
                            if prev_geom:
                                try:
                                    self.root.geometry(prev_geom)
                                except Exception:
                                    pass
                    except Exception:
                        # As a final fallback, attempt to normalize the window
                        try:
                            self.root.state('normal')
                        except Exception:
                            pass
                except Exception:
                    pass
                # Run callback (if provided) in mainloop
                if callable(on_complete):
                    try:
                        self.root.after(0, on_complete)
                    except Exception:
                        try:
                            on_complete()
                        except Exception:
                            pass
                return
            
            minutes, seconds = divmod(int(remaining_time), 60)
            if minutes > 0:
                timer_text = f"{minutes}:{seconds:02d}"
            else:
                timer_text = f"{seconds} seconds"
                
            self.break_timer_label.config(text=f"Time remaining: {timer_text}")
            
            # Update progress bar
            progress = ((break_duration - remaining_time) / break_duration) * 100
            self.progress_var.set(progress)
            
            self.root.after(100, update_break_timer)
        
        # Start the timer update
        update_break_timer()

    def ensure_settings_exist(self):
        """Ensure break settings are set, asking the user if necessary."""
        if not self.load_settings() or self.break_interval == 0 or self.break_duration == 0:
            self.set_initial_break_settings()
            self.save_settings()

    def save_settings(self):
        """Save settings to a file."""
        settings = {
            "break_interval": self.break_interval,
            "break_duration": self.break_duration,
            "custom_pause_message": self.custom_pause_message,
        }
        with open(self.SETTINGS_FILE, "w") as file:
            json.dump(settings, file)

    def load_settings(self):
        """Load settings from a file."""
        try:
            with open(self.SETTINGS_FILE, "r") as file:
                settings = json.load(file)
                self.break_interval = settings.get("break_interval", 0)
                self.break_duration = settings.get("break_duration", 0)
                self.custom_pause_message = settings.get("custom_pause_message", "Please take a short break!")
                return True
        except (FileNotFoundError, json.JSONDecodeError):
            return False

    def get_valid_input(self, prompt, min_val, max_val):
        """Prompt the user for valid input within a range."""
        while True:
            try:
                dialog = tk.Toplevel(self.root)
                dialog.title("CVShield Input")
                dialog.geometry("400x150")
                dialog.transient(self.root)
                dialog.grab_set()

                ttk.Label(dialog, text=prompt, wraplength=350).pack(pady=10)
                entry = ttk.Entry(dialog)
                entry.pack(pady=5)
                
                result = tk.StringVar()
                
                def submit():
                    try:
                        value = int(entry.get())
                        if min_val <= value <= max_val:
                            result.set(str(value))
                            dialog.destroy()
                        else:
                            messagebox.showerror("Invalid Input", 
                                               f"Please enter a number between {min_val} and {max_val}.")
                    except ValueError:
                        messagebox.showerror("Invalid Input", 
                                           "Please enter a valid number.")
                
                def on_enter(event):
                    submit()
                
                entry.bind('<Return>', on_enter)
                ttk.Button(dialog, text="OK", command=submit).pack(pady=10)
                
                # Focus the entry widget
                entry.focus_set()
                
                dialog.wait_window()
                
                if result.get():
                    return int(result.get())
                    
            except Exception as e:
                messagebox.showerror("Error", f"An error occurred: {str(e)}")
                continue

    def set_initial_break_settings(self):
        """Show the in-window preferences UI and require the user to save initial settings."""
        # Show preferences frame as modal-ish and require save
        # Populate fields with sensible defaults if empty
        if self.break_interval and self.break_interval > 0:
            self.pref_interval_var.set(str(self.break_interval // 60))
        else:
            self.pref_interval_var.set("20")
        if self.break_duration and self.break_duration > 0:
            self.pref_duration_var.set(str(self.break_duration))
        else:
            self.pref_duration_var.set("30")
        self.pref_message_var.set(self.custom_pause_message)

        # Hide other frames and show prefs
        self.main_frame.pack_forget()
        self.break_frame.pack_forget()
        self.pref_frame.pack(fill='both', expand=True)

        # Prepare variable to wait on
        self._pref_result_var = tk.BooleanVar(self.root, False)
        # Don't allow cancel during initial setup
        self.pref_cancel_btn.pack_forget()

        # Wait until user saves
        self.root.wait_variable(self._pref_result_var)
        # restore cancel button visibility
        try:
            self.pref_cancel_btn.pack(side='left', padx=5)
        except Exception:
            pass

    def update_preferences_display(self):
        """Update the display of current preferences in the settings frame."""
        if self.break_interval > 0 and self.break_duration > 0:
            interval_minutes = self.break_interval // 60
            self.interval_label.config(text=f"Interval: {interval_minutes} minutes")
            self.duration_label.config(text=f"Duration: {self.break_duration} seconds")
            self.message_label.config(text=f"Message: {self.custom_pause_message}")

    def edit_break(self, _=None):
        """Allow the user to temporarily edit break settings for the current session."""
        # Show preferences in same window for temporary edit
        # Populate current values
        self.pref_interval_var.set(str(self.break_interval // 60 if self.break_interval else 20))
        self.pref_duration_var.set(str(self.break_duration if self.break_duration else 30))
        self.pref_message_var.set(self.custom_pause_message)

        # Show pref frame
        self.main_frame.pack_forget()
        self.pref_frame.pack(fill='both', expand=True)

        # Wait for save/cancel
        self._pref_result_var = tk.BooleanVar(self.root, False)
        self.root.wait_variable(self._pref_result_var)

        # If saved, we already updated break_interval and break_duration in _on_pref_save
        self.save_settings()
        self.update_preferences_display()

    def get_custom_pause_message(self):
        """Prompt the user to set a custom pause message."""
        dialog = tk.Toplevel(self.root)
        dialog.title("Custom Pause Message")
        dialog.geometry("400x200")
        dialog.transient(self.root)
        dialog.grab_set()

        ttk.Label(dialog,
                 text="Enter a custom message to display during breaks\n(Leave blank for default):",
                 wraplength=350).pack(pady=10)
        
        entry = ttk.Entry(dialog, width=50)
        entry.pack(pady=10, padx=20)
        
        result = tk.StringVar()
        
        def submit():
            result.set(entry.get())
            dialog.destroy()
        
        ttk.Button(dialog, text="OK", command=submit).pack(pady=10)
        
        # Focus the entry widget
        entry.focus_set()
        
        dialog.wait_window()
        
        custom_message = result.get()
        if not custom_message.strip():
            return "Please take a short break!"
        return custom_message

    def reset_preferences(self, _=None):
        """Reset the user's preferences and ask them to reconfigure."""
        response = messagebox.askyesno(
            "Reset Preferences",
            "Are you sure you want to reset your preferences? This will delete all saved settings.",
            icon="warning"
        )
        if response:  # User clicked Yes
            self.break_interval = 0
            self.break_duration = 0
            self.custom_pause_message = "Please take a short break!"  # Reset to default
            self.save_settings()
            self.set_initial_break_settings()
            self.save_settings()
            self.update_preferences_display()

    def edit_preferences(self, _=None):
        """Allow the user to edit their preferences."""
        # Populate fields with current values
        self.pref_interval_var.set(str(self.break_interval // 60 if self.break_interval else 20))
        self.pref_duration_var.set(str(self.break_duration if self.break_duration else 30))
        self.pref_message_var.set(self.custom_pause_message)

        # Show preferences frame
        self.main_frame.pack_forget()
        self.pref_frame.pack(fill='both', expand=True)

        # Wait for save/cancel
        self._pref_result_var = tk.BooleanVar(self.root, False)
        self.root.wait_variable(self._pref_result_var)

        # Persist and update
        self.save_settings()
        self.update_preferences_display()


if __name__ == "__main__":
    # Create and run the application without system tray initially
    app = CVShield()
    app.root.mainloop()