import database


def test_create_and_dismiss_prompt(test_db):
    u = test_db.create_user("prompted", "pr@test.com", "hash")
    pid = database.create_hermes_prompt(u, "connection", "Message Sarah!", "/messages/5")
    prompts = database.get_hermes_prompts(u)
    assert len(prompts) == 1
    database.dismiss_hermes_prompt(pid)
    prompts2 = database.get_hermes_prompts(u)
    assert len(prompts2) == 0
