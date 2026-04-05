from __future__ import annotations
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

    canvas_regions = []
    for region in regions:
        pl = placement_map.get(region.name)
        if pl is None:
            continue
        centroid = region.centroid()
        rot = pl["rotation"]
        ox, oy = pl["canvas_x"], pl["canvas_y"]

        def xform(pt: Point, _centroid=centroid, _rot=rot, _ox=ox, _oy=oy) -> Point:
            return transform_point_around_centroid(pt, _centroid, _rot, _ox, _oy)

        canvas_boundary = [xform(p) for p in region.boundary]
        canvas_sp = xform(region.start_point.position)
        canvas_ta = xform(region.target_area.position)
        canvas_vehicle = None
        vehicle_angle = 0
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
            "vehicle_angle": vehicle_angle,
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
