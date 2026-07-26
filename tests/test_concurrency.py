import asyncio

from tests.conftest import upload_and_wait


async def test_concurrent_uploads(http_client):
    results = await asyncio.gather(
        upload_and_wait(http_client, "sample.pdf"),
        upload_and_wait(http_client, "multipage.pdf"),
        upload_and_wait(http_client, "numbers.pdf"),
    )
    assert "Hello OCR" in results[0][0]["result"]
    assert "First Page" in results[1][0]["result"]
    assert "Invoice 1234" in results[2][0]["result"]
