import warnings

import pytest

from pdfdancer import TextLayoutRequest
from pdfdancer.text_editing import TextLayoutProfile


def test_keep_line_breaks_sends_the_no_reflow_wire_value():
    assert TextLayoutProfile.KEEP_LINE_BREAKS.value == "noReflow"


def test_lookup_by_wire_value_returns_the_new_member():
    assert TextLayoutProfile("noReflow") is TextLayoutProfile.KEEP_LINE_BREAKS


def test_new_name_does_not_warn():
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        assert (
            TextLayoutProfile.KEEP_LINE_BREAKS is TextLayoutProfile["KEEP_LINE_BREAKS"]
        )


def test_deprecated_attribute_warns_and_is_the_same_member():
    with pytest.warns(DeprecationWarning, match="KEEP_LINE_BREAKS"):
        profile = TextLayoutProfile.NO_REFLOW

    assert profile is TextLayoutProfile.KEEP_LINE_BREAKS


def test_deprecated_item_lookup_warns_and_is_the_same_member():
    with pytest.warns(DeprecationWarning, match="KEEP_LINE_BREAKS"):
        profile = TextLayoutProfile["NO_REFLOW"]

    assert profile is TextLayoutProfile.KEEP_LINE_BREAKS


def test_deprecated_and_new_names_produce_identical_layout_json():
    with pytest.warns(DeprecationWarning):
        old = TextLayoutRequest.reflow_when_supported(TextLayoutProfile.NO_REFLOW)
    new = TextLayoutRequest.reflow_when_supported(TextLayoutProfile.KEEP_LINE_BREAKS)

    assert old.to_dict() == new.to_dict()
    assert new.to_dict()["profile"] == "noReflow"


def test_unknown_attribute_still_raises():
    with pytest.raises(AttributeError):
        TextLayoutProfile.DOES_NOT_EXIST
    with pytest.raises(KeyError):
        TextLayoutProfile["DOES_NOT_EXIST"]


def test_layout_without_mode_or_profile_defaults_to_keep_line_breaks():
    layout = TextLayoutRequest().to_dict()

    assert layout == {"profile": "noReflow"}
