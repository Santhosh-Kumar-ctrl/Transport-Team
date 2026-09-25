from app.core.roles import Role


async def test_route_with_ordered_stops(world):
    route = await world.route(n_stops=3, gap_min=15)
    assert [s["sequence"] for s in route["stops"]] == [1, 2, 3]
    assert [s["offset_min"] for s in route["stops"]] == [0, 15, 30]
    assert route["stops"][-1]["stop"]["name"] == "Campus"


async def test_reorder_keeps_route_stop_ids(world, client):
    route = await world.route(n_stops=3)
    first, second, campus = route["stops"]
    body = [{"stop_id": second["stop_id"], "offset_min": 0},
            {"stop_id": first["stop_id"], "offset_min": 8},
            {"stop_id": campus["stop_id"], "offset_min": 20}]
    r = await client.put(f"/routes/{route['id']}/stops", json=body, headers=world.admin["headers"])
    assert r.status_code == 200, r.text
    new = r.json()["stops"]
    assert [s["stop_id"] for s in new] == [second["stop_id"], first["stop_id"], campus["stop_id"]]
    # same RouteStop rows, re-sequenced (allocations pointing at them survive)
    assert {s["id"] for s in new} == {first["id"], second["id"], campus["id"]}


async def test_route_stop_validation(world, client):
    route = await world.route(n_stops=2)
    a, b = route["stops"]
    dup = [{"stop_id": a["stop_id"], "offset_min": 0}, {"stop_id": a["stop_id"], "offset_min": 5}]
    r = await client.put(f"/routes/{route['id']}/stops", json=dup, headers=world.admin["headers"])
    assert r.status_code == 422 and r.json()["code"] == "duplicate_stop"
    backwards = [{"stop_id": a["stop_id"], "offset_min": 10}, {"stop_id": b["stop_id"], "offset_min": 5}]
    r = await client.put(f"/routes/{route['id']}/stops", json=backwards, headers=world.admin["headers"])
    assert r.status_code == 422 and r.json()["code"] == "bad_offsets"


async def test_bus_crud_and_permissions(world):
    bus = await world.bus(capacity=45)
    assert bus["registration_no"].startswith("TN09AB")
    dup = await world.post("/buses", {"registration_no": bus["registration_no"].lower(), "capacity": 30}, expect=409)
    assert dup.status_code == 409
    student = await world.user(Role.STUDENT)
    await world.post("/buses", {"registration_no": "KA01X1", "capacity": 30}, who=student, expect=403)
    # students can still read routes (they need the line diagram)
    await world.get("/routes", who=student)
