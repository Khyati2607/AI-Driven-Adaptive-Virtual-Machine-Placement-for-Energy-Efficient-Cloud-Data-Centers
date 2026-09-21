"""Generate docs/architecture.png (simple pipeline diagram)."""

from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
DOCS.mkdir(parents=True, exist_ok=True)

boxes = [
    "Historical dataset\n(Bitbrains GWA-T-12)",
    "Preprocessing\n+ lag features",
    "Random Forest\nworkload prediction",
    "Predictions CSV",
    "Adaptive placement\n(RF + thresholds)",
    "CloudSim Plus\ntrace simulation",
    "Metrics\nEnergy · SLA · Carbon",
    "Comparison\nFirst Fit · Best Fit · Adaptive",
]

fig, ax = plt.subplots(figsize=(8, 10))
ax.set_xlim(0, 10)
ax.set_ylim(0, len(boxes) * 1.4 + 1)
ax.axis("off")

y = len(boxes) * 1.4
for text in boxes:
    patch = FancyBboxPatch(
        (1.5, y - 0.9),
        7,
        0.9,
        boxstyle="round,pad=0.05",
        linewidth=1.2,
        edgecolor="#334155",
        facecolor="#e2e8f0",
    )
    ax.add_patch(patch)
    ax.text(5, y - 0.45, text, ha="center", va="center", fontsize=10)
    if y > 1.4:
        ax.annotate("", xy=(5, y - 1.0), xytext=(5, y - 1.25), arrowprops=dict(arrowstyle="->", lw=1.2))
    y -= 1.4

ax.set_title("System architecture", fontsize=14, fontweight="bold")
fig.tight_layout()
fig.savefig(DOCS / "architecture.png", dpi=150)
plt.close(fig)
print(f"Wrote {DOCS / 'architecture.png'}")
