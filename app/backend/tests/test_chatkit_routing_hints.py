from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.routers.chatkit.routing_hints import augment_user_message_for_routing


def test_adds_waiver_routing_hint_for_credit_card_fee_waiver() -> None:
    message = "I want a waiver for my credit card annual fee"

    routed = augment_user_message_for_routing(message)

    assert "intent=credit_card_annual_fee_waiver" in routed
    assert "target_agent=AccountAgent" in routed
    assert "required_tool=requestCreditCardFeeWaiver" in routed


def test_adds_company_web_routing_hint_for_savings_account_opening() -> None:
    message = "How to open saving bank account?"

    routed = augment_user_message_for_routing(message)

    assert "intent=savings_account_opening_information" in routed
    assert "target_agent=CompanyWebAgent" in routed
    assert "required_tool=fetchCompanyWebsiteContent" in routed


def test_keeps_unrelated_messages_unchanged() -> None:
    message = "Show my recent credit card transactions"

    routed = augment_user_message_for_routing(message)

    assert routed == message
