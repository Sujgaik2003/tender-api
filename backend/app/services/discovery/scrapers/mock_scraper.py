import asyncio
from datetime import datetime, timedelta
from typing import List
from app.services.discovery.base import BaseScraper, DiscoveredTender

class MockPortalScraper(BaseScraper):
    async def scan(self) -> List[DiscoveredTender]:
        """Simulate scanning a portal."""
        # In a real scraper, this would use httpx or Playwright
        await asyncio.sleep(1) # Simulate network lag
        
        return [
            DiscoveredTender(
                external_ref_id="TEND-2024-001",
                title="AI-Powered Document Analysis System for Defense Department",
                authority="Ministry of Defense",
                publish_date=datetime.now() - timedelta(days=2),
                submission_deadline=datetime.now() + timedelta(days=20),
                category="IT Services / AI",
                source_portal="Government E-Marketplace",
                description="The Ministry of Defense requires a secure, AI-powered system to analyze internal documents and extract key requirements automatically."
            ),
            DiscoveredTender(
                external_ref_id="TEND-2024-002",
                title="Cloud Infrastructure Modernization Phase 2",
                authority="Public Health Authority",
                publish_date=datetime.now() - timedelta(days=1),
                submission_deadline=datetime.now() + timedelta(days=15),
                category="Infrastructure",
                source_portal="ProcureNet Private",
                description="Modernization of legacy cloud servers to a hybrid cloud architecture using Kubernetes and AWS/Azure."
            )
        ]

    async def get_details(self, tender: DiscoveredTender) -> DiscoveredTender:
        """Simulate fetching deep details and attachments."""
        if tender.external_ref_id == "TEND-2024-001":
            tender.attachments = [
                {"name": "Technical_Specifications.pdf", "url": "https://example.com/files/spec.pdf"},
                {"name": "Financial_Bid_Format.xlsx", "url": "https://example.com/files/bid.xlsx"}
            ]
        elif tender.external_ref_id == "TEND-2024-002":
            tender.attachments = [
                {"name": "Infra_Modernization_Scope.pdf", "url": "https://example.com/files/scope.pdf"}
            ]
        return tender
