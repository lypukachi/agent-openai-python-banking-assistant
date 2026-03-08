def augment_user_message_for_routing(message: str) -> str:
    """Add deterministic routing hints for intents that must map to a specific tool."""
    normalized = message.lower()
    has_waiver_intent = "waiver" in normalized or "fee reversal" in normalized or "fee refund" in normalized
    has_card_fee_context = "card" in normalized and "fee" in normalized
    has_annual_fee_context = "annual fee" in normalized and "credit" in normalized

    if has_waiver_intent and (has_card_fee_context or has_annual_fee_context):
        return (
            f"{message}\n\n"
            "[routing_hint]\n"
            "intent=credit_card_annual_fee_waiver\n"
            "target_agent=AccountAgent\n"
            "required_tool=requestCreditCardFeeWaiver\n"
        )

    return message
