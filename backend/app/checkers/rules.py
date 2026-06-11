"""
WCAG Accessibility Rules Engine
Checks DOM elements against WCAG 2.1 Level A and AA criteria.
"""
from dataclasses import dataclass, field
from typing import List, Optional
from bs4 import BeautifulSoup, Tag
from app.checkers.contrast import (
    contrast_with_alpha,
    suggest_color_for_contrast,
    meets_contrast_requirement,
    parse_color,
    gradient_worst_contrast,
)
import re


@dataclass
class Issue:
    rule_id: str
    rule_name: str
    severity: str  # critical, serious, moderate, minor
    wcag_level: str  # A, AA
    wcag_criterion: str
    element_selector: str
    element_html: str
    element_tag: str
    page_region: str
    description: str
    impact_group: str
    fix_suggestion: str
    fix_code: str = ""
    contrast_actual: Optional[float] = None
    contrast_required: Optional[float] = None
    suggested_color: Optional[str] = None


NON_DESCRIPTIVE_LINK_TEXTS = {
    "click here", "here", "read more", "more", "learn more",
    "click", "link", "this", "go", "details", "info",
    "点击这里", "查看更多", "更多", "详情", "了解更多", "这里",
}

VALID_ARIA_ROLES = {
    "alert", "alertdialog", "application", "article", "banner",
    "button", "cell", "checkbox", "columnheader", "combobox",
    "complementary", "contentinfo", "definition", "dialog",
    "directory", "document", "feed", "figure", "form", "grid",
    "gridcell", "group", "heading", "img", "link", "list",
    "listbox", "listitem", "log", "main", "marquee", "math",
    "menu", "menubar", "menuitem", "menuitemcheckbox",
    "menuitemradio", "navigation", "none", "note", "option",
    "presentation", "progressbar", "radio", "radiogroup",
    "region", "row", "rowgroup", "rowheader", "scrollbar",
    "search", "searchbox", "separator", "slider", "spinbutton",
    "status", "switch", "tab", "table", "tablist", "tabpanel",
    "term", "textbox", "timer", "toolbar", "tooltip", "tree",
    "treegrid", "treeitem",
}

ARIA_REQUIRED_PROPERTIES = {
    "checkbox": ["aria-checked"],
    "combobox": ["aria-expanded"],
    "heading": ["aria-level"],
    "meter": ["aria-valuenow"],
    "option": ["aria-selected"],
    "radio": ["aria-checked"],
    "scrollbar": ["aria-controls", "aria-valuenow"],
    "slider": ["aria-valuenow"],
    "spinbutton": ["aria-valuenow"],
    "switch": ["aria-checked"],
}


def get_element_selector(element: Tag) -> str:
    """Generate a CSS selector for an element."""
    parts = []
    tag = element.name
    if element.get("id"):
        return f"#{element['id']}"

    selector = tag
    if element.get("class"):
        classes = element["class"] if isinstance(element["class"], list) else [element["class"]]
        selector += "." + ".".join(classes[:2])

    parent = element.parent
    if parent and parent.name != "[document]":
        siblings = parent.find_all(tag, recursive=False)
        if len(siblings) > 1:
            idx = siblings.index(element) + 1
            selector += f":nth-of-type({idx})"

    return selector


def get_page_region(element: Tag) -> str:
    """Determine which page region an element belongs to."""
    current = element
    while current and current.name != "[document]":
        tag = current.name if current.name else ""
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


def get_element_html_snippet(element: Tag, max_len: int = 200) -> str:
    """Get a truncated HTML representation of an element."""
    html = str(element)
    if len(html) > max_len:
        html = html[:max_len] + "..."
    return html


class AccessibilityChecker:
    def __init__(self, html: str, url: str = "", styles: dict = None):
        self.soup = BeautifulSoup(html, "lxml")
        self.url = url
        self.styles = styles or {}
        self.issues: List[Issue] = []

    def run_all_checks(self) -> List[Issue]:
        self.check_images_alt()
        self.check_form_labels()
        self.check_link_text()
        self.check_heading_hierarchy()
        self.check_color_contrast()
        self.check_keyboard_access()
        self.check_aria_usage()
        self.check_document_language()
        self.check_page_title()
        return self.issues

    def check_images_alt(self):
        """WCAG 1.1.1 - Non-text Content (Level A)"""
        images = self.soup.find_all("img")
        for img in images:
            alt = img.get("alt")
            role = img.get("role", "")

            if role == "presentation" or role == "none":
                continue

            if alt is None:
                self.issues.append(Issue(
                    rule_id="img-alt-missing",
                    rule_name="Image missing alt attribute",
                    severity="critical",
                    wcag_level="A",
                    wcag_criterion="1.1.1",
                    element_selector=get_element_selector(img),
                    element_html=get_element_html_snippet(img),
                    element_tag="img",
                    page_region=get_page_region(img),
                    description="Image element is missing the alt attribute. Screen readers cannot describe this image to users.",
                    impact_group="blind",
                    fix_suggestion="Add a descriptive alt attribute. If the image is decorative, use alt=\"\" or role=\"presentation\".",
                    fix_code=f'<img src="{img.get("src", "")}" alt="Descriptive text about the image">',
                ))
            elif alt.strip() == "" and not (role == "presentation" or role == "none"):
                src = img.get("src", "")
                if not self._is_likely_decorative(img):
                    self.issues.append(Issue(
                        rule_id="img-alt-empty",
                        rule_name="Image has empty alt text but may not be decorative",
                        severity="moderate",
                        wcag_level="A",
                        wcag_criterion="1.1.1",
                        element_selector=get_element_selector(img),
                        element_html=get_element_html_snippet(img),
                        element_tag="img",
                        page_region=get_page_region(img),
                        description="Image has empty alt text. If this is a meaningful image, it needs descriptive alt text.",
                        impact_group="blind",
                        fix_suggestion="If the image conveys information, add descriptive alt text. If decorative, add role=\"presentation\".",
                        fix_code=f'<img src="{src}" alt="Description" /> or <img src="{src}" alt="" role="presentation" />',
                    ))

    def _is_likely_decorative(self, img: Tag) -> bool:
        """Heuristic to determine if an image is likely decorative."""
        src = img.get("src", "").lower()
        classes = " ".join(img.get("class", [])).lower()
        decorative_hints = ["icon", "spacer", "border", "decoration", "bg", "bullet", "separator"]
        return any(hint in src or hint in classes for hint in decorative_hints)

    def check_form_labels(self):
        """WCAG 1.3.1 / 4.1.2 - Form inputs must have labels (Level A)"""
        inputs = self.soup.find_all(["input", "select", "textarea"])
        for inp in inputs:
            input_type = inp.get("type", "text").lower()
            if input_type in ("hidden", "submit", "button", "reset", "image"):
                continue

            has_label = False
            input_id = inp.get("id")
            if input_id:
                label = self.soup.find("label", attrs={"for": input_id})
                if label:
                    has_label = True

            if not has_label:
                parent_label = inp.find_parent("label")
                if parent_label:
                    has_label = True

            if not has_label:
                if inp.get("aria-label") or inp.get("aria-labelledby") or inp.get("title"):
                    has_label = True

            if not has_label:
                self.issues.append(Issue(
                    rule_id="form-label-missing",
                    rule_name="Form input missing label",
                    severity="critical",
                    wcag_level="A",
                    wcag_criterion="4.1.2",
                    element_selector=get_element_selector(inp),
                    element_html=get_element_html_snippet(inp),
                    element_tag=inp.name,
                    page_region=get_page_region(inp),
                    description=f"Form {inp.name} element (type={input_type}) has no associated label. Screen reader users won't know what this field is for.",
                    impact_group="blind",
                    fix_suggestion="Add a <label> element with a 'for' attribute matching the input's id, or wrap the input in a <label>, or add aria-label.",
                    fix_code=f'<label for="field-id">Field Name</label>\n<input type="{input_type}" id="field-id">',
                ))

    def check_link_text(self):
        """WCAG 2.4.4 - Link Purpose (Level A)"""
        links = self.soup.find_all("a")
        for link in links:
            text = link.get_text(strip=True)
            aria_label = link.get("aria-label", "").strip()
            title = link.get("title", "").strip()

            effective_text = aria_label or text or title

            if not effective_text:
                img = link.find("img")
                if img and img.get("alt"):
                    continue
                self.issues.append(Issue(
                    rule_id="link-text-empty",
                    rule_name="Link has no accessible text",
                    severity="critical",
                    wcag_level="A",
                    wcag_criterion="2.4.4",
                    element_selector=get_element_selector(link),
                    element_html=get_element_html_snippet(link),
                    element_tag="a",
                    page_region=get_page_region(link),
                    description="Link has no text content. Screen reader users cannot determine the link's purpose.",
                    impact_group="blind",
                    fix_suggestion="Add descriptive text inside the link, or use aria-label to describe its purpose.",
                    fix_code=f'<a href="{link.get("href", "#")}" aria-label="Descriptive purpose">...</a>',
                ))
            elif effective_text.lower() in NON_DESCRIPTIVE_LINK_TEXTS:
                self.issues.append(Issue(
                    rule_id="link-text-generic",
                    rule_name="Link has non-descriptive text",
                    severity="serious",
                    wcag_level="A",
                    wcag_criterion="2.4.4",
                    element_selector=get_element_selector(link),
                    element_html=get_element_html_snippet(link),
                    element_tag="a",
                    page_region=get_page_region(link),
                    description=f'Link text "{effective_text}" is not descriptive. Users navigating by links list cannot determine its purpose.',
                    impact_group="blind",
                    fix_suggestion=f'Replace "{effective_text}" with text describing where the link goes or what it does, e.g., "View pricing details" or "Read the documentation".',
                    fix_code=f'<a href="{link.get("href", "#")}">Descriptive action or destination</a>',
                ))

    def check_heading_hierarchy(self):
        """WCAG 1.3.1 - Heading levels should not skip (Level A)"""
        headings = self.soup.find_all(re.compile(r"^h[1-6]$"))
        if not headings:
            return

        prev_level = 0
        for heading in headings:
            level = int(heading.name[1])
            if prev_level > 0 and level > prev_level + 1:
                self.issues.append(Issue(
                    rule_id="heading-skip",
                    rule_name="Heading level skipped",
                    severity="moderate",
                    wcag_level="A",
                    wcag_criterion="1.3.1",
                    element_selector=get_element_selector(heading),
                    element_html=get_element_html_snippet(heading),
                    element_tag=heading.name,
                    page_region=get_page_region(heading),
                    description=f"Heading jumps from <h{prev_level}> to <h{level}>, skipping level(s). This confuses screen reader users navigating by headings.",
                    impact_group="blind",
                    fix_suggestion=f"Change this heading to <h{prev_level + 1}> to maintain proper hierarchy, or add the missing intermediate heading levels.",
                    fix_code=f"<h{prev_level + 1}>{heading.get_text(strip=True)}</h{prev_level + 1}>",
                ))
            prev_level = level

    def check_color_contrast(self):
        """WCAG 1.4.3 - Contrast Minimum (Level AA)"""
        if not self.styles:
            return

        for selector, style_info in self.styles.items():
            color = style_info.get("color", "")
            bg_color = style_info.get("background-color", style_info.get("backgroundColor", ""))
            font_size = style_info.get("font-size", style_info.get("fontSize", "16px"))
            font_weight = style_info.get("font-weight", style_info.get("fontWeight", "400"))
            element_html = style_info.get("element_html", "")
            element_tag = style_info.get("element_tag", "")
            page_region = style_info.get("page_region", "body")
            parent_bg = style_info.get("parent_bg", "#ffffff")

            if not color or not bg_color:
                continue

            # Check for gradient backgrounds
            gradient_match = re.search(
                r"(?:linear|radial)-gradient\(([^)]+)\)", bg_color
            )
            if gradient_match:
                gradient_colors = re.findall(
                    r"(#[0-9a-fA-F]{3,8}|rgba?\([^)]+\)|[a-z]+)",
                    gradient_match.group(1),
                )
                gradient_colors = [c for c in gradient_colors if parse_color(c)]
                if gradient_colors:
                    ratio, worst_bg = gradient_worst_contrast(
                        color, gradient_colors, parent_bg
                    )
                    bg_color = worst_bg
                else:
                    continue
            else:
                ratio = contrast_with_alpha(color, bg_color, parent_bg)

            is_large = self._is_large_text(font_size, font_weight)
            required_ratio = 3.0 if is_large else 4.5

            if ratio < required_ratio and ratio > 0:
                suggested = suggest_color_for_contrast(bg_color, required_ratio)
                self.issues.append(Issue(
                    rule_id="contrast-insufficient",
                    rule_name="Insufficient color contrast",
                    severity="serious" if ratio < 3.0 else "moderate",
                    wcag_level="AA",
                    wcag_criterion="1.4.3",
                    element_selector=selector,
                    element_html=element_html,
                    element_tag=element_tag,
                    page_region=page_region,
                    description=f"Text color {color} on background {bg_color} has contrast ratio {ratio:.2f}:1, below the required {required_ratio}:1 for {'large' if is_large else 'normal'} text.",
                    impact_group="low_vision,color_blind",
                    fix_suggestion=f"Change the text color to {suggested} (or darker) to achieve at least {required_ratio}:1 contrast ratio. Alternatively, darken the background or increase font size to 18px+ / 14px+ bold.",
                    fix_code=f"color: {suggested}; /* contrast ratio: {required_ratio}:1+ */",
                    contrast_actual=round(ratio, 2),
                    contrast_required=required_ratio,
                    suggested_color=suggested,
                ))

    def _is_large_text(self, font_size: str, font_weight: str) -> bool:
        """Determine if text qualifies as 'large text' per WCAG."""
        size_px = 16.0
        if font_size:
            match = re.match(r"([\d.]+)(px|pt|em|rem)?", str(font_size))
            if match:
                val = float(match.group(1))
                unit = match.group(2) or "px"
                if unit == "pt":
                    size_px = val * 1.333
                elif unit in ("em", "rem"):
                    size_px = val * 16
                else:
                    size_px = val

        is_bold = False
        if font_weight:
            fw = str(font_weight).lower()
            if fw in ("bold", "bolder") or (fw.isdigit() and int(fw) >= 700):
                is_bold = True

        # Large text: 18pt (24px) or 14pt (18.67px) bold
        if size_px >= 24:
            return True
        if size_px >= 18.67 and is_bold:
            return True
        return False

    def check_keyboard_access(self):
        """WCAG 2.1.1 - Keyboard (Level A)"""
        # Check for click handlers without keyboard equivalents
        clickable = self.soup.find_all(attrs={"onclick": True})
        for elem in clickable:
            tag = elem.name
            if tag in ("a", "button", "input", "select", "textarea"):
                continue

            has_keyboard = (
                elem.get("onkeydown")
                or elem.get("onkeyup")
                or elem.get("onkeypress")
                or elem.get("tabindex") is not None
                or elem.get("role") in ("button", "link", "menuitem", "tab")
            )

            if not has_keyboard:
                self.issues.append(Issue(
                    rule_id="keyboard-no-access",
                    rule_name="Element not keyboard accessible",
                    severity="critical",
                    wcag_level="A",
                    wcag_criterion="2.1.1",
                    element_selector=get_element_selector(elem),
                    element_html=get_element_html_snippet(elem),
                    element_tag=tag,
                    page_region=get_page_region(elem),
                    description=f"<{tag}> element has onclick handler but no keyboard event handler or focusability. Keyboard-only users cannot activate it.",
                    impact_group="motor",
                    fix_suggestion="Add tabindex=\"0\" and an onkeydown handler (for Enter/Space), or use a <button> element instead.",
                    fix_code=f'<button onclick="..." type="button">{elem.get_text(strip=True)[:50]}</button>',
                ))

        # Check for positive tabindex (anti-pattern)
        pos_tabindex = self.soup.find_all(attrs={"tabindex": True})
        for elem in pos_tabindex:
            try:
                tabval = int(elem.get("tabindex", 0))
                if tabval > 0:
                    self.issues.append(Issue(
                        rule_id="keyboard-tabindex-positive",
                        rule_name="Positive tabindex disrupts navigation order",
                        severity="moderate",
                        wcag_level="A",
                        wcag_criterion="2.4.3",
                        element_selector=get_element_selector(elem),
                        element_html=get_element_html_snippet(elem),
                        element_tag=elem.name,
                        page_region=get_page_region(elem),
                        description=f"Element has tabindex={tabval}. Positive tabindex values disrupt the natural tab order and confuse keyboard users.",
                        impact_group="motor",
                        fix_suggestion="Remove the tabindex or set it to 0. Rearrange DOM order to achieve the desired tab sequence.",
                        fix_code=f'<{elem.name} tabindex="0">...</{elem.name}>',
                    ))
            except (ValueError, TypeError):
                pass

    def check_aria_usage(self):
        """WCAG 4.1.2 - ARIA attributes must be used correctly (Level A)"""
        # Check for invalid roles
        elements_with_role = self.soup.find_all(attrs={"role": True})
        for elem in elements_with_role:
            role = elem.get("role", "").strip().lower()
            if role and role not in VALID_ARIA_ROLES:
                self.issues.append(Issue(
                    rule_id="aria-invalid-role",
                    rule_name="Invalid ARIA role",
                    severity="serious",
                    wcag_level="A",
                    wcag_criterion="4.1.2",
                    element_selector=get_element_selector(elem),
                    element_html=get_element_html_snippet(elem),
                    element_tag=elem.name,
                    page_region=get_page_region(elem),
                    description=f'Invalid ARIA role "{role}". Assistive technologies will not recognize this role.',
                    impact_group="blind",
                    fix_suggestion=f'Use a valid ARIA role. Common roles: button, link, navigation, banner, main, complementary, form, search.',
                    fix_code=f'<{elem.name} role="valid-role">...</{elem.name}>',
                ))

            # Check required properties for the role
            if role in ARIA_REQUIRED_PROPERTIES:
                for prop in ARIA_REQUIRED_PROPERTIES[role]:
                    if not elem.get(prop):
                        self.issues.append(Issue(
                            rule_id="aria-missing-property",
                            rule_name="Missing required ARIA property",
                            severity="serious",
                            wcag_level="A",
                            wcag_criterion="4.1.2",
                            element_selector=get_element_selector(elem),
                            element_html=get_element_html_snippet(elem),
                            element_tag=elem.name,
                            page_region=get_page_region(elem),
                            description=f'Element with role="{role}" is missing required property "{prop}".',
                            impact_group="blind",
                            fix_suggestion=f'Add the {prop} attribute to the element with role="{role}".',
                            fix_code=f'<{elem.name} role="{role}" {prop}="value">...</{elem.name}>',
                        ))

        # Check aria-hidden on focusable elements
        hidden_elems = self.soup.find_all(attrs={"aria-hidden": "true"})
        for elem in hidden_elems:
            focusable = elem.find_all(["a", "button", "input", "select", "textarea"])
            if not focusable:
                if elem.name in ("a", "button", "input", "select", "textarea"):
                    focusable = [elem]
            for foc in focusable:
                tabindex = foc.get("tabindex")
                if tabindex == "-1":
                    continue
                self.issues.append(Issue(
                    rule_id="aria-hidden-focusable",
                    rule_name="Focusable element inside aria-hidden",
                    severity="critical",
                    wcag_level="A",
                    wcag_criterion="4.1.2",
                    element_selector=get_element_selector(foc),
                    element_html=get_element_html_snippet(foc),
                    element_tag=foc.name,
                    page_region=get_page_region(foc),
                    description="Focusable element is inside aria-hidden=\"true\". This creates a confusing experience where the element receives focus but is not announced.",
                    impact_group="blind",
                    fix_suggestion="Either remove aria-hidden=\"true\" from the ancestor, or add tabindex=\"-1\" to remove the element from tab order.",
                    fix_code=f'<{foc.name} tabindex="-1">...</{foc.name}>',
                ))

    def check_document_language(self):
        """WCAG 3.1.1 - Language of Page (Level A)"""
        html_tag = self.soup.find("html")
        if html_tag and not html_tag.get("lang"):
            self.issues.append(Issue(
                rule_id="html-lang-missing",
                rule_name="Page language not specified",
                severity="serious",
                wcag_level="A",
                wcag_criterion="3.1.1",
                element_selector="html",
                element_html="<html>",
                element_tag="html",
                page_region="body",
                description="The <html> element does not have a lang attribute. Screen readers cannot determine the correct pronunciation.",
                impact_group="blind",
                fix_suggestion='Add a lang attribute to the <html> element, e.g., lang="zh-CN" for Chinese or lang="en" for English.',
                fix_code='<html lang="zh-CN">',
            ))

    def check_page_title(self):
        """WCAG 2.4.2 - Page Titled (Level A)"""
        title = self.soup.find("title")
        if not title or not title.get_text(strip=True):
            self.issues.append(Issue(
                rule_id="page-title-missing",
                rule_name="Page title missing",
                severity="serious",
                wcag_level="A",
                wcag_criterion="2.4.2",
                element_selector="head",
                element_html="<head>...</head>",
                element_tag="title",
                page_region="header",
                description="The page has no <title> or it is empty. Users cannot identify the page in browser tabs or bookmarks.",
                impact_group="blind,cognitive",
                fix_suggestion="Add a descriptive <title> element that identifies the page content.",
                fix_code="<title>Page Name - Site Name</title>",
            ))
