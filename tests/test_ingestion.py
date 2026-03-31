"""Tests for the ingestion pipeline (PDF parser, chunker, embedder)."""
from __future__ import annotations

import io
from pathlib import Path
from typing import List
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from src.ingestion.chunker import TextChunk, TextChunker
from src.ingestion.pdf_parser import PDFParser, ParsedPage


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_parsed_pages(texts: List[str], source: str = "test.pdf") -> List[ParsedPage]:
    """Helper: create ParsedPage objects from a list of strings."""
    return [
        ParsedPage(
            text=text,
            page_number=i + 1,
            source_file=source,
            lecture_title="Test Lecture",
        )
        for i, text in enumerate(texts)
    ]


@pytest.fixture
def sample_pages() -> List[ParsedPage]:
    long_text = " ".join(["word"] * 200)
    return _make_parsed_pages([long_text, "Short page content with more than ten chars."])


# ---------------------------------------------------------------------------
# PDFParser tests
# ---------------------------------------------------------------------------


class TestPDFParser:
    """Tests for PDFParser."""

    def test_extract_lecture_title_simple(self) -> None:
        """Filename stems with underscores/hyphens become space-separated titles."""
        parser = PDFParser()
        assert parser._extract_lecture_title("Introduction_to_ML.pdf") == "Introduction to ML"

    def test_extract_lecture_title_hyphens(self) -> None:
        parser = PDFParser()
        assert parser._extract_lecture_title("lecture-03-neural-nets.pdf") == "lecture 03 neural nets"

    def test_extract_lecture_title_mixed(self) -> None:
        parser = PDFParser()
        assert parser._extract_lecture_title("Deep_Learning-Overview.pdf") == "Deep Learning Overview"

    def test_extract_lecture_title_no_extension(self) -> None:
        parser = PDFParser()
        assert parser._extract_lecture_title("Algorithm_Design") == "Algorithm Design"

    def test_extract_lecture_title_plain(self) -> None:
        parser = PDFParser()
        assert parser._extract_lecture_title("MachineLearning.pdf") == "MachineLearning"

    def test_parse_pdf_file_not_found(self, tmp_path: Path) -> None:
        """Parsing a non-existent file should raise FileNotFoundError."""
        parser = PDFParser()
        with pytest.raises(FileNotFoundError):
            parser.parse_pdf(tmp_path / "nonexistent.pdf")

    @patch("fitz.open")
    def test_parse_pdf_bytes_returns_pages(self, mock_fitz_open: MagicMock) -> None:
        """parse_pdf_bytes should return a list of ParsedPage objects."""
        mock_doc = MagicMock()
        mock_doc.__len__ = MagicMock(return_value=2)

        page_texts = [
            "This is page one with enough text to pass the minimum length check.",
            "This is page two with sufficient content for the parser to include it.",
        ]

        def get_item(idx: int) -> MagicMock:
            mock_page = MagicMock()
            mock_page.get_text.return_value = page_texts[idx]
            return mock_page

        mock_doc.__getitem__ = MagicMock(side_effect=get_item)
        mock_fitz_open.return_value = mock_doc

        parser = PDFParser()
        pages = parser.parse_pdf_bytes(b"%PDF-dummy", "test_lecture.pdf")

        assert len(pages) == 2
        assert all(isinstance(p, ParsedPage) for p in pages)
        assert pages[0].page_number == 1
        assert pages[1].page_number == 2
        assert pages[0].lecture_title == "test lecture"
        assert pages[0].source_file == "test_lecture.pdf"

    @patch("fitz.open")
    def test_parse_pdf_bytes_skips_short_pages(self, mock_fitz_open: MagicMock) -> None:
        """Pages with fewer than 10 characters should be skipped."""
        mock_doc = MagicMock()
        mock_doc.__len__ = MagicMock(return_value=3)

        page_texts = ["Tiny", "Also short", "This page has more than ten characters and should be kept."]

        def get_item(idx: int) -> MagicMock:
            mock_page = MagicMock()
            mock_page.get_text.return_value = page_texts[idx]
            return mock_page

        mock_doc.__getitem__ = MagicMock(side_effect=get_item)
        mock_fitz_open.return_value = mock_doc

        parser = PDFParser()
        pages = parser.parse_pdf_bytes(b"%PDF-dummy", "lecture.pdf")

        assert len(pages) == 1
        assert pages[0].page_number == 3


# ---------------------------------------------------------------------------
# TextChunker tests
# ---------------------------------------------------------------------------


class TestTextChunker:
    """Tests for TextChunker."""

    def test_chunker_splits_long_text(self, sample_pages: List[ParsedPage]) -> None:
        """A long text should be split into multiple chunks."""
        chunker = TextChunker(chunk_size=100, chunk_overlap=10)
        chunks = chunker.chunk(sample_pages)

        assert len(chunks) > 1
        assert all(isinstance(c, TextChunk) for c in chunks)

    def test_chunker_preserves_metadata(self, sample_pages: List[ParsedPage]) -> None:
        """Each chunk should carry metadata from its source page."""
        chunker = TextChunker(chunk_size=100, chunk_overlap=10)
        chunks = chunker.chunk(sample_pages)

        source_files = {c.source_file for c in chunks}
        assert "test.pdf" in source_files

        lecture_titles = {c.lecture_title for c in chunks}
        assert "Test Lecture" in lecture_titles

    def test_chunker_unique_chunk_indices(self, sample_pages: List[ParsedPage]) -> None:
        """Every chunk must have a unique chunk_index."""
        chunker = TextChunker(chunk_size=100, chunk_overlap=10)
        chunks = chunker.chunk(sample_pages)

        indices = [c.chunk_index for c in chunks]
        assert len(indices) == len(set(indices)), "Chunk indices must be unique"

    def test_chunker_empty_input(self) -> None:
        """Chunking an empty list should return an empty list."""
        chunker = TextChunker()
        assert chunker.chunk([]) == []

    def test_chunker_chunk_size_respected(self) -> None:
        """No chunk should exceed chunk_size by more than a small margin."""
        chunk_size = 100
        chunker = TextChunker(chunk_size=chunk_size, chunk_overlap=10)
        long_text = "a" * 1000
        pages = _make_parsed_pages([long_text])
        chunks = chunker.chunk(pages)

        for chunk in chunks:
            # Allow slight overflow due to separator heuristics
            assert len(chunk.text) <= chunk_size + 20, f"Chunk too long: {len(chunk.text)}"


# ---------------------------------------------------------------------------
# DocumentEmbedder tests
# ---------------------------------------------------------------------------


class TestDocumentEmbedder:
    """Tests for DocumentEmbedder using a mocked SentenceTransformer."""

    @patch("sentence_transformers.SentenceTransformer")
    def test_embed_query_returns_list_of_float(self, mock_st_cls: MagicMock) -> None:
        """embed_query should return a plain list of floats."""
        dim = 384
        mock_model = MagicMock()
        mock_model.encode.return_value = np.random.rand(dim).astype(np.float32)
        mock_st_cls.return_value = mock_model

        from src.ingestion.embedder import DocumentEmbedder

        embedder = DocumentEmbedder(model_name="mock-model")
        result = embedder.embed_query("What is machine learning?")

        assert isinstance(result, list)
        assert len(result) == dim
        assert all(isinstance(v, float) for v in result)

    @patch("sentence_transformers.SentenceTransformer")
    def test_embed_chunks_returns_embedded_chunks(self, mock_st_cls: MagicMock) -> None:
        """embed_chunks should return EmbeddedChunk list with correct length."""
        dim = 384
        mock_model = MagicMock()
        mock_model.encode.return_value = np.random.rand(3, dim).astype(np.float32)
        mock_st_cls.return_value = mock_model

        from src.ingestion.embedder import DocumentEmbedder, EmbeddedChunk

        chunks = [
            TextChunk(
                text=f"Text {i}",
                source_file="test.pdf",
                page_number=1,
                chunk_index=i,
                lecture_title="Test",
            )
            for i in range(3)
        ]

        embedder = DocumentEmbedder(model_name="mock-model")
        embedded = embedder.embed_chunks(chunks)

        assert len(embedded) == 3
        assert all(isinstance(e, EmbeddedChunk) for e in embedded)
        assert all(len(e.embedding) == dim for e in embedded)

    @patch("sentence_transformers.SentenceTransformer")
    def test_embed_empty_chunks(self, mock_st_cls: MagicMock) -> None:
        """Embedding an empty list should return an empty list."""
        mock_st_cls.return_value = MagicMock()
        from src.ingestion.embedder import DocumentEmbedder

        embedder = DocumentEmbedder(model_name="mock-model")
        result = embedder.embed_chunks([])
        assert result == []
