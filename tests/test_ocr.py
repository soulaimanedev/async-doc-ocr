from tests.conftest import upload_and_wait


async def test_ocr_single_page(http_client):
    result, status = await upload_and_wait(http_client, "sample.pdf")
    assert status == "success"
    assert "Hello OCR" in result["result"]


async def test_ocr_multipage(http_client):
    result, status = await upload_and_wait(http_client, "multipage.pdf")
    assert status == "success"
    assert "First Page" in result["result"]
    assert "Second Page" in result["result"]


async def test_ocr_numbers(http_client):
    result, status = await upload_and_wait(http_client, "numbers.pdf")
    assert status == "success"
    assert "Invoice 1234" in result["result"]
    assert "Total 99" in result["result"]


async def test_ocr_special_chars(http_client):
    result, status = await upload_and_wait(http_client, "special_chars.pdf")
    assert status == "success"
    assert "$29.99" in result["result"]
    assert "25%" in result["result"]
    assert "#AB-1234" in result["result"]


async def test_ocr_blank_pdf(http_client):
    result, status = await upload_and_wait(http_client, "blank.pdf")
    assert status == "success"
    assert result["result"] is not None
    assert result["result"].strip() == ""


async def test_ocr_heavy(http_client):
    result, status = await upload_and_wait(http_client, "heavy.pdf")
    assert status == "success"
    text = result["result"]
    assert "QUARTERLY PERFORMANCE REPORT Q3 2024" in text
    assert "2847392" in text
    assert "18420" in text
    assert "North America" in text
    assert "982341" in text
    assert "11381568" in text
    assert "Strategic Priorities for Q4 2024" in text
    assert "11200000" in text
