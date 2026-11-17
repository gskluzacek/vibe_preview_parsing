from cof.common.settings import PROJECT_ROOT, Settings
from cof.normalize.rules import load_rules


def test_rule_table_in_the_spec_matches_rules_yaml() -> None:
    text = (PROJECT_ROOT / "documentation" / "normalized_cof_spec.md").read_text(encoding="utf-8")
    rows = {}
    for line in text.splitlines():
        cells = [c.strip() for c in line.strip().strip("|").replace("\\|", "\x00").split("|")]
        if len(cells) == 6 and cells[0][:1] in "FLI" and cells[0][1:].isdigit():
            rows[cells[0]] = cells
    rules = load_rules(Settings())
    assert set(rows) == set(rules)
    for rid, rule in rules.items():
        _, _, rule_class, which, description, _ = rows[rid]
        assert rule_class == rule.rule_class, rid
        assert which == ("optional" if rule.optional else "required"), rid
        assert description.replace("\x00", "|") == rule.description, rid
