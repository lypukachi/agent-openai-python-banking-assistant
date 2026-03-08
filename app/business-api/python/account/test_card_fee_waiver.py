import pytest

from services import CardService


def test_request_credit_card_fee_waiver_submitted_for_credit_card() -> None:
    service = CardService()

    result = service.request_credit_card_fee_waiver(
        card_id="55555",
        reason="I have been a loyal customer and request annual fee waiver.",
    )

    assert result["status"] == "submitted"
    assert result["cardId"] == "55555"
    assert result["requestId"].startswith("waiver-")


def test_request_credit_card_fee_waiver_rejects_non_credit_card() -> None:
    service = CardService()

    with pytest.raises(RuntimeError, match="supported only for credit cards"):
        service.request_credit_card_fee_waiver(
            card_id="66666",
            reason="Please waive annual fee",
        )
