from __future__ import annotations

from pathlib import Path
from typing import Any

import ezdxf

from app.config import settings


LAYERS = {
    "PLOT": 3,
    "HYDRANT": 1,
    "HOSE_REEL": 4,
    "SPRINKLER": 5,
    "PUMP": 6,
    "TANK": 30,
    "EXTINGUISHER": 2,
    "RISER": 40,
    "NOTES": 7,
}


def generate_dxf(project_id: int, design: dict[str, Any]) -> Path:
    doc = ezdxf.new("R2010")
    msp = doc.modelspace()
    for name, color in LAYERS.items():
        if name not in doc.layers:
            doc.layers.add(name, color=color)

    footprint = design.get("plot_footprint_m") or {"width": 40, "depth": 24}
    w, d = float(footprint.get("width", 40)), float(footprint.get("depth", 24))
    msp.add_lwpolyline([(0, 0), (w, 0), (w, d), (0, d), (0, 0)], dxfattribs={"layer": "PLOT"})

    def _points(key: str, layer: str, size: float = 0.8) -> None:
        for item in design.get(key) or []:
            x, y = float(item.get("x", 0)), float(item.get("y", 0))
            msp.add_circle((x, y), size, dxfattribs={"layer": layer})
            label = item.get("id") or item.get("type") or key
            msp.add_text(str(label), dxfattribs={"layer": "NOTES", "height": 0.45}).set_placement((x + 0.5, y + 0.5))

    _points("hydrants", "HYDRANT", 0.9)
    _points("hose_reels", "HOSE_REEL", 0.6)
    _points("sprinklers", "SPRINKLER", 0.35)
    _points("extinguishers", "EXTINGUISHER", 0.4)
    _points("risers", "RISER", 0.7)

    for pump in design.get("pumps") or []:
        x, y = float(pump.get("x", 2)), float(pump.get("y", 2))
        msp.add_lwpolyline(
            [(x, y), (x + 2.5, y), (x + 2.5, y + 1.6), (x, y + 1.6), (x, y)],
            dxfattribs={"layer": "PUMP"},
        )
        msp.add_text(pump.get("id", "PUMP"), dxfattribs={"layer": "NOTES", "height": 0.4}).set_placement((x, y + 1.8))

    for tank in design.get("tanks") or []:
        x, y = float(tank.get("x", 1)), float(tank.get("y", 1))
        msp.add_lwpolyline(
            [(x, y), (x + 4, y), (x + 4, y + 3), (x, y + 3), (x, y)],
            dxfattribs={"layer": "TANK"},
        )
        cap = tank.get("capacity_kl", "")
        msp.add_text(f"{tank.get('id', 'TANK')} {cap}kL", dxfattribs={"layer": "NOTES", "height": 0.4}).set_placement(
            (x, y + 3.2)
        )

    y_note = d + 1.5
    for note in design.get("notes") or []:
        msp.add_text(str(note), dxfattribs={"layer": "NOTES", "height": 0.5}).set_placement((0, y_note))
        y_note += 0.8

    path = settings.output_dir / f"project_{project_id}.dxf"
    doc.saveas(path)
    return path
