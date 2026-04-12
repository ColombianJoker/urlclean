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

# Check if DEBUG is set to "true"
DEBUG_MODE = os.environ.get("DEBUG", "").lower() == "true"


def debug(msg):
    """Prints debug messages to the console if DEBUG_MODE is enabled."""
    if DEBUG_MODE:
        print(f"[DEBUG] {msg}")


# The default configuration replicates the old hardcoded logic using a Python one-liner
DEFAULT_CONFIG = """SOUND_FILE="Bottle.aiff"

# Extension 1: Default Clean Clipboard URL (Extracts nested URLs)
EXT_MENU1="🫧 Clean Clipboard URL"
EXT_COMMAND1="python3 -c 'import sys; from urllib.parse import urlparse, parse_qs, unquote; url=sys.stdin.read().strip(); p=urlparse(url); q=parse_qs(p.query); k=[\\"url\\", \\"dest\\", \\"link\\", \\"target\\", \\"u\\", \\"redirect_to\\"]; res=next((unquote(q[x][0]) for x in k if x in q), url); print(res)'"
"""


def ensure_config_exists():
    """Creates a default configuration file if one does not already exist."""
    if not os.path.exists(CONFIG_PATH):
        debug(f"Config file not found at {CONFIG_PATH}. Creating default config.")
        try:
            with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                f.write(DEFAULT_CONFIG)
            debug("Default config created successfully.")
        except Exception as e:
            debug(f"Failed to create default config: {e}")


def parse_config_file():
    """Reads the config file and returns a dictionary of keys and values."""
    ensure_config_exists()
    config = {}
    debug(f"Parsing config file: {CONFIG_PATH}")
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
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
        debug(f"Loaded {len(config)} configuration items.")
    except Exception as e:
        debug(f"Error parsing config: {e}")
    return config


class URLCleanerApp(rumps.App):
    def __init__(self):
        super(URLCleanerApp, self).__init__(name="Clean")
        self.title = "🫧"

        # The menu is now entirely dynamic based on the config file
        self.menu = []

        self.config = parse_config_file()
        self.extensions_map = {}
        self.build_dynamic_menus()

    def build_dynamic_menus(self):
        """Finds EXT_MENU keys in config and generates menu items for them."""
        extensions = []
        debug("Building dynamic menus based on config.")

        for key, title in self.config.items():
            match = re.match(r"EXT_MENU(\d+)", key)
            if match:
                idx = match.group(1)
                cmd = self.config.get(f"EXT_COMMAND{idx}")
                e_cmd = self.config.get(f"EXT_ECOMMAND{idx}")
                regex_exp = self.config.get(f"EXT_EXP{idx}")
                regex_rep = self.config.get(f"EXT_REP{idx}")
                placeholder = self.config.get(f"EXT_REPLACEMENT{idx}", "{}")

                if e_cmd:
                    extensions.append(
                        {
                            "idx": int(idx),
                            "title": title,
                            "type": "ecommand",
                            "command": e_cmd,
                        }
                    )
                elif cmd:
                    extensions.append(
                        {
                            "idx": int(idx),
                            "title": title,
                            "type": "command",
                            "command": cmd,
                            "placeholder": placeholder,
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

        extensions.sort(key=lambda x: x["idx"])

        if extensions:
            debug(f"Adding {len(extensions)} extensions to menu.")
            for ext in extensions:
                self.extensions_map[ext["title"]] = ext
                self.menu.add(
                    rumps.MenuItem(ext["title"], callback=self.handle_extension)
                )
        else:
            debug("No extensions found to add to menu.")

    def get_clipboard(self):
        try:
            content = subprocess.check_output(
                "pbpaste", env={"LANG": "en_US.UTF-8"}
            ).decode("utf-8")
            debug(f"Clipboard read. Length: {len(content)}")
            return content
        except Exception as e:
            debug(f"Failed to read clipboard: {e}")
            return ""

    def set_clipboard(self, text):
        try:
            process = subprocess.Popen(["pbcopy"], stdin=subprocess.PIPE)
            process.communicate(input=text.encode("utf-8"))
            debug("Clipboard successfully updated.")
        except Exception as e:
            debug(f"Failed to set clipboard: {e}")

    def resolve_sound_path(self):
        sound_setting = self.config.get("SOUND_FILE")
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
        debug(f"Playing sound: {sound_to_play}")
        os.system(f"afplay '{sound_to_play}'")

    def handle_extension(self, sender):
        """Handler for all dynamically generated extension menus."""
        debug(f"Menu item clicked: {sender.title}")
        ext = self.extensions_map.get(sender.title)
        if not ext:
            debug("Extension mapping not found.")
            return

        content = ""
        if ext["type"] != "ecommand":
            content = self.get_clipboard()
            if not content:
                debug("Clipboard is empty. Aborting.")
                rumps.notification(
                    "URL Cleaner", "Empty Clipboard", "Nothing to process."
                )
                return

        result = None
        try:
            if ext["type"] == "ecommand":
                debug(f"Executing ecommand: {ext['command']}")
                proc = subprocess.run(
                    ext["command"], capture_output=True, text=True, shell=True
                )
                result = proc.stdout
            elif ext["type"] == "command":
                if ext["placeholder"] in ext["command"]:
                    final_cmd = ext["command"].replace(
                        ext["placeholder"], shlex.quote(content)
                    )
                    debug(f"Executing command with placeholder replacement.")
                    proc = subprocess.run(
                        final_cmd, capture_output=True, text=True, shell=True
                    )
                else:
                    debug(f"Executing command via stdin.")
                    proc = subprocess.run(
                        ext["command"],
                        input=content,
                        capture_output=True,
                        text=True,
                        shell=True,
                    )
                result = proc.stdout
            elif ext["type"] == "regex":
                debug(f"Executing regex substitution. Exp: {ext['exp']}")
                result = re.sub(ext["exp"], ext["rep"], content)

            debug(f"Operation completed. Result length: {len(result) if result else 0}")
        except Exception as e:
            debug(f"Error during execution: {e}")
            rumps.notification("Extension Error", sender.title, str(e))
            return

        if result is not None:
            # Preserve missing trailing newlines from original clipboard content
            if not content.endswith("\n") and result.endswith("\n"):
                result = result[:-1]

            # Don't overwrite clipboard or play sound if nothing actually changed
            if result.strip() == content.strip():
                debug("Result matches original content. No changes made.")
                rumps.notification(
                    "URL Cleaner",
                    "Already Clean",
                    "No changes were made to the clipboard.",
                )
                return

            self.set_clipboard(result)
            self.play_notification_sound()


if __name__ == "__main__":
    debug("Starting URL Cleaner App.")
    URLCleanerApp().run()
