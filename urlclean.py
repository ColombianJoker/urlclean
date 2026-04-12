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
from datetime import datetime
from urllib.parse import parse_qs, unquote, urlparse

import rumps

CONFIG_PATH = os.path.expanduser("~/.urlclean")
LOG_PATH = os.path.expanduser("~/.urlclean.log")
DEFAULT_FALLBACK = "/System/Library/Sounds/Tink.aiff"

# ==========================================
# 🛠️ DEBUG MODE CONFIGURATION
# ==========================================
# 1. Check if launched via terminal with DEBUG=true
DEBUG_MODE = os.environ.get("DEBUG", "").lower() == "true"

# 2. Check the ~/.urlclean file for a DEBUG=true option (Great for Finder)
if not DEBUG_MODE and os.path.exists(CONFIG_PATH):
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            for line in f:
                if (
                    line.strip().replace('"', "").replace("'", "").lower()
                    == "debug=true"
                ):
                    DEBUG_MODE = True
                    break
    except Exception:
        pass

# ==========================================
# 🛠️ MAC OS FINDER FIX
# ==========================================
APP_ENV = os.environ.copy()
APP_ENV["LANG"] = "en_US.UTF-8"
APP_ENV["LC_ALL"] = "en_US.UTF-8"
APP_ENV["PATH"] = (
    f"/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:{APP_ENV.get('PATH', '')}"
)

# Prevent bundled app Python paths from crashing system Python subprocesses
APP_ENV.pop("PYTHONHOME", None)
APP_ENV.pop("PYTHONPATH", None)


def debug(msg):
    """Writes debug messages ONLY if DEBUG_MODE is True."""
    if not DEBUG_MODE:
        return

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] [DEBUG] {msg}\n"

    print(log_entry.strip())
    try:
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(log_entry)
    except Exception:
        pass


DEFAULT_CONFIG = """SOUND_FILE="Bottle.aiff"
DEBUG=false

# Extension 1: Default Clean Clipboard URL
EXT_MENU1="🫧 Clean Clipboard URL"
EXT_COMMAND1="python3 -c 'import sys; from urllib.parse import urlparse, parse_qs, unquote; url=sys.stdin.read().strip(); p=urlparse(url); q=parse_qs(p.query); k=[\\"url\\", \\"dest\\", \\"link\\", \\"target\\", \\"u\\", \\"redirect_to\\"]; res=next((unquote(q[x][0]) for x in k if x in q), url); print(res)'"
"""


def ensure_config_exists():
    if not os.path.exists(CONFIG_PATH):
        debug(f"Config file not found. Creating default at {CONFIG_PATH}.")
        try:
            with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                f.write(DEFAULT_CONFIG)
        except Exception as e:
            debug(f"Failed to create default config: {e}")


def parse_config_file():
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

        self.menu = []
        self.config = parse_config_file()
        self.extensions_map = {}
        self.build_dynamic_menus()

    def build_dynamic_menus(self):
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
            for ext in extensions:
                self.extensions_map[ext["title"]] = ext
                self.menu.add(
                    rumps.MenuItem(ext["title"], callback=self.handle_extension)
                )

    def get_clipboard(self):
        try:
            content = subprocess.check_output("pbpaste", env=APP_ENV).decode("utf-8")
            return content
        except Exception as e:
            debug(f"Failed to read clipboard: {e}")
            return ""

    def set_clipboard(self, text):
        try:
            process = subprocess.Popen(["pbcopy"], env=APP_ENV, stdin=subprocess.PIPE)
            process.communicate(input=text.encode("utf-8"))
            debug("Clipboard successfully updated.")
        except Exception as e:
            debug(f"Failed to set clipboard: {e}")

    def resolve_sound_path(self):
        sound_setting = self.config.get("SOUND_FILE")
        if not sound_setting:
            return DEFAULT_FALLBACK
        if "/" in sound_setting:
            expanded = os.path.expanduser(sound_setting)
            if os.path.isfile(expanded):
                return expanded
        else:
            user_path = os.path.expanduser(f"~/Library/Sounds/{sound_setting}")
            if os.path.isfile(user_path):
                return user_path
        return DEFAULT_FALLBACK

    def play_notification_sound(self):
        sound_to_play = self.resolve_sound_path()
        os.system(f"afplay '{sound_to_play}'")

    def handle_extension(self, sender):
        debug(f"Menu item clicked: {sender.title}")
        ext = self.extensions_map.get(sender.title)
        if not ext:
            return

        content = ""
        if ext["type"] != "ecommand":
            content = self.get_clipboard()
            if not content:
                rumps.notification(
                    "URL Cleaner", "Empty Clipboard", "Nothing to process."
                )
                return

        result = None
        try:
            if ext["type"] == "ecommand":
                debug(f"Executing ecommand: {ext['command']}")
                proc = subprocess.run(
                    ext["command"],
                    capture_output=True,
                    text=True,
                    shell=True,
                    env=APP_ENV,
                )

                if proc.returncode != 0:
                    error_msg = proc.stderr.strip() or "Unknown error"
                    debug(f"Command failed: {error_msg}")
                    rumps.notification("Command Failed", sender.title, error_msg)
                    return
                result = proc.stdout

            elif ext["type"] == "command":
                if ext["placeholder"] in ext["command"]:
                    final_cmd = ext["command"].replace(
                        ext["placeholder"], shlex.quote(content)
                    )
                    proc = subprocess.run(
                        final_cmd,
                        capture_output=True,
                        text=True,
                        shell=True,
                        env=APP_ENV,
                    )
                else:
                    proc = subprocess.run(
                        ext["command"],
                        input=content,
                        capture_output=True,
                        text=True,
                        shell=True,
                        env=APP_ENV,
                    )

                if proc.returncode != 0:
                    error_msg = proc.stderr.strip() or "Unknown error"
                    debug(f"Command failed: {error_msg}")
                    rumps.notification("Command Failed", sender.title, error_msg)
                    return
                result = proc.stdout

            elif ext["type"] == "regex":
                result = re.sub(ext["exp"], ext["rep"], content)

        except Exception as e:
            debug(f"Exception during execution: {e}")
            rumps.notification("Extension Error", sender.title, str(e))
            return

        if result is not None:
            if not content.endswith("\n") and result.endswith("\n"):
                result = result[:-1]

            if result.strip() == content.strip():
                debug("Result matches original content. No changes made.")
                rumps.notification(
                    "URL Cleaner", "Already Clean", "No changes were made."
                )
                return

            self.set_clipboard(result)
            self.play_notification_sound()


if __name__ == "__main__":
    debug("Starting URL Cleaner App.")
    URLCleanerApp().run()
