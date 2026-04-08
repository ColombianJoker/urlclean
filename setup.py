from setuptools import setup

APP = ["urlclean.py"]
DATA_FILES = []

# OPTIONS contains the macOS specific build instructions
OPTIONS = {
    "argv_emulation": True,
    "plist": {
        # LSUIElement tells macOS this is a background/menu bar app.
        # It prevents a blank icon from appearing in your Dock!
        "LSUIElement": True,
    },
    "packages": ["rumps"],
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={"py2app": OPTIONS},
    setup_requires=["py2app"],
)
