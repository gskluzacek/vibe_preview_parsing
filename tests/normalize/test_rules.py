from cof.common.settings import Settings
from cof.normalize.rules import detector_ids, load_rules


def test_every_rule_has_a_detector_and_the_reverse() -> None:
    rules = load_rules(Settings())
    assert set(rules) == detector_ids()


def test_rules_reference_known_anomalies_once() -> None:
    rules = load_rules(Settings())
    assert all(r.severity in {"error", "warning", "info"} for r in rules.values())
    assert rules["I02"].anomaly == "A1" and rules["I02"].rule_class == "auto-derived"
