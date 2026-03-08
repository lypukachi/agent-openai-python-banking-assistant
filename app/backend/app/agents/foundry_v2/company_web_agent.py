from agent_framework.azure import AzureAIClient
from agent_framework import tool, Agent

from app.tools.company_website_fetcher import CompanyWebsiteFetcher

import logging


logger = logging.getLogger(__name__)


@tool(
    name="handoff_to_TriageAgent", description="Handoff to the triage-agent agent."
)
def handoff_to_triage_agent(context: str | None = None) -> str:
    """Transfer the conversation back to the triage agent."""
    return "Handoff to TriageAgent"


class CompanyWebAgent:
    instructions = """
    You answer questions using information retrieved from company websites.
    Always call fetchCompanyWebsiteContent before answering factual questions about company websites.
    If user does not provide website URLs, call fetchCompanyWebsiteContent with an empty string to use configured COMPANY_WEBSITES.
    If neither user URLs nor configured COMPANY_WEBSITES are available, ask the user to provide one or more website URLs.
    When multiple websites are provided, compare and summarize differences clearly.
    Mention the source URL(s) used in your answer.
    Configured company/bank websites:
    {configured_websites}
    Use markdown for final responses.
    """
    name = "CompanyWebAgent"
    description = "This agent retrieves and summarizes information from one or many company websites."

    def __init__(
        self,
        azure_ai_client: AzureAIClient,
        company_website_fetcher: CompanyWebsiteFetcher,
        configured_websites: str | None = None,
    ):
        self.azure_ai_client = azure_ai_client
        self.company_website_fetcher = company_website_fetcher
        self.configured_websites = configured_websites or "(not configured)"

    async def build_af_agent(self) -> Agent:
        logger.info("Building request scoped CompanyWebAgent run")
        full_instructions = CompanyWebAgent.instructions.format(configured_websites=self.configured_websites)

        agent = Agent(
            client=self.azure_ai_client,
            instructions=full_instructions.strip(),
            name=CompanyWebAgent.name,
            tools=[self.company_website_fetcher.fetch_company_website_content, handoff_to_triage_agent],
        )
        agent.default_options["tools"] = [self.company_website_fetcher.fetch_company_website_content, handoff_to_triage_agent]
        return agent
