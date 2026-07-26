import asyncio
import os
from pathlib import Path

import pytest_asyncio
from httpx import AsyncClient

API_URL = os.environ.get("API_URL", "http://localhost:8000")
FIXTURES = Path(__file__).parent / "fixtures"


def load(name):
    return (FIXTURES / name).read_bytes()


@pytest_asyncio.fixture
async def http_client():
    async with AsyncClient(base_url=API_URL, timeout=60.0) as client:
        yield client


async def upload(http_client, filename, content=None, content_type="application/pdf"):
    data = content if content is not None else load(filename)
    files = {"file": (filename, data, content_type)}
    return await http_client.post("/documents", files=files)


async def wait_for_terminal(http_client, doc_id, timeout=30):
    for _ in range(timeout):
        await asyncio.sleep(1)
        resp = await http_client.get(f"/documents/{doc_id}/status")
        assert resp.status_code == 200
        status = resp.json()["status"]
        if status in ("success", "failed"):
            return status
    raise TimeoutError(f"document {doc_id} did not reach a terminal state in {timeout}s")


async def upload_and_wait(http_client, filename, content=None):
    resp = await upload(http_client, filename, content=content)
    assert resp.status_code == 200
    doc_id = resp.json()["id"]
    status = await wait_for_terminal(http_client, doc_id)
    result = await http_client.get(f"/documents/{doc_id}/result")
    assert result.status_code == 200
    return result.json(), status
