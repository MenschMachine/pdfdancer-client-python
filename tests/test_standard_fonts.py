"""
Tests for StandardFonts enum - validates all 14 standard PDF fonts.
"""

import pytest

from pdfdancer import StandardFonts


class TestStandardFonts:
    """Test StandardFonts enum functionality."""

    def test_enum_has_14_fonts(self):
        """Test that StandardFonts enum contains exactly 14 standard PDF fonts."""
        assert len(StandardFonts) == 14

    def test_times_family_fonts(self):
        """Test Times family fonts (4 variants)."""
        assert StandardFonts.TIMES_ROMAN.value == "Times-Roman"
        assert StandardFonts.TIMES_BOLD.value == "Times-Bold"
        assert StandardFonts.TIMES_ITALIC.value == "Times-Italic"
        assert StandardFonts.TIMES_BOLD_ITALIC.value == "Times-BoldItalic"

    def test_helvetica_family_fonts(self):
        """Test Helvetica family fonts (4 variants)."""
        assert StandardFonts.HELVETICA.value == "Helvetica"
        assert StandardFonts.HELVETICA_BOLD.value == "Helvetica-Bold"
        assert StandardFonts.HELVETICA_OBLIQUE.value == "Helvetica-Oblique"
        assert StandardFonts.HELVETICA_BOLD_OBLIQUE.value == "Helvetica-BoldOblique"

    def test_courier_family_fonts(self):
        """Test Courier family fonts (4 variants)."""
        assert StandardFonts.COURIER.value == "Courier"
        assert StandardFonts.COURIER_BOLD.value == "Courier-Bold"
        assert StandardFonts.COURIER_OBLIQUE.value == "Courier-Oblique"
        assert StandardFonts.COURIER_BOLD_OBLIQUE.value == "Courier-BoldOblique"

    def test_symbol_fonts(self):
        """Test Symbol and ZapfDingbats fonts."""
        assert StandardFonts.SYMBOL.value == "Symbol"
        assert StandardFonts.ZAPF_DINGBATS.value == "ZapfDingbats"

    def test_all_font_names_are_unique(self):
        """Test that all font names are unique."""
        font_values = [font.value for font in StandardFonts]
        assert len(font_values) == len(set(font_values))

    def test_all_font_enum_names_are_unique(self):
        """Test that all enum names are unique."""
        font_names = [font.name for font in StandardFonts]
        assert len(font_names) == len(set(font_names))

    def test_enum_access_by_name(self):
        """Test accessing fonts by enum name."""
        assert StandardFonts.TIMES_ROMAN == StandardFonts["TIMES_ROMAN"]
        assert StandardFonts.HELVETICA == StandardFonts["HELVETICA"]
        assert StandardFonts.COURIER == StandardFonts["COURIER"]

    def test_enum_access_by_value(self):
        """Test accessing fonts by their string value."""
        assert StandardFonts("Times-Roman") == StandardFonts.TIMES_ROMAN
        assert StandardFonts("Helvetica") == StandardFonts.HELVETICA
        assert StandardFonts("Courier") == StandardFonts.COURIER

    def test_font_name_format_follows_pdf_spec(self):
        """Test that font names follow PDF specification format."""
        # Verify specific font name formats according to PDF spec
        assert StandardFonts.ZAPF_DINGBATS.value == "ZapfDingbats"
        assert StandardFonts.SYMBOL.value == "Symbol"

        # Base fonts (no modifiers)
        assert StandardFonts.HELVETICA.value == "Helvetica"
        assert StandardFonts.COURIER.value == "Courier"
        assert StandardFonts.TIMES_ROMAN.value == "Times-Roman"

        # Modified fonts should have hyphens
        modified_fonts = [
            f for f in StandardFonts
            if f not in [StandardFonts.HELVETICA, StandardFonts.COURIER,
                         StandardFonts.SYMBOL, StandardFonts.ZAPF_DINGBATS]
        ]
        for font in modified_fonts:
            assert "-" in font.value

    def test_iteration_over_fonts(self):
        """Test that we can iterate over all fonts."""
        font_list = list(StandardFonts)
        assert len(font_list) == 14
        assert StandardFonts.TIMES_ROMAN in font_list
        assert StandardFonts.HELVETICA in font_list
        assert StandardFonts.COURIER in font_list
        assert StandardFonts.SYMBOL in font_list
        assert StandardFonts.ZAPF_DINGBATS in font_list

    def test_font_enum_is_immutable(self):
        """Test that font enum values cannot be modified."""
        with pytest.raises(AttributeError):
            StandardFonts.TIMES_ROMAN = "NewValue"

    def test_times_family_count(self):
        """Test that Times family has exactly 4 variants."""
        times_fonts = [f for f in StandardFonts if f.value.startswith("Times")]
        assert len(times_fonts) == 4

    def test_helvetica_family_count(self):
        """Test that Helvetica family has exactly 4 variants."""
        helvetica_fonts = [f for f in StandardFonts if f.value.startswith("Helvetica")]
        assert len(helvetica_fonts) == 4

    def test_courier_family_count(self):
        """Test that Courier family has exactly 4 variants."""
        courier_fonts = [f for f in StandardFonts if f.value.startswith("Courier")]
        assert len(courier_fonts) == 4

    def test_symbol_family_count(self):
        """Test that there are exactly 2 symbol fonts."""
        symbol_fonts = [f for f in StandardFonts if f in [StandardFonts.SYMBOL, StandardFonts.ZAPF_DINGBATS]]
        assert len(symbol_fonts) == 2

    def test_font_value_string_representation(self):
        """Test that font values are properly formatted strings."""
        for font in StandardFonts:
            assert isinstance(font.value, str)
            assert len(font.value) > 0
            # Font names should not contain spaces
            assert " " not in font.value

    def test_all_fonts_accessible(self):
        """Test that all 14 fonts are accessible by their enum names."""
        fonts = [
            StandardFonts.TIMES_ROMAN,
            StandardFonts.TIMES_BOLD,
            StandardFonts.TIMES_ITALIC,
            StandardFonts.TIMES_BOLD_ITALIC,
            StandardFonts.HELVETICA,
            StandardFonts.HELVETICA_BOLD,
            StandardFonts.HELVETICA_OBLIQUE,
            StandardFonts.HELVETICA_BOLD_OBLIQUE,
            StandardFonts.COURIER,
            StandardFonts.COURIER_BOLD,
            StandardFonts.COURIER_OBLIQUE,
            StandardFonts.COURIER_BOLD_OBLIQUE,
            StandardFonts.SYMBOL,
            StandardFonts.ZAPF_DINGBATS,
        ]
        assert len(fonts) == 14
        assert len(set(fonts)) == 14  # All unique

    def test_invalid_font_value_raises_error(self):
        """Test that accessing an invalid font value raises ValueError."""
        with pytest.raises(ValueError):
            StandardFonts("InvalidFont")

    def test_invalid_font_name_raises_error(self):
        """Test that accessing an invalid font name raises KeyError."""
        with pytest.raises(KeyError):
            StandardFonts["INVALID_FONT"]

    def test_font_comparison(self):
        """Test that font comparison works correctly."""
        assert StandardFonts.TIMES_ROMAN == StandardFonts.TIMES_ROMAN
        assert StandardFonts.TIMES_ROMAN != StandardFonts.TIMES_BOLD
        assert StandardFonts.HELVETICA == StandardFonts.HELVETICA
        assert StandardFonts.COURIER != StandardFonts.TIMES_ROMAN
