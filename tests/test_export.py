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
    assert exported["StartPoint"]["position"]["x"] == 0
    assert exported["StartPoint"]["position"]["y"] == 0
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
