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
