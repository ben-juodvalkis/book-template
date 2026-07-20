"""
Geometry + config tests — the print math that the parity/safe-margin guards and
the cover generator depend on. These lock down the single source of truth in
scripts/_build.py so a preset or refactor can't silently break the bleed model.
"""
import pytest

import _build as b


def cfg(**over):
    """A book.config dict starting from defaults, with overrides applied."""
    return dict(b.CONFIG_DEFAULTS, **over)


# ── length parsing ───────────────────────────────────────────────────────────

@pytest.mark.parametrize("text,inches", [
    ("8", 8.0), ("8in", 8.0), ("0.125in", 0.125),
    ("203mm", 203 / 25.4), ("25.4mm", 1.0), ("  10in ", 10.0),
])
def test_parse_length_in(text, inches):
    assert b.parse_length_in(text) == pytest.approx(inches)


# ── presets + aliases ────────────────────────────────────────────────────────

def test_default_preset_is_blurb_8x10():
    g = b.resolve_geometry(cfg())
    assert (g["trim_width"], g["trim_height"]) == (8.0, 10.0)
    assert g["binding"] == "saddle-stitch"


def test_every_preset_has_required_fields():
    required = {"trim_width", "trim_height", "bleed", "safe_binding",
               "safe_outside", "safe_top", "safe_bottom", "dpi", "binding"}
    for name, preset in b.PAGE_SIZE_PRESETS.items():
        assert required <= set(preset), f"{name} missing {required - set(preset)}"
        assert preset["binding"] in ("saddle-stitch", "perfect-bound")


def test_aliases_resolve_to_canonical_presets():
    for alias, target in b.PAGE_SIZE_ALIASES.items():
        assert target in b.PAGE_SIZE_PRESETS, f"{alias} -> unknown {target}"
        got = b.resolve_geometry(cfg(page_size=alias))
        want = b.resolve_geometry(cfg(page_size=target))
        assert got == want


def test_unknown_preset_falls_back_to_default(capsys):
    g = b.resolve_geometry(cfg(page_size="does-not-exist"))
    assert (g["trim_width"], g["trim_height"]) == (8.0, 10.0)
    assert "unknown page_size" in capsys.readouterr().out


def test_per_field_override_wins_over_preset():
    g = b.resolve_geometry(cfg(page_size="trade-6x9", safe_binding=0.75))
    assert g["safe_binding"] == 0.75
    assert g["trim_width"] == 6.0   # untouched fields still from the preset


# ── derived geometry ─────────────────────────────────────────────────────────

def test_derived_geometry_blurb_8x10():
    g = b.geometry(cfg())
    assert g["div_w"] == pytest.approx(8.25)      # trim + 2*bleed
    assert g["div_h"] == pytest.approx(10.25)
    assert g["page_margin"] == pytest.approx(-0.125)
    assert g["page_w"] == pytest.approx(8.125)    # trim + one (outside) bleed
    assert g["page_h"] == pytest.approx(10.25)
    assert g["css_safe_binding"] == pytest.approx(0.625)   # safe + bleed
    assert g["css_safe_outside"] == pytest.approx(0.625)
    assert g["css_safe_top"] == pytest.approx(0.375)
    assert g["spread_w"] == pytest.approx(16.25)  # 2*(trim + bleed)
    assert g["spread_recto_x"] == pytest.approx(-8.0)


def test_css_safe_is_always_safe_plus_one_bleed():
    for name in b.PAGE_SIZE_PRESETS:
        g = b.geometry(cfg(page_size=name))
        assert g["css_safe_binding"] == pytest.approx(g["safe_binding"] + g["bleed"])
        assert g["css_safe_outside"] == pytest.approx(g["safe_outside"] + g["bleed"])
        assert g["css_safe_top"] == pytest.approx(g["safe_top"] + g["bleed"])
        assert g["css_safe_bottom"] == pytest.approx(g["safe_bottom"] + g["bleed"])


# ── binding + page-count policy ──────────────────────────────────────────────

def test_resolve_binding_from_preset_and_override():
    assert b.resolve_binding(cfg(page_size="blurb-8x10")) == "saddle-stitch"
    assert b.resolve_binding(cfg(page_size="trade-6x9")) == "perfect-bound"
    # explicit book.config wins over the preset's binding
    assert b.resolve_binding(cfg(page_size="blurb-8x10", binding_type="perfect-bound")) == "perfect-bound"


def test_min_pages_binding_aware_and_overridable():
    assert b.min_pages(cfg(page_size="blurb-8x10")) == 20
    assert b.min_pages(cfg(page_size="trade-6x9")) == 24
    assert b.min_pages(cfg(min_pages=8)) == 8


# ── spine + cover ────────────────────────────────────────────────────────────

def test_resolve_ppi_sources():
    assert b.resolve_ppi(cfg(paper_ppi=500)) == 500                 # explicit wins
    assert b.resolve_ppi(cfg(paper_stock="cream")) == b.PAPER_STOCKS["cream"]
    assert b.resolve_ppi(cfg()) == b.DEFAULT_PAPER_PPI              # default (white)


def test_resolve_ppi_unknown_stock_warns_and_defaults(capsys):
    assert b.resolve_ppi(cfg(paper_stock="unobtanium")) == b.DEFAULT_PAPER_PPI
    assert "unknown paper_stock" in capsys.readouterr().out


def test_spine_width():
    assert b.spine_width_in(100, 400) == pytest.approx(0.25)
    assert b.spine_width_in(120, 444) == pytest.approx(120 / 444)


def test_cover_geometry_composition():
    c = b.cover_geometry(120, cfg())         # blurb 8x10, white 444 ppi
    spine = 120 / 444
    assert c["spine_w"] == pytest.approx(spine)
    assert c["cover_trim_w"] == pytest.approx(2 * 8.0 + spine)
    assert c["cover_trim_h"] == pytest.approx(10.0)
    assert c["cover_div_w"] == pytest.approx(2 * 8.0 + spine + 2 * 0.125)
    assert c["cover_div_h"] == pytest.approx(10.25)
    assert c["back_w"] == pytest.approx(8.125)
    assert c["front_w"] == pytest.approx(8.125)
    # the two panels plus the spine exactly fill the flat cover with bleed
    assert c["back_w"] + c["spine_w"] + c["front_w"] == pytest.approx(c["cover_div_w"])


# ── injected CSS variables ───────────────────────────────────────────────────

def test_geometry_css_vars_emit_expected_lengths():
    css = b.geometry_css_vars(b.geometry(cfg()))
    assert "--trim-w: 8in" in css
    assert "--div-w: 8.25in" in css
    assert "--safe-binding: 0.625in" in css


def test_cover_css_vars_emit_spine_and_panels():
    css = b.cover_css_vars(b.cover_geometry(120, cfg()))
    assert "--spine-w:" in css and "--back-w: 8.125in" in css
    assert "--cover-trim-w:" in css
