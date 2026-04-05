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
