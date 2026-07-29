import database
from auth import hash_password


def test_create_starter_pack(test_db):
    u = test_db.create_user("pack_owner", "po@test.com", "hash")
    pid = test_db.create_starter_pack(u, "Cool People", "A curated list")
    assert pid > 0
    pack = test_db.get_starter_pack(pid)
    assert pack["name"] == "Cool People"
    assert pack["description"] == "A curated list"
    assert pack["user_id"] == u


def test_get_starter_pack_missing(test_db):
    pack = test_db.get_starter_pack(99999)
    assert pack is None


def test_list_starter_packs(test_db):
    u = test_db.create_user("pack_lister", "pl@test.com", "hash")
    test_db.create_starter_pack(u, "Pack A", "First")
    test_db.create_starter_pack(u, "Pack B", "Second")
    packs = test_db.list_starter_packs()
    assert len(packs) == 2
    names = {p["name"] for p in packs}
    assert names == {"Pack A", "Pack B"}


def test_list_starter_packs_member_count(test_db):
    a = test_db.create_user("count_a", "ca@test.com", "hash")
    b = test_db.create_user("count_b", "cb@test.com", "hash")
    c = test_db.create_user("count_c", "cc@test.com", "hash")
    pid = test_db.create_starter_pack(a, "Counted", "desc")
    test_db.add_to_starter_pack(pid, b)
    test_db.add_to_starter_pack(pid, c)
    packs = test_db.list_starter_packs()
    assert packs[0]["member_count"] == 2


def test_add_to_starter_pack(test_db):
    a = test_db.create_user("add_a", "aa@test.com", "hash")
    b = test_db.create_user("add_b", "ab@test.com", "hash")
    pid = test_db.create_starter_pack(a, "Adders", "")
    mid = test_db.add_to_starter_pack(pid, b, sort_order=5)
    assert mid > 0
    members = test_db.get_starter_pack_members(pid)
    assert len(members) == 1
    assert members[0]["user_id"] == b
    assert members[0]["sort_order"] == 5
    assert members[0]["username"] == "add_b"


def test_remove_from_starter_pack(test_db):
    a = test_db.create_user("rem_a", "ra@test.com", "hash")
    b = test_db.create_user("rem_b", "rb@test.com", "hash")
    pid = test_db.create_starter_pack(a, "Removers", "")
    test_db.add_to_starter_pack(pid, b)
    assert len(test_db.get_starter_pack_members(pid)) == 1
    deleted = test_db.remove_from_starter_pack(pid, b)
    assert deleted is True
    assert len(test_db.get_starter_pack_members(pid)) == 0
    # Removing again returns False
    deleted2 = test_db.remove_from_starter_pack(pid, b)
    assert deleted2 is False


def test_get_starter_pack_members_sorted(test_db):
    a = test_db.create_user("sort_a", "sa@test.com", "hash")
    b = test_db.create_user("sort_b", "sb@test.com", "hash")
    c = test_db.create_user("sort_c", "sc@test.com", "hash")
    pid = test_db.create_starter_pack(a, "Sorted", "")
    test_db.add_to_starter_pack(pid, c, sort_order=2)
    test_db.add_to_starter_pack(pid, b, sort_order=1)
    members = test_db.get_starter_pack_members(pid)
    assert len(members) == 2
    assert members[0]["user_id"] == b  # sort_order=1
    assert members[1]["user_id"] == c  # sort_order=2


def test_follow_all_in_pack(test_db):
    a = test_db.create_user("fol_a", "fa@test.com", "hash")
    b = test_db.create_user("fol_b", "fb@test.com", "hash")
    c = test_db.create_user("fol_c", "fc@test.com", "hash")
    d = test_db.create_user("fol_d", "fd@test.com", "hash")
    pid = test_db.create_starter_pack(a, "Followers", "")
    test_db.add_to_starter_pack(pid, b)
    test_db.add_to_starter_pack(pid, c)
    # d follows all in pack (b and c) — 2 new requests
    count = test_db.follow_all_in_pack(d, pid)
    assert count == 2
    # Check friendships exist
    assert test_db.get_friendship(d, b) is not None
    assert test_db.get_friendship(d, c) is not None


def test_follow_all_in_pack_skips_self(test_db):
    a = test_db.create_user("self_a", "sea@test.com", "hash")
    b = test_db.create_user("self_b", "seb@test.com", "hash")
    pid = test_db.create_starter_pack(a, "Self Skip", "")
    test_db.add_to_starter_pack(pid, a)  # add self to pack
    test_db.add_to_starter_pack(pid, b)
    # a follows all — should skip self, only follow b
    count = test_db.follow_all_in_pack(a, pid)
    assert count == 1


def test_follow_all_in_pack_skips_existing_friends(test_db):
    a = test_db.create_user("exist_a", "ea@test.com", "hash")
    b = test_db.create_user("exist_b", "eb@test.com", "hash")
    c = test_db.create_user("exist_c", "ec@test.com", "hash")
    pid = test_db.create_starter_pack(a, "Existing", "")
    test_db.add_to_starter_pack(pid, b)
    test_db.add_to_starter_pack(pid, c)
    # a is already pending-friends with b
    test_db.send_friend_request(a, b)
    # a follows all — only c is new (b already has a request)
    count = test_db.follow_all_in_pack(a, pid)
    assert count == 1


def test_follow_all_in_pack_empty(test_db):
    a = test_db.create_user("empty_a", "ema@test.com", "hash")
    pid = test_db.create_starter_pack(a, "Empty", "")
    count = test_db.follow_all_in_pack(a, pid)
    assert count == 0


# ---------------------------------------------------------------------------
# Route tests
# ---------------------------------------------------------------------------

def test_packs_route(client):
    client.post("/signup", data={
        "username": "packs_user", "email": "pu@test.com",
        "password": "password123", "password2": "password123",
    }, follow_redirects=True)
    rv = client.get("/packs", follow_redirects=True)
    assert rv.status_code == 200
    assert b"Starter Packs" in rv.data


def test_pack_new_route(client):
    client.post("/signup", data={
        "username": "new_pack_user", "email": "npu@test.com",
        "password": "password123", "password2": "password123",
    }, follow_redirects=True)
    rv = client.post("/pack/new", data={
        "name": "Route Pack",
        "description": "Via route",
    }, follow_redirects=True)
    assert rv.status_code == 200
    assert b"Route Pack" in rv.data


def test_pack_detail_route(client):
    client.post("/signup", data={
        "username": "detail_user", "email": "du@test.com",
        "password": "password123", "password2": "password123",
    }, follow_redirects=True)
    import database as db
    uid = db.get_user_by_username("detail_user")["id"]
    pid = db.create_starter_pack(uid, "Detail Pack", "Detail desc")
    rv = client.get(f"/pack/{pid}", follow_redirects=True)
    assert rv.status_code == 200
    assert b"Detail Pack" in rv.data


def test_pack_add_remove_route(client):
    client.post("/signup", data={
        "username": "addrem_user", "email": "aru@test.com",
        "password": "password123", "password2": "password123",
    }, follow_redirects=True)
    import database as db
    uid = db.get_user_by_username("addrem_user")["id"]
    other = db.create_user("addrem_other", "aro@test.com", hash_password("pass"))
    pid = db.create_starter_pack(uid, "Add Rem", "")
    # Add
    rv = client.post(f"/pack/{pid}/add", data={"user_id": other}, follow_redirects=True)
    assert rv.status_code == 200
    members = db.get_starter_pack_members(pid)
    assert len(members) == 1
    assert members[0]["user_id"] == other
    # Remove
    rv = client.post(f"/pack/{pid}/remove", data={"user_id": other}, follow_redirects=True)
    assert rv.status_code == 200
    assert len(db.get_starter_pack_members(pid)) == 0


def test_pack_follow_all_route(client):
    client.post("/signup", data={
        "username": "follow_user", "email": "fu@test.com",
        "password": "password123", "password2": "password123",
    }, follow_redirects=True)
    import database as db
    uid = db.get_user_by_username("follow_user")["id"]
    m1 = db.create_user("follow_m1", "fm1@test.com", hash_password("pass"))
    m2 = db.create_user("follow_m2", "fm2@test.com", hash_password("pass"))
    pid = db.create_starter_pack(uid, "Follow Pack", "")
    db.add_to_starter_pack(pid, m1)
    db.add_to_starter_pack(pid, m2)
    rv = client.post(f"/pack/{pid}/follow-all", follow_redirects=True)
    assert rv.status_code == 200
    assert db.get_friendship(uid, m1) is not None
    assert db.get_friendship(uid, m2) is not None