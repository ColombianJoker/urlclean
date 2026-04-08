#!/usr/bin/env uv run
# /// script
# dependencies = [
#   "rumps",
# ]
# ///
import os
import subprocess
from urllib.parse import parse_qs, unquote, urlparse

import rumps

# Path to your specific sound file
SOUND_PATH = "/System/Library/Sounds/Bottle.aiff"


class URLCleanerApp(rumps.App):
    def __init__(self):
        super(URLCleanerApp, self).__init__("Clean", icon=None, template=True)
        self.title = "🫧"

    def get_clipboard(self):
        """Reads the macOS clipboard."""
        return subprocess.check_output("pbpaste", env={"LANG": "en_US.UTF-8"}).decode(
            "utf-8"
        )

    def set_clipboard(self, text):
        """Writes text back to the macOS clipboard."""
        process = subprocess.Popen(["pbcopy"], stdin=subprocess.PIPE)
        process.communicate(input=text.encode("utf-8"))

    def play_bottle_sound(self):
        """Plays the bottle sound using the macOS native afplay utility."""
        if os.path.exists(SOUND_PATH):
            os.system(f"afplay {SOUND_PATH}")
        else:
            # Fallback to system beep if the specific bottle path differs
            os.system("afplay /System/Library/Sounds/Tink.aiff")

    def clean_url_logic(self, raw_url):
        """The extraction logic for tracker parameters."""
        try:
            parsed = urlparse(raw_url)
            query_params = parse_qs(parsed.query)

            # Common tracker keys
            target_keys = ["url", "dest", "link", "target", "u"]

            for key in target_keys:
                if key in query_params:
                    return unquote(query_params[key][0])

            return raw_url
        except:
            return raw_url

    @rumps.clicked("Clean Clipboard URL")
    def clean_button(self, _):
        content = self.get_clipboard().strip()

        # Check if it looks like a URL
        if content.startswith("http"):
            cleaned = self.clean_url_logic(content)

            if cleaned != content:
                self.set_clipboard(cleaned)
                self.play_bottle_sound()
                rumps.notification(
                    "URL Cleaned",
                    "Success",
                    "The cleaned URL is now in your clipboard.",
                )
            else:
                rumps.notification(
                    "URL Cleaner",
                    "No tracker found",
                    "The URL appears to be already clean.",
                )
        else:
            rumps.notification(
                "URL Cleaner",
                "Invalid Content",
                "Clipboard does not contain a valid URL.",
            )

    @rumps.clicked("Quit")
    def quit_app(self, _):
        rumps.quit_application()


if __name__ == "__main__":
    URLCleanerApp().run()
