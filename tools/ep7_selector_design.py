"""Host-only proposed selector behavior. NOT native firmware/emulator/patch.

Stock IDs0..3 retain their order. Proposed IDs4/5 are new H/L views only;
there is no claim native firmware has these entries or verified H/L storage.
This model never reads/writes camera state, firmware, or saturation settings.
"""
from dataclasses import dataclass
from typing import Optional, Sequence

STOCK_CATEGORIES = (0, 1, 2, 3)
PROPOSED_HUE = 4
PROPOSED_LUMINANCE = 5
COLOR_MODES = frozenset((54, 55, 56, 64))


def enabled_categories(public_mode: int) -> tuple[bool, ...]:
    """Only the proposed entries are gated here; native category masks are unknown."""
    color = public_mode in COLOR_MODES
    return (True, True, True, True, color, color)


def normalize_index(remembered: Optional[int], enabled: Sequence[bool]) -> Optional[int]:
    """Fail closed on empty/all-disabled; otherwise preserve valid active focus."""
    if type(remembered) is int and 0 <= remembered < len(enabled) and enabled[remembered]:
        return remembered
    return next((index for index, active in enumerate(enabled) if active), None)


def navigate(remembered: Optional[int], enabled: Sequence[bool], direction: int) -> Optional[int]:
    """Bounded wraparound proposal, not a byte-accurate native CPU emulation."""
    if type(direction) is not int or direction not in (-1, 1):
        raise ValueError('direction must be -1 or 1')
    current = normalize_index(remembered, enabled)
    if current is None:
        return None
    for step in range(1, len(enabled) + 1):
        candidate = (current + step * direction) % len(enabled)
        if enabled[candidate]:
            return candidate
    return None


@dataclass(frozen=True)
class SelectorDesign:
    public_mode: int
    focus: Optional[int] = 0
    categories: tuple[int, ...] = (*STOCK_CATEGORIES, PROPOSED_HUE, PROPOSED_LUMINANCE)

    def change_mode(self, public_mode: int) -> 'SelectorDesign':
        # Explicitly normalize proposed H/L focus when leaving COLOR; no persistence.
        return SelectorDesign(public_mode, normalize_index(self.focus, enabled_categories(public_mode)))

    def step(self, direction: int) -> 'SelectorDesign':
        return SelectorDesign(self.public_mode, navigate(self.focus, enabled_categories(self.public_mode), direction))

    def selected_view(self) -> Optional[str]:
        focus = normalize_index(self.focus, enabled_categories(self.public_mode))
        if focus is None:
            return None
        return {4: 'proposed_hue', 5: 'proposed_luminance'}.get(focus, f'stock_category_{focus}')
