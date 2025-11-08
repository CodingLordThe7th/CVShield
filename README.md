# CVShield - Eye Health and Break Timer

CVShield is a Python-based desktop application designed to protect your eye health by reminding you to take regular breaks during computer use. It features a clean interface, customizable break intervals, and fullscreen break reminders with calming scenery.

## Features

- 🕒 Customizable break intervals and durations
- 👀 Randomized eye exercises during breaks
- 🖼️ Fullscreen break mode with scenic backgrounds
- 💻 System tray integration for easy access
- ⚙️ Configurable preferences
- 📝 Custom break messages

## Installation

1. Ensure you have Python 3.x installed on your system
2. Clone this repository:
```bash
git clone https://github.com/CodingLordThe7th/CVShield.git
cd CVShield
```

3. Install required dependencies:
```bash
pip install pillow pystray
```

## Usage

1. Run the application:
```bash
python CVShield.py
```

2. The app will start with default settings (20-minute intervals, 30-second breaks)
3. Use "Edit Preferences" to customize:
   - Break interval (1-60 minutes)
   - Break duration (5-3600 seconds)
   - Custom pause message

### Controls

- **Start Timer**: Begin the break countdown
- **Pause/Resume**: Temporarily pause the timer
- **Edit Break**: Modify current session settings
- **Edit Preferences**: Change default settings
- **Reset Preferences**: Restore default settings

### System Tray

CVShield minimizes to your system tray for easy access. Right-click the tray icon to:
- Show/hide the main window
- Start/stop the timer
- Access preferences
- Quit the application

## Break Screen

During breaks, CVShield:
- Displays a fullscreen window with calming scenery
- Shows a countdown timer
- Suggests random eye exercises
- Displays progress toward break completion

## Directory Structure

```
CVShield/
├── CVShield.py        # Main application
├── images/            # Image assets
│   ├── logo.png      # Application icon
│   └── scenery.jpg   # Break screen background
└── cvshield_settings.json  # User preferences
```

## Contributing

Feel free to open issues or submit pull requests with improvements. Some areas for potential enhancement:
- Additional background images
- More eye exercises
- Break statistics tracking
- Multi-monitor support
- Localization

## License

This project is available for use under open-source terms. See LICENSE file for details.

## Credits

- Eye exercises curated from professional vision care recommendations
- Built with Python and Tkinter
- Uses PIL for image processing
- System tray integration via pystray

---

Built with ❤️ for healthy eyes 👀