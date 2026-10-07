import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "runtime" / "spikes"))

import base_frame  # noqa: E402

# A home base from a real test save: Position is planet-centred, Forward is tangent to the surface.
POSITION = [-76359.59375, 19496.30078125, -103605.5]
FORWARD = [0.7328844666481018, 0.5163803696632385, -0.4429805874824524]


def close(a, b, tol=1e-6):
    return all(math.isclose(x, y, abs_tol=tol) for x, y in zip(a, b))


def test_the_up_axis_points_away_from_the_planet_centre():
    x, y, z = base_frame.base_basis(POSITION, FORWARD)
    length = math.sqrt(sum(c * c for c in POSITION))
    assert close(y, [c / length for c in POSITION])


def test_the_basis_is_orthonormal():
    axes = base_frame.base_basis(POSITION, FORWARD)
    for i, a in enumerate(axes):
        for j, b in enumerate(axes):
            assert math.isclose(sum(p * q for p, q in zip(a, b)), 1.0 if i == j else 0.0, abs_tol=1e-9)


def test_world_and_local_round_trip():
    for local in ([0.0, 0.0, 0.0], [3.0, 0.5, -12.0], [250.0, -4.0, 80.0]):
        world = base_frame.local_to_world(POSITION, FORWARD, local)
        assert close(base_frame.world_to_local(POSITION, FORWARD, world), local, tol=1e-5)


def test_the_base_origin_maps_to_the_base_position():
    assert close(base_frame.local_to_world(POSITION, FORWARD, [0.0, 0.0, 0.0]), POSITION, tol=1e-6)
