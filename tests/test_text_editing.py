import base64
import math

import pytest

from pdfdancer import (
    PdfAffineTransform,
    PdfColorRequest,
    TextDeleteRequest,
    TextEditResponse,
    TextInsertRequest,
    TextLayoutMode,
    TextLayoutProfile,
    TextLayoutRequest,
    TextReplaceRequest,
    TextStyleNumericFilterRequest,
    TextStylePatchRequest,
    TextStyleRequest,
    TextStyleRunFilterRequest,
    TextStyleRunsSelectorRequest,
    TextStyleSelectorRequest,
    TextStyleSetRequest,
)
from pdfdancer.exceptions import ValidationException


def test_affine_transform_identity_and_exact_matrix():
    assert PdfAffineTransform.builder().build().to_pdf_matrix() == (1, 0, 0, 1, 0, 0)
    matrix = [20, 0, 5, 10, 3, -2]
    transform = PdfAffineTransform.from_pdf_matrix(matrix)
    matrix[0] = 999
    assert transform.to_pdf_matrix() == (20, 0, 5, 10, 3, -2)


def test_affine_transform_operations_apply_in_invocation_order():
    transform = PdfAffineTransform.builder().scale(2, 3).translate(5, 7).build()
    assert transform.to_pdf_matrix() == (2, 0, 0, 3, 5, 7)


def test_affine_transform_rotation_and_shear():
    rotation = PdfAffineTransform.builder().rotate_degrees(90).build()
    shear = PdfAffineTransform.builder().shear(0.25, -0.5).build()
    assert rotation.to_pdf_matrix() == pytest.approx((0, 1, -1, 0, 0, 0))
    assert shear.to_pdf_matrix() == (1, -0.5, 0.25, 1, 0, 0)


@pytest.mark.parametrize(
    "value",
    [[], [1] * 5, [1] * 7, [1, 0, 0, 1, math.nan, 0]],
)
def test_affine_transform_rejects_invalid_matrices(value):
    with pytest.raises(ValidationException):
        PdfAffineTransform.from_pdf_matrix(value)


def test_color_serialization_and_validation():
    assert PdfColorRequest.rgb(0.1, 0.2, 0.3).alpha(0.4).to_dict() == {
        "space": "rgb",
        "components": [0.1, 0.2, 0.3],
        "alpha": 0.4,
    }
    assert PdfColorRequest.cmyk(0, 0.1, 0.2, 0.3).to_dict()["space"] == "cmyk"
    assert PdfColorRequest.gray(0.5).to_dict()["components"] == [0.5]
    with pytest.raises(ValidationException):
        PdfColorRequest.rgb(-0.1, 0, 0)
    with pytest.raises(ValidationException):
        PdfColorRequest.gray(1.1)


def test_replace_literal_serializes_all_selector_options():
    request = (
        TextReplaceRequest.literal("source", "result")
        .pages(1, 3)
        .case_sensitive(False)
        .whole_words(True)
        .max_matches(2)
        .build()
    )
    assert request.to_dict() == {
        "pages": [1, 3],
        "select": {
            "literal": "source",
            "caseSensitive": False,
            "wholeWords": True,
            "maxMatches": 2,
        },
        "replaceWith": "result",
    }


def test_replace_regex_reflow_and_hyphenation_serialization():
    request = (
        TextReplaceRequest.regex(r"\bsource\b", "result")
        .require_reflow(TextLayoutProfile.BODY_TEXT)
        .hyphenation_enabled(False)
        .build()
    )
    assert request.to_dict()["layout"] == {
        "mode": "requireReflow",
        "profile": "bodyText",
        "hyphenationEnabled": False,
    }


def test_replace_serializes_every_atomic_style_override():
    style = (
        TextReplaceRequest.literal("source", "result")
        .font("Helvetica-Bold")
        .size(17)
        .fill_color(PdfColorRequest.rgb(0.1, 0.2, 0.3))
        .stroke_color(PdfColorRequest.gray(0.4))
        .character_spacing(0.5)
        .word_spacing(1.25)
        .build()
        .to_dict()["style"]
    )
    assert style == {
        "font": "Helvetica-Bold",
        "size": 17,
        "fillColor": {"space": "rgb", "components": [0.1, 0.2, 0.3]},
        "strokeColor": {"space": "gray", "components": [0.4]},
        "characterSpacing": 0.5,
        "wordSpacing": 1.25,
    }


def test_replace_reset_spacing_and_empty_replacement():
    request = TextReplaceRequest.literal("source", "").reset_spacing_overrides().build()
    assert request.to_dict()["replaceWith"] == ""
    assert request.to_dict()["style"] == {"resetSpacingOverrides": True}


def test_replace_image_uses_base64_and_pdf_matrix_order():
    request = (
        TextReplaceRequest.builder()
        .literal("{{logo}}")
        .replace_with_image(
            b"image-bytes",
            PdfAffineTransform.from_pdf_matrix((20, 0, 5, 10, 3, -2)),
        )
        .build()
    )
    assert request.to_dict()["replaceWithImage"] == {
        "data": base64.b64encode(b"image-bytes").decode("ascii"),
        "transformationMatrix": [20, 0, 5, 10, 3, -2],
    }


@pytest.mark.parametrize(
    "builder",
    [
        lambda: TextReplaceRequest.literal("", "x"),
        lambda: TextReplaceRequest.regex(" ", "x"),
        lambda: TextReplaceRequest.literal("x", "y").pages(0),
        lambda: TextReplaceRequest.literal("x", "y").max_matches(0),
        lambda: TextReplaceRequest.literal("x", "y").size(0),
        lambda: TextReplaceRequest.literal("x", "y").font(" "),
        lambda: TextReplaceRequest.literal("x", "y").hyphenation_enabled(True),
    ],
)
def test_replace_rejects_invalid_contract_values(builder):
    with pytest.raises(ValidationException):
        builder().build()


def test_delete_serializes_literal_and_regex_layout():
    assert TextDeleteRequest.literal("obsolete").pages(2).build().to_dict() == {
        "pages": [2],
        "select": {"literal": "obsolete"},
    }
    request = (
        TextDeleteRequest.regex("obsolete.*")
        .reflow_when_supported(TextLayoutProfile.DEFAULT)
        .build()
    )
    assert request.to_dict()["select"] == {"regex": "obsolete.*"}
    assert request.to_dict()["layout"] == {
        "mode": "reflowWhenSupported",
        "profile": "default",
    }


def test_insert_literal_anchor_and_whitespace_only_insert():
    request = (
        TextInsertRequest.after("anchor", " ")
        .pages(1, 2)
        .case_sensitive(True)
        .whole_words(True)
        .max_matches(3)
        .build()
    )
    assert request.to_dict() == {
        "target": {
            "anchor": {
                "pages": [1, 2],
                "select": {
                    "literal": "anchor",
                    "caseSensitive": True,
                    "wholeWords": True,
                    "maxMatches": 3,
                },
                "caret": "after",
            }
        },
        "insert": " ",
        "style": {"from": "anchor"},
    }


def test_insert_regex_before_with_style_patch_and_layout():
    request = (
        TextInsertRequest.before_regex("TOTAL", "GRAND ")
        .font("Helvetica-Bold")
        .size(12)
        .fill_color(PdfColorRequest.rgb(1, 0, 0))
        .reflow_when_supported(TextLayoutProfile.DEFAULT)
        .build()
    )
    payload = request.to_dict()
    assert payload["target"]["anchor"]["select"] == {"regex": "TOTAL"}
    assert payload["target"]["anchor"]["caret"] == "before"
    assert payload["style"] == {
        "from": "anchor",
        "patch": {
            "font": "Helvetica-Bold",
            "size": 12,
            "fillColor": {"space": "rgb", "components": [1.0, 0.0, 0.0]},
        },
    }


def test_coordinate_insert_requires_complete_style_and_serializes_rotation():
    request = (
        TextInsertRequest.at(1, 72, 144, "Coordinate Text")
        .rotation_degrees(90)
        .font("Helvetica-Bold")
        .size(12)
        .build()
    )
    assert request.to_dict() == {
        "target": {
            "coordinate": {
                "page": 1,
                "x": 72,
                "y": 144,
                "rotationDegrees": 90,
            }
        },
        "insert": "Coordinate Text",
        "style": {"patch": {"font": "Helvetica-Bold", "size": 12}},
    }
    with pytest.raises(ValidationException):
        TextInsertRequest.at(1, 72, 144, "x").font("Helvetica").build()


def test_page_scoped_coordinate_request_can_be_completed_after_build():
    request = (
        TextInsertRequest.builder()
        .coordinate(72, 144)
        .insert("Page scoped")
        .font("Helvetica")
        .size(10)
        .build()
        .with_pages((3,))
    )
    assert request.to_dict()["target"]["coordinate"]["page"] == 3


def test_style_literal_serializes_all_fields():
    request = (
        TextStyleRequest.literal("target")
        .pages(1)
        .font("Helvetica")
        .size(11)
        .fill_color(PdfColorRequest.rgb(0, 0, 0))
        .stroke_color(PdfColorRequest.gray(1))
        .character_spacing(0.25)
        .word_spacing(0.5)
        .source_anchored()
        .build()
    )
    payload = request.to_dict()
    assert payload["select"] == {"literal": "target"}
    assert payload["style"]["font"] == "Helvetica"
    assert payload["style"]["wordSpacing"] == 0.5
    assert payload["layout"] == {"mode": "sourceAnchored"}


def test_style_runs_where_serializes_supported_filters():
    request = (
        TextStyleRequest.runs_where()
        .where_text_contains("Total")
        .where_font("Helvetica-Bold")
        .where_size(12, 0.25)
        .where_fill_color(PdfColorRequest.rgb(0, 0, 0))
        .where_character_spacing(0, 0.1)
        .where_word_spacing(0, 0.1)
        .where_contains_unmapped_glyphs(False)
        .max_matches(4)
        .font("Helvetica")
        .build()
    )
    runs = request.to_dict()["select"]["runs"]
    assert runs["maxMatches"] == 4
    assert runs["where"]["size"] == {"eq": 12, "tolerance": 0.25}
    assert runs["where"]["containsUnmappedGlyphs"] is False


def test_style_and_style_patch_validation():
    with pytest.raises(ValidationException):
        TextStylePatchRequest().validated()
    with pytest.raises(ValidationException):
        TextStyleSetRequest(reset_spacing_overrides=False).validated()
    with pytest.raises(ValidationException):
        TextStyleSetRequest(
            character_spacing=1, reset_spacing_overrides=True
        ).validated()
    with pytest.raises(ValidationException):
        TextStyleRequest.literal("x").build()
    with pytest.raises(ValidationException):
        TextStyleRequest.runs_where().font("Helvetica").build()


def test_direct_style_selector_validation():
    numeric = TextStyleNumericFilterRequest.equal_to(12, 0.5)
    run_filter = TextStyleRunFilterRequest(font="Helvetica", size=numeric)
    selector = TextStyleSelectorRequest(
        runs=TextStyleRunsSelectorRequest(run_filter, 2)
    )
    assert selector.to_dict()["runs"]["where"]["font"] == "Helvetica"
    with pytest.raises(ValidationException):
        TextStyleSelectorRequest(literal="x", regex="y").validated()


@pytest.mark.parametrize(
    "factory",
    [
        lambda: TextReplaceRequest.literal("a", "b"),
        lambda: TextDeleteRequest.literal("a"),
        lambda: TextInsertRequest.after("a", "b"),
        lambda: TextStyleRequest.literal("a").font("Helvetica"),
    ],
)
def test_require_reflow_and_hyphenation_are_available_on_every_builder(factory):
    payload = (
        factory()
        .require_reflow(TextLayoutProfile.NO_REFLOW)
        .hyphenation_enabled(True)
        .build()
        .to_dict()
    )
    assert payload["layout"] == {
        "mode": "requireReflow",
        "profile": "noReflow",
        "hyphenationEnabled": True,
    }


def test_text_edit_response_parses_complete_diagnostics():
    response = TextEditResponse.from_dict(
        {
            "matched": 1,
            "changed": 1,
            "pagesChanged": [2],
            "change": [
                {
                    "page": 2,
                    "operation": "replace",
                    "sourceText": "a",
                    "resultText": "b",
                    "requestedLayoutMode": "requireReflow",
                    "requestedLayoutProfile": "bodyText",
                    "effectiveHyphenationEnabled": True,
                    "appliedLayoutMode": "REFLOW",
                    "elementIds": ["e1"],
                    "generatedElementIds": ["e2"],
                    "reflowUnitIds": ["r1"],
                }
            ],
            "warnings": [{"page": 2, "code": "W", "message": "warning"}],
            "errors": [],
        }
    )
    assert response.pages_changed == (2,)
    assert response.change[0].effective_hyphenation_enabled is True
    assert response.warnings[0].code == "W"


def test_text_edit_response_preserves_omitted_lists_as_none():
    response = TextEditResponse.from_dict({"matched": 0, "changed": 0})

    assert response.pages_changed is None
    assert response.change is None
    assert response.warnings is None
    assert response.errors is None


def test_layout_enum_aliases_match_java_nesting():
    assert TextLayoutRequest.Mode is TextLayoutMode
    assert TextLayoutRequest.Profile is TextLayoutProfile
