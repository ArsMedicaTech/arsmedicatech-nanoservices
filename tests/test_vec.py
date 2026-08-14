"""
Unit tests for amt_nano.db.vec Vec helpers.
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from amt_nano.db.vec import Vec


@pytest.mark.unit
def test_embed_one_uses_configured_model():
    """embed_one returns the embedding for a single string."""
    mock_client = MagicMock()
    mock_resp = MagicMock()
    mock_resp.data = [MagicMock(embedding=[0.1, 0.2, 0.3])]
    mock_client.embeddings.create = AsyncMock(return_value=mock_resp)

    vec = Vec(openai_client=mock_client, embed_model="text-embedding-3-small")
    result = asyncio.run(vec.embed_one("hello"))

    assert result == [0.1, 0.2, 0.3]
    mock_client.embeddings.create.assert_awaited_once_with(
        model="text-embedding-3-small", input=["hello"]
    )


@pytest.mark.unit
def test_embed_one_requires_client():
    """embed_one raises ValueError when no OpenAI client is configured."""
    vec = Vec(openai_client=None)
    with pytest.raises(ValueError, match="OpenAI client"):
        asyncio.run(vec.embed_one("hello"))


@pytest.mark.unit
@patch("amt_nano.db.vec.AsyncSurreal")
def test_get_context_records_returns_full_records(mock_surreal_cls):
    """get_context_records projects requested fields and supports a where clause."""
    mock_db = MagicMock()
    mock_db.connect = AsyncMock()
    mock_db.signin = AsyncMock()
    mock_db.use = AsyncMock()
    mock_db.close = AsyncMock()
    mock_db.query = AsyncMock(
        return_value=[
            {"id": "structured_content:bp", "title": "BP", "tags": ["cardio"]},
            {"id": "structured_content:hr", "title": "HR", "tags": ["cardio"]},
        ]
    )
    mock_surreal_cls.return_value = mock_db

    mock_client = MagicMock()
    mock_resp = MagicMock()
    mock_resp.data = [MagicMock(embedding=[0.5] * 1536)]
    mock_client.embeddings.create = AsyncMock(return_value=mock_resp)

    vec = Vec(openai_client=mock_client, surrealdb_table="structured_content")
    result = asyncio.run(
        vec.get_context_records(
            question="blood pressure",
            k=4,
            table_name="structured_content",
            fields="id, title, tags",
            where="scope = 'global'",
        )
    )

    assert result is not None
    assert len(result) == 2
    assert result[0]["title"] == "BP"

    mock_db.connect.assert_awaited_once()
    mock_db.signin.assert_awaited_once()
    mock_db.use.assert_awaited_once()
    mock_db.close.assert_awaited_once()

    query_arg = mock_db.query.await_args[0][0]
    assert "SELECT id, title, tags FROM structured_content" in query_arg
    assert "embedding <|4, COSINE|> $vec" in query_arg
    assert "AND (scope = 'global')" in query_arg


@pytest.mark.unit
@patch("amt_nano.db.vec.AsyncSurreal")
def test_get_context_records_returns_none_on_db_error(mock_surreal_cls):
    """get_context_records returns None when SurrealDB raises an exception."""
    mock_db = MagicMock()
    mock_db.connect = AsyncMock()
    mock_db.signin = AsyncMock()
    mock_db.use = AsyncMock()
    mock_db.close = AsyncMock()
    mock_db.query = AsyncMock(side_effect=RuntimeError("connection lost"))
    mock_surreal_cls.return_value = mock_db

    mock_client = MagicMock()
    mock_resp = MagicMock()
    mock_resp.data = [MagicMock(embedding=[0.5] * 1536)]
    mock_client.embeddings.create = AsyncMock(return_value=mock_resp)

    vec = Vec(openai_client=mock_client)
    result = asyncio.run(vec.get_context_records("question"))

    assert result is None
    mock_db.close.assert_awaited_once()


@pytest.mark.unit
@patch("amt_nano.db.vec.AsyncSurreal")
def test_get_context_projects_text_from_records(mock_surreal_cls):
    """get_context delegates to get_context_records and extracts text values."""
    mock_db = MagicMock()
    mock_db.connect = AsyncMock()
    mock_db.signin = AsyncMock()
    mock_db.use = AsyncMock()
    mock_db.close = AsyncMock()
    mock_db.query = AsyncMock(
        return_value=[
            {"text": "first context"},
            {"text": "second context"},
        ]
    )
    mock_surreal_cls.return_value = mock_db

    mock_client = MagicMock()
    mock_resp = MagicMock()
    mock_resp.data = [MagicMock(embedding=[0.5] * 1536)]
    mock_client.embeddings.create = AsyncMock(return_value=mock_resp)

    vec = Vec(openai_client=mock_client)
    result = asyncio.run(vec.get_context("question", k=2, table_name="knowledge"))

    assert result == ["first context", "second context"]

    query_arg = mock_db.query.await_args[0][0]
    assert "SELECT text FROM knowledge" in query_arg
    assert "embedding <|2, COSINE|> $vec" in query_arg
