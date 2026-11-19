import pytest

from engine.config import Config, load_config


def test_default_basket_is_880_dollars():
    cfg = Config()
    assert sum(n.initial_price for n in cfg.needs) == 88_000


def test_four_base_needs_in_payment_order():
    cfg = Config()
    names = [n.name for n in sorted(cfg.needs, key=lambda n: n.priority)]
    assert names == ["food", "housing", "appliances", "entertainment"]
    assert cfg.need("food").essential and cfg.need("housing").essential
    assert not cfg.need("appliances").essential


def test_override_dotted_need_key():
    cfg = load_config(None, ["needs.housing.initial_price=40000", "population_cap=150"])
    assert cfg.need("housing").initial_price == 40000
    assert cfg.population_cap == 150


def test_unknown_dial_raises():
    with pytest.raises(KeyError, match="populaton_cap"):
        load_config(None, ["populaton_cap=10"])
    with pytest.raises(KeyError, match="rent"):
        load_config(None, ["needs.housing.rent=10"])


def test_round_trip():
    cfg = load_config(None, ["seed=7", "needs.food.initial_price=41000"])
    assert Config.from_dict(cfg.to_dict()) == cfg


def test_settings_file_then_overrides(tmp_path):
    p = tmp_path / "s.json"
    p.write_text('{"seed": 9, "needs": {"food": {"initial_price": 39000}}}')
    cfg = load_config(str(p), ["seed=11"])
    assert cfg.seed == 11
    assert cfg.need("food").initial_price == 39000


def test_unknown_price_rule_raises():
    with pytest.raises(ValueError, match="price_rule"):
        load_config(None, ["price_rule=serach"])
    assert load_config(None, ["price_rule=search"]).price_rule == "search"


def test_impossible_values_are_refused():
    for bad in ("snapshot_every=0", "register_every=0", "years=0", "population_cap=2",
                "quarter_weeks=0", "weeks_per_year=0"):
        with pytest.raises(ValueError, match=bad.split("=")[0]):
            load_config(None, [bad])


def test_a_run_can_be_rerun_from_its_own_settings_file(tmp_path):
    import json
    cfg = load_config(None, ["seed=7", "needs.food.initial_price=41000", "price_rule=search"])
    path = tmp_path / "config.json"
    path.write_text(json.dumps(cfg.to_dict()))          # exactly what a run folder holds
    assert load_config(str(path)) == cfg
    assert load_config(str(path), ["seed=8"]).seed == 8


def test_bad_value_inside_a_settings_file_is_refused(tmp_path):
    path = tmp_path / "s.json"
    path.write_text('{"price_rule": "upward"}')
    with pytest.raises(ValueError, match="price_rule"):
        load_config(str(path))
