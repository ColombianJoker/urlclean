#!/usr/bin/env uv run
# /// script
# dependencies = [
#   "rumps",
# ]
# ///

import os
import re
import shlex
import subprocess
from urllib.parse import parse_qs, unquote, urlparse

import rumps

CONFIG_PATH = os.path.expanduser("~/.urlclean")
DEFAULT_FALLBACK = "/System/Library/Sounds/Tink.aiff"


def parse_config_file():
    """Reads the ~/.urlclean file and returns a dictionary of keys and values."""
    config = {}
    if not os.path.exists(CONFIG_PATH):
        return config
    try:
        with open(CONFIG_PATH, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, val = line.split("=", 1)
                    key, val = key.strip(), val.strip()
                    # Remove surrounding quotes if they exist
                    if (val.startswith('"') and val.endswith('"')) or (
                        val.startswith("'") and val.endswith("'")
                    ):
                        val = val[1:-1]
                    config[key] = val
    except Exception as e:
        print(f"Error parsing config: {e}")
    return config


class URLCleanerApp(rumps.App):
    def __init__(self):
        super(URLCleanerApp, self).__init__(name="Clean")
        self.title = "🫧"

        # Build the initial menu
        self.menu = ["Clean Clipboard URL"]

        # Read the configuration to build dynamic extensions
        self.config = parse_config_file()
        self.extensions_map = {}
        self.build_dynamic_menus()

    def build_dynamic_menus(self):
        """Finds EXT_MENU keys in config and generates menu items for them."""
        extensions = []

        # 1. Identify all menus and their corresponding indices
        for key, title in self.config.items():
            match = re.match(r"EXT_MENU(\d+)", key)
            if match:
                idx = match.group(1)

                cmd = self.config.get(f"EXT_COMMAND{idx}")
                regex_exp = self.config.get(f"EXT_EXP{idx}")
                regex_rep = self.config.get(f"EXT_REP{idx}")

                if cmd:
                    extensions.append(
                        {
                            "idx": int(idx),
                            "title": title,
                            "type": "command",
                            "command": cmd,
                        }
                    )
                elif regex_exp is not None and regex_rep is not None:
                    extensions.append(
                        {
                            "idx": int(idx),
                            "title": title,
                            "type": "regex",
                            "exp": regex_exp,
                            "rep": regex_rep,
                        }
                    )

        # 2. Sort them by their index number
        extensions.sort(key=lambda x: x["idx"])

        # 3. Add to rumps menu and map them for the callback handler
        if extensions:
            self.menu.add(rumps.separator)
            for ext in extensions:
                self.extensions_map[ext["title"]] = ext
                # rumps allows assigning a callback directly to a new MenuItem
                item = rumps.MenuItem(ext["title"], callback=self.handle_extension)
                self.menu.add(item)

    def get_clipboard(self):
        try:
            return subprocess.check_output(
                "pbpaste", env={"LANG": "en_US.UTF-8"}
            ).decode("utf-8")
        except Exception:
            return ""

    def set_clipboard(self, text):
        process = subprocess.Popen(["pbcopy"], stdin=subprocess.PIPE)
        process.communicate(input=text.encode("utf-8"))

    def resolve_sound_path(self):
        """Determines the sound file path dynamically so it updates without restart."""
        # Re-read config just for sound so it can be changed without restarting app
        live_config = parse_config_file()
        sound_setting = live_config.get("SOUND_FILE")

        if not sound_setting:
            return DEFAULT_FALLBACK

        if "/" in sound_setting:
            expanded_path = os.path.expanduser(sound_setting)
            if os.path.isfile(expanded_path):
                return expanded_path
        else:
            user_sound_path = os.path.expanduser(f"~/Library/Sounds/{sound_setting}")
            if os.path.isfile(user_sound_path):
                return user_sound_path

        return DEFAULT_FALLBACK

    def play_notification_sound(self):
        sound_to_play = self.resolve_sound_path()
        os.system(f"afplay '{sound_to_play}'")

    def clean_url_logic(self, raw_url):
        try:
            parsed = urlparse(raw_url)
            query_params = parse_qs(parsed.query)
            target_keys = ["url", "dest", "link", "target", "u", "redirect_to"]

            for key in target_keys:
                if key in query_params:
                    return unquote(query_params[key][0])
            return raw_url
        except Exception:
            return raw_url

    @rumps.clicked("Clean Clipboard URL")
    def clean_button(self, _):
        content = self.get_clipboard().strip()
        if content.startswith("http"):
            cleaned = self.clean_url_logic(content)
            if cleaned != content:
                self.set_clipboard(cleaned)
                self.play_notification_sound()
            else:
                rumps.notification(
                    "URL Cleaner", "Already Clean", "No tracker parameters found."
                )
        else:
            rumps.notification(
                "URL Cleaner", "Invalid Content", "Clipboard does not contain a URL."
            )

    def handle_extension(self, sender):
        """Handler for all dynamically generated extension menus."""
        ext = self.extensions_map.get(sender.title)
        if not ext:
            return

        content = self.get_clipboard()
        if not content:
            rumps.notification(
                "Extension App", "Empty Clipboard", "Nothing to process."
            )
            return

        result = None
        try:
            if ext["type"] == "command":
                cmd = ext["command"]

                # Check if it uses the {} insertion pattern
                if "{}" in cmd:
                    # shlex.quote ensures arbitrary clipboard text doesn't cause shell injection
                    safe_content = shlex.quote(content)
                    final_cmd = cmd.replace("{}", safe_content)
                    proc = subprocess.run(
                        final_cmd, capture_output=True, text=True, shell=True
                    )
                    result = proc.stdout
                else:
                    # Stdin -> Stdout pattern
                    proc = subprocess.run(
                        cmd, input=content, capture_output=True, text=True, shell=True
                    )
                    result = proc.stdout

            elif ext["type"] == "regex":
                # Apply Regex replacement
                result = re.sub(ext["exp"], ext["rep"], content)

        except Exception as e:
            rumps.notification("Extension Error", sender.title, str(e))
            return

        # If a valid result was generated and it actually changed the text
        if result is not None and result != content:
            # Subprocess commands often add a trailing newline; we usually want to strip it
            # if the original clipboard didn't have one.
            if not content.endswith("\n") and result.endswith("\n"):
                result = result[:-1]

            self.set_clipboard(result)
            self.play_notification_sound()


if __name__ == "__main__":
    URLCleanerApp().run()
