from services.presentation.hardware_policy import (
    HardwareIndicatorPolicyResolver,
)
from services.presentation.hardware_state import (
    HardwareIndicatorPolicy,
    NESHardwareIndicatorPolicy,
)


def test_nes_resolves_to_nes_policy():
    policy = HardwareIndicatorPolicyResolver().resolve(
        "platform.nintendo.nes"
    )

    assert isinstance(
        policy,
        NESHardwareIndicatorPolicy,
    )


def test_snes_currently_falls_back_to_generic_policy():
    policy = HardwareIndicatorPolicyResolver().resolve(
        "platform.nintendo.snes"
    )

    assert type(policy) is HardwareIndicatorPolicy


def test_unknown_platform_falls_back_to_generic_policy():
    policy = HardwareIndicatorPolicyResolver().resolve(
        "platform.unknown.future"
    )

    assert type(policy) is HardwareIndicatorPolicy


def test_empty_platform_falls_back_to_generic_policy():
    policy = HardwareIndicatorPolicyResolver().resolve("")

    assert type(policy) is HardwareIndicatorPolicy


def test_whitespace_platform_falls_back_to_generic_policy():
    policy = HardwareIndicatorPolicyResolver().resolve("   ")

    assert type(policy) is HardwareIndicatorPolicy


def test_missing_platform_falls_back_to_generic_policy():
    policy = HardwareIndicatorPolicyResolver().resolve(None)

    assert type(policy) is HardwareIndicatorPolicy


def test_resolver_returns_fresh_policy_instances():
    resolver = HardwareIndicatorPolicyResolver()

    first = resolver.resolve(
        "platform.nintendo.nes"
    )
    second = resolver.resolve(
        "platform.nintendo.nes"
    )

    assert first is not second
