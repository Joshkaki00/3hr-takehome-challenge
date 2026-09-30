from werkzeug.middleware.proxy_fix import ProxyFix

from app import create_app


def test_proxy_fix_off_by_default(redis_client):
    app = create_app({"TESTING": True, "REDIS_CLIENT": redis_client})
    assert not isinstance(app.wsgi_app, ProxyFix)


def test_proxy_fix_enabled_when_count_set(redis_client):
    app = create_app(
        {
            "TESTING": True,
            "REDIS_CLIENT": redis_client,
            "PROXY_COUNT": 1,
        }
    )
    assert isinstance(app.wsgi_app, ProxyFix)
