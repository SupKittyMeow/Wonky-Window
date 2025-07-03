import plistlib
from pathlib import Path

plist_path = Path("dist/Wonky Window.app/Contents/Info.plist")
with plist_path.open("rb") as f:
    plist = plistlib.load(f)

plist["LSUIElement"] = True

with plist_path.open("wb") as f:
    plistlib.dump(plist, f)

print("LSUIElement set to True.")
