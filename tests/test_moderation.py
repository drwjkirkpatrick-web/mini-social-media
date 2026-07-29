from moderation import moderate_text, status_from_score


def test_clean_post():
    score, reason = moderate_text("Having a great day at the park!")
    assert score < 30
    assert status_from_score(score) == "approved"


def test_flagged_post():
    score, reason = moderate_text("This is spam spam spam")
    assert score >= 30
    assert status_from_score(score) in ("pending", "rejected")


def test_rejected_post():
    score, reason = moderate_text("Kill them all! spam scam hate")
    assert score > 70 or status_from_score(score) == "rejected"
