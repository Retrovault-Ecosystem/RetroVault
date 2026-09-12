from .hardware_state import (
    HardwareIndicatorPolicy,
    NESHardwareIndicatorPolicy,
)


class HardwareIndicatorPolicyResolver:
    """
    Resolve canonical RVDB platform identity to RVV hardware policy.

    Unknown, missing, or unsupported platforms deliberately receive the
    generic all-off policy. RetroVault must never invent hardware
    indicators for a platform without an explicit policy.
    """

    _POLICIES = {
        "platform.nintendo.nes": NESHardwareIndicatorPolicy,
    }

    def resolve(
        self,
        platform_id,
    ) -> HardwareIndicatorPolicy:
        if not isinstance(platform_id, str):
            return HardwareIndicatorPolicy()

        platform_id = platform_id.strip()

        if not platform_id:
            return HardwareIndicatorPolicy()

        policy_type = self._POLICIES.get(
            platform_id,
            HardwareIndicatorPolicy,
        )

        return policy_type()
