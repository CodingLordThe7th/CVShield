import rumps
import pygame
import time
import random
import json
from datetime import timedelta


class CVShield(rumps.App):
    SETTINGS_FILE = "cvshield_settings.json"

    def __init__(self):
        super().__init__("😎 CVShield - Inactive", quit_button=None)
        self.icon = None
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


        # Ensure settings exist at startup
        self.ensure_settings_exist()

        # Initialize menu
        self.menu.add(rumps.MenuItem("Start Timer", callback=self.start_timer))
        self.menu.add(rumps.MenuItem("Edit Preferences", callback=self.edit_preferences))
        self.menu.add(rumps.MenuItem("Reset Preferences", callback=self.reset_preferences))
        self.timer = rumps.Timer(self.track_time, 1)  # Check every second

        # Ensure Quit is always added last
        self.ensure_quit_last()

        # Display preferences in the menu before starting the timer
        self.update_preferences_display()

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
                self.custom_pause_message = settings.get("custom_pause_message", "")
                return True
        except (FileNotFoundError, json.JSONDecodeError):
            return False

    def ensure_quit_last(self):
        """Ensure the Quit button is always the last item in the menu."""
        if "Quit" in self.menu:
            self.menu.pop("Quit")  # Remove it temporarily
        self.menu.add(rumps.MenuItem("Quit", callback=rumps.quit_application))  # Add it back as the last item

    def reset_preferences(self, _):
        """Reset the user's preferences and ask them to reconfigure."""
        response = rumps.alert(
            title="Reset Preferences",
            message="Are you sure you want to reset your preferences? This will delete all saved settings.",
            ok="Yes, Reset",
            cancel="Cancel",
        )
        if response == 1:  # User clicked "Yes, Reset"
            self.break_interval = 0
            self.break_duration = 0
            self.custom_pause_message = "Please take a short break!"  # Reset to default
            self.save_settings()
            self.set_initial_break_settings()
            self.save_settings()
        self.ensure_quit_last()

    def edit_preferences(self, _):
        """Allow the user to edit their preferences."""
        self.set_initial_break_settings()
        self.custom_pause_message = self.get_custom_pause_message()
        self.save_settings()
        self.update_preferences_display()  # Update preferences in the menu
        self.ensure_quit_last()

    def get_custom_pause_message(self):
        """Prompt the user to set a custom pause message."""
        custom_message = rumps.Window(
            "Enter a custom message to display during breaks (Leave blank for default):",
            title="Custom Pause Message"
        ).run().text
        if not custom_message.strip():
            return "Please take a short break!"  # Default message if left blank
        return custom_message

    def set_initial_break_settings(self):
        """Prompt user to configure break settings at the first run or after reset."""
        break_type = self.get_valid_input(
            "Choose your break type:\n"
            "1. Short (1-20 min interval, 20-60 sec duration)\n"
            "2. Medium (21-40 min interval, 60-180 sec duration)\n"
            "3. Long (41-60 min interval, 180-300 sec duration)\n"
            "Enter the number for your choice:",
            1, 3
        )

        # Set interval and duration based on selection
        if break_type == 1:  # Short break
            self.break_interval = self.get_valid_input("Set interval (1-20 minutes):", 1, 20) * 60
            self.break_duration = self.get_valid_input("Set duration (20-60 seconds):", 20, 60)
        elif break_type == 2:  # Medium break
            self.break_interval = self.get_valid_input("Set interval (21-40 minutes):", 21, 40) * 60
            self.break_duration = self.get_valid_input("Set duration (60-180 seconds):", 60, 180)
        elif break_type == 3:  # Long break
            self.break_interval = self.get_valid_input("Set interval (41-60 minutes):", 41, 60) * 60
            self.break_duration = self.get_valid_input("Set duration (180-300 seconds):", 180, 300)

    def update_preferences_display(self):
        """Update the display of current preferences in the menu."""
        self.menu.clear()
        self.menu.add(rumps.MenuItem("Start Timer", callback=self.start_timer))

        # Display preferences before starting the timer
        if self.break_interval > 0 and self.break_duration > 0:
            interval_minutes = self.break_interval // 60
            self.menu.add(f"Current Interval: {interval_minutes} minutes")
            self.menu.add(f"Current Duration: {self.break_duration} seconds")
            self.menu.add(f"Pause Message: {self.custom_pause_message}")

        self.menu.add(rumps.MenuItem("Edit Preferences", callback=self.edit_preferences))
        self.menu.add(rumps.MenuItem("Reset Preferences", callback=self.reset_preferences))
        if self.is_timer_running:
            self.menu.add(rumps.MenuItem("Edit Break", callback=self.edit_break))  # Only visible when timer is running
        self.ensure_quit_last()

    def edit_break(self, _):
        """Allow the user to temporarily edit break settings for the current session."""
        rumps.alert(
            title="Edit Break",
            message="You are temporarily editing the break settings for this session only.",
            ok="Continue"
        )

        # Identify the current break type to restrict input ranges
        if 60 <= self.break_interval <= 20 * 60:
            break_type = "Short (1-20 minutes, 20-60 seconds)"
            min_interval, max_interval = 1, 20
            min_duration, max_duration = 20, 60
        elif 21 * 60 <= self.break_interval <= 40 * 60:
            break_type = "Medium (21-40 minutes, 60-180 seconds)"
            min_interval, max_interval = 21, 40
            min_duration, max_duration = 60, 180
        elif 41 * 60 <= self.break_interval <= 60 * 60:
            break_type = "Long (41-60 minutes, 180-300 seconds)"
            min_interval, max_interval = 41, 60
            min_duration, max_duration = 180, 300
        else:
            rumps.alert("Unable to determine current break type. Restart the timer to reset settings.")
            return

        rumps.alert(f"You are editing a {break_type} break.")

        # Allow user to edit interval and duration within the valid range for the break type
        self.break_interval = self.get_valid_input(
            f"Set interval (in minutes, {min_interval}-{max_interval}):", min_interval, max_interval
        ) * 60
        self.break_duration = self.get_valid_input(
            f"Set duration (in seconds, {min_duration}-{max_duration}):", min_duration, max_duration
        )
        self.custom_pause_message = self.get_custom_pause_message()  # Allow temporary pause message change

        rumps.alert("Break settings updated for this session only!")

    def start_timer(self, _):
        """Start the timer and update the menu."""
        # Disable the "Start Timer" button
        self.menu["Start Timer"].set_callback(None)

        if self.break_interval == 0 or self.break_duration == 0:
            self.set_initial_break_settings()

        # Save settings in case they were just configured
        self.save_settings()

        # Remove preferences options from the menu if they exist
        if "Edit Preferences" in self.menu:
            self.menu.pop("Edit Preferences")
        if "Reset Preferences" in self.menu:
            self.menu.pop("Reset Preferences")

        # Add Pause, Stop Timer, and Edit Break buttons
        self.menu.add(rumps.MenuItem("Pause Timer", callback=self.toggle_pause_timer))
        self.menu.add(rumps.MenuItem("Stop Timer", callback=self.stop_timer))
        self.menu.add(rumps.MenuItem("Edit Break", callback=self.edit_break))  # Visible only when timer is running

        self.start_time = time.time()
        self.is_timer_running = True
        self.sent_notification = False
        self.timer.start()
        self.title = "😎 CVShield - Timer Running"

        self.ensure_quit_last()

    def stop_timer(self, _):
        """Stop the timer and reset the menu."""
        self.is_timer_running = False
        self.timer.stop()
        self.title = "😎 CVShield - Inactive"

        # Remove Pause, Stop Timer, and Edit Break buttons
        self.menu.pop("Pause Timer", None)
        self.menu.pop("Stop Timer", None)
        self.menu.pop("Edit Break", None)

        # Re-enable the "Start Timer" button
        self.menu["Start Timer"].set_callback(self.start_timer)

        self.update_preferences_display()
        self.ensure_quit_last()

    def toggle_pause_timer(self, _):
        """Pause or resume the timer."""
        if self.is_paused:
            paused_duration = time.time() - self.pause_time
            self.start_time += paused_duration
            self.is_paused = False
            self.title = "😎 CVShield - Timer Running"
            self.menu["Pause Timer"].title = "Pause Timer"
        else:
            self.is_paused = True
            self.pause_time = time.time()
            self.remaining_time = self.break_interval - (self.pause_time - self.start_time)
            minutes = int(self.remaining_time // 60)
            seconds = int(self.remaining_time % 60)
            self.title = f"😎 CVShield - Paused: {minutes}m {seconds}s left - {self.custom_pause_message}"
            self.menu["Pause Timer"].title = "Resume Timer"

    def track_time(self, _):
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
                    self.title = f"😎 CVShield - Time until break: 1 minute 1 second"
                else:
                    self.title = f"😎 CVShield - Time until break: 1 minute {seconds} seconds"
            else:
                if seconds == 1:
                    self.title = f"😎 CVShield - Time until break: {minutes} minutes 1 second"
                else:
                    self.title = f"😎 CVShield - Time until break: {minutes} minutes {seconds} seconds"
        else:
            if seconds == 1:
                self.title = f"😎 CVShield - Time until break: 1 second"
            else:
                self.title = f"😎 CVShield - Time until break: {seconds} seconds"
        # Notify the user 10 seconds before the break
        if 10 <= remaining_time <= 11 and not self.sent_notification:
            rumps.notification(
                title="Break Reminder",
                subtitle="Heads-up!",
                message="Your break starts in 10 seconds.",
            )
            self.sent_notification = True
        elif remaining_time > 10.5:
            # Reset notification flag if we're far from the next break
            self.sent_notification = False



    def start_break(self):
        """Start a break."""
        self.timer.stop()
        self.title = "😎 CVShield - Break!"
        self.sent_notification = False
        self.block_screen_for_break(self.break_duration)
        self.start_time = time.time()
        self.timer.start()
        self.title = "😎 CVShield - Timer Running"

    def block_screen_for_break(self, break_duration):
        """Display a break screen with a random exercise and progress."""
        pygame.init()
        screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)  # Fullscreen window
        pygame.display.set_caption("Break Time!")
        font = pygame.font.SysFont("Arial", 50)
        exercise_font = pygame.font.SysFont("Arial", 40)
        clock = pygame.time.Clock()
        train_x = 0

        start_time = time.time()
        current_exercise = random.choice(self.eye_exercises)  # Randomly select an exercise at the start of the break

        # Get screen dimensions
        screen_width = screen.get_width()
        screen_height = screen.get_height()

        progress_bar_width = 600
        progress_bar_height = 50
        progress_bar_x = (screen_width - progress_bar_width) // 2  # Center the progress bar horizontally
        progress_bar_y = screen_height // 2 + 100  # Vertical position for the progress bar

        running = True
        while running:
            elapsed_time = time.time() - start_time
            remaining_time = max(0, break_duration - elapsed_time)

            if remaining_time <= 0:
                running = False
                continue  # Skip rendering for this iteration

            # Calculate remaining minutes and seconds
            minutes, seconds = divmod(int(remaining_time), 60)

            # Adjust timer format
            if minutes == 0:
                timer_text_content = f"{seconds} seconds"  # Only display seconds if less than a minute
            elif seconds == 0:
                timer_text_content = f"{minutes} minutes"  # Only display minutes if no seconds remain
            else:
                timer_text_content = f"{minutes} minutes {seconds} seconds"  # Display both minutes and seconds

            # Sky background
            screen.fill((135, 206, 250))  # Sky blue background

            # Sun
            pygame.draw.circle(screen, (255, 223, 0), (screen.get_width() - 100, 100), 60)

            # Grey mountains with ice caps (back layer)
            pygame.draw.polygon(
                screen, (169, 169, 169), [(100, 600), (300, 250), (500, 600)]
            )  # Left grey mountain
            pygame.draw.polygon(
                screen, (255, 255, 255), [(275, 275), (300, 250), (325, 275)]
            )  # Ice cap for left grey mountain
            pygame.draw.polygon(
                screen, (169, 169, 169), [(500, 600), (700, 300), (900, 600)]
            )  # Right grey mountain
            pygame.draw.polygon(
                screen, (255, 255, 255), [(675, 325), (700, 300), (725, 325)]
            )  # Ice cap for right grey mountain

            # Ground
            pygame.draw.rect(screen, (139, 69, 19), (0, 600, screen.get_width(), screen.get_height()))  # Brown ground

            # Trees
            for x in range(100, screen.get_width(), 150):
                pygame.draw.rect(screen, (139, 69, 19), (x + 25, 570, 20, 50))  # Tree trunk
                pygame.draw.polygon(
                    screen, (34, 139, 34), [(x, 570), (x + 35, 520), (x + 70, 570)]
                )  # Tree foliage

            # Moving object for eye exercise (multi-car train)
            car_color = (0, 0, 255)
            car_spacing = 160
            num_cars = 5
            train_width = num_cars * car_spacing  # Total train length
            for i in range(num_cars):
                car_x = train_x + i * car_spacing
                pygame.draw.rect(screen, car_color, (car_x, 630, 150, 30))  # Train car body
                pygame.draw.circle(screen, (0, 0, 0), (car_x + 25, 660), 10)  # Left wheel
                pygame.draw.circle(screen, (0, 0, 0), (car_x + 125, 660), 10)  # Right wheel
            train_x += 10  # Move train to the right

            # Reset train position when it fully leaves the screen
            if train_x > screen.get_width():
                train_x = -train_width

            # Render the randomly selected exercise text
            exercise_text = exercise_font.render(current_exercise, True, (255, 255, 255))
            exercise_text_y = progress_bar_y - progress_bar_height - 30  # Position just above the progress bar

            # Draw a hollow white rectangle behind the progress bar (slightly bigger than the progress bar)
            pygame.draw.rect(screen, (255, 255, 255), (progress_bar_x - 5, progress_bar_y - 5, progress_bar_width + 10, progress_bar_height + 10), 5)

            # Draw a progress bar filling from left to right
            progress = (break_duration - remaining_time) / break_duration
            pygame.draw.rect(screen, (0, 255, 0), (progress_bar_x, progress_bar_y, progress_bar_width * progress, progress_bar_height))

            # Render and center the timer text
            timer_text = font.render(timer_text_content, True, (255, 255, 255))
            screen.blit(timer_text, (screen_width // 2 - timer_text.get_width() // 2, 100))

            # Render the exercise text above the progress bar
            screen.blit(exercise_text, (screen_width // 2 - exercise_text.get_width() // 2, exercise_text_y))

            pygame.display.flip()
            clock.tick(30)

        pygame.quit()

    def get_valid_input(self, prompt, min_val, max_val):
        """Prompt the user for valid input within a range."""
        while True:
            response = rumps.Window(prompt, title="CVShield Input").run()
            if response.clicked:
                try:
                    value = int(response.text)
                    if min_val <= value <= max_val:
                        return value
                except ValueError:
                    pass
            rumps.alert(f"Please enter a valid number between {min_val} and {max_val}.")


if __name__ == "__main__":
    CVShield().run()
