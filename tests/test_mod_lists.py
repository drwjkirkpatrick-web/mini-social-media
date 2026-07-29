import database


# ---------------------------------------------------------------------------
# CRUD tests (test_db fixture from conftest.py)
# ---------------------------------------------------------------------------

def test_create_and_get_mod_list(test_db):
    u = test_db.create_user("mod_owner", "owner@test.com", "hash")
    lid = database.create_mod_list(u, "Bad Actors", "Spammers and trolls", "block")
    assert lid > 0
    ml = database.get_mod_list(lid)
    assert ml is not None
    assert ml["name"] == "Bad Actors"
    assert ml["description"] == "Spammers and trolls"
    assert ml["list_type"] == "block"
    assert ml["user_id"] == u
    assert ml["member_count"] == 0


def test_create_mod_list_defaults_to_block(test_db):
    u = test_db.create_user("mod_owner2", "owner2@test.com", "hash")
    lid = database.create_mod_list(u, "Muted Users")
    ml = database.get_mod_list(lid)
    assert ml["list_type"] == "block"
    assert ml["description"] == ""


def test_create_mod_list_mute_type(test_db):
    u = test_db.create_user("mod_owner3", "owner3@test.com", "hash")
    lid = database.create_mod_list(u, "Quiet List", "", "mute")
    ml = database.get_mod_list(lid)
    assert ml["list_type"] == "mute"


def test_get_mod_list_nonexistent(test_db):
    assert database.get_mod_list(99999) is None


def test_list_mod_lists(test_db):
    u = test_db.create_user("lister", "lister@test.com", "hash")
    database.create_mod_list(u, "List A", "", "block")
    database.create_mod_list(u, "List B", "", "mute")
    lists = database.list_mod_lists(limit=50)
    assert len(lists) == 2
    # list_mod_lists should include member_count column
    assert "member_count" in lists[0]


def test_list_mod_lists_with_limit(test_db):
    u = test_db.create_user("lister2", "lister2@test.com", "hash")
    for i in range(5):
        database.create_mod_list(u, f"List {i}", "", "block")
    lists = database.list_mod_lists(limit=3)
    assert len(lists) == 3


def test_list_my_mod_lists(test_db):
    u1 = test_db.create_user("mine1", "mine1@test.com", "hash")
    u2 = test_db.create_user("mine2", "mine2@test.com", "hash")
    database.create_mod_list(u1, "Mine", "", "block")
    database.create_mod_list(u2, "Theirs", "", "block")
    mine = database.list_my_mod_lists(u1)
    assert len(mine) == 1
    assert mine[0]["name"] == "Mine"


def test_add_and_get_mod_list_members(test_db):
    owner = test_db.create_user("mem_owner", "mo@test.com", "hash")
    target = test_db.create_user("mem_target", "mt@test.com", "hash")
    lid = database.create_mod_list(owner, "Block List", "", "block")
    mid = database.add_to_mod_list(lid, target)
    assert mid > 0
    members = database.get_mod_list_members(lid)
    assert len(members) == 1
    assert members[0]["target_user_id"] == target
    assert members[0]["username"] == "mem_target"
    # member_count in get_mod_list should reflect this
    ml = database.get_mod_list(lid)
    assert ml["member_count"] == 1


def test_remove_from_mod_list(test_db):
    owner = test_db.create_user("rem_owner", "ro@test.com", "hash")
    target = test_db.create_user("rem_target", "rt@test.com", "hash")
    lid = database.create_mod_list(owner, "Remove List", "", "block")
    database.add_to_mod_list(lid, target)
    removed = database.remove_from_mod_list(lid, target)
    assert removed is True
    members = database.get_mod_list_members(lid)
    assert len(members) == 0
    # Removing again should return False
    removed2 = database.remove_from_mod_list(lid, target)
    assert removed2 is False


def test_subscribe_and_get_subscribed(test_db):
    owner = test_db.create_user("sub_owner", "so@test.com", "hash")
    subscriber = test_db.create_user("sub_user", "su@test.com", "hash")
    lid = database.create_mod_list(owner, "Shared Block List", "", "block")
    sid = database.subscribe_mod_list(subscriber, lid)
    assert sid > 0
    subs = database.get_subscribed_mod_lists(subscriber)
    assert len(subs) == 1
    assert subs[0]["mod_list_id"] == lid
    assert subs[0]["name"] == "Shared Block List"
    assert subs[0]["owner_username"] == "sub_owner"


def test_unsubscribe_mod_list(test_db):
    owner = test_db.create_user("unsub_owner", "uo@test.com", "hash")
    subscriber = test_db.create_user("unsub_user", "uu@test.com", "hash")
    lid = database.create_mod_list(owner, "Unsub List", "", "block")
    database.subscribe_mod_list(subscriber, lid)
    removed = database.unsubscribe_mod_list(subscriber, lid)
    assert removed is True
    subs = database.get_subscribed_mod_lists(subscriber)
    assert len(subs) == 0
    # Unsubscribing again returns False
    removed2 = database.unsubscribe_mod_list(subscriber, lid)
    assert removed2 is False


def test_get_all_blocked_from_subscribed(test_db):
    owner = test_db.create_user("blk_owner", "bo@test.com", "hash")
    subscriber = test_db.create_user("blk_sub", "bs@test.com", "hash")
    t1 = test_db.create_user("blk_t1", "bt1@test.com", "hash")
    t2 = test_db.create_user("blk_t2", "bt2@test.com", "hash")
    lid = database.create_mod_list(owner, "Block List", "", "block")
    database.add_to_mod_list(lid, t1)
    database.add_to_mod_list(lid, t2)
    database.subscribe_mod_list(subscriber, lid)
    blocked = database.get_all_blocked_from_subscribed(subscriber)
    assert set(blocked) == {t1, t2}


def test_get_all_muted_from_subscribed(test_db):
    owner = test_db.create_user("mut_owner", "mo@test.com", "hash")
    subscriber = test_db.create_user("mut_sub", "ms@test.com", "hash")
    t1 = test_db.create_user("mut_t1", "mt1@test.com", "hash")
    t2 = test_db.create_user("mut_t2", "mt2@test.com", "hash")
    lid = database.create_mod_list(owner, "Mute List", "", "mute")
    database.add_to_mod_list(lid, t1)
    database.add_to_mod_list(lid, t2)
    database.subscribe_mod_list(subscriber, lid)
    muted = database.get_all_muted_from_subscribed(subscriber)
    assert set(muted) == {t1, t2}


def test_get_all_blocked_excludes_mute_lists(test_db):
    owner = test_db.create_user("mix_owner", "mo@test.com", "hash")
    subscriber = test_db.create_user("mix_sub", "ms@test.com", "hash")
    blk_target = test_db.create_user("mix_blk", "mb@test.com", "hash")
    mut_target = test_db.create_user("mix_mut", "mm@test.com", "hash")
    blk_list = database.create_mod_list(owner, "Block", "", "block")
    mut_list = database.create_mod_list(owner, "Mute", "", "mute")
    database.add_to_mod_list(blk_list, blk_target)
    database.add_to_mod_list(mut_list, mut_target)
    database.subscribe_mod_list(subscriber, blk_list)
    database.subscribe_mod_list(subscriber, mut_list)
    blocked = database.get_all_blocked_from_subscribed(subscriber)
    muted = database.get_all_muted_from_subscribed(subscriber)
    assert blk_target in blocked
    assert mut_target not in blocked
    assert mut_target in muted
    assert blk_target not in muted


def test_get_all_from_subscribed_no_subs(test_db):
    subscriber = test_db.create_user("nosub", "ns@test.com", "hash")
    assert database.get_all_blocked_from_subscribed(subscriber) == []
    assert database.get_all_muted_from_subscribed(subscriber) == []


def test_get_all_from_subscribed_multiple_lists_dedup(test_db):
    owner = test_db.create_user("dedup_owner", "do@test.com", "hash")
    subscriber = test_db.create_user("dedup_sub", "ds@test.com", "hash")
    target = test_db.create_user("dedup_target", "dt@test.com", "hash")
    l1 = database.create_mod_list(owner, "Block List 1", "", "block")
    l2 = database.create_mod_list(owner, "Block List 2", "", "block")
    # Same target in both lists
    database.add_to_mod_list(l1, target)
    database.add_to_mod_list(l2, target)
    database.subscribe_mod_list(subscriber, l1)
    database.subscribe_mod_list(subscriber, l2)
    blocked = database.get_all_blocked_from_subscribed(subscriber)
    # Should be deduplicated to a single entry
    assert blocked == [target]


# ---------------------------------------------------------------------------
# Route tests (client fixture from conftest.py)
# ---------------------------------------------------------------------------

def _signup_and_login(client, username="moduser", email="mod@test.com"):
    client.post("/signup", data={
        "username": username, "email": email,
        "password": "password123", "password2": "password123",
    }, follow_redirects=True)


def test_modlists_page(client):
    _signup_and_login(client)
    rv = client.get("/modlists")
    assert rv.status_code == 200
    assert b"Moderation Lists" in rv.data


def test_new_mod_list_get(client):
    _signup_and_login(client)
    rv = client.get("/modlist/new")
    assert rv.status_code == 200
    assert b"Create" in rv.data


def test_new_mod_list_post(client):
    _signup_and_login(client)
    rv = client.post("/modlist/new", data={
        "name": "My Block List",
        "description": "Test description",
        "list_type": "block",
    }, follow_redirects=True)
    assert rv.status_code == 200
    assert b"My Block List" in rv.data


def test_mod_list_detail_page(client):
    _signup_and_login(client)
    # Create a list via the route
    client.post("/modlist/new", data={
        "name": "Detail Test",
        "description": "For detail page",
        "list_type": "block",
    }, follow_redirects=True)
    rv = client.get("/modlist/1")
    assert rv.status_code == 200
    assert b"Detail Test" in rv.data


def test_mod_list_detail_404(client):
    _signup_and_login(client)
    rv = client.get("/modlist/99999")
    assert rv.status_code == 404


def test_mod_list_add_member(client):
    _signup_and_login(client, username="add_owner", email="ao@test.com")
    # Create a list
    client.post("/modlist/new", data={
        "name": "Add Member List", "description": "", "list_type": "block",
    }, follow_redirects=True)
    # Create a target user
    import database
    target = database.create_user("add_target", "at@test.com", "hash")
    rv = client.post("/modlist/1/add", data={"target_user_id": target}, follow_redirects=True)
    assert rv.status_code == 200
    assert b"add_target" in rv.data


def test_mod_list_remove_member(client):
    _signup_and_login(client, username="rem_owner", email="ro@test.com")
    client.post("/modlist/new", data={
        "name": "Remove Member List", "description": "", "list_type": "block",
    }, follow_redirects=True)
    import database
    target = database.create_user("rem_target", "rt2@test.com", "hash")
    client.post("/modlist/1/add", data={"target_user_id": target}, follow_redirects=True)
    rv = client.post("/modlist/1/remove", data={"target_user_id": target}, follow_redirects=True)
    assert rv.status_code == 200
    assert b"No members yet" in rv.data


def test_mod_list_subscribe(client):
    _signup_and_login(client, username="sub_route", email="sr@test.com")
    # Create a list first
    client.post("/modlist/new", data={
        "name": "Subscribe Test", "description": "", "list_type": "block",
    }, follow_redirects=True)
    rv = client.post("/modlist/1/subscribe", follow_redirects=True)
    assert rv.status_code == 200
    # After subscribing, the lists page should show Unsubscribe button
    rv = client.get("/modlists")
    assert b"Unsubscribe" in rv.data


def test_mod_list_unsubscribe(client):
    _signup_and_login(client, username="unsub_route", email="usr@test.com")
    client.post("/modlist/new", data={
        "name": "Unsubscribe Test", "description": "", "list_type": "block",
    }, follow_redirects=True)
    client.post("/modlist/1/subscribe", follow_redirects=True)
    rv = client.post("/modlist/1/unsubscribe", follow_redirects=True)
    assert rv.status_code == 200
    # After unsubscribing, the lists page should show Subscribe button
    rv = client.get("/modlists")
    assert b"Subscribe" in rv.data


def test_modlists_requires_login(client):
    rv = client.get("/modlists")
    # Should redirect to login (302) since @login_required
    assert rv.status_code == 302