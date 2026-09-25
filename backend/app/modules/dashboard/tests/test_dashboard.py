from datetime import datetime, timedelta

from app.core.roles import Role


async def test_admin_board_shows_live_trip_delay_and_occupancy(world):
    w = await world.running_trip(n_stops=4, capacity=30)
    trip = w["trip"]
    student = await world.user(Role.STUDENT)
    await world.allocate(student, w["route"], 0)
    await world.board(student, trip["id"], w["driver"])
    await world.post(f"/trips/{trip['id']}/stops/2/arrive",
                     {"arrived_at": world.at(trip["stops"][1]["scheduled_at"], 9)})

    dash = (await world.get("/dashboard/admin")).json()
    row = next(r for r in dash["board"] if r["trip_id"] == trip["id"])
    assert row["status"] == "in_progress" and row["delay_min"] == 9
    assert row["boarded"] == 1 and row["capacity"] == 30
    assert row["next_stop"]["sequence"] == 3
    assert dash["counts"]["in_progress"] == 1 and dash["counts"]["delayed_now"] == 1
    assert any(a["type"] == "TripDelayed" for a in dash["alerts"])


async def test_student_dashboard_expected_time_at_my_stop(world):
    w = await world.running_trip(n_stops=4)
    trip = w["trip"]
    student = await world.user(Role.STUDENT)
    await world.allocate(student, w["route"], 2)
    await world.post(f"/trips/{trip['id']}/stops/2/arrive",
                     {"arrived_at": world.at(trip["stops"][1]["scheduled_at"], 6)})
    dash = (await world.get("/dashboard/student", who=student)).json()
    assert dash["allocation"]["route"]["id"] == w["route"]["id"]
    view = dash["trips"][0]
    assert view["delay_min"] == 6 and view["boarded"] is False
    expected = datetime.fromisoformat(view["my_stop"]["expected_at"])
    scheduled = datetime.fromisoformat(view["my_stop"]["scheduled_at"])
    assert expected - scheduled == timedelta(minutes=6)
    assert dash["unread_notifications"] >= 1


async def test_unallocated_student_dashboard_is_empty(world):
    student = await world.user(Role.STUDENT)
    dash = (await world.get("/dashboard/student", who=student)).json()
    assert dash["allocation"] is None and dash["trips"] == []


async def test_driver_dashboard_active_trip(world):
    w = await world.running_trip()
    dash = (await world.get("/dashboard/driver", who=w["driver"])).json()
    assert dash["active"]["trip"]["id"] == w["trip"]["id"]
    assert dash["active"]["capacity"] == 40
