from app.core.roles import Role
from app.modules.capacity.schemas import Level
from app.modules.capacity.service import level_for


def test_levels():
    assert level_for(5, 40) == Level.OK
    assert level_for(36, 40) == Level.WARNING  # 90%
    assert level_for(40, 40) == Level.FULL
    assert level_for(41, 40) == Level.OVER
    assert level_for(3, None) == Level.UNKNOWN


async def test_capacity_alerts_raise_once_each(world):
    w = await world.running_trip(capacity=2)
    tid, driver = w["trip"]["id"], w["driver"]
    students = [await world.user(Role.STUDENT) for _ in range(4)]
    for s in students:
        await world.allocate(s, w["route"], 0, force=True)

    await world.board(students[0], tid, driver)  # 1/2 = 50%
    assert (await world.get(f"/capacity/trips/{tid}")).json()["level"] == "ok"
    await world.board(students[1], tid, driver)  # 2/2 -> full: CapacityWarning
    assert (await world.get(f"/capacity/trips/{tid}")).json()["level"] == "full"
    await world.board(students[2], tid, driver)  # 3/2 -> OverCapacity
    await world.board(students[3], tid, driver)  # still over: no duplicate alert

    occ = (await world.get(f"/capacity/trips/{tid}")).json()
    assert occ["boarded"] == 4 and occ["level"] == "over"
    types = [n["type"] for n in await world.inbox(driver)]
    assert types.count("CapacityWarning") == 1
    assert types.count("OverCapacity") == 1
    admin_types = [n["type"] for n in await world.inbox(world.admin)]
    assert "OverCapacity" in admin_types


async def test_route_utilization(world):
    route = await world.route()
    await world.schedule(route, await world.bus(4), await world.user(Role.DRIVER))
    for _ in range(3):
        await world.allocate(await world.user(Role.STUDENT), route, 0)
    util = {u["route_id"]: u for u in (await world.get("/capacity/routes")).json()}
    assert util[route["id"]]["allocated"] == 3
    assert util[route["id"]]["seat_capacity"] == 4
    assert util[route["id"]]["pct"] == 75
