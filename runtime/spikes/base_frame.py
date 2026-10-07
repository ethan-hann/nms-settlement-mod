"""Planet-centred world <-> base-local conversion for a planet base (pure Python, no NMS.py needed).

Evidence for the frame (not invented here):
- Decoded save copy, X:\\Files\\Documents\\!SAVED GAMES AND CONFIGS\\No Mans Sky\\scratch dir\\corvette-destroyer\\save3.hg.json:
  PersistentPlayerBases[i].Objects[*].Position is small (tens to hundreds of units) with ^BASE_FLAG at
  ~(0,0,0), Up (0,1,0), At (0,0,1); the base's own Position is planet-centred (tens of thousands of
  units) and its Forward is a unit vector exactly perpendicular to normalize(Position) (dot = 0.0000 on
  all five home-planet bases).
- NMSE Core/BaseLogic.cs (MoveBaseComputer comments): Y = normalize(Position), Z = Forward made
  perpendicular to Y (Gram-Schmidt), X = cross(Y, Z), world = Position + x*X + y*Y + z*Z.
  https://github.com/vectorcmdr/NMSE/blob/main/Core/BaseLogic.cs  (AGPL-3.0: used as a reference, not copied)

Settlement positions in the save (SettlementStatesV2[*].Position) are in the same planet-centred frame.

Run `python base_frame.py` for the self-test. Unverified in game: that Up/At of a part are rotated by the
same basis, and what scale looks like (non-unit Up/At lengths appear on scaled parts in the save copy).
"""

import math

Vec = tuple


def _sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _add(a, b):
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def _dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def _scale(a, s):
    return (a[0] * s, a[1] * s, a[2] * s)


def _norm(a):
    n = math.sqrt(_dot(a, a))
    if n == 0.0:
        raise ValueError("zero-length vector")
    return _scale(a, 1.0 / n)


def base_basis(base_position, base_forward):
    """Return (x, y, z) unit axes of the base-local frame, in planet-centred space."""
    y = _norm(base_position)
    z = _norm(_sub(base_forward, _scale(y, _dot(base_forward, y))))  # Gram-Schmidt
    x = _norm(_cross(y, z))
    return x, y, z


def local_to_world(base_position, base_forward, local):
    x, y, z = base_basis(base_position, base_forward)
    return _add(base_position, _add(_add(_scale(x, local[0]), _scale(y, local[1])), _scale(z, local[2])))


def world_to_local(base_position, base_forward, world):
    x, y, z = base_basis(base_position, base_forward)
    d = _sub(world, base_position)
    return (_dot(d, x), _dot(d, y), _dot(d, z))


def direction_to_local(base_position, base_forward, direction):
    """Rotate a world-space direction (e.g. a path heading or a surface normal) into the base frame."""
    x, y, z = base_basis(base_position, base_forward)
    return (_dot(direction, x), _dot(direction, y), _dot(direction, z))


def _self_test():
    # Numbers shaped like home base 0 in the save copy: |Position| ~ 98k, Forward perpendicular to it.
    pos = (-90521.0, 3785.0, -38479.0)
    raw_fwd = (-0.05, 0.98, 0.21)
    y = _norm(pos)
    fwd = _norm(_sub(raw_fwd, _scale(y, _dot(raw_fwd, y))))
    assert abs(_dot(fwd, y)) < 1e-9
    for local in [(0.0, 0.0, 0.0), (-19.7, 0.1, 29.3), (127.8, 35.9, -583.8)]:
        back = world_to_local(pos, fwd, local_to_world(pos, fwd, local))
        assert max(abs(a - b) for a, b in zip(back, local)) < 1e-6, (local, back)
    x, y2, z = base_basis(pos, fwd)
    assert abs(_dot(x, y2)) < 1e-9 and abs(_dot(x, z)) < 1e-9 and abs(_dot(y2, z)) < 1e-9
    # BASE_FLAG sits at local (0,0,0) and so maps to the base Position itself.
    assert local_to_world(pos, fwd, (0.0, 0.0, 0.0)) == pos
    # Surface normal in the base frame is (0,1,0) by construction.
    n = direction_to_local(pos, fwd, y2)
    assert abs(n[0]) < 1e-9 and abs(n[1] - 1.0) < 1e-9 and abs(n[2]) < 1e-9
    print("base_frame self-test ok")


if __name__ == "__main__":
    _self_test()
