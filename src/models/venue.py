from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class Point:
    x: float
    y: float

    def to_dict(self) -> dict:
        return {"x": self.x, "y": self.y}

    @classmethod
    def from_dict(cls, data: dict) -> "Point":
        return cls(x=data["x"], y=data["y"])


@dataclass
class Wall:
    points: list[Point] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {"points": [p.to_dict() for p in self.points]}

    @classmethod
    def from_dict(cls, data: dict) -> "Wall":
        return cls(points=[Point.from_dict(p) for p in data["points"]])


@dataclass
class Obstacle:
    name: str
    type: str
    points: list[Point] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "type": self.type,
            "points": [p.to_dict() for p in self.points],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Obstacle":
        return cls(
            name=data["name"],
            type=data["type"],
            points=[Point.from_dict(p) for p in data["points"]],
        )


@dataclass
class Venue:
    grid_size: float = 0.5
    walls: list[Wall] = field(default_factory=list)
    obstacles: list[Obstacle] = field(default_factory=list)
    background_image: str | None = None

    def to_dict(self) -> dict:
        return {
            "grid_size": self.grid_size,
            "walls": [w.to_dict() for w in self.walls],
            "obstacles": [o.to_dict() for o in self.obstacles],
            "background_image": self.background_image,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Venue":
        return cls(
            grid_size=data.get("grid_size", 0.5),
            walls=[Wall.from_dict(w) for w in data.get("walls", [])],
            obstacles=[Obstacle.from_dict(o) for o in data.get("obstacles", [])],
            background_image=data.get("background_image"),
        )
