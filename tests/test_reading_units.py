from unittest.mock import Mock

import pytest

from pdfdancer import (
    ReadingUnit,
    ReadingUnitBounds,
    ReadingUnitMode,
    ReadingUnitProvenance,
    ReadingUnitRelationship,
    ReadingUnitRelationshipType,
    ReadingUnitRole,
    ReadingUnitStreamMembership,
)
from pdfdancer.pdfdancer_v2 import PDFDancer


def test_unknown_enum_values_preserve_raw_values():
    role, raw_role = ReadingUnitRole.from_value("SIDEBAR")
    relationship = ReadingUnitRelationship.from_dict(
        {"type": "SIDEBAR_FOR", "targetUnitId": "u2"}
    )
    assert role is ReadingUnitRole.UNKNOWN
    assert raw_role == "SIDEBAR"
    assert relationship.type is ReadingUnitRelationshipType.UNKNOWN
    assert relationship.raw_type == "SIDEBAR_FOR"


def test_complete_reading_unit_fields_are_typed():
    unit = ReadingUnit(
        id="u1",
        role=ReadingUnitRole.PARAGRAPH,
        raw_role="PARAGRAPH",
        text="Body",
        stream={"PRIMARY": ReadingUnitStreamMembership(True, 1)},
        provenance=ReadingUnitProvenance(
            2, ["text-1"], ReadingUnitBounds(10, 20, 30, 40)
        ),
        relationships=[],
    )
    assert unit.provenance.page_number == 2
    assert unit.provenance.bounds.width == 30
    assert unit.stream["PRIMARY"].order == 1
    assert ReadingUnitMode.from_value("FUTURE")[0] is ReadingUnitMode.UNKNOWN


def test_analysis_methods_use_fresh_session_requests_without_mode_parameter():
    client = object.__new__(PDFDancer)
    responses = [
        {"pageCount": 2, "mode": "PRIMARY", "pages": []},
        {"pageCount": 2, "mode": "PRIMARY", "pages": []},
        {"pageNumber": 2, "mode": "PRIMARY", "units": []},
    ]
    calls = []

    def make_request(method, path, data=None, params=None):
        calls.append((method, path, data, params))
        response = Mock()
        response.json.return_value = responses.pop(0)
        return response

    client._make_request = make_request
    client.analyze_reading_units()
    client.analyze_reading_units()
    client.analyze_reading_units(2)

    assert calls == [
        ("GET", "/pdf/document/reading-units", None, None),
        ("GET", "/pdf/document/reading-units", None, None),
        ("GET", "/pdf/page/2/reading-units", None, None),
    ]

    with pytest.raises(Exception, match="Page number"):
        client.analyze_reading_units(0)
