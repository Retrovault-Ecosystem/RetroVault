from dataclasses import dataclass

from .hardware_state import (
    HardwareIndicatorSnapshot,
    IndicatorState,
)


@dataclass(frozen=True)
class IndicatorRenderInstruction:
    """
    One presentation-facing hardware-indicator instruction.

    This object describes what RVV should render. It deliberately does
    not know about Qt, RetroArch, PNG files, overlay descriptors, or
    platform-specific hardware policy.
    """

    indicator: str
    state: IndicatorState

    def __post_init__(self) -> None:
        if not isinstance(self.indicator, str):
            raise TypeError(
                "Indicator name must be a string."
            )

        if not self.indicator.strip():
            raise ValueError(
                "Indicator name cannot be empty."
            )

        if not isinstance(self.state, IndicatorState):
            raise TypeError(
                "Indicator render state must be an IndicatorState."
            )


@dataclass(frozen=True)
class IndicatorRenderFrame:
    """
    Immutable render frame derived from one hardware snapshot.

    A later renderer may translate these instructions into small
    artwork layers or another presentation backend without changing
    lifecycle or platform-policy code.
    """

    instructions: tuple[IndicatorRenderInstruction, ...]

    def instruction_for(
        self,
        indicator: str,
    ) -> IndicatorRenderInstruction:
        if not isinstance(indicator, str):
            raise TypeError(
                "Indicator name must be a string."
            )

        normalized = indicator.strip().casefold()

        if not normalized:
            raise ValueError(
                "Indicator name cannot be empty."
            )

        for instruction in self.instructions:
            if (
                instruction.indicator.casefold()
                == normalized
            ):
                return instruction

        raise KeyError(
            f"Unknown indicator: {indicator}"
        )


class HardwareIndicatorRenderBridge:
    """
    Translate hardware-state snapshots into render instructions.

    The bridge is presentation-owned and intentionally pure:

      - no Qt
      - no RetroArch
      - no filesystem writes
      - no image manipulation
      - no platform-policy selection
      - no lifecycle transitions

    It consumes only the immutable result of those earlier layers.
    """

    _INDICATORS = (
        "power",
        "reset",
    )

    def frame_for(
        self,
        snapshot: HardwareIndicatorSnapshot,
    ) -> IndicatorRenderFrame:
        if not isinstance(
            snapshot,
            HardwareIndicatorSnapshot,
        ):
            raise TypeError(
                "Snapshot must be a "
                "HardwareIndicatorSnapshot."
            )

        instructions = tuple(
            IndicatorRenderInstruction(
                indicator=name,
                state=getattr(snapshot, name),
            )
            for name in self._INDICATORS
        )

        return IndicatorRenderFrame(
            instructions=instructions
        )
