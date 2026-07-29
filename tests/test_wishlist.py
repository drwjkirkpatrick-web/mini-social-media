import database


def test_wishlist_and_claim(test_db):
    u = test_db.create_user("wisher", "w@test.com", "hash")
    c = test_db.create_user("claimer", "c@test.com", "hash")
    wid = database.add_wishlist_item(u, "New Book", "https://book.com", "$15")
    items = database.get_wishlist(u)
    assert len(items) == 1
    database.claim_wishlist_item(wid, c)
    items2 = database.get_wishlist(u)
    assert items2[0]["is_claimed"] == 1
