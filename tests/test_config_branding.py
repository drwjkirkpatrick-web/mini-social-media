from config import get_config


def test_config_has_branding_fields():
    cfg = get_config()
    assert hasattr(cfg, "site_logo_url")
    assert hasattr(cfg, "site_motto")
