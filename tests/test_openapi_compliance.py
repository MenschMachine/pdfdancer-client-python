#!/usr/bin/env python3
"""
Test script to verify OpenAPI compliance of request wrapper types.
"""

from pdfdancer.models import (
    AddRequest,
    ClearClippingRequest,
    ClearPathGroupClippingRequest,
    DeleteRequest,
    FindRequest,
    Font,
    ModifyRequest,
    ModifyTextRequest,
    MoveRequest,
    ObjectRef,
    ObjectType,
    Paragraph,
    Position,
)


def test_find_request():
    """Test FindRequest serialization."""
    print("Testing FindRequest...")
    position = Position.at_page_coordinates(1, 10.0, 20.0)
    find_req = FindRequest(ObjectType.PARAGRAPH, position, "test hint")
    result = find_req.to_dict()

    expected_keys = {"objectType", "position", "hint"}
    assert (
        set(result.keys()) == expected_keys
    ), f"FindRequest keys mismatch: {result.keys()}"
    assert result["objectType"] == "PARAGRAPH"
    assert result["hint"] == "test hint"
    print("✓ FindRequest serialization correct")


def test_delete_request():
    """Test DeleteRequest serialization."""
    print("Testing DeleteRequest...")
    position = Position(page_number=1)
    obj_ref = ObjectRef("test-id", position, ObjectType.PARAGRAPH)
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
    obj_ref = ObjectRef("test-id", position, ObjectType.PARAGRAPH)
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
    paragraph = Paragraph(
        position=position, text_lines=["test line"], font=Font("Arial", 12)
    )
    add_req = AddRequest(paragraph)
    result = add_req.to_dict()

    assert "object" in result, f"AddRequest should use 'object' field: {result.keys()}"
    assert result["object"]["type"] == "PARAGRAPH"
    print("✓ AddRequest serialization correct")


def test_modify_request():
    """Test ModifyRequest serialization."""
    print("Testing ModifyRequest...")
    position = Position(page_number=1)
    obj_ref = ObjectRef("test-id", position, ObjectType.PARAGRAPH)
    new_paragraph = Paragraph(position=position, text_lines=["new text"])
    modify_req = ModifyRequest(obj_ref, new_paragraph)
    result = modify_req.to_dict()

    expected_keys = {"ref", "newObject"}
    assert (
        set(result.keys()) == expected_keys
    ), f"ModifyRequest keys mismatch: {result.keys()}"
    assert "internalId" in result["ref"]
    print("✓ ModifyRequest serialization correct")


def test_modify_text_request():
    """Test ModifyTextRequest serialization."""
    print("Testing ModifyTextRequest...")
    position = Position(page_number=1)
    obj_ref = ObjectRef("test-id", position, ObjectType.TEXT_LINE)
    modify_text_req = ModifyTextRequest(obj_ref, "new text content")
    result = modify_text_req.to_dict()

    expected_keys = {"ref", "newTextLine"}
    assert (
        set(result.keys()) == expected_keys
    ), f"ModifyTextRequest keys mismatch: {result.keys()}"
    assert result["newTextLine"] == "new text content"
    print("✓ ModifyTextRequest serialization correct")


def test_object_ref():
    """Test ObjectRef serialization."""
    print("Testing ObjectRef...")
    position = Position.at_page_coordinates(1, 10.0, 20.0)
    obj_ref = ObjectRef("test-id", position, ObjectType.PARAGRAPH)
    result = obj_ref.to_dict()

    expected_keys = {"internalId", "position", "type"}
    assert (
        set(result.keys()) == expected_keys
    ), f"ObjectRef keys mismatch: {result.keys()}"
    assert result["internalId"] == "test-id"
    assert result["type"] == "PARAGRAPH"
    print("✓ ObjectRef serialization correct")


def test_clear_clipping_request():
    """Test ClearClippingRequest serialization."""
    print("Testing ClearClippingRequest...")
    position = Position(page_number=1)
    obj_ref = ObjectRef("clip-id", position, ObjectType.TEXT_LINE)
    clear_req = ClearClippingRequest(obj_ref)
    result = clear_req.to_dict()

    expected_keys = {"objectRef"}
    assert (
        set(result.keys()) == expected_keys
    ), f"ClearClippingRequest keys mismatch: {result.keys()}"
    assert result["objectRef"]["internalId"] == "clip-id"
    print("✓ ClearClippingRequest serialization correct")


def test_clear_path_group_clipping_request():
    """Test ClearPathGroupClippingRequest serialization."""
    print("Testing ClearPathGroupClippingRequest...")
    clear_req = ClearPathGroupClippingRequest(page_number=2, group_id="group-123")
    result = clear_req.to_dict()

    expected_keys = {"pageNumber", "groupId"}
    assert (
        set(result.keys()) == expected_keys
    ), f"ClearPathGroupClippingRequest keys mismatch: {result.keys()}"
    assert result["pageNumber"] == 2
    assert result["groupId"] == "group-123"
    print("✓ ClearPathGroupClippingRequest serialization correct")
