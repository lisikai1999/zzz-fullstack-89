"""
WCAG 2.1 Color Contrast Calculation
Implements relative luminance and contrast ratio per WCAG 2.1 §1.4.3 / §1.4.6.
Handles alpha blending for semi-transparent colors and gradient worst-case analysis.
"""
import re
import math
from typing import Tuple, Optional, List


def parse_color(color_str: str) -> Optional[Tuple[int, int, int, float]]:
    """Parse CSS color string to (R, G, B, A) tuple."""
    if not color_str:
        return None

    color_str = color_str.strip().lower()

    named_colors = {
        "white": (255, 255, 255, 1.0),
        "black": (0, 0, 0, 1.0),
        "red": (255, 0, 0, 1.0),
        "green": (0, 128, 0, 1.0),
        "blue": (0, 0, 255, 1.0),
        "gray": (128, 128, 128, 1.0),
        "grey": (128, 128, 128, 1.0),
        "transparent": (0, 0, 0, 0.0),
        "silver": (192, 192, 192, 1.0),
        "navy": (0, 0, 128, 1.0),
        "orange": (255, 165, 0, 1.0),
        "yellow": (255, 255, 0, 1.0),
        "purple": (128, 0, 128, 1.0),
    }

    if color_str in named_colors:
        return named_colors[color_str]

    hex_match = re.match(r"^#([0-9a-f]{3,8})$", color_str)
    if hex_match:
        h = hex_match.group(1)
        if len(h) == 3:
            r, g, b = int(h[0] * 2, 16), int(h[1] * 2, 16), int(h[2] * 2, 16)
            return (r, g, b, 1.0)
        elif len(h) == 4:
            r, g, b = int(h[0] * 2, 16), int(h[1] * 2, 16), int(h[2] * 2, 16)
            a = int(h[3] * 2, 16) / 255
            return (r, g, b, a)
        elif len(h) == 6:
            r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
            return (r, g, b, 1.0)
        elif len(h) == 8:
            r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
            a = int(h[6:8], 16) / 255
            return (r, g, b, a)

    rgba_match = re.match(
        r"rgba?\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*(?:,\s*([\d.]+))?\s*\)",
        color_str,
    )
    if rgba_match:
        r = int(rgba_match.group(1))
        g = int(rgba_match.group(2))
        b = int(rgba_match.group(3))
        a = float(rgba_match.group(4)) if rgba_match.group(4) else 1.0
        return (r, g, b, a)

    rgba_match2 = re.match(
        r"rgba?\(\s*(\d+)\s+(\d+)\s+(\d+)\s*(?:/\s*([\d.]+%?))?\s*\)",
        color_str,
    )
    if rgba_match2:
        r = int(rgba_match2.group(1))
        g = int(rgba_match2.group(2))
        b = int(rgba_match2.group(3))
        a_str = rgba_match2.group(4)
        if a_str:
            a = float(a_str.rstrip("%")) / 100 if "%" in a_str else float(a_str)
        else:
            a = 1.0
        return (r, g, b, a)

    return None


def alpha_blend(
    fg: Tuple[int, int, int, float], bg: Tuple[int, int, int, float]
) -> Tuple[int, int, int, float]:
    """Blend foreground color over background color using alpha compositing."""
    fg_r, fg_g, fg_b, fg_a = fg
    bg_r, bg_g, bg_b, bg_a = bg

    if fg_a >= 1.0:
        return (fg_r, fg_g, fg_b, 1.0)

    out_a = fg_a + bg_a * (1 - fg_a)
    if out_a == 0:
        return (0, 0, 0, 0.0)

    out_r = int((fg_r * fg_a + bg_r * bg_a * (1 - fg_a)) / out_a)
    out_g = int((fg_g * fg_a + bg_g * bg_a * (1 - fg_a)) / out_a)
    out_b = int((fg_b * fg_a + bg_b * bg_a * (1 - fg_a)) / out_a)

    return (
        max(0, min(255, out_r)),
        max(0, min(255, out_g)),
        max(0, min(255, out_b)),
        out_a,
    )


def relative_luminance(r: int, g: int, b: int) -> float:
    """Calculate relative luminance per WCAG 2.1 definition."""
    rs = r / 255.0
    gs = g / 255.0
    bs = b / 255.0

    r_lin = rs / 12.92 if rs <= 0.04045 else ((rs + 0.055) / 1.055) ** 2.4
    g_lin = gs / 12.92 if gs <= 0.04045 else ((gs + 0.055) / 1.055) ** 2.4
    b_lin = bs / 12.92 if bs <= 0.04045 else ((bs + 0.055) / 1.055) ** 2.4

    return 0.2126 * r_lin + 0.7152 * g_lin + 0.0722 * b_lin


def contrast_ratio(color1: Tuple[int, int, int], color2: Tuple[int, int, int]) -> float:
    """Calculate contrast ratio between two opaque colors."""
    l1 = relative_luminance(*color1)
    l2 = relative_luminance(*color2)
    lighter = max(l1, l2)
    darker = min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)


def contrast_with_alpha(
    fg_color: str, bg_color: str, parent_bg: str = "#ffffff"
) -> float:
    """Calculate contrast ratio accounting for alpha transparency."""
    fg = parse_color(fg_color)
    bg = parse_color(bg_color)
    parent = parse_color(parent_bg)

    if not fg or not bg:
        return 0.0
    if not parent:
        parent = (255, 255, 255, 1.0)

    # Blend background onto parent first
    effective_bg = alpha_blend(bg, parent)
    # Then blend foreground onto effective background
    effective_fg = alpha_blend(fg, effective_bg)

    return contrast_ratio(
        (effective_fg[0], effective_fg[1], effective_fg[2]),
        (effective_bg[0], effective_bg[1], effective_bg[2]),
    )


def gradient_worst_contrast(
    text_color: str, gradient_colors: List[str], parent_bg: str = "#ffffff"
) -> Tuple[float, str]:
    """
    Find the worst (lowest) contrast ratio between text and gradient background.
    Samples the gradient at multiple points and returns the minimum contrast.
    """
    fg = parse_color(text_color)
    if not fg:
        return (0.0, "")

    parent = parse_color(parent_bg) or (255, 255, 255, 1.0)
    parsed_stops = [parse_color(c) for c in gradient_colors]
    parsed_stops = [c for c in parsed_stops if c is not None]

    if len(parsed_stops) < 2:
        if parsed_stops:
            ratio = contrast_with_alpha(text_color, gradient_colors[0], parent_bg)
            return (ratio, gradient_colors[0])
        return (0.0, "")

    worst_ratio = float("inf")
    worst_color = ""

    # Sample 20 points along the gradient
    num_samples = 20
    for i in range(num_samples + 1):
        t = i / num_samples
        segment_pos = t * (len(parsed_stops) - 1)
        idx = int(segment_pos)
        local_t = segment_pos - idx

        if idx >= len(parsed_stops) - 1:
            idx = len(parsed_stops) - 2
            local_t = 1.0

        c1 = parsed_stops[idx]
        c2 = parsed_stops[idx + 1]

        # Linear interpolation
        r = int(c1[0] + (c2[0] - c1[0]) * local_t)
        g = int(c1[1] + (c2[1] - c1[1]) * local_t)
        b = int(c1[2] + (c2[2] - c1[2]) * local_t)
        a = c1[3] + (c2[3] - c1[3]) * local_t

        sample_bg = (r, g, b, a)
        effective_bg = alpha_blend(sample_bg, parent)
        effective_fg = alpha_blend(fg, effective_bg)

        ratio = contrast_ratio(
            (effective_fg[0], effective_fg[1], effective_fg[2]),
            (effective_bg[0], effective_bg[1], effective_bg[2]),
        )

        if ratio < worst_ratio:
            worst_ratio = ratio
            worst_color = f"rgb({r}, {g}, {b})"

    return (worst_ratio, worst_color)


def suggest_color_for_contrast(
    bg_color: str, target_ratio: float = 4.5, prefer_dark: bool = True
) -> str:
    """
    Suggest a foreground color that meets the target contrast ratio against the given background.
    Uses binary search to find the closest color with sufficient contrast.
    """
    bg = parse_color(bg_color)
    if not bg:
        return "#000000" if prefer_dark else "#ffffff"

    bg_rgb = (bg[0], bg[1], bg[2])
    bg_lum = relative_luminance(*bg_rgb)

    if prefer_dark:
        # Search from dark to light
        low, high = 0, 255
        while low < high:
            mid = (low + high) // 2
            candidate = (mid, mid, mid)
            ratio = contrast_ratio(bg_rgb, candidate)
            if ratio >= target_ratio:
                low = mid + 1
            else:
                high = mid
        # Verify and use the result
        val = max(0, low - 1)
        candidate = (val, val, val)
        if contrast_ratio(bg_rgb, candidate) >= target_ratio:
            return f"#{val:02x}{val:02x}{val:02x}"
        # Fall back to black
        return "#000000"
    else:
        # Search from light to dark
        low, high = 0, 255
        while low < high:
            mid = (low + high) // 2
            candidate = (255 - mid, 255 - mid, 255 - mid)
            ratio = contrast_ratio(bg_rgb, candidate)
            if ratio >= target_ratio:
                high = mid
            else:
                low = mid + 1
        val = 255 - low
        candidate = (val, val, val)
        if contrast_ratio(bg_rgb, candidate) >= target_ratio:
            return f"#{val:02x}{val:02x}{val:02x}"
        return "#ffffff"


def meets_contrast_requirement(
    ratio: float, is_large_text: bool = False, level: str = "AA"
) -> bool:
    """Check if contrast ratio meets WCAG requirement."""
    if level == "AAA":
        return ratio >= (4.5 if is_large_text else 7.0)
    # AA
    return ratio >= (3.0 if is_large_text else 4.5)
