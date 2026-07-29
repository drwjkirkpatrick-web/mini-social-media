import database


def test_create_album_and_add_photos(test_db):
    u = test_db.create_user("photog", "p@test.com", "hash")
    aid = database.create_album(u, "Vacation", "Summer 2026")
    assert aid > 0
    album = database.get_album(aid)
    assert album["title"] == "Vacation"
    pid = database.add_photo_to_album(aid, "/static/uploads/test.jpg", "Beach day", exif_data="{camera: 'Canon'}")
    photos = database.get_album_photos(aid)
    assert len(photos) == 1
    assert photos[0]["caption"] == "Beach day"
