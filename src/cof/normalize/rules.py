"""The rule registry: rule metadata from ``config/rules.yaml`` and the detector function of each rule."""

from collections.abc import Callable, Iterator
from functools import cache
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
    optional: bool = False  # runs only with --full-checks
    params: dict[str, Any] = Field(default_factory=dict)  # tunable numbers for the detector


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


@cache
def _default_rules() -> dict[str, Rule]:
    """Read the rules once with the default settings (for :func:`rule_param`)."""
    return load_rules()


def rule_param(rule_id: str, name: str) -> int | float | str:
    """Return a tunable number of a rule from ``config/rules.yaml``.

    Args:
        rule_id: The rule id, for example ``"L03"``.
        name: The key under the rule's ``params``.

    Returns:
        The configured value.
    """
    value: int | float | str = _default_rules()[rule_id].params[name]
    return value


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


def detect_all(ctx: FileContext, include_optional: bool = True) -> list[Issue]:
    """Run every registered detector on a file.

    A file that is not a COF text file at all (rule F01) is reported only for its file-level facts, because
    line-level findings on a foreign layout would be noise.

    Args:
        ctx: The decoded, classified file.
        include_optional: Also run the rules marked ``optional`` in ``config/rules.yaml``. Selection and
            analysis always use all rules; the normalizer skips the optional ones unless asked.

    Returns:
        All issues, ordered by line number then rule id (whole-file issues first).
    """
    optional = set() if include_optional else {r.id for r in _default_rules().values() if r.optional}
    issues: list[Issue] = []
    foreign = list(_DETECTORS["F01"](ctx))
    issues += foreign
    for rule_id, func in _DETECTORS.items():
        if rule_id == "F01" or rule_id in optional or (foreign and not rule_id.startswith("F")):
            continue
        issues += func(ctx)
    return sorted(issues, key=lambda i: (i.line or 0, i.rule_id))
