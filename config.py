# config.py

import csv
import os

# Path to the CSV file where settings are saved.
SETTINGS_FILE = "settings.csv"

# Global dictionary for user settings.
# These settings include the current theme, font preferences, and (for the default theme)
# color properties. It's best to store them all in one place for consistency.
settings = {
    "Theme": "Light",
    "FontFamily": "Arial",
    "FontSize": "10",
    "hFontSize": "12",
    # Default color settings (used for the "Light" theme by default)
    "bg": "white",
    "fg": "black",
    "button_bg": "#f0f0f0",
    "button_fg": "black"
}

# A separate dictionary for theme-specific color settings.
# This allows you to easily switch between themes (e.g., Light and Dark) without changing
# the user settings for font or other properties.
theme_settings = {
    "Light": {
        "bg": "white",
        "fg": "black",
        "button_bg": "#f0f0f0",
        "button_fg": "black"
    },
    "Dark": {
        "bg": "#2e2e2e",
        "fg": "white",
        "button_bg": "#444444",
        "button_fg": "white"
    }
}

def load_settings():
    """
    Load settings from the CSV file.
    If the file does not exist, save the default settings to create it.
    Returns the settings dictionary.
    """
    
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r", newline="", encoding="utf-8") as csvfile:
            reader = csv.reader(csvfile)
            header = next(reader, None)  # Skip the header row, if present.
            for row in reader:
                if len(row) >= 2:
                    key, value = row[0], row[1]
                    settings[key] = value
    else:
        # If the file doesn't exist, create it with default settings.
        save_settings()
    return settings

def save_settings(settings):
    """
    Save the current settings to the CSV file.
    This writes a header row followed by each key-value pair in the settings dictionary.
    """
    
    with open(SETTINGS_FILE, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Setting", "Value"])
        for key, value in settings.items():
            writer.writerow([key, value])
