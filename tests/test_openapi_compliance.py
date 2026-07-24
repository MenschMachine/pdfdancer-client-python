#!/usr/bin/env python3
"""
Test script to verify OpenAPI compliance of request wrapper types.
"""

from pdfdancer.models import (
    AddRequest,
    DeleteRequest,
    FindRequest,
    Image,
    ModifyRequest,
    MoveRequest,
    ObjectRef,
    ObjectType,
    Position,
)


def test_object_type_values_match_v2_contract():
    assert {object_type.value for object_type in ObjectType} == {
        "PDF",
        "PAGE",
        "TEXT_ELEMENT",
        "IMAGE",
        "PATH",
        "LINE",
        "RECTANGLE",
        "BEZIER",
        "CLIPPING",
        "FORM_X_OBJECT",
        "FORM_FIELD",
        "WORD",
        "TEXT_LINE",
        "TEXT_FIELD",
        "RADIO_BUTTON",
        "BUTTON",
        "DROPDOWN",
        "CHECKBOX",
    }


def test_find_request():
    """Test FindRequest serialization."""
    print("Testing FindRequest...")
    position = Position.at_page_coordinates(1, 10.0, 20.0)
    find_req = FindRequest(ObjectType.TEXT_LINE, position, "test hint")
    result = find_req.to_dict()

    expected_keys = {"objectType", "position", "hint"}
    assert (
        set(result.keys()) == expected_keys
    ), f"FindRequest keys mismatch: {result.keys()}"
    assert result["objectType"] == "TEXT_LINE"
    assert result["hint"] == "test hint"
    print("✓ FindRequest serialization correct")


def test_delete_request():
    """Test DeleteRequest serialization."""
    print("Testing DeleteRequest...")
    position = Position(page_number=1)
    obj_ref = ObjectRef("test-id", position, ObjectType.TEXT_LINE)
    delete_req = DeleteRequest(obj_ref)
    result = delete_req.to_dict()

    assert "objectRef" in result, f"DeleteRequest missing objectRef wrapper: {result}"
    assert "internalId" in result["objectRef"]
    assert result["objectRef"]["internalId"] == "test-id"
    print("✓ DeleteRequest serialization correct")


def test_move_request():
    """Test MoveRequest serialization."""
    print("Testing MoveRequest...")
    position = Position(page_number=1)
    obj_ref = ObjectRef("test-id", position, ObjectType.TEXT_LINE)
    new_position = Position.at_page_coordinates(2, 50.0, 60.0)
    move_req = MoveRequest(obj_ref, new_position)
    result = move_req.to_dict()

    expected_keys = {"objectRef", "newPosition"}
    assert (
        set(result.keys()) == expected_keys
    ), f"MoveRequest keys mismatch: {result.keys()}"
    assert "internalId" in result["objectRef"]
    print("✓ MoveRequest serialization correct")


def test_add_request():
    """Test AddRequest serialization."""
    print("Testing AddRequest...")
    position = Position.at_page_coordinates(1, 10.0, 20.0)
    image = Image(position=position, format="PNG", data=b"image")
    add_req = AddRequest(image)
    result = add_req.to_dict()

    assert "object" in result, f"AddRequest should use 'object' field: {result.keys()}"
    assert result["object"]["type"] == "IMAGE"
    print("✓ AddRequest serialization correct")


def test_modify_request():
    """Test ModifyRequest serialization."""
    print("Testing ModifyRequest...")
    position = Position(page_number=1)
    obj_ref = ObjectRef("test-id", position, ObjectType.IMAGE)
    new_image = Image(position=position, format="PNG", data=b"new-image")
    modify_req = ModifyRequest(obj_ref, new_image)
    result = modify_req.to_dict()

    expected_keys = {"ref", "newObject"}
    assert (
        set(result.keys()) == expected_keys
    ), f"ModifyRequest keys mismatch: {result.keys()}"
    assert "internalId" in result["ref"]
    print("✓ ModifyRequest serialization correct")


def test_object_ref():
    """Test ObjectRef serialization."""
    print("Testing ObjectRef...")
    position = Position.at_page_coordinates(1, 10.0, 20.0)
    obj_ref = ObjectRef("test-id", position, ObjectType.TEXT_LINE)
    result = obj_ref.to_dict()

    expected_keys = {"internalId", "position", "type"}
    assert (
        set(result.keys()) == expected_keys
    ), f"ObjectRef keys mismatch: {result.keys()}"
    assert result["internalId"] == "test-id"
    assert result["type"] == "TEXT_LINE"
    print("✓ ObjectRef serialization correct")
