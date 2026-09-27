"""app/core/cache.py itself, plus a couple of integration checks that a
public list endpoint's cache doesn't survive a write to that same resource -
the existing create-then-list assertions all over test_content.py already
prove invalidation works in practice (they'd fail on a stale cache); this
file is about the caching mechanism itself."""
from unittest.mock import MagicMock

from app.core import cache as content_cache


def test_cached_only_computes_once_per_key():
    compute = MagicMock(return_value="value")
    assert content_cache.cached("some:key", compute) == "value"
    assert content_cache.cached("some:key", compute) == "value"
    compute.assert_called_once()


def test_cached_recomputes_for_a_different_key():
    compute = MagicMock(side_effect=["a", "b"])
    assert content_cache.cached("key:a", compute) == "a"
    assert content_cache.cached("key:b", compute) == "b"
    assert compute.call_count == 2


def test_invalidate_clears_only_matching_prefix():
    content_cache.cached("temple:profile", lambda: "profile")
    content_cache.cached("temple:timings", lambda: "timings")
    content_cache.cached("gallery:list", lambda: "gallery")

    content_cache.invalidate("temple:")

    fresh_profile = MagicMock(return_value="fresh-profile")
    fresh_gallery = MagicMock(return_value="fresh-gallery")
    assert content_cache.cached("temple:profile", fresh_profile) == "fresh-profile"
    fresh_profile.assert_called_once()  # recomputed - invalidated
    assert content_cache.cached("gallery:list", fresh_gallery) == "gallery"
    fresh_gallery.assert_not_called()  # untouched by the "temple:" invalidation


def test_pooja_public_list_is_served_from_cache_between_requests(client, admin, db):
    _, headers = admin
    client.post("/api/v1/poojas/", headers=headers, json={"name": "Archana", "pooja_type": "daily"})

    first = client.get("/api/v1/poojas/").json()
    assert len(first) == 1

    # A row inserted straight into the DB (bypassing the create endpoint, so
    # nothing calls invalidate()) must NOT appear until the cache expires -
    # that's the whole point of caching.
    from app.models.pooja import Pooja
    db.add(Pooja(name="Untracked Pooja", pooja_type="daily", is_paid=False, is_active=True))
    db.commit()

    second = client.get("/api/v1/poojas/").json()
    assert second == first  # still cached - the direct DB insert isn't visible yet

    content_cache.invalidate("poojas:")
    third = client.get("/api/v1/poojas/").json()
    assert len(third) == 2  # now recomputed against current DB state
