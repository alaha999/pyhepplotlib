from pathlib import Path

BASE = Path(__file__).resolve().parent
OUTPUT = BASE / "outputs"
README = BASE / "README.md"

# Collect PNG files
files = sorted(OUTPUT.glob("*.png"))

lines = ["# Plot Gallery", ""]

# Generate 3-column gallery
for i in range(0, len(files), 3):
    row = files[i:i + 3]
    images = [f'<img src="outputs/{f.name}" width="300">' for f in row]
    images += [""] * (3 - len(images))
    lines.append("| " + " | ".join(images) + " |")

    if i == 0:
        lines.insert(2, "|:---:|:---:|:---:|")

lines.insert(2, "| Plot | Plot | Plot |")

README.write_text("\n".join(lines) + "\n", encoding="utf-8")
print(f"Generated {README} with {len(files)} plots.")
