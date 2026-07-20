"""
Build-helper tests — the fragment/HTML plumbing shared by every build script:
page-range parsing, page-div counting/extraction, section wrapping, the odd/even
bleed-swap, and spread-photo parity warnings.
"""
import pytest

import _build as b

FRAGMENT = """
<style>@page p1 { background: #fff; }</style>
<div class="page" style="page:p1;"><span class="page-number"></span>A</div>
<div class="page spread-photo spread-photo-verso" style="page:p2;">B</div>
<div class="page spread-photo spread-photo-recto" style="page:p3;">C</div>
"""


# ── page ranges ──────────────────────────────────────────────────────────────

@pytest.mark.parametrize("spec,expected", [
    ("1", [0]), ("2", [1]), ("2-4", [1, 2, 3]), ("3-3", [2]),
])
def test_parse_page_range_ok(spec, expected):
    assert b.parse_page_range(spec) == expected


@pytest.mark.parametrize("spec", ["0", "abc", "3-1", "-2", ""])
def test_parse_page_range_bad_exits(spec):
    with pytest.raises(SystemExit):
        b.parse_page_range(spec)


# ── page-div counting + extraction ───────────────────────────────────────────

def test_count_page_divs():
    assert b.count_page_divs(FRAGMENT) == 3
    assert b.count_page_divs("<div>no pages</div>") == 0


def test_extract_pages_keeps_preamble_and_selection():
    body = b.strip_outer_tags(FRAGMENT)
    one = b.extract_pages(body, [0])
    assert "@page p1" in one          # preamble (style) retained
    assert ">A</div>" in one
    assert ">B</div>" not in one
    two = b.extract_pages(body, [1, 2])
    assert ">B</div>" in two and ">C</div>" in two and ">A</div>" not in two


def test_extract_pages_out_of_range_exits():
    with pytest.raises(SystemExit):
        b.extract_pages(b.strip_outer_tags(FRAGMENT), [9])


# ── section wrapping + numbering + bleed parity swap ─────────────────────────

def test_odd_start_no_swap_and_counter_reset():
    html = b.per_section_style(first_page_num=1, front_matter_pages=0)
    assert "counter-reset: page-num 0" in html   # first page increments to 1
    assert "@page :right" not in html            # odd start: base CSS parity, no swap


def test_even_start_injects_bleed_swap():
    html = b.per_section_style(first_page_num=2, front_matter_pages=0)
    # even/LEFT-hand start: swap so physical :right bleeds LEFT, :left bleeds RIGHT
    assert "@page :right" in html and "@page :left" in html
    assert "bleed-left:   var(--bleed)" in html


def test_front_matter_shifts_counter_so_body_starts_at_one():
    # opening(3 front-matter) then first body page is physical 4 -> displayed 1
    html = b.per_section_style(first_page_num=4, front_matter_pages=3)
    assert "counter-reset: page-num 0" in html   # increments to 1 on the first body page


def test_build_section_html_injects_geometry_vars_and_wraps():
    out = b.build_section_html(FRAGMENT, first_page_num=1, front_matter_pages=0)
    assert "<html" in out and "</html>" in out
    assert "--trim-w: 8in" in out                # geometry vars injected into <head>
    assert 'class="page' in out


# ── spread-photo parity warnings ─────────────────────────────────────────────

def test_spread_photo_parity_ok_when_verso_even_recto_odd():
    # verso on page 2 (even/left) + recto on page 3 (odd/right) = correct
    assert b.spread_photo_parity_warnings(FRAGMENT, first_page_num=1) == []


def test_spread_photo_parity_warns_when_halves_on_wrong_hand():
    # start on page 2: verso lands on 3 (odd) and recto on 4 (even) -> both wrong
    warns = b.spread_photo_parity_warnings(FRAGMENT, first_page_num=2)
    assert len(warns) == 2
    assert any("verso" in w for w in warns) and any("recto" in w for w in warns)


# ── generator chunking (scripts/generate.py) ─────────────────────────────────

def test_gallery_chunks_images_into_pages():
    import generate
    assert list(generate.chunk([1, 2, 3, 4, 5], 4)) == [[1, 2, 3, 4], [5]]
    assert list(generate.chunk([1, 2], 2)) == [[1, 2]]
    assert list(generate.chunk([], 3)) == []
