from pathlib import Path

import pytest

from pdfdancer import Image, ImageFlipDirection, ObjectType, ValidationException
from pdfdancer.pdfdancer_v1 import PDFDancer
from tests.e2e import _require_env_and_fixture
from tests.e2e.pdf_assertions import PDFAssertions


class TestImageScale:
    def test_scale_image_by_factor_half(self):
        """Test scaling an image to half size and verify dimensions changed."""
        base_url, token, pdf_path = _require_env_and_fixture("Showcase.pdf")

        with PDFDancer.open(
            pdf_path, token=token, base_url=base_url, timeout=30.0
        ) as pdf:
            images = pdf.select_images()
            assert len(images) > 0

            image = images[0]
            image_id = image.internal_id
            bbox = image.position.bounding_rect
            original_width = bbox.width
            original_height = bbox.height
            original_ratio = original_width / original_height

            result = image.scale(0.5)
            assert result.success, f"Scale failed: {result.message}"

            # Verify with PDFAssertions
            assertions = PDFAssertions(pdf)
            assertions.assert_image_scaled_by_factor(
                image_id, original_width, original_height, 0.5, epsilon=2.0
            )
            # Aspect ratio should be preserved
            assertions.assert_image_aspect_ratio(image_id, original_ratio, epsilon=0.1)

    def test_scale_image_by_factor_double(self):
        """Test scaling an image to double size."""
        base_url, token, pdf_path = _require_env_and_fixture("Showcase.pdf")

        with PDFDancer.open(
            pdf_path, token=token, base_url=base_url, timeout=30.0
        ) as pdf:
            images = pdf.select_images()
            image = images[0]
            image_id = image.internal_id
            bbox = image.position.bounding_rect
            original_width = bbox.width
            original_height = bbox.height

            result = image.scale(2.0)
            assert result.success, f"Scale failed: {result.message}"

            assertions = PDFAssertions(pdf)
            assertions.assert_image_scaled_by_factor(
                image_id, original_width, original_height, 2.0, epsilon=2.0
            )

    def test_scale_image_to_target_size_preserving_aspect(self):
        """Test scaling to target size while preserving aspect ratio."""
        base_url, token, pdf_path = _require_env_and_fixture("Showcase.pdf")

        with PDFDancer.open(
            pdf_path, token=token, base_url=base_url, timeout=30.0
        ) as pdf:
            images = pdf.select_images()
            image = images[0]
            image_id = image.internal_id
            bbox = image.position.bounding_rect
            original_ratio = bbox.width / bbox.height

            result = image.scale_to(100, 100, preserve_aspect_ratio=True)
            assert result.success, f"Scale to target size failed: {result.message}"

            # Aspect ratio should be preserved
            assertions = PDFAssertions(pdf)
            assertions.assert_image_aspect_ratio(image_id, original_ratio, epsilon=0.1)

    def test_scale_image_to_target_size_not_preserving_aspect(self):
        """Test scaling to target size without preserving aspect ratio."""
        base_url, token, pdf_path = _require_env_and_fixture("Showcase.pdf")

        with PDFDancer.open(
            pdf_path, token=token, base_url=base_url, timeout=30.0
        ) as pdf:
            images = pdf.select_images()
            image = images[0]
            image_id = image.internal_id
            bbox = image.position.bounding_rect
            original_ratio = bbox.width / bbox.height

            target_width = 150.0
            target_height = 75.0
            target_ratio = target_width / target_height  # 2.0

            result = image.scale_to(
                target_width, target_height, preserve_aspect_ratio=False
            )
            assert (
                result.success
            ), f"Scale without aspect ratio failed: {result.message}"

            # Verify aspect ratio changed from original
            assertions = PDFAssertions(pdf)
            new_width, new_height = assertions.get_image_size(image_id)
            new_ratio = new_width / new_height
            # The new ratio should be closer to target_ratio than original_ratio
            # (unless original was already 2.0)
            if abs(original_ratio - target_ratio) > 0.1:
                assert abs(new_ratio - target_ratio) < abs(
                    original_ratio - target_ratio
                ), (
                    f"Aspect ratio should change toward target. Original: {original_ratio:.3f}, "
                    f"New: {new_ratio:.3f}, Target: {target_ratio:.3f}"
                )


class TestImageRotate:
    def test_rotate_image_90_degrees(self):
        """Test rotating an image by 90 degrees - dimensions should swap."""
        base_url, token, pdf_path = _require_env_and_fixture("Showcase.pdf")

        with PDFDancer.open(
            pdf_path, token=token, base_url=base_url, timeout=30.0
        ) as pdf:
            images = pdf.select_images()
            image = images[0]
            image_id = image.internal_id
            bbox = image.position.bounding_rect
            original_width = bbox.width
            original_height = bbox.height

            result = image.rotate(90)
            assert result.success, f"Rotate 90 degrees failed: {result.message}"

            # After 90 degree rotation, width and height should swap
            assertions = PDFAssertions(pdf)
            assertions.assert_image_size(
                image_id, original_height, original_width, epsilon=2.0
            )

    def test_rotate_image_180_degrees(self):
        """Test rotating an image by 180 degrees - dimensions should stay same."""
        base_url, token, pdf_path = _require_env_and_fixture("Showcase.pdf")

        with PDFDancer.open(
            pdf_path, token=token, base_url=base_url, timeout=30.0
        ) as pdf:
            images = pdf.select_images()
            image = images[0]
            image_id = image.internal_id
            bbox = image.position.bounding_rect
            original_width = bbox.width
            original_height = bbox.height

            result = image.rotate(180)
            assert result.success, f"Rotate 180 degrees failed: {result.message}"

            # After 180 degree rotation, dimensions should remain the same
            assertions = PDFAssertions(pdf)
            assertions.assert_image_size(
                image_id, original_width, original_height, epsilon=2.0
            )

    def test_rotate_image_270_degrees(self):
        """Test rotating an image by 270 degrees - dimensions should swap."""
        base_url, token, pdf_path = _require_env_and_fixture("Showcase.pdf")

        with PDFDancer.open(
            pdf_path, token=token, base_url=base_url, timeout=30.0
        ) as pdf:
            images = pdf.select_images()
            image = images[0]
            image_id = image.internal_id
            bbox = image.position.bounding_rect
            original_width = bbox.width
            original_height = bbox.height

            result = image.rotate(270)
            assert result.success, f"Rotate 270 degrees failed: {result.message}"

            # After 270 degree rotation, width and height should swap
            assertions = PDFAssertions(pdf)
            assertions.assert_image_size(
                image_id, original_height, original_width, epsilon=2.0
            )


class TestImageFlip:
    def test_flip_image_horizontal(self):
        """Test flipping an image horizontally succeeds."""
        base_url, token, pdf_path = _require_env_and_fixture("Showcase.pdf")

        with PDFDancer.open(
            pdf_path, token=token, base_url=base_url, timeout=30.0
        ) as pdf:
            images = pdf.select_images()
            image = images[0]
            image_id = image.internal_id
            page_num = image.position.page_number

            result = image.flip(ImageFlipDirection.HORIZONTAL)
            assert result.success, f"Horizontal flip failed: {result.message}"

            # Verify image still exists
            assertions = PDFAssertions(pdf)
            image_after = assertions.get_image_by_id(image_id, page_num)
            assert image_after is not None

    def test_flip_image_vertical(self):
        """Test flipping an image vertically succeeds."""
        base_url, token, pdf_path = _require_env_and_fixture("Showcase.pdf")

        with PDFDancer.open(
            pdf_path, token=token, base_url=base_url, timeout=30.0
        ) as pdf:
            images = pdf.select_images()
            image = images[0]
            image_id = image.internal_id
            page_num = image.position.page_number

            result = image.flip(ImageFlipDirection.VERTICAL)
            assert result.success, f"Vertical flip failed: {result.message}"

            assertions = PDFAssertions(pdf)
            image_after = assertions.get_image_by_id(image_id, page_num)
            assert image_after is not None

    def test_flip_image_both(self):
        """Test flipping an image both directions succeeds."""
        base_url, token, pdf_path = _require_env_and_fixture("Showcase.pdf")

        with PDFDancer.open(
            pdf_path, token=token, base_url=base_url, timeout=30.0
        ) as pdf:
            images = pdf.select_images()
            image = images[0]
            image_id = image.internal_id
            page_num = image.position.page_number

            result = image.flip(ImageFlipDirection.BOTH)
            assert result.success, f"Both directions flip failed: {result.message}"

            assertions = PDFAssertions(pdf)
            image_after = assertions.get_image_by_id(image_id, page_num)
            assert image_after is not None

    def test_flip_preserves_aspect_ratio(self):
        """Test that flipping preserves aspect ratio."""
        base_url, token, pdf_path = _require_env_and_fixture("Showcase.pdf")

        with PDFDancer.open(
            pdf_path, token=token, base_url=base_url, timeout=30.0
        ) as pdf:
            images = pdf.select_images()
            image = images[0]
            image_id = image.internal_id
            bbox = image.position.bounding_rect
            original_ratio = bbox.width / bbox.height

            result = image.flip(ImageFlipDirection.HORIZONTAL)
            assert result.success

            assertions = PDFAssertions(pdf)
            assertions.assert_image_aspect_ratio(image_id, original_ratio, epsilon=0.1)


class TestImageOpacity:
    def test_set_image_opacity_half(self):
        """Test setting opacity to 50% succeeds."""
        base_url, token, pdf_path = _require_env_and_fixture("Showcase.pdf")

        with PDFDancer.open(
            pdf_path, token=token, base_url=base_url, timeout=30.0
        ) as pdf:
            images = pdf.select_images()
            image = images[0]
            image_id = image.internal_id
            page_num = image.position.page_number

            result = image.set_opacity(0.5)
            assert result.success, f"Set opacity failed: {result.message}"

            # Verify image still exists
            assertions = PDFAssertions(pdf)
            image_after = assertions.get_image_by_id(image_id, page_num)
            assert image_after is not None

    def test_set_image_opacity_fully_transparent(self):
        """Test setting image to fully transparent."""
        base_url, token, pdf_path = _require_env_and_fixture("Showcase.pdf")

        with PDFDancer.open(
            pdf_path, token=token, base_url=base_url, timeout=30.0
        ) as pdf:
            images = pdf.select_images()
            image = images[0]
            image_id = image.internal_id
            page_num = image.position.page_number

            result = image.set_opacity(0.0)
            assert result.success, f"Set fully transparent failed: {result.message}"

            assertions = PDFAssertions(pdf)
            image_after = assertions.get_image_by_id(image_id, page_num)
            assert image_after is not None

    def test_set_image_opacity_fully_opaque(self):
        """Test setting image to fully opaque."""
        base_url, token, pdf_path = _require_env_and_fixture("Showcase.pdf")

        with PDFDancer.open(
            pdf_path, token=token, base_url=base_url, timeout=30.0
        ) as pdf:
            images = pdf.select_images()
            image = images[0]
            image_id = image.internal_id
            page_num = image.position.page_number

            result = image.set_opacity(1.0)
            assert result.success, f"Set fully opaque failed: {result.message}"

            assertions = PDFAssertions(pdf)
            image_after = assertions.get_image_by_id(image_id, page_num)
            assert image_after is not None

    def test_set_image_opacity_preserves_aspect_ratio(self):
        """Test that setting opacity preserves aspect ratio."""
        base_url, token, pdf_path = _require_env_and_fixture("Showcase.pdf")

        with PDFDancer.open(
            pdf_path, token=token, base_url=base_url, timeout=30.0
        ) as pdf:
            images = pdf.select_images()
            image = images[0]
            image_id = image.internal_id
            bbox = image.position.bounding_rect
            original_ratio = bbox.width / bbox.height

            result = image.set_opacity(0.5)
            assert result.success

            assertions = PDFAssertions(pdf)
            assertions.assert_image_aspect_ratio(image_id, original_ratio, epsilon=0.1)

    def test_set_image_opacity_invalid_above_1_raises_error(self):
        """Test that opacity > 1.0 raises ValidationException."""
        base_url, token, pdf_path = _require_env_and_fixture("Showcase.pdf")

        with PDFDancer.open(
            pdf_path, token=token, base_url=base_url, timeout=30.0
        ) as pdf:
            images = pdf.select_images()
            image = images[0]

            with pytest.raises(ValidationException):
                image.set_opacity(1.5)

    def test_set_image_opacity_invalid_below_0_raises_error(self):
        """Test that opacity < 0.0 raises ValidationException."""
        base_url, token, pdf_path = _require_env_and_fixture("Showcase.pdf")

        with PDFDancer.open(
            pdf_path, token=token, base_url=base_url, timeout=30.0
        ) as pdf:
            images = pdf.select_images()
            image = images[0]

            with pytest.raises(ValidationException):
                image.set_opacity(-0.1)


class TestImageCrop:
    def test_crop_image_reduces_size(self):
        """Test that cropping reduces image dimensions."""
        base_url, token, pdf_path = _require_env_and_fixture("Showcase.pdf")

        with PDFDancer.open(
            pdf_path, token=token, base_url=base_url, timeout=30.0
        ) as pdf:
            images = pdf.select_images()
            image = images[0]
            image_id = image.internal_id
            bbox = image.position.bounding_rect
            original_width = bbox.width
            original_height = bbox.height

            crop_amount = 10
            result = image.crop(
                left=crop_amount, top=crop_amount, right=crop_amount, bottom=crop_amount
            )
            assert result.success, f"Crop failed: {result.message}"

            # Verify dimensions decreased
            assertions = PDFAssertions(pdf)
            assertions.assert_image_width_changed(image_id, original_width, epsilon=5.0)
            assertions.assert_image_height_changed(
                image_id, original_height, epsilon=5.0
            )

    def test_crop_image_from_left_only(self):
        """Test cropping from left edge only reduces width."""
        base_url, token, pdf_path = _require_env_and_fixture("Showcase.pdf")

        with PDFDancer.open(
            pdf_path, token=token, base_url=base_url, timeout=30.0
        ) as pdf:
            images = pdf.select_images()
            image = images[0]
            image_id = image.internal_id
            bbox = image.position.bounding_rect
            original_width = bbox.width

            result = image.crop(left=20)
            assert result.success, f"Left crop failed: {result.message}"

            # Width should decrease
            assertions = PDFAssertions(pdf)
            assertions.assert_image_width_changed(image_id, original_width, epsilon=5.0)

    def test_crop_image_from_top_only(self):
        """Test cropping from top edge only reduces height."""
        base_url, token, pdf_path = _require_env_and_fixture("Showcase.pdf")

        with PDFDancer.open(
            pdf_path, token=token, base_url=base_url, timeout=30.0
        ) as pdf:
            images = pdf.select_images()
            image = images[0]
            image_id = image.internal_id
            bbox = image.position.bounding_rect
            original_height = bbox.height

            result = image.crop(top=20)
            assert result.success, f"Top crop failed: {result.message}"

            # Height should decrease
            assertions = PDFAssertions(pdf)
            assertions.assert_image_height_changed(
                image_id, original_height, epsilon=5.0
            )


class TestImageReplace:
    def test_replace_image_with_new_image(self):
        """Test replacing an image with a new image file."""
        base_url, token, pdf_path = _require_env_and_fixture("Showcase.pdf")

        with PDFDancer.open(
            pdf_path, token=token, base_url=base_url, timeout=30.0
        ) as pdf:
            images = pdf.select_images()
            original_count = len(images)
            assert original_count > 0

            image = images[0]
            image_id = image.internal_id
            page_num = image.position.page_number

            # Load a replacement image
            img_path = (
                Path(__file__).resolve().parent.parent / "fixtures" / "logo-80.png"
            )
            new_image = Image(data=img_path.read_bytes())

            result = image.replace(new_image)
            assert result.success, f"Replace image failed: {result.message}"

            # Verify image count is preserved on the page
            assertions = PDFAssertions(pdf)
            assertions.assert_number_of_images(
                len(pdf.page(page_num).select_images()), page_num
            )

    def test_replace_image_preserves_position(self):
        """Test that replacing an image keeps it at approximately the same position."""
        base_url, token, pdf_path = _require_env_and_fixture("Showcase.pdf")

        with PDFDancer.open(
            pdf_path, token=token, base_url=base_url, timeout=30.0
        ) as pdf:
            images = pdf.select_images()
            image = images[0]
            original_x = image.position.x()
            original_y = image.position.y()
            page_num = image.position.page_number

            img_path = (
                Path(__file__).resolve().parent.parent / "fixtures" / "logo-80.png"
            )
            new_image = Image(data=img_path.read_bytes())

            result = image.replace(new_image)
            assert result.success, f"Replace image failed: {result.message}"

            # Verify image still exists at original position
            assertions = PDFAssertions(pdf)
            assertions.assert_image_at(original_x, original_y, page_num)


class TestImageTransformChaining:
    def test_scale_then_rotate(self):
        """Test chaining scale and rotate operations."""
        base_url, token, pdf_path = _require_env_and_fixture("Showcase.pdf")

        with PDFDancer.open(
            pdf_path, token=token, base_url=base_url, timeout=30.0
        ) as pdf:
            images = pdf.select_images()
            image = images[0]
            image_id = image.internal_id
            bbox = image.position.bounding_rect
            original_width = bbox.width
            original_height = bbox.height

            # Scale to half
            result1 = image.scale(0.5)
            assert result1.success

            # Then rotate 90 degrees
            # Need to re-select the image after first transform
            images = pdf.select_images()
            image = next(i for i in images if i.internal_id == image_id)
            result2 = image.rotate(90)
            assert result2.success

            # After scale(0.5) + rotate(90):
            # Expected: width = original_height * 0.5, height = original_width * 0.5
            assertions = PDFAssertions(pdf)
            expected_width = original_height * 0.5
            expected_height = original_width * 0.5
            assertions.assert_image_size(
                image_id, expected_width, expected_height, epsilon=3.0
            )

    def test_multiple_rotations(self):
        """Test that 4x 90 degree rotations return to original dimensions."""
        base_url, token, pdf_path = _require_env_and_fixture("Showcase.pdf")

        with PDFDancer.open(
            pdf_path, token=token, base_url=base_url, timeout=30.0
        ) as pdf:
            images = pdf.select_images()
            image = images[0]
            image_id = image.internal_id
            bbox = image.position.bounding_rect
            original_width = bbox.width
            original_height = bbox.height

            # Rotate 90 degrees 4 times
            for _ in range(4):
                images = pdf.select_images()
                image = next(i for i in images if i.internal_id == image_id)
                result = image.rotate(90)
                assert result.success

            # Should be back to original dimensions
            assertions = PDFAssertions(pdf)
            assertions.assert_image_size(
                image_id, original_width, original_height, epsilon=2.0
            )
