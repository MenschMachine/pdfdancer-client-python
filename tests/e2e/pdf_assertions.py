import re
import tempfile
import zlib
from typing import Dict, List, Optional, Tuple

import pytest

from pdfdancer import Bezier, Color, Line, Orientation, PathSegment, PDFDancer, Point


class PDFAssertions(object):

    # noinspection PyProtectedMember
    def __init__(self, pdf_dancer: PDFDancer):
        token = pdf_dancer._token
        base_url = pdf_dancer._base_url
        # Create a temporary file
        with tempfile.NamedTemporaryFile(
                delete=False, suffix=".pdf", mode="w+t"
        ) as temp_file:
            pdf_dancer.save(temp_file.name)
            print(f"Saving PDF file to {temp_file.name}")
        self.pdf = PDFDancer.open(temp_file.name, token=token, base_url=base_url)
        self._saved_pdf_path = temp_file.name
        self._draw_events_cache = {}

    def assert_text_has_color(self, text, color: Color, page=1):
        self.assert_textline_has_color(text, color, page)

        paragraphs = self.pdf.page(page).select_paragraphs_matching(text)
        assert len(paragraphs) == 1, f"Expected 1 paragraph but got {len(paragraphs)}"
        reference = paragraphs[0].object_ref()
        assert text in reference.get_text()
        assert color == reference.get_color(), f"{color} != {reference.get_color()}"
        return self

    def assert_text_has_font(self, text, font_name, font_size, page=1):
        self.assert_textline_has_font(text, font_name, font_size, page)

        paragraphs = self.pdf.page(page).select_paragraphs_matching(f".*{text}.*")
        assert len(paragraphs) == 1, f"Expected 1 paragraph but got {len(paragraphs)}"
        reference = paragraphs[0].object_ref()
        assert (
                font_name == reference.get_font_name()
        ), f"Expected {reference.get_font_name()} to match {font_name}"
        assert font_size == reference.get_font_size()

        return self

    def assert_paragraph_is_at(
            self, text, x, y, page=1, epsilon=2
    ):  # adjust for baseline vs bounding box differences
        paragraphs = self.pdf.page(page).select_paragraphs_matching(f".*{text}.*")
        assert len(paragraphs) == 1, f"Expected 1 paragraph but got {len(paragraphs)}"
        reference = paragraphs[0].object_ref()

        assert reference.get_position().x() == pytest.approx(
            x, rel=epsilon, abs=epsilon
        ), f"{x} != {reference.get_position().x()}"
        assert reference.get_position().y() == pytest.approx(
            y, rel=epsilon, abs=epsilon
        ), f"{y} != {reference.get_position().y()}"

        paragraph_by_position = self.pdf.page(page).select_paragraphs_at(x, y)
        if len(paragraph_by_position) == 0:
            raise AssertionError("No such paragraph found")
        assert paragraphs[0] == paragraph_by_position[0]
        return self

    def assert_text_has_font_matching(self, text, font_name, font_size, page=1):
        self.assert_textline_has_font_matching(text, font_name, font_size, page)

        paragraphs = self.pdf.page(page).select_paragraphs_matching(f".*{text}.*")
        assert len(paragraphs) == 1, f"Expected 1 paragraph but got {len(paragraphs)}"
        reference = paragraphs[0].object_ref()
        assert (
                font_name in reference.get_font_name()
        ), f"Expected {reference.get_font_name()} to match {font_name}"
        assert font_size == reference.get_font_size()
        return self

    def assert_textline_has_color(self, text: str, color: Color, page=1):
        lines = self.pdf.page(page).select_text_lines_matching(text)
        assert len(lines) == 1, f"Expected 1 line but got {len(lines)}"
        reference = lines[0].object_ref()
        assert color == reference.get_color(), f"{color} != {reference.get_color()}"
        assert text in reference.get_text()
        return self

    def assert_textline_has_font(
            self, text: str, font_name: str, font_size: int, page=1
    ):
        lines = self.pdf.page(page).select_text_lines_starting_with(text)
        assert len(lines) == 1, f"Expected 1 line but got {len(lines)}"
        reference = lines[0].object_ref()
        assert (
                font_name == reference.get_font_name()
        ), f"Expected {font_name} but got {reference.get_font_name()}"
        assert (
                font_size == reference.get_font_size()
        ), f"{font_size} != {reference.get_font_size()}"
        return self

    def assert_textline_has_font_matching(
            self, text, font_name: str, font_size: int, page=1
    ):
        lines = self.pdf.page(page).select_text_lines_starting_with(text)
        assert len(lines) == 1, f"Expected 1 line but got {len(lines)}"
        reference = lines[0].object_ref()
        assert (
                font_name in reference.get_font_name()
        ), f"Expected {reference.get_font_name()} to match {font_name}"
        assert font_size == reference.get_font_size()
        return self

    def assert_textline_is_at(
            self, text: str, x: float, y: float, page=1, epsilon=1e-6
    ):
        lines = self.pdf.page(page).select_text_lines_starting_with(text)
        assert len(lines) == 1
        reference = lines[0].object_ref()
        assert reference.get_position().x() == pytest.approx(
            x, rel=epsilon, abs=epsilon
        ), f"{x} != {reference.get_position().x()}"
        assert reference.get_position().y() == pytest.approx(
            y, rel=epsilon, abs=epsilon
        ), f"{y} != {reference.get_position().y()}"

        by_position = self.pdf.page(page).select_text_lines_at(x, y)
        assert lines[0] == by_position[0]
        return self

    def assert_textline_does_not_exist(self, text, page=1):
        lines = self.pdf.page(page).select_text_lines_starting_with(text)
        assert len(lines) == 0
        return self

    def assert_textline_exists(self, text, page=1):
        lines = self.pdf.page(page).select_text_lines_matching(f".*{text}.*")
        assert len(lines) > 0
        return self

    def assert_paragraph_exists(self, text, page=1):
        paragraphs = self.pdf.page(page).select_paragraphs_starting_with(text)
        assert (
                len(paragraphs) > 0
        ), f"No paragraphs starting with {text} found on page {page}"
        return self

    def assert_number_of_pages(self, page_count: int):
        assert (
                len(self.pdf.pages()) == page_count
        ), f"Expected {page_count} pages, but got {len(self.pdf.pages())}"
        return self

    def get_pdf(self):
        return self.pdf

    @staticmethod
    def _matrix_multiply(
            left: Tuple[float, float, float, float, float, float],
            right: Tuple[float, float, float, float, float, float],
    ) -> Tuple[float, float, float, float, float, float]:
        a1, b1, c1, d1, e1, f1 = left
        a2, b2, c2, d2, e2, f2 = right
        return (
            a1 * a2 + b1 * c2,
            a1 * b2 + b1 * d2,
            c1 * a2 + d1 * c2,
            c1 * b2 + d1 * d2,
            e1 * a2 + f1 * c2 + e2,
            e1 * b2 + f1 * d2 + f2,
        )

    @staticmethod
    def _apply_matrix(
            matrix: Tuple[float, float, float, float, float, float],
            x: float,
            y: float,
    ) -> Tuple[float, float]:
        a, b, c, d, e, f = matrix
        return a * x + c * y + e, b * x + d * y + f

    @staticmethod
    def _bbox_area(bbox: Tuple[float, float, float, float]) -> float:
        return max(0.0, bbox[2] - bbox[0]) * max(0.0, bbox[3] - bbox[1])

    @staticmethod
    def _bbox_contains_point(
            bbox: Tuple[float, float, float, float],
            x: float,
            y: float,
            tolerance: float = 0.5,
    ) -> bool:
        return (
                bbox[0] - tolerance <= x <= bbox[2] + tolerance
                and bbox[1] - tolerance <= y <= bbox[3] + tolerance
        )

    @staticmethod
    def _bbox_intersection_area(
            a: Tuple[float, float, float, float],
            b: Tuple[float, float, float, float],
    ) -> float:
        left = max(a[0], b[0])
        bottom = max(a[1], b[1])
        right = min(a[2], b[2])
        top = min(a[3], b[3])
        if left >= right or bottom >= top:
            return 0.0
        return (right - left) * (top - bottom)

    @staticmethod
    def _bbox_center_distance(
            bbox: Tuple[float, float, float, float], x: float, y: float
    ) -> float:
        center_x = (bbox[0] + bbox[2]) / 2.0
        center_y = (bbox[1] + bbox[3]) / 2.0
        return ((center_x - x) ** 2 + (center_y - y) ** 2) ** 0.5

    @staticmethod
    def _is_word_char(char: Optional[str]) -> bool:
        return bool(char and re.match(r"[A-Za-z0-9_]", char))

    @classmethod
    def _is_token_boundary(cls, text: str, index: int, token_length: int) -> bool:
        before = text[index - 1] if index > 0 else None
        after = text[index + token_length] if index + token_length < len(text) else None
        return not cls._is_word_char(before) and not cls._is_word_char(after)

    @classmethod
    def _index_of_token(cls, text: str, token: str, from_index: int = 0) -> int:
        index = text.find(token, from_index)
        while index != -1:
            if cls._is_token_boundary(text, index, len(token)):
                return index
            index = text.find(token, index + 1)
        return -1

    @staticmethod
    def _skip_line_break(text: str, index: int) -> int:
        if text.startswith("\r\n", index):
            return index + 2
        if index < len(text) and text[index] in ("\r", "\n"):
            return index + 1
        return index

    @staticmethod
    def _trim_trailing_line_breaks(text: str, start: int, end: int) -> int:
        cursor = end
        while cursor > start and text[cursor - 1] in ("\n", "\r"):
            cursor -= 1
        return cursor

    @staticmethod
    def _parse_integer_token(value: str) -> Optional[int]:
        match = re.match(r"^\s*([+-]?\d+)", value)
        if not match:
            return None
        parsed = int(match.group(1))
        return parsed if parsed >= 0 else None

    @classmethod
    def _resolve_length_from_raw_pdf(
            cls, raw_pdf: str, object_id: int
    ) -> Optional[int]:
        pattern = re.compile(
            rf"(^|[\r\n]){object_id}\s+\d+\s+obj\b([\s\S]*?)endobj", re.MULTILINE
        )
        match = pattern.search(raw_pdf)
        if not match:
            return None
        return cls._parse_integer_token(match.group(2))

    @classmethod
    def _extract_stream_length(
            cls,
            dictionary: str,
            parsed_objects: Dict[int, Dict[str, object]],
            raw_pdf: str,
    ) -> Optional[int]:
        length_ref_match = re.search(r"/Length\s+(\d+)\s+\d+\s+R\b", dictionary)
        if length_ref_match:
            length_object_id = int(length_ref_match.group(1))
            parsed = parsed_objects.get(length_object_id)
            if parsed:
                parsed_length = cls._parse_integer_token(str(parsed["dictionary"]))
                if parsed_length is not None:
                    return parsed_length
            return cls._resolve_length_from_raw_pdf(raw_pdf, length_object_id)

        direct_length_match = re.search(
            r"/Length\s+(\d+)\b(?!\s+\d+\s+R\b)", dictionary
        )
        if not direct_length_match:
            return None

        direct_length = int(direct_length_match.group(1))
        return direct_length if direct_length >= 0 else None

    @classmethod
    def _parse_pdf_objects(cls, pdf_bytes: bytes) -> Dict[int, Dict[str, object]]:
        raw_pdf = pdf_bytes.decode("latin1")
        objects: Dict[int, Dict[str, object]] = {}
        object_regex = re.compile(r"(^|[\r\n])(\d+)\s+(\d+)\s+obj\b", re.MULTILINE)

        for match in object_regex.finditer(raw_pdf):
            object_id = int(match.group(2))
            body_start = match.end()
            first_endobj_index = cls._index_of_token(raw_pdf, "endobj", body_start)
            if first_endobj_index == -1:
                break

            stream_index = cls._index_of_token(raw_pdf, "stream", body_start)
            if stream_index == -1 or stream_index > first_endobj_index:
                objects[object_id] = {
                    "object_id": object_id,
                    "dictionary": raw_pdf[body_start:first_endobj_index].strip(),
                }
                continue

            dictionary = raw_pdf[body_start:stream_index].strip()
            parsed: Dict[str, object] = {
                "object_id": object_id,
                "dictionary": dictionary,
            }
            stream_start = cls._skip_line_break(raw_pdf, stream_index + len("stream"))
            stream_length = cls._extract_stream_length(dictionary, objects, raw_pdf)

            endobj_index = first_endobj_index
            if stream_length is not None:
                stream_end = min(len(pdf_bytes), stream_start + stream_length)
                parsed["stream"] = pdf_bytes[stream_start:stream_end]

                endstream_search_start = cls._skip_line_break(raw_pdf, stream_end)
                endstream_index = cls._index_of_token(
                    raw_pdf, "endstream", endstream_search_start
                )
                if endstream_index != -1:
                    resolved_endobj_index = cls._index_of_token(
                        raw_pdf, "endobj", endstream_index + len("endstream")
                    )
                    if resolved_endobj_index != -1:
                        endobj_index = resolved_endobj_index
            else:
                endstream_index = cls._index_of_token(
                    raw_pdf, "endstream", stream_start
                )
                if endstream_index != -1:
                    stream_end = cls._trim_trailing_line_breaks(
                        raw_pdf, stream_start, endstream_index
                    )
                    parsed["stream"] = pdf_bytes[stream_start:stream_end]
                    resolved_endobj_index = cls._index_of_token(
                        raw_pdf, "endobj", endstream_index + len("endstream")
                    )
                    if resolved_endobj_index != -1:
                        endobj_index = resolved_endobj_index

            objects[object_id] = parsed
            object_regex.search(raw_pdf, endobj_index + len("endobj"))

        return objects

    @staticmethod
    def _extract_referenced_object_ids(value: str) -> List[int]:
        return [int(match.group(1)) for match in re.finditer(r"(\d+)\s+\d+\s+R", value)]

    @staticmethod
    def _parse_number_operands(
            operands: List[str], count: int
    ) -> Optional[List[float]]:
        if len(operands) < count:
            return None
        values = []
        for operand in operands[-count:]:
            try:
                values.append(float(operand))
            except ValueError:
                return None
        return values

    @staticmethod
    def _tokenize_content_stream(content: str) -> List[str]:
        tokens = []
        index = 0
        while index < len(content):
            char = content[index]

            if char.isspace():
                index += 1
                continue

            if char == "%":
                while index < len(content) and content[index] not in ("\n", "\r"):
                    index += 1
                continue

            if char == "(":
                start = index
                index += 1
                depth = 1
                while index < len(content) and depth > 0:
                    if content[index] == "\\":
                        index += 1
                        if index < len(content):
                            index += 1
                        continue
                    if content[index] == "(":
                        depth += 1
                    elif content[index] == ")":
                        depth -= 1
                    index += 1
                tokens.append(content[start:index])
                continue

            if char == "<":
                if index + 1 < len(content) and content[index + 1] == "<":
                    tokens.append("<<")
                    index += 2
                    continue

                end = index + 1
                while end < len(content) and content[end] != ">":
                    end += 1
                end = min(end + 1, len(content))
                tokens.append(content[index:end])
                index = end
                continue

            if char == ">":
                if index + 1 < len(content) and content[index + 1] == ">":
                    tokens.append(">>")
                    index += 2
                    continue
                tokens.append(char)
                index += 1
                continue

            if char in "[]{}":
                tokens.append(char)
                index += 1
                continue

            end = index
            while end < len(content) and (
                    not content[end].isspace() and content[end] not in "[]<>(){}"
            ):
                end += 1
            tokens.append(content[index:end])
            index = end

        return tokens

    @staticmethod
    def _decode_pdf_literal_string(token: str) -> Optional[str]:
        if len(token) < 2 or token[0] != "(" or token[-1] != ")":
            return None

        result = []
        index = 1
        end = len(token) - 1
        escapes = {
            "n": "\n",
            "r": "\r",
            "t": "\t",
            "b": "\b",
            "f": "\f",
            "(": "(",
            ")": ")",
            "\\": "\\",
        }

        while index < end:
            char = token[index]
            if char != "\\":
                result.append(char)
                index += 1
                continue

            index += 1
            if index >= end:
                break

            escaped = token[index]
            if escaped in ("\n", "\r"):
                if escaped == "\r" and index + 1 < end and token[index + 1] == "\n":
                    index += 1
                index += 1
                continue

            if escaped in escapes:
                result.append(escapes[escaped])
                index += 1
                continue

            if escaped.isdigit() and escaped < "8":
                octal_digits = [escaped]
                index += 1
                while (
                        index < end
                        and len(octal_digits) < 3
                        and token[index].isdigit()
                        and token[index] < "8"
                ):
                    octal_digits.append(token[index])
                    index += 1
                result.append(chr(int("".join(octal_digits), 8)))
                continue

            result.append(escaped)
            index += 1

        return "".join(result)

    @staticmethod
    def _decode_pdf_hex_string(token: str) -> Optional[str]:
        if (
                len(token) < 2
                or token[0] != "<"
                or token[-1] != ">"
                or token.startswith("<<")
        ):
            return None

        hex_data = re.sub(r"\s+", "", token[1:-1])
        if not hex_data:
            return ""
        if len(hex_data) % 2 == 1:
            hex_data += "0"
        try:
            return bytes.fromhex(hex_data).decode("latin1")
        except ValueError:
            return None

    @classmethod
    def _decode_pdf_text_token(cls, token: str) -> Optional[str]:
        decoded = cls._decode_pdf_literal_string(token)
        if decoded is not None:
            return decoded
        return cls._decode_pdf_hex_string(token)

    @classmethod
    def _extract_text_from_operands(cls, operands: List[str], operator: str) -> str:
        if operator in {"Tj", "'", '"'}:
            for operand in reversed(operands):
                decoded = cls._decode_pdf_text_token(operand)
                if decoded is not None:
                    return decoded
            return ""

        if operator == "TJ":
            parts = []
            for operand in operands:
                decoded = cls._decode_pdf_text_token(operand)
                if decoded is not None:
                    parts.append(decoded)
            return "".join(parts)

        return ""

    @staticmethod
    def _decode_stream_content(dictionary: str, stream: bytes) -> str:
        if re.search(r"/Filter[\s\S]*/FlateDecode", dictionary):
            try:
                return zlib.decompress(stream).decode("latin1")
            except zlib.error:
                try:
                    return zlib.decompress(stream, -zlib.MAX_WBITS).decode("latin1")
                except zlib.error:
                    return ""
        return stream.decode("latin1")

    @classmethod
    def _extract_page_object_ids_in_order(
            cls, objects: Dict[int, Dict[str, object]]
    ) -> List[int]:
        catalog = next(
            (
                obj
                for obj in objects.values()
                if re.search(r"/Type\s*/Catalog\b", str(obj["dictionary"]))
            ),
            None,
        )
        root_pages_match = (
            re.search(r"/Pages\s+(\d+)\s+\d+\s+R", str(catalog["dictionary"]))
            if catalog
            else None
        )
        root_pages_object_id = (
            int(root_pages_match.group(1)) if root_pages_match else None
        )
        if root_pages_object_id is None:
            root_pages = next(
                (
                    obj
                    for obj in objects.values()
                    if re.search(r"/Type\s*/Pages\b", str(obj["dictionary"]))
                       and not re.search(
                    r"/Parent\s+\d+\s+\d+\s+R", str(obj["dictionary"])
                )
                ),
                None,
            )
            root_pages_object_id = int(root_pages["object_id"]) if root_pages else None

        if root_pages_object_id is None:
            return []

        ordered = []
        visited = set()

        def walk(object_id: int):
            if object_id in visited:
                return
            visited.add(object_id)

            obj = objects.get(object_id)
            if not obj:
                return

            dictionary = str(obj["dictionary"])
            if re.search(r"/Type\s*/Page\b", dictionary) and not re.search(
                    r"/Type\s*/Pages\b", dictionary
            ):
                ordered.append(object_id)
                return

            kids_match = re.search(r"/Kids\s*\[([\s\S]*?)]", dictionary)
            if not kids_match:
                return
            for child_ref in cls._extract_referenced_object_ids(kids_match.group(1)):
                walk(child_ref)

        walk(root_pages_object_id)
        return ordered

    def _extract_page_content_object_ids(
            self, objects: Dict[int, Dict[str, object]], page: int
    ) -> List[int]:
        ordered_page_object_ids = self._extract_page_object_ids_in_order(objects)
        fallback_page_object_ids = [
            int(obj["object_id"])
            for obj in sorted(objects.values(), key=lambda item: int(item["object_id"]))
            if re.search(r"/Type\s*/Page\b", str(obj["dictionary"]))
               and not re.search(r"/Type\s*/Pages\b", str(obj["dictionary"]))
        ]
        page_object_ids = ordered_page_object_ids or fallback_page_object_ids
        stream_object_ids = [
            int(obj["object_id"])
            for obj in objects.values()
            if obj.get("stream") is not None
        ]

        if not page_object_ids or page < 1 or page > len(page_object_ids):
            return stream_object_ids

        page_object = objects.get(page_object_ids[page - 1])
        if not page_object:
            return stream_object_ids

        contents_match = re.search(
            r"/Contents\s+(\[[\s\S]*?]|\d+\s+\d+\s+R)", str(page_object["dictionary"])
        )
        if not contents_match:
            return stream_object_ids

        referenced = self._extract_referenced_object_ids(contents_match.group(1))
        return referenced or stream_object_ids

    def _extract_page_draw_events(
            self, page: int
    ) -> Dict[str, List[Dict[str, object]]]:
        if page in self._draw_events_cache:
            return self._draw_events_cache[page]

        with open(self._saved_pdf_path, "rb") as fh:
            pdf_bytes = fh.read()

        objects = self._parse_pdf_objects(pdf_bytes)
        content_object_ids = self._extract_page_content_object_ids(objects, page)
        path_events: List[Dict[str, object]] = []
        image_events: List[Dict[str, object]] = []
        text_events: List[Dict[str, object]] = []
        paint_ops = {"S", "s", "f", "F", "f*", "B", "B*", "b", "b*"}
        path_ops = {"m", "l", "c", "v", "y", "h", "re"}
        state_stack = []
        has_clip = False
        pending_clip = False
        ctm = (1.0, 0.0, 0.0, 1.0, 0.0, 0.0)
        in_text = False
        text_matrix = (1.0, 0.0, 0.0, 1.0, 0.0, 0.0)
        text_line_matrix = (1.0, 0.0, 0.0, 1.0, 0.0, 0.0)
        text_leading = 0.0
        font_size = 12.0
        current_path_points: List[Tuple[float, float]] = []

        def add_path_point(raw_x: float, raw_y: float):
            current_path_points.append(self._apply_matrix(ctm, raw_x, raw_y))

        def move_text_to_next_line():
            nonlocal text_matrix, text_line_matrix
            translation = (1.0, 0.0, 0.0, 1.0, 0.0, -text_leading)
            text_line_matrix = self._matrix_multiply(translation, text_line_matrix)
            text_matrix = text_line_matrix

        for content_object_id in content_object_ids:
            obj = objects.get(content_object_id)
            if not obj or obj.get("stream") is None:
                continue

            decoded = self._decode_stream_content(str(obj["dictionary"]), obj["stream"])
            if not decoded:
                continue

            tokens = self._tokenize_content_stream(decoded)
            operands: List[str] = []

            for token in tokens:
                is_operator = bool(re.match(r"^[A-Za-z*'\"]+$", token))
                if not is_operator:
                    operands.append(token)
                    continue

                if token == "q":
                    state_stack.append(
                        {
                            "has_clip": has_clip,
                            "pending_clip": pending_clip,
                            "ctm": ctm,
                            "in_text": in_text,
                            "text_matrix": text_matrix,
                            "text_line_matrix": text_line_matrix,
                            "text_leading": text_leading,
                            "font_size": font_size,
                        }
                    )
                    operands = []
                    continue

                if token == "Q":
                    previous = state_stack.pop() if state_stack else None
                    if previous:
                        has_clip = previous["has_clip"]
                        pending_clip = previous["pending_clip"]
                        ctm = previous["ctm"]
                        in_text = previous["in_text"]
                        text_matrix = previous["text_matrix"]
                        text_line_matrix = previous["text_line_matrix"]
                        text_leading = previous["text_leading"]
                        font_size = previous["font_size"]
                    current_path_points = []
                    operands = []
                    continue

                if token == "cm":
                    values = self._parse_number_operands(operands, 6)
                    if values:
                        ctm = self._matrix_multiply(tuple(values), ctm)
                    operands = []
                    continue

                if token in {"W", "W*"}:
                    pending_clip = True
                    operands = []
                    continue

                if token == "n":
                    if pending_clip:
                        has_clip = True
                        pending_clip = False
                    current_path_points = []
                    operands = []
                    continue

                if token == "BT":
                    in_text = True
                    text_matrix = (1.0, 0.0, 0.0, 1.0, 0.0, 0.0)
                    text_line_matrix = (1.0, 0.0, 0.0, 1.0, 0.0, 0.0)
                    operands = []
                    continue

                if token == "ET":
                    in_text = False
                    operands = []
                    continue

                if token == "Tf":
                    values = self._parse_number_operands(operands, 1)
                    if values:
                        font_size = abs(values[0])
                    operands = []
                    continue

                if token == "Tm":
                    values = self._parse_number_operands(operands, 6)
                    if values:
                        text_matrix = tuple(values)
                        text_line_matrix = text_matrix
                    operands = []
                    continue

                if token in {"Td", "TD"}:
                    values = self._parse_number_operands(operands, 2)
                    if values:
                        translation = (1.0, 0.0, 0.0, 1.0, values[0], values[1])
                        text_line_matrix = self._matrix_multiply(
                            translation, text_line_matrix
                        )
                        text_matrix = text_line_matrix
                        if token == "TD":
                            text_leading = -values[1]
                    operands = []
                    continue

                if token == "T*":
                    move_text_to_next_line()
                    operands = []
                    continue

                if in_text and token in {"Tj", "TJ", "'", '"'}:
                    if token in {"'", '"'}:
                        move_text_to_next_line()

                    drawn_text = self._extract_text_from_operands(operands, token)
                    text_x, text_y = self._apply_matrix(
                        ctm, text_matrix[4], text_matrix[5]
                    )
                    padding = max(4.0, font_size * 0.5)
                    text_events.append(
                        {
                            "bbox": (
                                text_x - padding,
                                text_y - padding,
                                text_x + padding,
                                text_y + padding,
                            ),
                            "clipped": has_clip or pending_clip,
                            "paint_op": token,
                            "text": drawn_text,
                        }
                    )
                    operands = []
                    continue

                if token in path_ops:
                    if token in {"m", "l"}:
                        values = self._parse_number_operands(operands, 2)
                        if values:
                            add_path_point(values[0], values[1])
                    elif token == "c":
                        values = self._parse_number_operands(operands, 6)
                        if values:
                            add_path_point(values[0], values[1])
                            add_path_point(values[2], values[3])
                            add_path_point(values[4], values[5])
                    elif token in {"v", "y"}:
                        values = self._parse_number_operands(operands, 4)
                        if values:
                            add_path_point(values[0], values[1])
                            add_path_point(values[2], values[3])
                    elif token == "re":
                        values = self._parse_number_operands(operands, 4)
                        if values:
                            x, y, width, height = values
                            add_path_point(x, y)
                            add_path_point(x + width, y)
                            add_path_point(x + width, y + height)
                            add_path_point(x, y + height)
                    operands = []
                    continue

                if token in paint_ops:
                    if current_path_points:
                        xs = [point[0] for point in current_path_points]
                        ys = [point[1] for point in current_path_points]
                        path_events.append(
                            {
                                "bbox": (
                                    min(xs),
                                    min(ys),
                                    max(xs),
                                    max(ys),
                                ),
                                "clipped": has_clip or pending_clip,
                                "paint_op": token,
                            }
                        )
                    if pending_clip:
                        has_clip = True
                        pending_clip = False
                    current_path_points = []
                    operands = []
                    continue

                if token == "Do":
                    p0 = self._apply_matrix(ctm, 0.0, 0.0)
                    p1 = self._apply_matrix(ctm, 1.0, 0.0)
                    p2 = self._apply_matrix(ctm, 0.0, 1.0)
                    p3 = self._apply_matrix(ctm, 1.0, 1.0)
                    xs = [p0[0], p1[0], p2[0], p3[0]]
                    ys = [p0[1], p1[1], p2[1], p3[1]]
                    image_events.append(
                        {
                            "bbox": (
                                min(xs),
                                min(ys),
                                max(xs),
                                max(ys),
                            ),
                            "clipped": has_clip or pending_clip,
                            "name": operands[-1] if operands else None,
                        }
                    )
                    operands = []
                    continue

                operands = []

        events = {"paths": path_events, "images": image_events, "texts": text_events}
        self._draw_events_cache[page] = events
        return events

    def _find_path_clipping_state(self, internal_id: str, page: int) -> bool:
        paths = self.pdf.page(page).select_paths()
        path_ref = next(
            (path for path in paths if path.internal_id == internal_id), None
        )
        assert (
                path_ref is not None
        ), f"Path with ID {internal_id} not found on page {page}"

        x = path_ref.position.x()
        y = path_ref.position.y()
        assert x is not None and y is not None

        matches = [
            event
            for event in self._extract_page_draw_events(page)["paths"]
            if self._bbox_contains_point(event["bbox"], x, y)
        ]
        assert matches, f"No path draw event found near {internal_id} at ({x}, {y})"
        best = min(matches, key=lambda event: self._bbox_area(event["bbox"]))
        return bool(best["clipped"])

    def _find_image_clipping_state(self, internal_id: str, page: int) -> bool:
        image = self.get_image_by_id(internal_id, page)
        bbox = image.position.bounding_rect
        assert bbox is not None, f"Image {internal_id} has no bounding rect"

        target_bbox = (bbox.x, bbox.y, bbox.x + bbox.width, bbox.y + bbox.height)
        matches = [
            event
            for event in self._extract_page_draw_events(page)["images"]
            if self._bbox_intersection_area(target_bbox, event["bbox"]) > 0
        ]
        assert matches, f"No image draw event matched image {internal_id}"
        best = max(
            matches,
            key=lambda event: self._bbox_intersection_area(target_bbox, event["bbox"]),
        )
        return bool(best["clipped"])

    def _find_text_draw_event(
            self,
            text: str,
            page: int,
            x: float,
            y: float,
            target_bbox: Optional[Tuple[float, float, float, float]] = None,
    ):
        exact_matches = [
            event
            for event in self._extract_page_draw_events(page)["texts"]
            if event.get("text") == text
        ]
        assert exact_matches, f"No text draw event found for {text!r} on page {page}"

        if target_bbox is not None:
            bbox_matches = [
                event
                for event in exact_matches
                if self._bbox_intersection_area(target_bbox, event["bbox"]) > 0
            ]
            if bbox_matches:
                return max(
                    bbox_matches,
                    key=lambda event: self._bbox_intersection_area(
                        target_bbox, event["bbox"]
                    ),
                )

        point_matches = [
            event
            for event in exact_matches
            if self._bbox_contains_point(event["bbox"], x, y, tolerance=2.0)
        ]
        assert (
            point_matches
        ), f"No text draw event found for {text!r} near ({x}, {y}) on page {page}"
        return min(
            point_matches,
            key=lambda event: self._bbox_center_distance(event["bbox"], x, y),
        )

    def _find_textline_clipping_state(self, text: str, page: int) -> bool:
        line = self.pdf.page(page).select_text_line_starting_with(text)
        assert (
                line is not None
        ), f"No text line starting with {text!r} found on page {page}"

        x = line.position.x()
        y = line.position.y()
        assert x is not None and y is not None

        bbox = line.position.bounding_rect
        target_bbox = None
        if bbox is not None:
            target_bbox = (bbox.x, bbox.y, bbox.x + bbox.width, bbox.y + bbox.height)

        return bool(
            self._find_text_draw_event(text, page, x, y, target_bbox)["clipped"]
        )

    def _find_paragraph_clipping_state(self, text: str, page: int) -> bool:
        paragraph = self.pdf.page(page).select_paragraph_starting_with(text)
        assert paragraph is not None, f"No paragraph starting with {text!r} found"

        x = paragraph.position.x()
        y = paragraph.position.y()
        assert x is not None and y is not None

        bbox = paragraph.position.bounding_rect
        target_bbox = None
        if bbox is not None:
            target_bbox = (bbox.x, bbox.y, bbox.x + bbox.width, bbox.y + bbox.height)

        return bool(
            self._find_text_draw_event(text, page, x, y, target_bbox)["clipped"]
        )

    def assert_path_has_clipping(
            self, internal_id: str, page: int = 1
    ) -> "PDFAssertions":
        assert self._find_path_clipping_state(internal_id, page) is True
        return self

    def assert_path_has_no_clipping(
            self, internal_id: str, page: int = 1
    ) -> "PDFAssertions":
        assert self._find_path_clipping_state(internal_id, page) is False
        return self

    def assert_image_has_clipping(
            self, internal_id: str, page: int = 1
    ) -> "PDFAssertions":
        assert self._find_image_clipping_state(internal_id, page) is True
        return self

    def assert_image_has_no_clipping(
            self, internal_id: str, page: int = 1
    ) -> "PDFAssertions":
        assert self._find_image_clipping_state(internal_id, page) is False
        return self

    def assert_textline_has_clipping(self, text: str, page: int = 1) -> "PDFAssertions":
        assert self._find_textline_clipping_state(text, page) is True
        return self

    def assert_textline_has_no_clipping(
            self, text: str, page: int = 1
    ) -> "PDFAssertions":
        assert self._find_textline_clipping_state(text, page) is False
        return self

    def assert_paragraph_has_clipping(
            self, text: str, page: int = 1
    ) -> "PDFAssertions":
        assert self._find_paragraph_clipping_state(text, page) is True
        return self

    def assert_paragraph_has_no_clipping(
            self, text: str, page: int = 1
    ) -> "PDFAssertions":
        assert self._find_paragraph_clipping_state(text, page) is False
        return self

    def assert_path_has_bounds(
            self,
            internal_id: str,
            expected_width: float,
            expected_height: float,
            page=1,
            epsilon: float = 1.0,
    ) -> "PDFAssertions":
        paths = self.pdf.page(page).select_paths()
        ref = None
        for p in paths:
            if p.internal_id == internal_id:
                ref = p
                break
        assert ref is not None, f"Path with ID {internal_id} not found on page {page}"

        bbox = ref.position.bounding_rect
        assert bbox is not None, f"Path {internal_id} has no bounding rect"
        assert bbox.width == pytest.approx(
            expected_width, abs=epsilon
        ), f"Path {internal_id} width: expected {expected_width} but got {bbox.width}"
        assert bbox.height == pytest.approx(
            expected_height, abs=epsilon
        ), f"Path {internal_id} height: expected {expected_height} but got {bbox.height}"
        return self

    def assert_path_is_at(
            self, internal_id: str, x: float, y: float, page=1, epsilon=1e-6
    ):
        paths = self.pdf.page(page).select_paths_at(x, y)
        assert len(paths) == 1
        reference = paths[0].object_ref()
        assert (
                reference.internal_id == internal_id
        ), f"{internal_id} != {reference.internal_id}"
        assert reference.get_position().x() == pytest.approx(
            x, rel=epsilon, abs=epsilon
        ), f"{x} != {reference.get_position().x()}"
        assert reference.get_position().y() == pytest.approx(
            y, rel=epsilon, abs=epsilon
        ), f"{y} != {reference.get_position().y()}"

        return self

    def assert_no_path_at(self, x: float, y: float, page=1):
        paths = self.pdf.page(page).select_paths_at(x, y)
        assert len(paths) == 0
        return self

    def assert_number_of_paths(self, path_count: int, page=1):
        paths = self.pdf.page(page).select_paths()
        assert (
                len(paths) == path_count
        ), f"Expected {path_count} paths, but got {len(paths)}"
        return self

    def assert_number_of_images(self, image_count, page=1):
        images = self.pdf.page(page).select_images()
        assert (
                len(images) == image_count
        ), f"Expected {image_count} image but got {len(images)}"
        return self

    def assert_image_at(self, x: float, y: float, page=1):
        images = self.pdf.page(page).select_images_at(x, y)
        all_images = self.pdf.page(page).select_images()
        assert (
                len(images) == 1
        ), f"Expected 1 image but got {len(images)}, total images: {len(all_images)}, first pos: {all_images[0].position}"
        return self

    def assert_no_image_at(self, x: float, y: float, page=1) -> "PDFAssertions":
        images = self.pdf.page(page).select_images_at(x, y)
        assert (
                len(images) == 0
        ), f"Expected 0 image at {x}/{y} but got {len(images)}, {images[0].internal_id}"
        return self

    def assert_image_with_id_at(
            self, internal_id: str, x: float, y: float, page=1
    ) -> "PDFAssertions":
        images = self.pdf.page(page).select_images_at(x, y)
        assert len(images) == 1, f"Expected 1 image but got {len(images)}"
        assert (
                images[0].internal_id == internal_id
        ), f"{internal_id} != {images[0].internal_id}"
        return self

    def assert_total_number_of_elements(
            self, nr_of_elements, page_number=None
    ) -> "PDFAssertions":
        total = 0
        if page_number is None:
            for page in self.pdf.pages():
                total = total + len(page.select_elements())
        else:
            total = len(self.pdf.page(page_number).select_elements())
        assert (
                total == nr_of_elements
        ), f"Total number of elements differ, actual {total} != expected {nr_of_elements}"
        return self

    def assert_page_count(self, page_count: int) -> "PDFAssertions":
        assert page_count == len(self.pdf.pages())
        return self

    def assert_page_dimension(
            self,
            width: float,
            height: float,
            orientation: Optional[Orientation] = None,
            page_number=1,
    ) -> "PDFAssertions":
        page = self.pdf.page(page_number)
        assert width == page.size.width, f"{width} != {page.size.width}"
        assert height == page.size.height, f"{height} != {page.size.height}"
        if orientation is not None:
            actual_orientation = page.orientation
            if isinstance(actual_orientation, str):
                try:
                    actual_orientation = Orientation(actual_orientation.strip().upper())
                except ValueError:
                    pass
            assert (
                    orientation == actual_orientation
            ), f"{orientation} != {actual_orientation}"
        return self

    def assert_number_of_formxobjects(
            self, nr_of_formxobjects, page_number=1
    ) -> "PDFAssertions":
        assert nr_of_formxobjects == len(
            self.pdf.page(page_number).select_forms()
        ), f"Expected nr of formxobjects {nr_of_formxobjects} but got {len(self.pdf.page(page_number).select_forms())}"
        return self

    def assert_number_of_form_fields(
            self, nr_of_form_fields, page_number=1
    ) -> "PDFAssertions":
        assert nr_of_form_fields == len(
            self.pdf.page(page_number).select_form_fields()
        ), f"Expected nr of form fields {nr_of_form_fields} but got {len(self.pdf.page(page_number).select_form_fields())}"
        return self

    def assert_form_field_at(self, x: float, y: float, page=1) -> "PDFAssertions":
        form_fields = self.pdf.page(page).select_form_fields_at(x, y, 1)
        all_form_fields = self.pdf.page(page).select_form_fields()
        assert (
                len(form_fields) == 1
        ), f"Expected 1 form field but got {len(form_fields)}, total form_fields: {len(all_form_fields)}, first pos: {all_form_fields[0].position}"
        return self

    def assert_form_field_not_at(self, x: float, y: float, page=1) -> "PDFAssertions":
        form_fields = self.pdf.page(page).select_form_fields_at(x, y, 1)
        assert (
                len(form_fields) == 0
        ), f"Expected 0 form fields at {x}/{y} but got {len(form_fields)}, {form_fields[0].internal_id}"
        return self

    def assert_form_field_exists(
            self, field_name: str, page_number=1
    ) -> "PDFAssertions":
        form_fields = self.pdf.page(page_number).select_form_fields_by_name(field_name)
        assert (
                len(form_fields) == 1
        ), f"Expected 1 form field but got {len(form_fields)}"
        return self

    def assert_form_field_has_value(
            self, field_name: str, field_value: str, page_number=1
    ) -> "PDFAssertions":
        form_fields = self.pdf.page(page_number).select_form_fields_by_name(field_name)
        assert (
                len(form_fields) == 1
        ), f"Expected 1 form field but got {len(form_fields)}"
        assert (
                form_fields[0].value == field_value
        ), f"{form_fields[0].value} != {field_value}"
        return self

    # ========================================
    # Path-specific assertions
    # ========================================

    def assert_path_exists_at(
            self, x: float, y: float, page=1, tolerance: float = 5.0
    ) -> "PDFAssertions":
        """Assert that at least one path exists at the specified coordinates."""
        paths = self.pdf.page(page).select_paths_at(x, y, tolerance)
        assert (
                len(paths) > 0
        ), f"Expected at least 1 path at ({x}, {y}) on page {page}, but found none"
        return self

    def assert_path_count_at(
            self, count: int, x: float, y: float, page=1, tolerance: float = 5.0
    ) -> "PDFAssertions":
        """Assert exact number of paths at the specified coordinates."""
        paths = self.pdf.page(page).select_paths_at(x, y, tolerance)
        assert (
                len(paths) == count
        ), f"Expected {count} paths at ({x}, {y}) but got {len(paths)}"
        return self

    def assert_path_has_id(
            self, internal_id: str, x: float, y: float, page=1, tolerance: float = 5.0
    ) -> "PDFAssertions":
        """Assert that a path with specific ID exists at the coordinates."""
        paths = self.pdf.page(page).select_paths_at(x, y, tolerance)
        path_ids = [p.internal_id for p in paths]
        assert (
                internal_id in path_ids
        ), f"Expected path {internal_id} at ({x}, {y}), but found: {path_ids}"
        return self

    def assert_path_bounding_box(
            self,
            x: float,
            y: float,
            width: float,
            height: float,
            page=1,
            tolerance: float = 5.0,
            epsilon: float = 1.0,
    ) -> "PDFAssertions":
        """Assert that a path at the coordinates has the specified bounding box."""
        paths = self.pdf.page(page).select_paths_at(x, y, tolerance)
        assert len(paths) > 0, f"No paths found at ({x}, {y})"

        path = paths[0]
        bbox = path.position.bounding_rect
        assert bbox is not None, f"Path {path.internal_id} has no bounding rect"

        assert bbox.x == pytest.approx(
            x, abs=epsilon
        ), f"Bounding box x {bbox.x} != {x}"
        assert bbox.y == pytest.approx(
            y, abs=epsilon
        ), f"Bounding box y {bbox.y} != {y}"
        assert bbox.width == pytest.approx(
            width, abs=epsilon
        ), f"Bounding box width {bbox.width} != {width}"
        assert bbox.height == pytest.approx(
            height, abs=epsilon
        ), f"Bounding box height {bbox.height} != {height}"
        return self

    def get_path_at(self, x: float, y: float, page=1, tolerance: float = 5.0):
        """Helper to get the first path at coordinates for detailed inspection."""
        paths = self.pdf.page(page).select_paths_at(x, y, tolerance)
        assert len(paths) > 0, f"No paths found at ({x}, {y})"
        return paths[0]

    def assert_path_segment_count(
            self, expected_count: int, x: float, y: float, page=1, tolerance: float = 5.0
    ) -> "PDFAssertions":
        """Assert the number of segments in a path at the specified coordinates.

        Note: This requires the path to have detailed segment information loaded.
        """
        # This would work if the path object has path_segments loaded
        # For now, we'll document that this needs API support
        paths = self.pdf.page(page).select_paths_at(x, y, tolerance)
        assert len(paths) > 0, f"No paths found at ({x}, {y})"

        path = paths[0]
        # Note: This assumes the path has been enriched with segment data
        # In practice, this might require a special API call to get full path details
        if hasattr(path, "path_segments") and path.path_segments is not None:
            actual_count = len(path.path_segments)
            assert (
                    actual_count == expected_count
            ), f"Expected {expected_count} segments but got {actual_count}"
        else:
            pytest.skip("Path segment inspection requires full path data from API")
        return self

    def assert_line_segment_points(
            self, segment: Line, p0: Point, p1: Point, epsilon: float = 0.1
    ) -> "PDFAssertions":
        """Assert that a Line segment has the expected start and end points."""
        assert segment.get_p0() is not None, "Line segment p0 is None"
        assert segment.get_p1() is not None, "Line segment p1 is None"

        assert segment.get_p0().x == pytest.approx(
            p0.x, abs=epsilon
        ), f"Line p0.x {segment.get_p0().x} != {p0.x}"
        assert segment.get_p0().y == pytest.approx(
            p0.y, abs=epsilon
        ), f"Line p0.y {segment.get_p0().y} != {p0.y}"

        assert segment.get_p1().x == pytest.approx(
            p1.x, abs=epsilon
        ), f"Line p1.x {segment.get_p1().x} != {p1.x}"
        assert segment.get_p1().y == pytest.approx(
            p1.y, abs=epsilon
        ), f"Line p1.y {segment.get_p1().y} != {p1.y}"
        return self

    def assert_bezier_segment_points(
            self,
            segment: Bezier,
            p0: Point,
            p1: Point,
            p2: Point,
            p3: Point,
            epsilon: float = 0.1,
    ) -> "PDFAssertions":
        """Assert that a Bezier segment has the expected four control points."""
        assert segment.get_p0() is not None, "Bezier segment p0 is None"
        assert segment.get_p1() is not None, "Bezier segment p1 is None"
        assert segment.get_p2() is not None, "Bezier segment p2 is None"
        assert segment.get_p3() is not None, "Bezier segment p3 is None"

        for actual, expected, name in [
            (segment.get_p0(), p0, "p0"),
            (segment.get_p1(), p1, "p1"),
            (segment.get_p2(), p2, "p2"),
            (segment.get_p3(), p3, "p3"),
        ]:
            assert actual.x == pytest.approx(
                expected.x, abs=epsilon
            ), f"Bezier {name}.x {actual.x} != {expected.x}"
            assert actual.y == pytest.approx(
                expected.y, abs=epsilon
            ), f"Bezier {name}.y {actual.y} != {expected.y}"
        return self

    def assert_segment_stroke_color(
            self, segment: PathSegment, color: Color
    ) -> "PDFAssertions":
        """Assert that a path segment has the expected stroke color."""
        stroke_color = segment.get_stroke_color()
        assert stroke_color is not None, "Segment has no stroke color"
        assert (
                stroke_color.r == color.r
        ), f"Stroke color R {stroke_color.r} != {color.r}"
        assert (
                stroke_color.g == color.g
        ), f"Stroke color G {stroke_color.g} != {color.g}"
        assert (
                stroke_color.b == color.b
        ), f"Stroke color B {stroke_color.b} != {color.b}"
        assert (
                stroke_color.a == color.a
        ), f"Stroke color A {stroke_color.a} != {color.a}"
        return self

    def assert_segment_fill_color(
            self, segment: PathSegment, color: Color
    ) -> "PDFAssertions":
        """Assert that a path segment has the expected fill color."""
        fill_color = segment.get_fill_color()
        assert fill_color is not None, "Segment has no fill color"
        assert fill_color.r == color.r, f"Fill color R {fill_color.r} != {color.r}"
        assert fill_color.g == color.g, f"Fill color G {fill_color.g} != {color.g}"
        assert fill_color.b == color.b, f"Fill color B {fill_color.b} != {color.b}"
        assert fill_color.a == color.a, f"Fill color A {fill_color.a} != {color.a}"
        return self

    def assert_segment_stroke_width(
            self, segment: PathSegment, width: float, epsilon: float = 0.1
    ) -> "PDFAssertions":
        """Assert that a path segment has the expected stroke width."""
        stroke_width = segment.get_stroke_width()
        assert stroke_width is not None, "Segment has no stroke width"
        assert stroke_width == pytest.approx(
            width, abs=epsilon
        ), f"Stroke width {stroke_width} != {width}"
        return self

    def assert_segment_has_dash_pattern(
            self,
            segment: PathSegment,
            dash_array: List[float],
            dash_phase: float = 0.0,
            epsilon: float = 0.1,
    ) -> "PDFAssertions":
        """Assert that a path segment has the expected dash pattern."""
        actual_array = segment.get_dash_array()
        assert actual_array is not None, "Segment has no dash array"
        assert len(actual_array) == len(
            dash_array
        ), f"Dash array length {len(actual_array)} != {len(dash_array)}"

        for i, (actual, expected) in enumerate(zip(actual_array, dash_array)):
            assert actual == pytest.approx(
                expected, abs=epsilon
            ), f"Dash array[{i}] {actual} != {expected}"

        actual_phase = segment.get_dash_phase()
        if actual_phase is not None:
            assert actual_phase == pytest.approx(
                dash_phase, abs=epsilon
            ), f"Dash phase {actual_phase} != {dash_phase}"
        return self

    def assert_segment_is_solid(self, segment: PathSegment) -> "PDFAssertions":
        """Assert that a path segment has no dash pattern (solid line)."""
        dash_array = segment.get_dash_array()
        assert (
                dash_array is None or len(dash_array) == 0
        ), f"Expected solid line but found dash pattern: {dash_array}"
        return self

    def assert_segment_type(
            self, segment: PathSegment, expected_type: type
    ) -> "PDFAssertions":
        """Assert that a segment is of a specific type (Line or Bezier)."""
        assert isinstance(
            segment, expected_type
        ), f"Expected segment type {expected_type.__name__} but got {type(segment).__name__}"
        return self

    def assert_path_has_even_odd_fill(
            self, x: float, y: float, expected: bool, page=1, tolerance: float = 5.0
    ) -> "PDFAssertions":
        """Assert that a path has the expected even-odd fill rule setting."""
        paths = self.pdf.page(page).select_paths_at(x, y, tolerance)
        assert len(paths) > 0, f"No paths found at ({x}, {y})"

        path = paths[0]
        if hasattr(path, "even_odd_fill") and path.even_odd_fill is not None:
            assert (
                    path.even_odd_fill == expected
            ), f"Expected even_odd_fill={expected} but got {path.even_odd_fill}"
        else:
            pytest.skip(
                "Path even-odd fill inspection requires full path data from API"
            )
        return self

    # ========================================
    # Image-specific assertions
    # ========================================

    def get_image_by_id(self, internal_id: str, page: int = None):
        """Get an image by its internal ID.

        Args:
            internal_id: The internal ID of the image
            page: Optional page number to search on. If None, searches all pages.

        Returns:
            The ImageObject with the specified ID

        Raises:
            AssertionError if no image with the ID is found
        """
        if page is not None:
            images = self.pdf.page(page).select_images()
        else:
            images = self.pdf.select_images()

        for img in images:
            if img.internal_id == internal_id:
                return img

        assert False, f"No image found with internal_id={internal_id}"

    def get_image_at(self, x: float, y: float, page: int = 1, tolerance: float = 5.0):
        """Get the first image at the specified coordinates.

        Args:
            x: X coordinate
            y: Y coordinate
            page: Page number (1-based)
            tolerance: Coordinate tolerance

        Returns:
            The ImageObject at the coordinates

        Raises:
            AssertionError if no image is found at the coordinates
        """
        images = self.pdf.page(page).select_images_at(x, y, tolerance)
        assert len(images) > 0, f"No image found at ({x}, {y}) on page {page}"
        return images[0]

    def assert_image_size(
            self,
            internal_id: str,
            width: float,
            height: float,
            page: int = None,
            epsilon: float = 1.0,
    ) -> "PDFAssertions":
        """Assert that an image has the expected size (from bounding rect).

        Args:
            internal_id: The internal ID of the image
            width: Expected width
            height: Expected height
            page: Optional page number
            epsilon: Tolerance for float comparison
        """
        image = self.get_image_by_id(internal_id, page)
        bbox = image.position.bounding_rect

        assert bbox is not None, f"Image {internal_id} has no bounding rect"
        assert bbox.width == pytest.approx(
            width, abs=epsilon
        ), f"Image width {bbox.width} != expected {width}"
        assert bbox.height == pytest.approx(
            height, abs=epsilon
        ), f"Image height {bbox.height} != expected {height}"
        return self

    def assert_image_size_at(
            self,
            x: float,
            y: float,
            width: float,
            height: float,
            page: int = 1,
            tolerance: float = 5.0,
            epsilon: float = 1.0,
    ) -> "PDFAssertions":
        """Assert that an image at the coordinates has the expected size.

        Args:
            x: X coordinate
            y: Y coordinate
            width: Expected width
            height: Expected height
            page: Page number (1-based)
            tolerance: Coordinate tolerance for finding the image
            epsilon: Tolerance for size comparison
        """
        image = self.get_image_at(x, y, page, tolerance)
        bbox = image.position.bounding_rect

        assert bbox is not None, f"Image at ({x}, {y}) has no bounding rect"
        assert bbox.width == pytest.approx(
            width, abs=epsilon
        ), f"Image width {bbox.width} != expected {width}"
        assert bbox.height == pytest.approx(
            height, abs=epsilon
        ), f"Image height {bbox.height} != expected {height}"
        return self

    def assert_image_aspect_ratio(
            self,
            internal_id: str,
            expected_ratio: float,
            page: int = None,
            epsilon: float = 0.05,
    ) -> "PDFAssertions":
        """Assert that an image has the expected aspect ratio (width/height).

        Args:
            internal_id: The internal ID of the image
            expected_ratio: Expected width/height ratio
            page: Optional page number
            epsilon: Tolerance for ratio comparison
        """
        image = self.get_image_by_id(internal_id, page)
        bbox = image.position.bounding_rect

        assert bbox is not None, f"Image {internal_id} has no bounding rect"
        assert bbox.height > 0, f"Image height is 0, cannot compute aspect ratio"

        actual_ratio = bbox.width / bbox.height
        assert actual_ratio == pytest.approx(
            expected_ratio, abs=epsilon
        ), f"Image aspect ratio {actual_ratio:.3f} != expected {expected_ratio:.3f}"
        return self

    def assert_image_aspect_ratio_at(
            self,
            x: float,
            y: float,
            expected_ratio: float,
            page: int = 1,
            tolerance: float = 5.0,
            epsilon: float = 0.05,
    ) -> "PDFAssertions":
        """Assert that an image at coordinates has the expected aspect ratio.

        Args:
            x: X coordinate
            y: Y coordinate
            expected_ratio: Expected width/height ratio
            page: Page number (1-based)
            tolerance: Coordinate tolerance for finding the image
            epsilon: Tolerance for ratio comparison
        """
        image = self.get_image_at(x, y, page, tolerance)
        bbox = image.position.bounding_rect

        assert bbox is not None, f"Image at ({x}, {y}) has no bounding rect"
        assert bbox.height > 0, f"Image height is 0, cannot compute aspect ratio"

        actual_ratio = bbox.width / bbox.height
        assert actual_ratio == pytest.approx(
            expected_ratio, abs=epsilon
        ), f"Image aspect ratio {actual_ratio:.3f} != expected {expected_ratio:.3f}"
        return self

    def assert_image_width_changed(
            self,
            internal_id: str,
            original_width: float,
            page: int = None,
            epsilon: float = 1.0,
    ) -> "PDFAssertions":
        """Assert that an image's width has changed from the original.

        Args:
            internal_id: The internal ID of the image
            original_width: The original width before transformation
            page: Optional page number
            epsilon: Tolerance - actual width must differ by more than this
        """
        image = self.get_image_by_id(internal_id, page)
        bbox = image.position.bounding_rect

        assert bbox is not None, f"Image {internal_id} has no bounding rect"
        assert (
                abs(bbox.width - original_width) > epsilon
        ), f"Image width {bbox.width} has not changed significantly from original {original_width}"
        return self

    def assert_image_height_changed(
            self,
            internal_id: str,
            original_height: float,
            page: int = None,
            epsilon: float = 1.0,
    ) -> "PDFAssertions":
        """Assert that an image's height has changed from the original.

        Args:
            internal_id: The internal ID of the image
            original_height: The original height before transformation
            page: Optional page number
            epsilon: Tolerance - actual height must differ by more than this
        """
        image = self.get_image_by_id(internal_id, page)
        bbox = image.position.bounding_rect

        assert bbox is not None, f"Image {internal_id} has no bounding rect"
        assert (
                abs(bbox.height - original_height) > epsilon
        ), f"Image height {bbox.height} has not changed significantly from original {original_height}"
        return self

    def assert_image_scaled_by_factor(
            self,
            internal_id: str,
            original_width: float,
            original_height: float,
            scale_factor: float,
            page: int = None,
            epsilon: float = 2.0,
    ) -> "PDFAssertions":
        """Assert that an image has been scaled by the expected factor.

        Args:
            internal_id: The internal ID of the image
            original_width: The original width before scaling
            original_height: The original height before scaling
            scale_factor: The expected scale factor
            page: Optional page number
            epsilon: Tolerance for size comparison
        """
        image = self.get_image_by_id(internal_id, page)
        bbox = image.position.bounding_rect

        assert bbox is not None, f"Image {internal_id} has no bounding rect"

        expected_width = original_width * scale_factor
        expected_height = original_height * scale_factor

        assert bbox.width == pytest.approx(
            expected_width, abs=epsilon
        ), f"Scaled width {bbox.width} != expected {expected_width} (original {original_width} * {scale_factor})"
        assert bbox.height == pytest.approx(
            expected_height, abs=epsilon
        ), f"Scaled height {bbox.height} != expected {expected_height} (original {original_height} * {scale_factor})"
        return self

    def get_image_size(self, internal_id: str, page: int = None) -> tuple:
        """Get the width and height of an image.

        Args:
            internal_id: The internal ID of the image
            page: Optional page number

        Returns:
            Tuple of (width, height)
        """
        image = self.get_image_by_id(internal_id, page)
        bbox = image.position.bounding_rect
        assert bbox is not None, f"Image {internal_id} has no bounding rect"
        return (bbox.width, bbox.height)
