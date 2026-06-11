"""
Page fetching and style extraction service.
Fetches HTML content and computes relevant styles for accessibility checking.
"""
import httpx
import re
from typing import Dict, Tuple
from bs4 import BeautifulSoup, Tag


async def fetch_page(url: str) -> Tuple[str, str]:
    """Fetch page HTML content. Returns (html, title)."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 WCAG-Checker/1.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5,zh-CN;q=0.3",
    }
    async with httpx.AsyncClient(follow_redirects=True, timeout=30.0, verify=False) as client:
        response = await client.get(url, headers=headers)
        response.raise_for_status()
        html = response.text

    soup = BeautifulSoup(html, "lxml")
    title_tag = soup.find("title")
    title = title_tag.get_text(strip=True) if title_tag else ""

    return html, title


def extract_inline_styles(html: str) -> Dict[str, dict]:
    """
    Extract computed style information from HTML.
    Parses inline styles and stylesheet rules to determine colors and font sizes.
    """
    soup = BeautifulSoup(html, "lxml")
    styles = {}

    # Parse embedded stylesheets
    stylesheet_rules = _parse_stylesheets(soup)

    # Check all text-containing elements
    text_elements = soup.find_all(
        ["p", "span", "a", "h1", "h2", "h3", "h4", "h5", "h6",
         "li", "td", "th", "label", "div", "strong", "em", "b", "i",
         "blockquote", "cite", "code", "pre", "small", "button"]
    )

    for elem in text_elements:
        if not elem.get_text(strip=True):
            continue

        style_info = _resolve_element_style(elem, stylesheet_rules)
        if style_info.get("color") or style_info.get("background-color"):
            selector = _build_selector(elem)
            style_info["element_html"] = str(elem)[:200]
            style_info["element_tag"] = elem.name
            style_info["page_region"] = _get_region(elem)
            styles[selector] = style_info

    return styles


def _parse_stylesheets(soup: BeautifulSoup) -> Dict[str, dict]:
    """Parse <style> tags to extract CSS rules."""
    rules = {}
    style_tags = soup.find_all("style")
    for style_tag in style_tags:
        css_text = style_tag.get_text()
        # Simple CSS rule parser
        rule_pattern = re.compile(r"([^{]+)\{([^}]+)\}")
        for match in rule_pattern.finditer(css_text):
            selector = match.group(1).strip()
            properties = match.group(2).strip()
            prop_dict = {}
            for prop in properties.split(";"):
                prop = prop.strip()
                if ":" in prop:
                    key, value = prop.split(":", 1)
                    prop_dict[key.strip().lower()] = value.strip()
            if selector not in rules:
                rules[selector] = {}
            rules[selector].update(prop_dict)
    return rules


def _resolve_element_style(elem: Tag, stylesheet_rules: Dict[str, dict]) -> dict:
    """Resolve the effective style for an element by checking inline + stylesheet rules."""
    style_info = {}

    # Check stylesheet rules (simple class and tag matching)
    for selector, props in stylesheet_rules.items():
        if _selector_matches(elem, selector):
            style_info.update(props)

    # Inline styles override
    inline_style = elem.get("style", "")
    if inline_style:
        for prop in inline_style.split(";"):
            prop = prop.strip()
            if ":" in prop:
                key, value = prop.split(":", 1)
                style_info[key.strip().lower()] = value.strip()

    # Resolve background color from ancestors if not found
    if "background-color" not in style_info:
        parent_bg = _find_ancestor_background(elem)
        if parent_bg:
            style_info["parent_bg"] = parent_bg
            style_info["background-color"] = parent_bg
        else:
            style_info["background-color"] = "#ffffff"
            style_info["parent_bg"] = "#ffffff"

    return style_info


def _selector_matches(elem: Tag, selector: str) -> bool:
    """Simple CSS selector matching."""
    selector = selector.strip()
    parts = [s.strip() for s in selector.split(",")]
    for part in parts:
        part = part.strip()
        if part.startswith("."):
            class_name = part[1:]
            elem_classes = elem.get("class", [])
            if class_name in elem_classes:
                return True
        elif part.startswith("#"):
            elem_id = elem.get("id", "")
            if part[1:] == elem_id:
                return True
        elif part == elem.name:
            return True
    return False


def _find_ancestor_background(elem: Tag) -> str:
    """Walk up the DOM tree to find the nearest ancestor with a background color."""
    current = elem.parent
    while current and current.name and current.name != "[document]":
        inline_style = current.get("style", "")
        if "background" in inline_style:
            for prop in inline_style.split(";"):
                prop = prop.strip()
                if prop.startswith("background-color") or prop.startswith("background"):
                    if ":" in prop:
                        _, value = prop.split(":", 1)
                        value = value.strip()
                        if not value.startswith("url") and not value.startswith("none"):
                            color_match = re.match(
                                r"(#[0-9a-fA-F]{3,8}|rgba?\([^)]+\)|[a-z]+)", value
                            )
                            if color_match:
                                return color_match.group(1)
        current = current.parent
    return ""


def _build_selector(elem: Tag) -> str:
    """Build a unique selector for an element."""
    if elem.get("id"):
        return f"#{elem['id']}"
    parts = [elem.name]
    if elem.get("class"):
        classes = elem["class"] if isinstance(elem["class"], list) else [elem["class"]]
        parts.append("." + ".".join(classes[:2]))
    parent = elem.parent
    if parent and parent.name and parent.name != "[document]":
        siblings = parent.find_all(elem.name, recursive=False)
        if len(siblings) > 1:
            idx = list(siblings).index(elem) + 1
            parts.append(f":nth-of-type({idx})")
    return "".join(parts)


def _get_region(elem: Tag) -> str:
    """Determine page region."""
    current = elem
    while current and current.name and current.name != "[document]":
        tag = current.name
        role = current.get("role", "")
        if tag == "header" or role == "banner":
            return "header"
        elif tag == "nav" or role == "navigation":
            return "nav"
        elif tag == "main" or role == "main":
            return "main"
        elif tag == "footer" or role == "contentinfo":
            return "footer"
        elif tag == "aside" or role == "complementary":
            return "aside"
        elif tag == "form" or role == "form":
            return "form"
        current = current.parent
    return "body"
