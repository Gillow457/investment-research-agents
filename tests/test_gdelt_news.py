from datetime import date

from research_agents.data.gdelt_news import GDELTNewsProvider


class FakeResponse:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def read(self) -> bytes:
        return (
            b'{"articles":[{"title":"Xiaomi growth remains strong",'
            b'"domain":"example.com","seendate":"20260518T120000Z"}]}'
        )


def test_gdelt_news_provider_maps_articles(monkeypatch) -> None:
    captured = {}

    def fake_urlopen(url: str, timeout: int):
        captured["url"] = url
        captured["timeout"] = timeout
        return FakeResponse()

    monkeypatch.setattr("research_agents.data.gdelt_news.urlopen", fake_urlopen)

    news = GDELTNewsProvider().get_news("1810.HK", date(2026, 5, 19))

    assert "Xiaomi" in captured["url"]
    assert captured["timeout"] == 15
    assert news[0].source == "example.com"
    assert news[0].sentiment > 0


def test_gdelt_news_provider_falls_back_when_empty(monkeypatch) -> None:
    class EmptyResponse(FakeResponse):
        def read(self) -> bytes:
            return b'{"articles":[]}'

    monkeypatch.setattr("research_agents.data.gdelt_news.urlopen", lambda url, timeout: EmptyResponse())

    news = GDELTNewsProvider().get_news("UNKNOWN", date(2026, 5, 19))

    assert news[0].source == "GDELT"
    assert news[0].sentiment == 0.0


def test_gdelt_news_provider_falls_back_on_request_error(monkeypatch) -> None:
    def fake_urlopen(url: str, timeout: int):
        raise OSError("network unavailable")

    monkeypatch.setattr("research_agents.data.gdelt_news.urlopen", fake_urlopen)

    news = GDELTNewsProvider().get_news("1810.HK", date(2026, 5, 19))

    assert news[0].source == "GDELT"
    assert "failed" in news[0].title
    assert news[0].sentiment == 0.0
