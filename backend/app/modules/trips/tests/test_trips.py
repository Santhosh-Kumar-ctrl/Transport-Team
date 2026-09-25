from datetime import datetime, time

from app.core.roles import Role


def _mins(a: str, b: str) -> int:
    return round((datetime.fromisoformat(a) - datetime.fromisoformat(b)).total_seconds() / 60)


async def test_generate_is_idempotent_and_plans_stop_times(world):
    route = await world.route(n_stops=4, gap_min=10)
    bus = await world.bus()
    driver = await world.user(Role.DRIVER)
    sched = await world.schedule(route, bus, driver, departure=time(7, 30))

    first = (await world.post("/trips/generate", {})).json()
    again = (await world.post("/trips/generate", {})).json()
    assert first["created"] == 1 and again["created"] == 0 and again["existing"] == 1

    trip = await world.todays_trip(sched)
    stops = trip["stops"]
    assert [s["stop_name"] for s in stops][-1] == "Campus"
    assert [_mins(s["scheduled_at"], trip["scheduled_departure"]) for s in stops] == [0, 10, 20, 30]


async def test_drop_trip_runs_route_in_reverse(world):
    route = await world.route(n_stops=3, gap_min=15)
    sched = await world.schedule(route, await world.bus(), await world.user(Role.DRIVER),
                                 direction="drop", departure=time(16, 30))
    trip = await world.todays_trip(sched)
    assert trip["stops"][0]["stop_name"] == "Campus"
    assert [_mins(s["scheduled_at"], trip["scheduled_departure"]) for s in trip["stops"]] == [0, 15, 30]


async def test_driver_workflow_start_arrive_end(world):
    w = await world.running_trip(n_stops=3)
    trip, driver = w["trip"], w["driver"]
    assert trip["status"] == "in_progress"
    assert trip["stops"][0]["arrived_at"] is not None  # leaving stop 1 = start
    assert trip["next_stop"]["sequence"] == 2

    trip = (await world.post(f"/trips/{trip['id']}/stops/2/arrive", who=driver)).json()
    assert trip["next_stop"]["sequence"] == 3
    again = await world.post(f"/trips/{trip['id']}/stops/2/arrive", who=driver, expect=409)
    assert again.json()["code"] == "already_arrived"

    trip = (await world.post(f"/trips/{trip['id']}/end", who=driver)).json()
    assert trip["status"] == "completed"
    assert trip["stops"][-1]["arrived_at"] is not None


async def test_only_assigned_driver_operates(world):
    route = await world.route()
    sched = await world.schedule(route, await world.bus(), await world.user(Role.DRIVER))
    trip = await world.todays_trip(sched)
    other = await world.user(Role.DRIVER)
    await world.post(f"/trips/{trip['id']}/start", who=other, expect=403)


async def test_out_of_order_and_state_rules(world):
    w = await world.running_trip(n_stops=4)
    tid, driver = w["trip"]["id"], w["driver"]
    await world.post(f"/trips/{tid}/stops/3/arrive", who=driver)  # skipping stop 2 is allowed
    r = await world.post(f"/trips/{tid}/stops/2/arrive", who=driver, expect=422)
    assert r.json()["code"] == "out_of_order"
    r = await world.post(f"/trips/{tid}/start", who=driver, expect=422)
    assert r.json()["code"] == "bad_trip_state"


async def test_driver_cannot_run_two_trips(world):
    route = await world.route()
    bus1, bus2 = await world.bus(), await world.bus()
    driver = await world.user(Role.DRIVER)
    s1 = await world.schedule(route, bus1, driver)
    s2 = await world.schedule(route, bus2, driver, departure=time(23, 0))
    t1, t2 = await world.todays_trip(s1), await world.todays_trip(s2)
    await world.post(f"/trips/{t1['id']}/start", who=driver)
    r = await world.post(f"/trips/{t2['id']}/start", who=driver, expect=409)
    assert r.json()["code"] == "already_running"


async def test_simulated_timestamps_only_for_admin(world):
    route = await world.route()
    driver = await world.user(Role.DRIVER)
    sched = await world.schedule(route, await world.bus(), driver)
    trip = await world.todays_trip(sched)
    late = world.at(trip["scheduled_departure"], 12)
    await world.post(f"/trips/{trip['id']}/start", {"started_at": late}, who=driver, expect=403)
    started = (await world.post(f"/trips/{trip['id']}/start", {"started_at": late})).json()
    assert started["current_delay_min"] == 12


async def test_cancel_trip(world):
    route = await world.route()
    sched = await world.schedule(route, await world.bus(), await world.user(Role.DRIVER))
    trip = await world.todays_trip(sched)
    r = (await world.post(f"/trips/{trip['id']}/cancel", {"reason": "Bus breakdown"})).json()
    assert r["status"] == "cancelled" and r["cancel_reason"] == "Bus breakdown"


async def test_schedule_requires_driver_role(world):
    route = await world.route()
    student = await world.user(Role.STUDENT)
    body = {"route_id": route["id"], "bus_id": (await world.bus())["id"], "driver_id": student["id"],
            "direction": "pickup", "departure_time": "07:30:00"}
    r = await world.post("/schedules", body, expect=422)
    assert r.json()["code"] == "wrong_role"
