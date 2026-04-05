from __future__ import annotations
import json
from dataclasses import dataclass, field
from src.models.venue import Point


@dataclass
class Size:
    x: float
    y: float

    def to_dict(self) -> dict:
        return {"x": self.x, "y": self.y}

    @classmethod
    def from_dict(cls, data: dict) -> "Size":
        return cls(x=data["x"], y=data["y"])


@dataclass
class StartPoint:
    position: Point
    angle: float = 0

    def to_dict(self) -> dict:
        return {"position": self.position.to_dict(), "angle": self.angle}

    @classmethod
    def from_dict(cls, data: dict) -> "StartPoint":
        return cls(position=Point.from_dict(data["position"]), angle=data.get("angle", 0))


@dataclass
class TargetArea:
    position: Point
    size: Size

    def to_dict(self) -> dict:
        return {"position": self.position.to_dict(), "size": self.size.to_dict()}

    @classmethod
    def from_dict(cls, data: dict) -> "TargetArea":
        return cls(position=Point.from_dict(data["position"]), size=Size.from_dict(data["size"]))


@dataclass
class Vehicle:
    relative_position: Point
    angle: float = 0

    def to_dict(self) -> dict:
        return {"relative_position": self.relative_position.to_dict(), "angle": self.angle}

    @classmethod
    def from_dict(cls, data: dict) -> "Vehicle":
        return cls(
            relative_position=Point.from_dict(data["relative_position"]),
            angle=data.get("angle", 0),
        )


VEHICLE_SIZE = Size(x=2.5, y=4.5)


@dataclass
class Region:
    name: str
    boundary: list[Point] = field(default_factory=list)
    start_point: StartPoint = field(default_factory=lambda: StartPoint(Point(0, 0)))
    target_area: TargetArea = field(default_factory=lambda: TargetArea(Point(0, 0), Size(1, 1)))
    has_vehicle: bool = False
    vehicle: Vehicle | None = None

    def centroid(self) -> tuple[float, float]:
        if not self.boundary:
            return (0.0, 0.0)
        cx = sum(p.x for p in self.boundary) / len(self.boundary)
        cy = sum(p.y for p in self.boundary) / len(self.boundary)
        return (cx, cy)

    def to_dict(self) -> dict:
        d = {
            "Name": self.name,
            "boundary": [p.to_dict() for p in self.boundary],
            "StartPoint": self.start_point.to_dict(),
            "TargetArea": self.target_area.to_dict(),
            "has_vehicle": self.has_vehicle,
        }
        if self.has_vehicle and self.vehicle:
            d["vehicle"] = self.vehicle.to_dict()
        return d

    @classmethod
    def from_dict(cls, data: dict) -> "Region":
        vehicle = None
        has_vehicle = data.get("has_vehicle", False)
        if has_vehicle and "vehicle" in data:
            vehicle = Vehicle.from_dict(data["vehicle"])
        return cls(
            name=data["Name"],
            boundary=[Point.from_dict(p) for p in data.get("boundary", [])],
            start_point=StartPoint.from_dict(data["StartPoint"]),
            target_area=TargetArea.from_dict(data["TargetArea"]),
            has_vehicle=has_vehicle,
            vehicle=vehicle,
        )

    @staticmethod
    def load_from_file(path: str) -> list["Region"]:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return [Region.from_dict(r) for r in data.get("Regions", [])]
