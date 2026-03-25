# VisualRouter Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a PySide6 desktop tool for planning VR venue layouts — edit floor plans, import VR region configs, drag/rotate regions, export coordinate JSON.

**Architecture:** Three-layer (UI / Interaction / Data) PySide6 app. Data models are plain Python dataclasses serialized to JSON. QGraphicsScene handles all 2D rendering and interaction. Single exe via PyInstaller.

**Tech Stack:** Python 3.11+, PySide6 6.6+, PyInstaller

**Spec:** `docs/superpowers/specs/2026-03-24-visualrouter-design.md`

---

## File Structure

```
visualrouter/
├── src/
│   ├── main.py                    # Entry point, QApplication setup
│   ├── models/
│   │   ├── __init__.py
│   │   ├── venue.py               # Wall, Obstacle, Venue dataclasses
│   │   ├── region.py              # Region, StartPoint, TargetArea, Vehicle dataclasses
│   │   └── project.py             # Project dataclass (venue + region placements), save/load
│   ├── graphics/
│   │   ├── __init__.py
│   │   ├── canvas.py              # VenueGraphicsView + VenueGraphicsScene (grid, zoom, pan)
│   │   ├── wall_item.py           # QGraphicsItem for walls
│   │   ├── obstacle_item.py       # QGraphicsItem for obstacles
│   │   └── region_item.py         # QGraphicsItem group for Region (boundary, start, target, vehicle)
│   ├── widgets/
│   │   ├── __init__.py
│   │   ├── main_window.py         # QMainWindow, menus, toolbar, layout
│   │   ├── side_panel.py          # Left panel: region list, property editor
│   │   └── toolbar.py             # Tool mode buttons (wall, obstacle, select)
│   └── export/
│       ├── __init__.py
│       └── exporter.py            # Coordinate transform + JSON export
├── tests/
│   ├── __init__.py
│   ├── test_models.py             # Data model serialization tests
│   ├── test_export.py             # Coordinate transform + export tests
│   └── test_project.py            # Project save/load tests
├── requirements.txt
└── visualrouter.spec              # PyInstaller spec (generated)
```

---

### Task 1: Project Setup

**Files:**
- Create: `src/main.py`
- Create: `requirements.txt`
- Create: `src/models/__init__.py`
- Create: `src/graphics/__init__.py`
- Create: `src/widgets/__init__.py`
- Create: `src/export/__init__.py`
- Create: `tests/__init__.py`

- [ ] **Step 1: Create requirements.txt**

```
PySide6>=6.6
pyinstaller>=6.0
pytest>=8.0
```

- [ ] **Step 2: Create .gitignore**

```
__pycache__/
*.pyc
dist/
build/
*.spec
.venv/
*.egg-info/
```

- [ ] **Step 3: Create conftest.py for pytest path resolution**

```python
# conftest.py (project root)
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
```

- [ ] **Step 4: Create directory structure and __init__.py files**

Create all directories and empty `__init__.py` files for packages: `src/models/`, `src/graphics/`, `src/widgets/`, `src/export/`, `tests/`.

- [ ] **Step 5: Create minimal main.py**

```python
import sys
from PySide6.QtWidgets import QApplication, QMainWindow


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("VisualRouter - VR场馆路线规划")
        self.setMinimumSize(1200, 800)


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
```

- [ ] **Step 6: Install dependencies and verify app launches**

Run: `pip install -r requirements.txt && python src/main.py`
Expected: Empty window appears with title "VisualRouter - VR场馆路线规划"

- [ ] **Step 7: Commit**

```bash
git init
git add -A
git commit -m "feat: initialize project structure with PySide6 skeleton"
```

---

### Task 2: Data Models (Venue)

**Files:**
- Create: `src/models/venue.py`
- Create: `tests/test_models.py`

- [ ] **Step 1: Write failing tests for Venue models**

```python
# tests/test_models.py
import json
from src.models.venue import Point, Wall, Obstacle, Venue


def test_point_creation():
    p = Point(1.5, 2.0)
    assert p.x == 1.5
    assert p.y == 2.0


def test_wall_to_dict():
    wall = Wall(points=[Point(0, 0), Point(10, 0), Point(10, 8), Point(0, 8)])
    d = wall.to_dict()
    assert d == {"points": [{"x": 0, "y": 0}, {"x": 10, "y": 0}, {"x": 10, "y": 8}, {"x": 0, "y": 8}]}


def test_wall_from_dict():
    data = {"points": [{"x": 0, "y": 0}, {"x": 5, "y": 0}]}
    wall = Wall.from_dict(data)
    assert len(wall.points) == 2
    assert wall.points[1].x == 5


def test_obstacle_to_dict():
    obs = Obstacle(name="柱子1", type="polygon", points=[Point(3, 2), Point(3.5, 2), Point(3.5, 2.5), Point(3, 2.5)])
    d = obs.to_dict()
    assert d["name"] == "柱子1"
    assert d["type"] == "polygon"
    assert len(d["points"]) == 4


def test_obstacle_from_dict():
    data = {"name": "柱子1", "type": "polygon", "points": [{"x": 3, "y": 2}, {"x": 3.5, "y": 2}]}
    obs = Obstacle.from_dict(data)
    assert obs.name == "柱子1"
    assert len(obs.points) == 2


def test_venue_to_dict():
    venue = Venue(
        grid_size=0.5,
        walls=[Wall(points=[Point(0, 0), Point(10, 0)])],
        obstacles=[],
        background_image="floor.png"
    )
    d = venue.to_dict()
    assert d["grid_size"] == 0.5
    assert d["background_image"] == "floor.png"
    assert len(d["walls"]) == 1


def test_venue_from_dict():
    data = {
        "grid_size": 0.5,
        "walls": [{"points": [{"x": 0, "y": 0}]}],
        "obstacles": [],
        "background_image": None
    }
    venue = Venue.from_dict(data)
    assert venue.grid_size == 0.5
    assert venue.background_image is None


def test_venue_no_background():
    venue = Venue(grid_size=0.5, walls=[], obstacles=[], background_image=None)
    d = venue.to_dict()
    assert d["background_image"] is None
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_models.py -v`
Expected: FAIL — cannot import `src.models.venue`

- [ ] **Step 3: Implement venue models**

```python
# src/models/venue.py
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_models.py -v`
Expected: All PASS

- [ ] **Step 5: Commit**

```bash
git add src/models/venue.py tests/test_models.py
git commit -m "feat: add Venue data models with serialization"
```

---

### Task 3: Data Models (Region)

**Files:**
- Create: `src/models/region.py`
- Modify: `tests/test_models.py`

- [ ] **Step 1: Write failing tests for Region models**

Append to `tests/test_models.py`:

```python
from src.models.region import StartPoint, TargetArea, Vehicle, Region, Size


def test_region_from_dict_with_vehicle():
    data = {
        "Name": "Region1",
        "boundary": [{"x": 0, "y": 0}, {"x": 3, "y": 0}, {"x": 3, "y": 4}, {"x": 0, "y": 4}],
        "StartPoint": {"position": {"x": 0, "y": 0}, "angle": 0},
        "TargetArea": {"position": {"x": 2, "y": 3}, "size": {"x": 1, "y": 1}},
        "has_vehicle": True,
        "vehicle": {"relative_position": {"x": 1.5, "y": 2}, "angle": 0}
    }
    region = Region.from_dict(data)
    assert region.name == "Region1"
    assert len(region.boundary) == 4
    assert region.start_point.position.x == 0
    assert region.start_point.angle == 0
    assert region.target_area.size.x == 1
    assert region.has_vehicle is True
    assert region.vehicle.relative_position.x == 1.5


def test_region_from_dict_without_vehicle():
    data = {
        "Name": "Region2",
        "boundary": [{"x": 0, "y": 0}, {"x": 2, "y": 0}, {"x": 2, "y": 2}, {"x": 0, "y": 2}],
        "StartPoint": {"position": {"x": 0, "y": 0}, "angle": 0},
        "TargetArea": {"position": {"x": 1, "y": 1}, "size": {"x": 0.5, "y": 0.5}},
        "has_vehicle": False
    }
    region = Region.from_dict(data)
    assert region.has_vehicle is False
    assert region.vehicle is None


def test_region_centroid():
    data = {
        "Name": "R1",
        "boundary": [{"x": 0, "y": 0}, {"x": 4, "y": 0}, {"x": 4, "y": 4}, {"x": 0, "y": 4}],
        "StartPoint": {"position": {"x": 0, "y": 0}, "angle": 0},
        "TargetArea": {"position": {"x": 2, "y": 2}, "size": {"x": 1, "y": 1}},
        "has_vehicle": False
    }
    region = Region.from_dict(data)
    cx, cy = region.centroid()
    assert cx == 2.0
    assert cy == 2.0


def test_load_regions_from_json(tmp_path):
    import json
    data = {
        "Regions": [
            {
                "Name": "R1",
                "boundary": [{"x": 0, "y": 0}, {"x": 1, "y": 0}, {"x": 1, "y": 1}, {"x": 0, "y": 1}],
                "StartPoint": {"position": {"x": 0, "y": 0}, "angle": 0},
                "TargetArea": {"position": {"x": 0.5, "y": 0.5}, "size": {"x": 0.5, "y": 0.5}},
                "has_vehicle": False
            }
        ]
    }
    f = tmp_path / "config.json"
    f.write_text(json.dumps(data), encoding="utf-8")
    regions = Region.load_from_file(str(f))
    assert len(regions) == 1
    assert regions[0].name == "R1"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_models.py -v -k "region"`
Expected: FAIL — cannot import `src.models.region`

- [ ] **Step 3: Implement Region models**

```python
# src/models/region.py
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_models.py -v`
Expected: All PASS

- [ ] **Step 5: Commit**

```bash
git add src/models/region.py tests/test_models.py
git commit -m "feat: add Region data models with JSON import"
```

---

### Task 4: Project Model (Save/Load)

**Files:**
- Create: `src/models/project.py`
- Create: `tests/test_project.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_project.py
import json
from src.models.project import Project, RegionPlacement
from src.models.venue import Venue, Wall, Point, Obstacle
from src.models.region import Region


def test_project_save_load(tmp_path):
    venue = Venue(
        grid_size=0.5,
        walls=[Wall(points=[Point(0, 0), Point(10, 0), Point(10, 8), Point(0, 8)])],
        obstacles=[Obstacle(name="柱子", type="polygon", points=[Point(3, 2), Point(4, 2), Point(4, 3), Point(3, 3)])],
        background_image="bg.png",
    )
    placements = [
        RegionPlacement(region_name="Region1", canvas_x=5.0, canvas_y=3.0, rotation=90),
        RegionPlacement(region_name="Region2", canvas_x=12.0, canvas_y=3.0, rotation=0),
    ]
    project = Project(venue=venue, region_placements=placements, vr_config_path="RegionData.json")

    path = tmp_path / "test.vrproject"
    project.save(str(path))

    loaded = Project.load(str(path))
    assert loaded.version == 1
    assert loaded.venue.grid_size == 0.5
    assert len(loaded.venue.walls) == 1
    assert len(loaded.region_placements) == 2
    assert loaded.region_placements[0].region_name == "Region1"
    assert loaded.region_placements[0].rotation == 90
    assert loaded.vr_config_path == "RegionData.json"


def test_project_empty(tmp_path):
    project = Project(venue=Venue(), region_placements=[], vr_config_path=None)
    path = tmp_path / "empty.vrproject"
    project.save(str(path))
    loaded = Project.load(str(path))
    assert loaded.venue.grid_size == 0.5
    assert len(loaded.region_placements) == 0
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_project.py -v`
Expected: FAIL — cannot import `src.models.project`

- [ ] **Step 3: Implement Project model**

```python
# src/models/project.py
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
    def from_dict(cls, data: dict) -> "RegionPlacement":
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
    def from_dict(cls, data: dict) -> "Project":
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
    def load(cls, path: str) -> "Project":
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls.from_dict(data)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_project.py -v`
Expected: All PASS

- [ ] **Step 5: Commit**

```bash
git add src/models/project.py tests/test_project.py
git commit -m "feat: add Project model with save/load"
```

---

### Task 5: Export Logic

**Files:**
- Create: `src/export/exporter.py`
- Create: `tests/test_export.py`

- [ ] **Step 1: Write failing tests for coordinate transform and export**

```python
# tests/test_export.py
import json
import math
from src.models.venue import Point
from src.models.region import Region, StartPoint, TargetArea, Vehicle, Size, VEHICLE_SIZE
from src.export.exporter import compute_export_regions, transform_point_around_centroid


def make_region(name, boundary_pts, sp_pos, sp_angle, ta_pos, ta_size, vehicle=None):
    return Region(
        name=name,
        boundary=[Point(*p) for p in boundary_pts],
        start_point=StartPoint(Point(*sp_pos), sp_angle),
        target_area=TargetArea(Point(*ta_pos), Size(*ta_size)),
        has_vehicle=vehicle is not None,
        vehicle=vehicle,
    )


def test_export_single_region_no_rotation():
    """Region1 at canvas position (5,3), no rotation. Export origin = Region1.StartPoint."""
    r1 = make_region("R1", [(0,0),(3,0),(3,4),(0,4)], (0,0), 0, (2,3), (1,1))
    placements = [{"region_name": "R1", "canvas_x": 5.0, "canvas_y": 3.0, "rotation": 0}]
    result = compute_export_regions([r1], placements)

    assert len(result) == 1
    exported = result[0]
    # Region1.StartPoint is at canvas (5+0, 3+0) = (5,3), which is the origin
    assert exported["StartPoint"]["position"]["x"] == 0
    assert exported["StartPoint"]["position"]["y"] == 0
    # Boundary point (3,0) -> canvas (8,3) -> export (3,0)
    assert exported["boundary"][1]["x"] == 3
    assert exported["boundary"][1]["y"] == 0


def test_export_two_regions_relative_coords():
    """Two regions, export coords relative to R1 StartPoint."""
    r1 = make_region("R1", [(0,0),(3,0),(3,4),(0,4)], (0,0), 0, (2,3), (1,1))
    r2 = make_region("R2", [(0,0),(2,0),(2,2),(0,2)], (0,0), 0, (1,1), (0.5,0.5))
    placements = [
        {"region_name": "R1", "canvas_x": 5.0, "canvas_y": 3.0, "rotation": 0},
        {"region_name": "R2", "canvas_x": 10.0, "canvas_y": 3.0, "rotation": 0},
    ]
    result = compute_export_regions([r1, r2], placements)

    # R2 StartPoint at canvas (10,3), R1 StartPoint at canvas (5,3)
    # Export: (10-5, 3-3) = (5, 0)
    assert result[1]["StartPoint"]["position"]["x"] == 5.0
    assert result[1]["StartPoint"]["position"]["y"] == 0.0


def test_export_with_vehicle():
    """Region with vehicle exports vehicle position and fixed size."""
    v = Vehicle(relative_position=Point(1.5, 2.0), angle=0)
    r1 = make_region("R1", [(0,0),(3,0),(3,4),(0,4)], (0,0), 0, (2,3), (1,1), vehicle=v)
    placements = [{"region_name": "R1", "canvas_x": 0, "canvas_y": 0, "rotation": 0}]
    result = compute_export_regions([r1], placements)

    assert "vehicle" in result[0]
    assert result[0]["vehicle"]["position"]["x"] == 1.5
    assert result[0]["vehicle"]["position"]["y"] == 2.0
    assert result[0]["vehicle"]["size"]["x"] == 2.5
    assert result[0]["vehicle"]["size"]["y"] == 4.5


def test_export_without_vehicle():
    """Region without vehicle has no vehicle key in export."""
    r1 = make_region("R1", [(0,0),(3,0),(3,4),(0,4)], (0,0), 0, (2,3), (1,1))
    placements = [{"region_name": "R1", "canvas_x": 0, "canvas_y": 0, "rotation": 0}]
    result = compute_export_regions([r1], placements)
    assert "vehicle" not in result[0]


def test_export_angle_additive():
    """Exported angle = original angle + user rotation."""
    r1 = make_region("R1", [(0,0),(4,0),(4,4),(0,4)], (0,0), 30, (2,2), (1,1))
    placements = [{"region_name": "R1", "canvas_x": 0, "canvas_y": 0, "rotation": 60}]
    result = compute_export_regions([r1], placements)
    assert result[0]["StartPoint"]["angle"] == 90


def test_transform_point_no_rotation():
    """Point transform with 0 rotation is just translation."""
    result = transform_point_around_centroid(
        local_point=Point(1, 1),
        centroid=(2, 2),
        rotation_deg=0,
        canvas_offset_x=5,
        canvas_offset_y=3,
    )
    assert abs(result.x - 6) < 1e-9
    assert abs(result.y - 4) < 1e-9


def test_transform_point_90_degree_rotation():
    """4x4 square, centroid (2,2), rotate 90 degrees CW, no offset."""
    result = transform_point_around_centroid(
        local_point=Point(4, 2),  # right-center
        centroid=(2, 2),
        rotation_deg=90,
        canvas_offset_x=0,
        canvas_offset_y=0,
    )
    assert abs(result.x - 2) < 1e-9
    assert abs(result.y - 4) < 1e-9
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_export.py -v`
Expected: FAIL — cannot import `src.export.exporter`

- [ ] **Step 3: Implement exporter**

```python
# src/export/exporter.py
import math
from src.models.venue import Point
from src.models.region import Region, VEHICLE_SIZE


def transform_point_around_centroid(
    local_point: Point,
    centroid: tuple[float, float],
    rotation_deg: float,
    canvas_offset_x: float,
    canvas_offset_y: float,
) -> Point:
    """Transform a point from Region-local coords to canvas coords.

    1. Translate so centroid is at origin
    2. Rotate around origin
    3. Translate back
    4. Add canvas offset
    """
    cx, cy = centroid
    dx = local_point.x - cx
    dy = local_point.y - cy

    rad = math.radians(rotation_deg)
    cos_a = math.cos(rad)
    sin_a = math.sin(rad)

    rx = dx * cos_a - dy * sin_a
    ry = dx * sin_a + dy * cos_a

    return Point(
        x=rx + cx + canvas_offset_x,
        y=ry + cy + canvas_offset_y,
    )


def compute_export_regions(
    regions: list[Region],
    placements: list[dict],
) -> list[dict]:
    """Compute export JSON data for all regions.

    placements: list of {"region_name", "canvas_x", "canvas_y", "rotation"}
    """
    placement_map = {p["region_name"]: p for p in placements}

    # First pass: compute all canvas positions
    canvas_regions = []
    for region in regions:
        pl = placement_map.get(region.name)
        if pl is None:
            continue
        centroid = region.centroid()
        rot = pl["rotation"]
        ox, oy = pl["canvas_x"], pl["canvas_y"]

        def xform(pt: Point) -> Point:
            return transform_point_around_centroid(pt, centroid, rot, ox, oy)

        canvas_boundary = [xform(p) for p in region.boundary]
        canvas_sp = xform(region.start_point.position)
        canvas_ta = xform(region.target_area.position)
        canvas_vehicle = None
        if region.has_vehicle and region.vehicle:
            canvas_vehicle = xform(region.vehicle.relative_position)
            vehicle_angle = region.vehicle.angle + rot
        sp_angle = region.start_point.angle + rot

        canvas_regions.append({
            "region": region,
            "boundary": canvas_boundary,
            "start_point": canvas_sp,
            "start_angle": sp_angle,
            "target_area": canvas_ta,
            "vehicle_pos": canvas_vehicle,
            "vehicle_angle": region.vehicle.angle + rot if region.has_vehicle and region.vehicle else 0,
        })

    if not canvas_regions:
        return []

    # Export origin = first region's StartPoint canvas position
    origin = canvas_regions[0]["start_point"]

    result = []
    for cr in canvas_regions:
        region = cr["region"]
        exported = {
            "Name": region.name,
            "boundary": [
                Point(p.x - origin.x, p.y - origin.y).to_dict()
                for p in cr["boundary"]
            ],
            "StartPoint": {
                "position": Point(
                    cr["start_point"].x - origin.x,
                    cr["start_point"].y - origin.y,
                ).to_dict(),
                "angle": cr["start_angle"],
            },
            "TargetArea": {
                "position": Point(
                    cr["target_area"].x - origin.x,
                    cr["target_area"].y - origin.y,
                ).to_dict(),
                "size": region.target_area.size.to_dict(),
            },
        }
        if region.has_vehicle and cr["vehicle_pos"]:
            exported["vehicle"] = {
                "position": Point(
                    cr["vehicle_pos"].x - origin.x,
                    cr["vehicle_pos"].y - origin.y,
                ).to_dict(),
                "size": VEHICLE_SIZE.to_dict(),
                "angle": cr["vehicle_angle"],
            }
        result.append(exported)

    return result


def export_to_file(regions: list[Region], placements: list[dict], path: str) -> None:
    import json
    data = {"Regions": compute_export_regions(regions, placements)}
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_export.py -v`
Expected: All PASS

- [ ] **Step 5: Commit**

```bash
git add src/export/exporter.py tests/test_export.py
git commit -m "feat: add coordinate transform and JSON export"
```

---

### Task 6: Canvas (Grid + Background + Zoom/Pan)

**Files:**
- Create: `src/graphics/canvas.py`
- Modify: `src/main.py`

- [ ] **Step 1: Implement VenueGraphicsScene with grid drawing**

```python
# src/graphics/canvas.py
from PySide6.QtWidgets import QGraphicsScene, QGraphicsView
from PySide6.QtCore import Qt, QRectF, Signal
from PySide6.QtGui import QPen, QColor, QPainter, QWheelEvent, QPixmap


class VenueGraphicsScene(QGraphicsScene):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.grid_size = 0.5  # meters
        self.setSceneRect(-50, -50, 100, 100)  # 100m x 100m default
        self._background_pixmap = None

    def set_background_image(self, path: str) -> None:
        self._background_pixmap = QPixmap(path)
        self.update()

    def clear_background_image(self) -> None:
        self._background_pixmap = None
        self.update()

    def drawBackground(self, painter: QPainter, rect: QRectF) -> None:
        super().drawBackground(painter, rect)

        # Draw background image if set
        if self._background_pixmap and not self._background_pixmap.isNull():
            painter.setOpacity(0.3)
            painter.drawPixmap(self.sceneRect().toRect(), self._background_pixmap)
            painter.setOpacity(1.0)

        # Draw grid
        pen = QPen(QColor(200, 200, 200), 0)
        painter.setPen(pen)

        left = int(rect.left() / self.grid_size) * self.grid_size
        top = int(rect.top() / self.grid_size) * self.grid_size

        x = left
        while x <= rect.right():
            painter.drawLine(int(x * 100) / 100, rect.top(), int(x * 100) / 100, rect.bottom())
            x += self.grid_size

        y = top
        while y <= rect.bottom():
            painter.drawLine(rect.left(), int(y * 100) / 100, rect.right(), int(y * 100) / 100)
            y += self.grid_size

        # Draw origin axes
        axis_pen = QPen(QColor(150, 150, 150), 0.02)
        painter.setPen(axis_pen)
        painter.drawLine(rect.left(), 0, rect.right(), 0)
        painter.drawLine(0, rect.top(), 0, rect.bottom())


class VenueGraphicsView(QGraphicsView):
    mouse_moved = Signal(float, float)  # emits scene coords in meters

    def __init__(self, scene: VenueGraphicsScene, parent=None):
        super().__init__(scene, parent)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setDragMode(QGraphicsView.DragMode.NoDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)
        self._panning = False
        self._pan_start = None
        # Scale: 1 scene unit = 1 meter. Initial zoom: ~50 pixels per meter
        self.scale(50, 50)

    def wheelEvent(self, event: QWheelEvent) -> None:
        factor = 1.15 if event.angleDelta().y() > 0 else 1 / 1.15
        self.scale(factor, factor)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.MiddleButton:
            self._panning = True
            self._pan_start = event.position()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
        else:
            super().mousePressEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.MiddleButton:
            self._panning = False
            self.setCursor(Qt.CursorShape.ArrowCursor)
        else:
            super().mouseReleaseEvent(event)

    def mouseMoveEvent(self, event) -> None:
        if self._panning and self._pan_start is not None:
            delta = event.position() - self._pan_start
            self._pan_start = event.position()
            self.horizontalScrollBar().setValue(
                self.horizontalScrollBar().value() - int(delta.x())
            )
            self.verticalScrollBar().setValue(
                self.verticalScrollBar().value() - int(delta.y())
            )
        else:
            super().mouseMoveEvent(event)
        # Emit mouse position in scene coordinates
        scene_pos = self.mapToScene(event.position().toPoint())
        self.mouse_moved.emit(scene_pos.x(), scene_pos.y())
```

- [ ] **Step 2: Wire canvas into main window**

Replace `src/main.py` with:

```python
import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QStatusBar
from src.graphics.canvas import VenueGraphicsScene, VenueGraphicsView


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("VisualRouter - VR场馆路线规划")
        self.setMinimumSize(1200, 800)

        self.scene = VenueGraphicsScene()
        self.view = VenueGraphicsView(self.scene)
        self.setCentralWidget(self.view)

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.view.mouse_moved.connect(self._update_mouse_pos)

    def _update_mouse_pos(self, x: float, y: float):
        self.status_bar.showMessage(f"X: {x:.2f}m  Y: {y:.2f}m")


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
```

- [ ] **Step 3: Verify manually — grid visible, scroll wheel zooms, middle mouse pans, status bar shows coords**

Run: `python src/main.py`
Expected: Grid canvas with zoom, pan, coordinate display in status bar.

- [ ] **Step 4: Commit**

```bash
git add src/graphics/canvas.py src/main.py
git commit -m "feat: add canvas with grid, zoom, pan, and coordinate display"
```

---

### Task 7: Wall Drawing Tool

**Files:**
- Create: `src/graphics/wall_item.py`
- Create: `src/widgets/toolbar.py`
- Modify: `src/graphics/canvas.py`
- Modify: `src/main.py`

- [ ] **Step 1: Implement WallItem**

```python
# src/graphics/wall_item.py
from PySide6.QtWidgets import QGraphicsPolygonItem, QGraphicsItem
from PySide6.QtGui import QPen, QBrush, QColor, QPolygonF
from PySide6.QtCore import QPointF, Qt


class WallItem(QGraphicsPolygonItem):
    def __init__(self, points: list[QPointF] | None = None, parent=None):
        super().__init__(parent)
        self.setPen(QPen(QColor(0, 0, 0), 0.05))
        self.setBrush(QBrush(Qt.BrushStyle.NoBrush))
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        if points:
            self.setPolygon(QPolygonF(points))

    def set_points(self, points: list[QPointF]) -> None:
        self.setPolygon(QPolygonF(points))
```

- [ ] **Step 2: Create toolbar with tool modes**

```python
# src/widgets/toolbar.py
from enum import Enum, auto
from PySide6.QtWidgets import QToolBar, QButtonGroup
from PySide6.QtGui import QAction
from PySide6.QtCore import Signal


class ToolMode(Enum):
    SELECT = auto()
    WALL = auto()
    OBSTACLE = auto()


class EditorToolBar(QToolBar):
    mode_changed = Signal(ToolMode)

    def __init__(self, parent=None):
        super().__init__("Tools", parent)
        self._actions = {}
        self._current_mode = ToolMode.SELECT

        for mode, label in [
            (ToolMode.SELECT, "选择 (S)"),
            (ToolMode.WALL, "画墙壁 (W)"),
            (ToolMode.OBSTACLE, "画障碍物 (O)"),
        ]:
            action = QAction(label, self)
            action.setCheckable(True)
            action.triggered.connect(lambda checked, m=mode: self._set_mode(m))
            self.addAction(action)
            self._actions[mode] = action

        self._actions[ToolMode.SELECT].setChecked(True)

    def _set_mode(self, mode: ToolMode) -> None:
        self._current_mode = mode
        for m, action in self._actions.items():
            action.setChecked(m == mode)
        self.mode_changed.emit(mode)

    @property
    def current_mode(self) -> ToolMode:
        return self._current_mode
```

- [ ] **Step 3: Add wall drawing interaction to canvas**

Add to `VenueGraphicsScene`:

```python
# Add these to VenueGraphicsScene.__init__:
self._drawing_wall = False
self._wall_points = []
self._preview_line = None
self._current_wall_item = None

# Add these methods:
def start_wall_drawing(self):
    self._drawing_wall = True
    self._wall_points = []

def stop_wall_drawing(self):
    self._drawing_wall = False
    self._wall_points = []
    if self._preview_line:
        self.removeItem(self._preview_line)
        self._preview_line = None

def _add_wall_point(self, scene_pos):
    from PySide6.QtCore import QPointF
    pt = QPointF(scene_pos.x(), scene_pos.y())
    self._wall_points.append(pt)

    if len(self._wall_points) >= 2:
        if self._current_wall_item:
            self.removeItem(self._current_wall_item)
        from src.graphics.wall_item import WallItem
        self._current_wall_item = WallItem(self._wall_points)
        self.addItem(self._current_wall_item)

def _finish_wall(self):
    if len(self._wall_points) >= 3:
        # Close the polygon
        if self._current_wall_item:
            self.removeItem(self._current_wall_item)
        from src.graphics.wall_item import WallItem
        self._current_wall_item = WallItem(self._wall_points)
        self.addItem(self._current_wall_item)
    self._current_wall_item = None
    self._wall_points = []
    self._drawing_wall = False
```

- [ ] **Step 4: Wire toolbar + wall drawing into main window**

Update `src/main.py` to add toolbar and handle click events for wall drawing mode. Add `mouseClickEvent` handling in the view that delegates to scene based on current tool mode.

- [ ] **Step 5: Verify manually — select wall tool, click to place points, double-click to finish polygon**

Run: `python src/main.py`
Expected: Can draw wall polygons on the canvas.

- [ ] **Step 6: Commit**

```bash
git add src/graphics/wall_item.py src/widgets/toolbar.py src/graphics/canvas.py src/main.py
git commit -m "feat: add wall drawing tool with polygon creation"
```

---

### Task 8: Obstacle Drawing Tool

**Files:**
- Create: `src/graphics/obstacle_item.py`
- Modify: `src/graphics/canvas.py`
- Modify: `src/main.py`

- [ ] **Step 1: Implement ObstacleItem**

```python
# src/graphics/obstacle_item.py
from PySide6.QtWidgets import QGraphicsPolygonItem, QGraphicsItem
from PySide6.QtGui import QPen, QBrush, QColor, QPolygonF
from PySide6.QtCore import QPointF, Qt


class ObstacleItem(QGraphicsPolygonItem):
    def __init__(self, points: list[QPointF] | None = None, parent=None):
        super().__init__(parent)
        self.setPen(QPen(QColor(100, 100, 100), 0.03))
        self.setBrush(QBrush(QColor(180, 180, 180, 150)))
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        if points:
            self.setPolygon(QPolygonF(points))

    def set_points(self, points: list[QPointF]) -> None:
        self.setPolygon(QPolygonF(points))
```

- [ ] **Step 2: Add obstacle drawing to canvas scene**

Same pattern as wall drawing: click to place points, double-click to finish. Reuse the point-collection logic but create ObstacleItem instead of WallItem.

- [ ] **Step 3: Wire obstacle tool mode into main window**

Connect toolbar OBSTACLE mode to scene obstacle drawing.

- [ ] **Step 4: Verify manually — draw obstacle polygons, they appear as gray filled shapes**

Run: `python src/main.py`
Expected: Can draw filled gray obstacle polygons.

- [ ] **Step 5: Commit**

```bash
git add src/graphics/obstacle_item.py src/graphics/canvas.py src/main.py
git commit -m "feat: add obstacle drawing tool"
```

---

### Task 9: Region Graphics Item (Display + Drag + Rotate)

**Files:**
- Create: `src/graphics/region_item.py`
- Modify: `src/graphics/canvas.py`

- [ ] **Step 1: Implement RegionItem as QGraphicsItemGroup**

```python
# src/graphics/region_item.py
import math
from PySide6.QtWidgets import (
    QGraphicsItemGroup, QGraphicsPolygonItem, QGraphicsEllipseItem,
    QGraphicsRectItem, QGraphicsItem, QGraphicsTextItem,
)
from PySide6.QtGui import QPen, QBrush, QColor, QPolygonF, QFont
from PySide6.QtCore import QPointF, QRectF, Qt

from src.models.region import Region, VEHICLE_SIZE


REGION_COLORS = [
    QColor(255, 80, 80, 80),    # red
    QColor(80, 80, 255, 80),    # blue
    QColor(80, 200, 80, 80),    # green
    QColor(180, 80, 255, 80),   # purple
    QColor(255, 160, 40, 80),   # orange
    QColor(255, 255, 80, 80),   # yellow
    QColor(80, 220, 220, 80),   # cyan
]


class RegionItem(QGraphicsItemGroup):
    def __init__(self, region: Region, color_index: int = 0, parent=None):
        super().__init__(parent)
        self.region = region
        self._color = REGION_COLORS[color_index % len(REGION_COLORS)]
        self._collision = False

        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges, True)

        self._build_children()

        # Set transform origin to centroid for rotation
        cx, cy = region.centroid()
        self.setTransformOriginPoint(QPointF(cx, cy))

    def _build_children(self):
        region = self.region

        # Boundary polygon
        pts = [QPointF(p.x, p.y) for p in region.boundary]
        self._boundary_item = QGraphicsPolygonItem(QPolygonF(pts))
        self._boundary_item.setPen(QPen(self._color.darker(150), 0.05))
        self._boundary_item.setBrush(QBrush(self._color))
        self.addToGroup(self._boundary_item)

        # StartPoint marker (green circle)
        sp = region.start_point.position
        r = 0.15
        self._start_marker = QGraphicsEllipseItem(sp.x - r, sp.y - r, r * 2, r * 2)
        self._start_marker.setBrush(QBrush(QColor(0, 200, 0, 180)))
        self._start_marker.setPen(QPen(Qt.PenStyle.NoPen))
        self.addToGroup(self._start_marker)

        # TargetArea marker (orange rect)
        ta = region.target_area
        self._target_rect = QGraphicsRectItem(
            ta.position.x, ta.position.y, ta.size.x, ta.size.y
        )
        self._target_rect.setBrush(QBrush(QColor(255, 165, 0, 120)))
        self._target_rect.setPen(QPen(QColor(255, 140, 0), 0.03))
        self.addToGroup(self._target_rect)

        # Vehicle marker (blue rect with direction arrow)
        if region.has_vehicle and region.vehicle:
            vp = region.vehicle.relative_position
            vw, vh = VEHICLE_SIZE.x, VEHICLE_SIZE.y
            self._vehicle_rect = QGraphicsRectItem(
                vp.x - vw / 2, vp.y - vh / 2, vw, vh
            )
            self._vehicle_rect.setBrush(QBrush(QColor(50, 100, 255, 100)))
            self._vehicle_rect.setPen(QPen(QColor(30, 60, 200), 0.03))
            self.addToGroup(self._vehicle_rect)

        # Name label
        label = QGraphicsTextItem(region.name)
        label.setDefaultTextColor(self._color.darker(200))
        font = QFont()
        font.setPointSizeF(0.3)
        label.setFont(font)
        cx, cy = region.centroid()
        label.setPos(cx - 0.5, cy - 0.2)
        self.addToGroup(label)

    def set_collision(self, colliding: bool) -> None:
        if colliding != self._collision:
            self._collision = colliding
            pen_color = QColor(255, 0, 0) if colliding else self._color.darker(150)
            self._boundary_item.setPen(QPen(pen_color, 0.08 if colliding else 0.05))

    def get_canvas_start_point(self) -> tuple[float, float]:
        """Return StartPoint position in scene/canvas coordinates."""
        sp = self.region.start_point.position
        scene_pt = self.mapToScene(QPointF(sp.x, sp.y))
        return (scene_pt.x(), scene_pt.y())

    def get_placement_dict(self) -> dict:
        """Return placement info for project save."""
        return {
            "region_name": self.region.name,
            "canvas_x": self.pos().x(),
            "canvas_y": self.pos().y(),
            "rotation": self.rotation(),
        }
```

- [ ] **Step 2: Add rotation handle interaction**

Add mouse event overrides to `RegionItem` for rotation: when the user holds Shift and drags, rotate the item around its centroid.

```python
    # Add to RegionItem:
    def mousePressEvent(self, event):
        if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
            self._rotating = True
            self._rotate_start_angle = self.rotation()
            center = self.transformOriginPoint()
            scene_center = self.mapToScene(center)
            scene_mouse = event.scenePos()
            self._rotate_start_mouse_angle = math.degrees(
                math.atan2(scene_mouse.y() - scene_center.y(), scene_mouse.x() - scene_center.x())
            )
        else:
            self._rotating = False
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if getattr(self, '_rotating', False):
            center = self.transformOriginPoint()
            scene_center = self.mapToScene(center)
            scene_mouse = event.scenePos()
            current_angle = math.degrees(
                math.atan2(scene_mouse.y() - scene_center.y(), scene_mouse.x() - scene_center.x())
            )
            delta = current_angle - self._rotate_start_mouse_angle
            self.setRotation(self._rotate_start_angle + delta)
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._rotating = False
        super().mouseReleaseEvent(event)
```

- [ ] **Step 3: Add method to scene for loading regions**

Add to `VenueGraphicsScene`:

```python
def load_regions(self, regions: list[Region]) -> list[RegionItem]:
    """Add Region items to scene, stacked at center."""
    center = self.sceneRect().center()
    items = []
    for i, region in enumerate(regions):
        item = RegionItem(region, color_index=i)
        item.setPos(center.x(), center.y())
        self.addItem(item)
        items.append(item)
    return items
```

- [ ] **Step 4: Add right-click context menu to RegionItem**

Add to `RegionItem`:

```python
def contextMenuEvent(self, event):
    from PySide6.QtWidgets import QMenu
    menu = QMenu()
    delete_action = menu.addAction("删除")
    props_action = menu.addAction("属性")
    action = menu.exec(event.screenPos())
    if action == delete_action:
        self.scene().removeItem(self)
    elif action == props_action:
        # Select to show in side panel
        self.setSelected(True)
```

Also add context menu to `WallItem` and `ObstacleItem` with "删除" action using the same pattern.

- [ ] **Step 5: Verify manually — create test regions in code, display on canvas, drag, Shift+drag to rotate, right-click shows menu**

Run: `python src/main.py` (with test region data hardcoded temporarily)
Expected: Colored region polygons appear, can drag, rotate, and right-click to delete.

- [ ] **Step 6: Commit**

```bash
git add src/graphics/region_item.py src/graphics/wall_item.py src/graphics/obstacle_item.py src/graphics/canvas.py
git commit -m "feat: add RegionItem with drag, rotate, and context menu"
```

---

### Task 10: Side Panel (Region List + Properties)

**Files:**
- Create: `src/widgets/side_panel.py`
- Modify: `src/main.py`

- [ ] **Step 1: Implement SidePanel with region list and property editor**

```python
# src/widgets/side_panel.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QListWidget, QGroupBox,
    QFormLayout, QDoubleSpinBox, QLabel, QListWidgetItem,
)
from PySide6.QtCore import Signal

from src.graphics.region_item import RegionItem


class SidePanel(QWidget):
    region_selected = Signal(str)  # region name

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(280)
        layout = QVBoxLayout(self)

        # Region list
        region_group = QGroupBox("Region 列表")
        region_layout = QVBoxLayout(region_group)
        self.region_list = QListWidget()
        self.region_list.currentItemChanged.connect(self._on_region_selected)
        region_layout.addWidget(self.region_list)
        layout.addWidget(region_group)

        # Property editor
        prop_group = QGroupBox("属性")
        prop_layout = QFormLayout(prop_group)

        self.pos_x_spin = QDoubleSpinBox()
        self.pos_x_spin.setRange(-1000, 1000)
        self.pos_x_spin.setDecimals(2)
        self.pos_x_spin.setSuffix(" m")
        prop_layout.addRow("X:", self.pos_x_spin)

        self.pos_y_spin = QDoubleSpinBox()
        self.pos_y_spin.setRange(-1000, 1000)
        self.pos_y_spin.setDecimals(2)
        self.pos_y_spin.setSuffix(" m")
        prop_layout.addRow("Y:", self.pos_y_spin)

        self.rotation_spin = QDoubleSpinBox()
        self.rotation_spin.setRange(-360, 360)
        self.rotation_spin.setDecimals(1)
        self.rotation_spin.setSuffix(" °")
        prop_layout.addRow("旋转:", self.rotation_spin)

        self.name_label = QLabel("-")
        prop_layout.addRow("名称:", self.name_label)

        layout.addWidget(prop_group)
        layout.addStretch()

        self._region_items: dict[str, RegionItem] = {}
        self._updating = False

        # Connect spin boxes
        self.pos_x_spin.valueChanged.connect(self._on_pos_changed)
        self.pos_y_spin.valueChanged.connect(self._on_pos_changed)
        self.rotation_spin.valueChanged.connect(self._on_rotation_changed)

    def set_region_items(self, items: list[RegionItem]) -> None:
        self.region_list.clear()
        self._region_items.clear()
        for item in items:
            list_item = QListWidgetItem(item.region.name)
            self.region_list.addItem(list_item)
            self._region_items[item.region.name] = item

    def update_properties(self, region_item: RegionItem) -> None:
        self._updating = True
        self.name_label.setText(region_item.region.name)
        self.pos_x_spin.setValue(region_item.pos().x())
        self.pos_y_spin.setValue(region_item.pos().y())
        self.rotation_spin.setValue(region_item.rotation())
        self._updating = False

    def _on_region_selected(self, current, previous):
        if current:
            name = current.text()
            self.region_selected.emit(name)
            if name in self._region_items:
                self.update_properties(self._region_items[name])

    def _on_pos_changed(self):
        if self._updating:
            return
        current = self.region_list.currentItem()
        if current and current.text() in self._region_items:
            item = self._region_items[current.text()]
            item.setPos(self.pos_x_spin.value(), self.pos_y_spin.value())

    def _on_rotation_changed(self):
        if self._updating:
            return
        current = self.region_list.currentItem()
        if current and current.text() in self._region_items:
            item = self._region_items[current.text()]
            item.setRotation(self.rotation_spin.value())
```

- [ ] **Step 2: Wire side panel into main window layout**

Update `src/main.py`: add `SidePanel` as left dock widget or in a `QSplitter` with the canvas.

- [ ] **Step 3: Sync side panel when regions are dragged on canvas**

Add `itemChange` to `RegionItem` to notify the side panel when position/rotation changes:

```python
# In RegionItem:
def itemChange(self, change, value):
    if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
        # Notify scene to update side panel
        if self.scene():
            self.scene().region_moved.emit(self.region.name)
    return super().itemChange(change, value)
```

Add signal to `VenueGraphicsScene`:
```python
region_moved = Signal(str)  # emits region name
```

In `MainWindow`, connect `scene.region_moved` to update the side panel:
```python
self.scene.region_moved.connect(self._on_region_moved)

def _on_region_moved(self, name):
    for item in self._region_items:
        if item.region.name == name and item.isSelected():
            self.side_panel.update_properties(item)
```

- [ ] **Step 4: Verify manually — region list shows items, clicking updates properties, editing spin boxes moves/rotates region, dragging region updates spin boxes**

Run: `python src/main.py`
Expected: Left panel shows region list and property editor, bidirectional sync with canvas.

- [ ] **Step 4: Commit**

```bash
git add src/widgets/side_panel.py src/main.py
git commit -m "feat: add side panel with region list and property editor"
```

---

### Task 11: Menu Bar (File Operations)

**Files:**
- Modify: `src/main.py`

- [ ] **Step 1: Add menu bar with file operations**

Add to `MainWindow`:

```python
def _create_menus(self):
    menu_bar = self.menuBar()

    file_menu = menu_bar.addMenu("文件")
    file_menu.addAction("新建项目", self._new_project, "Ctrl+N")
    file_menu.addAction("打开项目...", self._open_project, "Ctrl+O")
    file_menu.addAction("保存项目", self._save_project, "Ctrl+S")
    file_menu.addAction("另存为...", self._save_project_as, "Ctrl+Shift+S")
    file_menu.addSeparator()
    file_menu.addAction("导入VR配置...", self._import_vr_config)
    file_menu.addAction("导入背景图片...", self._import_background)
    file_menu.addSeparator()
    file_menu.addAction("导出配置JSON...", self._export_json)

    edit_menu = menu_bar.addMenu("编辑")
    edit_menu.addAction("撤销", self._undo, "Ctrl+Z")
    edit_menu.addAction("重做", self._redo, "Ctrl+Y")
    edit_menu.addSeparator()
    edit_menu.addAction("删除选中", self._delete_selected, "Delete")
```

- [ ] **Step 2: Initialize state attributes in MainWindow.__init__**

Add to `MainWindow.__init__()`:

```python
self._project = Project()
self._region_items = []
self._current_path = None
self._undo_stack = None  # initialized in Task 13
```

- [ ] **Step 3: Implement file dialog handlers and state management**

```python
def _new_project(self):
    self._project = Project()
    self.scene.clear()
    self._region_items = []
    self._current_path = None
    self.setWindowTitle("VisualRouter - 新建项目")

def _open_project(self):
    path, _ = QFileDialog.getOpenFileName(self, "打开项目", "", "VR Project (*.vrproject)")
    if path:
        self._project = Project.load(path)
        self._current_path = path
        self._load_project_to_scene()
        self.setWindowTitle(f"VisualRouter - {os.path.basename(path)}")

def _save_project(self):
    if self._current_path:
        self._collect_state_to_project()
        self._project.save(self._current_path)
    else:
        self._save_project_as()

def _save_project_as(self):
    path, _ = QFileDialog.getSaveFileName(self, "保存项目", "", "VR Project (*.vrproject)")
    if path:
        self._current_path = path
        self._collect_state_to_project()
        self._project.save(path)

def _import_vr_config(self):
    path, _ = QFileDialog.getOpenFileName(self, "导入VR配置", "", "JSON (*.json)")
    if path:
        regions = Region.load_from_file(path)
        self._region_items = self.scene.load_regions(regions)
        self.side_panel.set_region_items(self._region_items)
        self._project.vr_config_path = path

def _import_background(self):
    path, _ = QFileDialog.getOpenFileName(self, "导入背景图片", "", "Images (*.png *.jpg *.jpeg *.bmp)")
    if path:
        self.scene.set_background_image(path)
        # Store relative path if project file exists, otherwise absolute
        if self._current_path:
            project_dir = os.path.dirname(self._current_path)
            self._project.venue.background_image = os.path.relpath(path, project_dir)
        else:
            self._project.venue.background_image = path

def _export_json(self):
    path, _ = QFileDialog.getSaveFileName(self, "导出配置", "", "JSON (*.json)")
    if path:
        placements = [item.get_placement_dict() for item in self._region_items]
        regions = [item.region for item in self._region_items]
        export_to_file(regions, placements, path)

def _collect_state_to_project(self):
    """Harvest current canvas state into the Project model."""
    from src.graphics.wall_item import WallItem
    from src.graphics.obstacle_item import ObstacleItem
    from src.models.venue import Wall, Obstacle, Point

    # Collect walls
    self._project.venue.walls = []
    for item in self.scene.items():
        if isinstance(item, WallItem):
            polygon = item.polygon()
            points = [Point(polygon.at(i).x(), polygon.at(i).y()) for i in range(polygon.count())]
            self._project.venue.walls.append(Wall(points=points))

    # Collect obstacles
    self._project.venue.obstacles = []
    for item in self.scene.items():
        if isinstance(item, ObstacleItem):
            polygon = item.polygon()
            points = [Point(polygon.at(i).x(), polygon.at(i).y()) for i in range(polygon.count())]
            self._project.venue.obstacles.append(
                Obstacle(name=getattr(item, 'obstacle_name', '障碍物'), type="polygon", points=points)
            )

    # Collect region placements
    from src.models.project import RegionPlacement
    self._project.region_placements = [
        RegionPlacement(
            region_name=item.region.name,
            canvas_x=item.pos().x(),
            canvas_y=item.pos().y(),
            rotation=item.rotation(),
        )
        for item in self._region_items
    ]

def _load_project_to_scene(self):
    """Reconstruct canvas from saved Project state."""
    from PySide6.QtCore import QPointF
    from src.graphics.wall_item import WallItem
    from src.graphics.obstacle_item import ObstacleItem

    self.scene.clear()
    self._region_items = []

    # Restore background image
    if self._project.venue.background_image:
        bg_path = self._project.venue.background_image
        if self._current_path and not os.path.isabs(bg_path):
            bg_path = os.path.join(os.path.dirname(self._current_path), bg_path)
        if os.path.exists(bg_path):
            self.scene.set_background_image(bg_path)

    # Restore walls
    for wall in self._project.venue.walls:
        points = [QPointF(p.x, p.y) for p in wall.points]
        item = WallItem(points)
        self.scene.addItem(item)

    # Restore obstacles
    for obs in self._project.venue.obstacles:
        points = [QPointF(p.x, p.y) for p in obs.points]
        item = ObstacleItem(points)
        item.obstacle_name = obs.name
        self.scene.addItem(item)

    # Restore regions from VR config + placements
    if self._project.vr_config_path:
        vr_path = self._project.vr_config_path
        if self._current_path and not os.path.isabs(vr_path):
            vr_path = os.path.join(os.path.dirname(self._current_path), vr_path)
        if os.path.exists(vr_path):
            regions = Region.load_from_file(vr_path)
            self._region_items = self.scene.load_regions(regions)
            # Apply saved placements
            placement_map = {p.region_name: p for p in self._project.region_placements}
            for item in self._region_items:
                pl = placement_map.get(item.region.name)
                if pl:
                    item.setPos(pl.canvas_x, pl.canvas_y)
                    item.setRotation(pl.rotation)
            self.side_panel.set_region_items(self._region_items)

def _undo(self):
    if self._undo_stack:
        self._undo_stack.undo()

def _redo(self):
    if self._undo_stack:
        self._undo_stack.redo()

def _delete_selected(self):
    for item in self.scene.selectedItems():
        self.scene.removeItem(item)
        if item in self._region_items:
            self._region_items.remove(item)
```

- [ ] **Step 3: Verify manually — all menu items work: new/open/save project, import config, import background, export JSON**

Run: `python src/main.py`
Expected: Full file operation workflow functional.

- [ ] **Step 4: Commit**

```bash
git add src/main.py
git commit -m "feat: add menu bar with file operations"
```

---

### Task 12: Collision Detection

**Files:**
- Modify: `src/graphics/region_item.py`
- Modify: `src/graphics/canvas.py`

- [ ] **Step 1: Add collision checking to scene**

Add to `VenueGraphicsScene`:

```python
def check_collisions(self):
    """Check all RegionItems for collisions with obstacles, other regions, and walls."""
    from src.graphics.region_item import RegionItem
    from src.graphics.wall_item import WallItem
    from src.graphics.obstacle_item import ObstacleItem

    region_items = [item for item in self.items() if isinstance(item, RegionItem)]
    obstacles = [item for item in self.items() if isinstance(item, ObstacleItem)]
    walls = [item for item in self.items() if isinstance(item, WallItem)]

    for region in region_items:
        colliding = False
        # Check against obstacles
        for obs in obstacles:
            if region.collidesWithItem(obs):
                colliding = True
                break
        # Check against other regions
        if not colliding:
            for other in region_items:
                if other is not region and region.collidesWithItem(other):
                    colliding = True
                    break
        # Check against walls (region should be inside wall boundary)
        if not colliding and walls:
            from PySide6.QtGui import QPainterPath
            for wall in walls:
                wall_path = QPainterPath()
                wall_path.addPolygon(wall.polygon())
                wall_path.closeSubpath()
                region_scene_path = region.mapToScene(region._boundary_item.shape())
                region_path = QPainterPath()
                region_path.addPolygon(region_scene_path)
                if not wall_path.contains(region_path):
                    colliding = True
                    break

        region.set_collision(colliding)
```

- [ ] **Step 2: Trigger collision check on region movement**

Override `itemChange` in `RegionItem` to emit a signal when position changes, and connect it to `check_collisions` in the scene.

- [ ] **Step 3: Verify manually — drag a region over an obstacle, border turns red. Drag apart, border returns to normal.**

Run: `python src/main.py`
Expected: Red border warning on overlap.

- [ ] **Step 4: Commit**

```bash
git add src/graphics/region_item.py src/graphics/canvas.py
git commit -m "feat: add collision detection with visual warning"
```

---

### Task 13: Undo/Redo

**Files:**
- Modify: `src/main.py`
- Modify: `src/graphics/canvas.py`

- [ ] **Step 1: Add QUndoStack and undo commands for region movement/rotation**

Create undo commands for:
- `MoveRegionCommand` — stores old/new position
- `RotateRegionCommand` — stores old/new angle

```python
from PySide6.QtGui import QUndoCommand, QUndoStack

class MoveRegionCommand(QUndoCommand):
    def __init__(self, item, old_pos, new_pos):
        super().__init__(f"Move {item.region.name}")
        self.item = item
        self.old_pos = old_pos
        self.new_pos = new_pos

    def redo(self):
        self.item.setPos(self.new_pos)

    def undo(self):
        self.item.setPos(self.old_pos)
```

- [ ] **Step 2: Integrate undo stack into main window, wire Ctrl+Z / Ctrl+Y**

- [ ] **Step 3: Verify manually — move a region, Ctrl+Z undoes it, Ctrl+Y redoes it**

Run: `python src/main.py`
Expected: Undo/redo works for region movement.

- [ ] **Step 4: Commit**

```bash
git add src/main.py src/graphics/canvas.py
git commit -m "feat: add undo/redo for region operations"
```

---

### Task 14: Snap to Grid + Delete Selected

**Files:**
- Modify: `src/graphics/region_item.py`
- Modify: `src/graphics/canvas.py`
- Modify: `src/main.py`

- [ ] **Step 1: Add snap-to-grid option**

Merge snap-to-grid into RegionItem's `itemChange` (which already handles side panel sync from Task 10):

```python
def itemChange(self, change, value):
    if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange and self.scene():
        grid = self.scene().grid_size
        if self.scene()._snap_to_grid:
            x = round(value.x() / grid) * grid
            y = round(value.y() / grid) * grid
            value = QPointF(x, y)
        return value
    if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
        if self.scene():
            self.scene().region_moved.emit(self.region.name)
    return super().itemChange(change, value)
```

Add `self._snap_to_grid = True` to `VenueGraphicsScene.__init__`.

- [ ] **Step 2: Add toggle for snap-to-grid in toolbar/menu**

Add a checkable action "吸附网格 (G)" to toolbar.

- [ ] **Step 3: Add keyboard shortcuts for tool modes**

Override `keyPressEvent` in `MainWindow`:

```python
def keyPressEvent(self, event):
    key = event.key()
    if key == Qt.Key.Key_S:
        self.toolbar.set_mode(ToolMode.SELECT)
    elif key == Qt.Key.Key_W:
        self.toolbar.set_mode(ToolMode.WALL)
    elif key == Qt.Key.Key_O:
        self.toolbar.set_mode(ToolMode.OBSTACLE)
    elif key == Qt.Key.Key_G:
        self.scene._snap_to_grid = not self.scene._snap_to_grid
    elif key == Qt.Key.Key_Escape:
        self.scene.stop_wall_drawing()
        self.scene.stop_obstacle_drawing()
    else:
        super().keyPressEvent(event)
```

- [ ] **Step 4: Verify manually — toggle snap, items snap to grid. Keyboard shortcuts work. Select item, press Delete, item removed.**

Run: `python src/main.py`
Expected: Snap to grid and delete work.

- [ ] **Step 5: Commit**

```bash
git add src/graphics/region_item.py src/graphics/canvas.py src/main.py
git commit -m "feat: add snap-to-grid and delete selected"
```

---

### Task 15: Integration Testing + Polish

**Files:**
- Modify: `src/main.py`

- [ ] **Step 1: Full workflow test**

Manual end-to-end test:
1. Launch app
2. Draw venue walls (closed polygon)
3. Draw obstacle (pillar)
4. Import background image
5. Import VR config JSON
6. Drag and rotate regions to desired positions
7. Verify collision warnings work
8. Save as .vrproject
9. Close and reopen .vrproject — verify state restored
10. Export JSON — verify coordinates are relative to Region1 StartPoint

- [ ] **Step 2: Fix any issues found during integration test**

- [ ] **Step 3: Add keyboard shortcuts summary to status bar or help menu**

```
S: Select mode | W: Wall mode | O: Obstacle mode | G: Toggle grid snap
Delete: Remove selected | Ctrl+Z: Undo | Ctrl+Y: Redo
Middle mouse: Pan | Scroll: Zoom | Shift+drag: Rotate region
```

- [ ] **Step 4: Commit**

```bash
git add -A
git commit -m "feat: integration polish and keyboard shortcuts"
```

---

### Task 16: PyInstaller Packaging

**Files:**
- Modify: `src/main.py` (if needed for resource paths)

- [ ] **Step 1: Test PyInstaller build**

Run:
```bash
pyinstaller --onefile --windowed --name VisualRouter src/main.py
```
Expected: `dist/VisualRouter.exe` is created.

- [ ] **Step 2: Test the exe**

Run: `dist/VisualRouter.exe`
Expected: Application launches and works identically to `python src/main.py`.

- [ ] **Step 3: Fix any packaging issues** (common: missing PySide6 plugins, resource paths)

- [ ] **Step 4: Commit**

```bash
git add visualrouter.spec
git commit -m "feat: add PyInstaller packaging config"
```

---

## Summary

| Task | Description | Dependencies |
|------|-------------|--------------|
| 1 | Project setup | - |
| 2 | Venue data models | 1 |
| 3 | Region data models | 2 |
| 4 | Project model (save/load) | 2, 3 |
| 5 | Export logic | 3 |
| 6 | Canvas (grid, zoom, pan) | 1 |
| 7 | Wall drawing tool | 6 |
| 8 | Obstacle drawing tool | 6 |
| 9 | Region graphics item | 3, 6 |
| 10 | Side panel | 9 |
| 11 | Menu bar (file ops) | 4, 5, 9, 10 |
| 12 | Collision detection | 7, 8, 9 |
| 13 | Undo/redo | 9 |
| 14 | Snap to grid + delete + shortcuts | 9 |
| 15 | Integration testing | All above |
| 16 | PyInstaller packaging | 15 |

### Parallelization Opportunities

- **Tasks 2 + 6** can run in parallel (data models vs canvas, no code dependencies)
- **Tasks 5 + 7 + 8** can run in parallel (export logic, wall tool, obstacle tool are independent)
- **Tasks 12 + 13 + 14** can run in parallel (collision, undo, snap are independent features on top of RegionItem)
