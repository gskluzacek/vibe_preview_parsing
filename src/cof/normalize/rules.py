"""The rule registry: rule metadata from ``config/rules.yaml`` and the detector function of each rule."""

from collections.abc import Callable, Iterator
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from cof.common.settings import Settings, load_yaml
from cof.normalize.context import FileContext, Issue

RULE_CLASSES = ("auto-lossless", "auto-derived", "patch", "open", "info")

Detector = Callable[[FileContext], Iterator[Issue]]
_DETECTORS: dict[str, Detector] = {}


class Rule(BaseModel):
    """Metadata of one rule."""

    model_config = ConfigDict(populate_by_name=True)

    id: str
    name: str
    rule_class: str = Field(alias="class")
    severity: str
    description: str
    fix: str
    anomaly: str | None = None


def load_rules(settings: Settings | None = None) -> dict[str, Rule]:
    """Read ``config/rules.yaml``.

    Args:
        settings: Settings giving the configuration directory.

    Returns:
        Rules keyed by id, in file order.

    Raises:
        ValueError: If a rule id is repeated or a class is unknown.
    """
    data: Any = load_yaml("rules.yaml", settings)
    rules: dict[str, Rule] = {}
    for raw in data["rules"]:
        rule = Rule.model_validate(raw)
        if rule.id in rules:
            raise ValueError(f"duplicate rule id {rule.id}")
        if rule.rule_class not in RULE_CLASSES:
            raise ValueError(f"rule {rule.id}: unknown class {rule.rule_class!r}")
        rules[rule.id] = rule
    return rules


def detector(rule_id: str) -> Callable[[Detector], Detector]:
    """Register a function as the detector of a rule.

    Args:
        rule_id: The id of the rule in ``config/rules.yaml``.

    Returns:
        A decorator that records the function and returns it unchanged.
    """

    def register(func: Detector) -> Detector:
        if rule_id in _DETECTORS:
            raise ValueError(f"detector for {rule_id} registered twice")
        _DETECTORS[rule_id] = func
        return func

    return register


def detector_ids() -> set[str]:
    """Return the ids that have a registered detector."""
    return set(_DETECTORS)


def detect_all(ctx: FileContext) -> list[Issue]:
    """Run every registered detector on a file.

    A file that is not a COF text file at all (rule F01) is reported only for its file-level facts, because
    line-level findings on a foreign layout would be noise.

    Args:
        ctx: The decoded, classified file.

    Returns:
        All issues, ordered by line number then rule id (whole-file issues first).
    """
    issues: list[Issue] = []
    foreign = list(_DETECTORS["F01"](ctx))
    issues += foreign
    for rule_id, func in _DETECTORS.items():
        if rule_id == "F01" or (foreign and not rule_id.startswith("F")):
            continue
        issues += func(ctx)
    return sorted(issues, key=lambda i: (i.line or 0, i.rule_id))
