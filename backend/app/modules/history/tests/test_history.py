from app.core.roles import Role


async def test_trip_timeline_tells_the_story(world):
    w = await world.running_trip(n_stops=3)
    tid, driver = w["trip"]["id"], w["driver"]
    student = await world.user(Role.STUDENT)
    await world.allocate(student, w["route"], 0)
    await world.board(student, tid, driver)
    await world.post(f"/trips/{tid}/stops/2/arrive", who=driver)
    await world.post(f"/trips/{tid}/end", who=driver)

    timeline = (await world.get(f"/history/trips/{tid}/timeline")).json()
    types = [e["type"] for e in timeline]
    assert types[0] == "TripStarted"
    for expected in ("StudentBoarded", "StopArrived", "TripEnded", "AttendanceFinalized"):
        assert expected in types
    assert timeline[0]["actor_name"] == "Dev Driver"


async def test_trip_report_and_csv(world):
    w = await world.running_trip(n_stops=3)
    tid, driver = w["trip"]["id"], w["driver"]
    s1, s2 = await world.user(Role.STUDENT, "Anu"), await world.user(Role.STUDENT, "Bala")
    await world.allocate(s1, w["route"], 0)
    await world.allocate(s2, w["route"], 1)
    await world.board(s1, tid, driver)
    await world.post(f"/trips/{tid}/end", who=driver)

    report = next(r for r in (await world.get("/history/trips")).json() if r["trip_id"] == tid)
    assert (report["boarded"], report["present"], report["absent"]) == (1, 1, 1)
    assert report["driver_name"] == "Dev Driver"

    r = await world.get("/history/attendance", format="csv")
    assert r.headers["content-type"].startswith("text/csv")
    lines = r.text.strip().splitlines()
    assert lines[0].startswith("date,trip_id,route")
    assert any("Bala" in line and "absent" in line for line in lines)


async def test_event_filters(world):
    await world.route()
    routes = (await world.get("/history/events", type="RouteCreated")).json()
    assert routes and all(e["type"] == "RouteCreated" for e in routes)
    student = await world.user(Role.STUDENT)
    await world.get("/history/events", who=student, expect=403)
