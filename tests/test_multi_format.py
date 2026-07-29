from uploads import allowed_file


def test_multi_format_support():
    assert allowed_file("test.jpg")
    assert allowed_file("test.jpeg")
    assert allowed_file("test.png")
    assert allowed_file("test.gif")
    assert allowed_file("test.webp")
    assert allowed_file("test.heic")
    assert not allowed_file("test.pdf")
