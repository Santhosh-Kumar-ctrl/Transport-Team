from datetime import time

from app.core.roles import Role


async def test_assign_driver_hands_over_schedules_and_upcoming_trips(world, client):
    route = await world.route()
    bus = await world.bus()
    old, new = await world.user(Role.DRIVER, "Old Driver"), await world.user(Role.DRIVER, "New Driver")
    sched = await world.schedule(route, bus, old, departure=time(23, 0))
    trip = await world.todays_trip(sched)

    r = await world.put(f"/buses/{bus['id']}/driver", {"driver_id": new["id"]})
    assert r.json()["driver_id"] == new["id"] and r.json()["driver_name"] == "New Driver"

    schedules = (await world.get("/schedules")).json()
    assert next(s for s in schedules if s["id"] == sched["id"])["driver_id"] == new["id"]
    assert (await world.get(f"/trips/{trip['id']}")).json()["driver"]["id"] == new["id"]
    # the new driver now sees and can start the run; the old one can't
    assert [t["id"] for t in (await world.get("/trips/mine", who=new)).json()] == [trip["id"]]
    await world.post(f"/trips/{trip['id']}/start", who=old, expect=403)

    assert (await world.inbox(new))[0]["title"] == f"You're now driving bus {bus['registration_no']}"


async def test_running_trip_keeps_its_driver(world):
    w = await world.running_trip()
    new = await world.user(Role.DRIVER)
    await world.put(f"/buses/{w['bus']['id']}/driver", {"driver_id": new["id"]})
    assert (await world.get(f"/trips/{w['trip']['id']}")).json()["driver"]["id"] == w["driver"]["id"]


async def test_driver_on_one_bus_at_a_time(world):
    b1, b2 = await world.bus(), await world.bus()
    d = await world.user(Role.DRIVER)
    await world.put(f"/buses/{b1['id']}/driver", {"driver_id": d["id"]})
    r = await world.put(f"/buses/{b2['id']}/driver", {"driver_id": d["id"]}, expect=409)
    assert r.json()["code"] == "driver_taken" and r.json()["registration_no"] == b1["registration_no"]

    await world.put(f"/buses/{b2['id']}/driver", {"driver_id": d["id"], "move": True})
    buses = {b["id"]: b for b in (await world.get("/buses")).json()}
    assert buses[b1["id"]]["driver_id"] is None and buses[b2["id"]]["driver_id"] == d["id"]


async def test_only_drivers_and_removal(world):
    bus = await world.bus()
    student = await world.user(Role.STUDENT)
    r = await world.put(f"/buses/{bus['id']}/driver", {"driver_id": student["id"]}, expect=422)
    assert r.json()["code"] == "wrong_role"
    d = await world.user(Role.DRIVER)
    await world.put(f"/buses/{bus['id']}/driver", {"driver_id": d["id"]})
    r = await world.put(f"/buses/{bus['id']}/driver", {"driver_id": None})
    assert r.json()["driver_id"] is None
    assert "no longer assigned" in (await world.inbox(d))[0]["title"]


async def test_schedule_defaults_to_the_bus_driver(world):
    route = await world.route()
    bus = await world.bus()
    body = {"route_id": route["id"], "bus_id": bus["id"], "direction": "pickup", "departure_time": "07:30:00"}
    r = await world.post("/schedules", body, expect=422)
    assert r.json()["code"] == "driver_required"
    d = await world.user(Role.DRIVER)
    await world.put(f"/buses/{bus['id']}/driver", {"driver_id": d["id"]})
    assert (await world.post("/schedules", body, expect=201)).json()["driver_id"] == d["id"]
