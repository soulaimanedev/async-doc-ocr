import pytest

from tests.conftest import upload, upload_and_wait


async def test_upload_pdf_queues_document(http_client):
    response = await upload(http_client, "sample.pdf")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "sample.pdf"
    assert data["status"] == "pending"
    assert "id" in data


@pytest.mark.parametrize("filename,content_type,content", [
    ("document.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", b"fake docx"),
    ("image.png",     "image/png",        b"\x89PNG fake"),
    ("image.jpg",     "image/jpeg",       b"\xff\xd8\xff fake"),
    ("data.json",     "application/json", b'{"key": "value"}'),
    ("plain.txt",     "text/plain",       b"just text"),
])
async def test_upload_rejects_non_pdf(http_client, filename, content_type, content):
    response = await upload(http_client, filename, content=content, content_type=content_type)
    assert response.status_code == 400
    assert "PDF" in response.json()["detail"]


async def test_upload_empty_file_fails(http_client):
    result, status = await upload_and_wait(http_client, "empty.pdf", content=b"")
    assert status == "failed"
    assert result["result"] is None
    assert result["message"] is not None


async def test_upload_corrupt_pdf_fails(http_client):
    result, status = await upload_and_wait(http_client, "corrupt.pdf", content=b"not a pdf at all")
    assert status == "failed"
    assert result["result"] is None
    assert result["message"] is not None


async def test_duplicate_filename_creates_separate_documents(http_client):
    r1 = await upload(http_client, "sample.pdf")
    r2 = await upload(http_client, "sample.pdf")
    assert r1.status_code == 200
    assert r2.status_code == 200
    assert r1.json()["id"] != r2.json()["id"]


async def test_list_documents_returns_paginated_results(http_client):
    await upload(http_client, "sample.pdf")
    await upload(http_client, "sample.pdf")

    response = await http_client.get("/documents?limit=1&offset=0")
    assert response.status_code == 200
    data = response.json()
    assert data["limit"] == 1
    assert data["offset"] == 0
    assert data["total"] >= 2
    assert len(data["items"]) == 1
    item = data["items"][0]
    assert "id" in item
    assert "name" in item
    assert "status" in item
    assert "created_at" in item
    assert "text_preview" in item
    assert "extracted_text" not in item


async def test_list_documents_text_preview_is_truncated(http_client):
    result, _ = await upload_and_wait(http_client, "heavy.pdf")
    assert result["status"] == "success"

    response = await http_client.get("/documents?limit=1&offset=0")
    item = response.json()["items"][0]
    if item["text_preview"] is not None:
        assert len(item["text_preview"]) <= 203  # 200 chars + "..."


async def test_list_documents_default_limit(http_client):
    response = await http_client.get("/documents")
    assert response.status_code == 200
    data = response.json()
    assert data["limit"] == 20
    assert len(data["items"]) <= 20


async def test_list_documents_invalid_limit_returns_422(http_client):
    response = await http_client.get("/documents?limit=999")
    assert response.status_code == 422


async def test_get_status_not_found(http_client):
    response = await http_client.get("/documents/999999/status")
    assert response.status_code == 404


async def test_get_result_not_found(http_client):
    response = await http_client.get("/documents/999999/result")
    assert response.status_code == 404


async def test_get_status_invalid_id_returns_422(http_client):
    response = await http_client.get("/documents/not-an-int/status")
    assert response.status_code == 422


async def test_get_result_invalid_id_returns_422(http_client):
    response = await http_client.get("/documents/not-an-int/result")
    assert response.status_code == 422
