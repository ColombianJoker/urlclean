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

SOUND_PATH = "/System/Library/Sounds/Bottle.aiff"


class URLCleanerApp(rumps.App):
    def __init__(self):
        # Give it a proper internal name
        super(URLCleanerApp, self).__init__(name="Clean")

        # Explicitly set the menu items
        self.menu = ["Clean Clipboard URL"]

        # Set the visual icon
        self.title = "🫧"

    def get_clipboard(self):
        try:
            return subprocess.check_output(
                "pbpaste", env={"LANG": "en_US.UTF-8"}
            ).decode("utf-8")
        except:
            return ""

    def set_clipboard(self, text):
        process = subprocess.Popen(["pbcopy"], stdin=subprocess.PIPE)
        process.communicate(input=text.encode("utf-8"))

    def play_bottle_sound(self):
        if os.path.exists(SOUND_PATH):
            os.system(f"afplay {SOUND_PATH}")
        else:
            os.system("afplay /System/Library/Sounds/Tink.aiff")

    def clean_url_logic(self, raw_url):
        try:
            parsed = urlparse(raw_url)
            query_params = parse_qs(parsed.query)
            target_keys = ["url", "dest", "link", "target", "u", "redirect_to"]

            for key in target_keys:
                if key in query_params:
                    return unquote(query_params[key][0])
            return raw_url
        except:
            return raw_url

    # The string here MUST match the string in self.menu exactly
    @rumps.clicked("Clean Clipboard URL")
    def clean_button(self, _):
        content = self.get_clipboard().strip()

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
                    "URL Cleaner", "Already Clean", "No tracker parameters found."
                )
        else:
            rumps.notification(
                "URL Cleaner", "Invalid Content", "Clipboard does not contain a URL."
            )


if __name__ == "__main__":
    URLCleanerApp().run()
