# 🫧 urlclean

**urlclean** is a lightweight macOS menu bar utility designed to strip tracking parameters and redirect wrappers from URLs in your clipboard. It also features a powerful "Extension" system that allows you to run custom regex or shell commands (like ROT13, Base64, or text transformations) directly on your clipboard content.

---

## ✨ Features

- **One-Click Cleaning:** Instantly extracts the "true" destination from nested redirect URLs (e.g., Google, Amazon, or marketing links).
- **Custom Extensions:** Define your own text processing tools in a simple config file.
- **Audio Feedback:** Plays a customizable system sound when a transformation is successful.
- **Native Integration:** Built with `rumps` for a seamless macOS menu bar experience.

---

## 🚀 Installation

### Prerequisites

- **macOS** (uses `pbcopy`, `pbpaste`, and `afplay`)
- **Python 3.10+**

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/urlclean.git
   cd urlclean
   ```
2. Install dependencies:
   ```bash
   pip install rumps
   ```
3. Run the app:
   ```bash
   python3 urlclean.py
   ```

---

## ⚙️ Configuration (`~/.urlclean`)

The app looks for a configuration file at `~/.urlclean` to customize sounds and add custom menu items.

### Example Configuration

```ini
# Sound played on successful clean (searches ~/Library/Sounds/ or /System/Library/Sounds/)
SOUND_FILE="Bottle.aiff"

# Extension 1: Shell Command (Stdin -> Stdout)
EXT_MENU1="UPPERCASE"
EXT_COMMAND1="tr a-z A-Z"

# Extension 2: Shell Command with Placeholder
# {} is replaced with the shell-quoted clipboard content
EXT_MENU2="Base64 Encode"
EXT_COMMAND2="python3 -c 'import base64, sys; print(base64.b64encode(sys.argv[1].encode()).decode())' {}"

# Extension 3: Regex Replacement
EXT_MENU3="Remove Numbers"
EXT_EXP3="[0-9]+"
EXT_REP3=""

# Extension 4: ROT13
EXT_MENU4="ROT13"
EXT_COMMAND4="tr 'A-Za-z' 'N-ZA-Mn-za-m'"
```

---

## 🛠 Extension Logic

The utility supports two types of extensions:

1.  **Command Extensions:**
    - If `{}` (or a custom `EXT_REPLACEMENT{idx}`) is present in `EXT_COMMAND`, the clipboard content is escaped and swapped in.
    - If no placeholder is present, the clipboard content is piped into the command via `stdin`.
2.  **Regex Extensions:**
    - Uses `EXT_EXP` for the pattern and `EXT_REP` for the replacement string using Python's `re.sub()`.

---

## 📦 Building the App

To bundle this as a standalone `.app` on macOS, you can use `py2app`. A `setup.py` is provided in the repository:

```bash
python3 setup.py py2app
```

The resulting application will be located in the `dist/` folder.

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

_Created by **Ramón Barrios Láscar** — powered by Python and 🫧_
