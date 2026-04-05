from __future__ import annotations
import json
from dataclasses import dataclass, field
from src.models.venue import Venue


@dataclass
class RegionPlacement:
    region_name: str
    canvas_x: float
    canvas_y: float
    rotation: float = 0

    def to_dict(self) -> dict:
        return {
            "region_name": self.region_name,
            "canvas_position": {"x": self.canvas_x, "y": self.canvas_y},
            "rotation": self.rotation,
        }

    @classmethod
    def from_dict(cls, data: dict) -> RegionPlacement:
        pos = data["canvas_position"]
        return cls(
            region_name=data["region_name"],
            canvas_x=pos["x"],
            canvas_y=pos["y"],
            rotation=data.get("rotation", 0),
        )


@dataclass
class Project:
    venue: Venue = field(default_factory=Venue)
    region_placements: list[RegionPlacement] = field(default_factory=list)
    vr_config_path: str | None = None
    version: int = 1

    def to_dict(self) -> dict:
        return {
            "version": self.version,
            "venue": self.venue.to_dict(),
            "region_placements": [p.to_dict() for p in self.region_placements],
            "vr_config_path": self.vr_config_path,
        }

    @classmethod
    def from_dict(cls, data: dict) -> Project:
        return cls(
            version=data.get("version", 1),
            venue=Venue.from_dict(data.get("venue", {})),
            region_placements=[RegionPlacement.from_dict(p) for p in data.get("region_placements", [])],
            vr_config_path=data.get("vr_config_path"),
        )

    def save(self, path: str) -> None:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)

    @classmethod
    def load(cls, path: str) -> Project:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls.from_dict(data)
