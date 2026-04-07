from argparse import Namespace

from app.main import resolve_cog_ids


def test_resolve_cog_ids_supports_all_cogs_flag():
    args = Namespace(all_cogs=True, cog_id=[], cog_ids=[], cog_ids_file=None)
    assert resolve_cog_ids(args) == []


def test_resolve_cog_ids_supports_wildcard_value():
    args = Namespace(all_cogs=False, cog_id=["*"], cog_ids=["200032"], cog_ids_file=None)
    assert resolve_cog_ids(args) == []
