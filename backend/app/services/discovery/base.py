from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from pydantic import BaseModel
from datetime import datetime

class DiscoveredTender(BaseModel):
    external_ref_id: str
    title: str
    authority: Optional[str] = None
    publish_date: Optional[datetime] = None
    submission_deadline: Optional[datetime] = None
    category: Optional[str] = None
    department: Optional[str] = None
    source_portal: str
    location: Optional[str] = None
    description: Optional[str] = None
    attachments: List[Dict[str, str]] = [] # [{"name": "...", "url": "..."}]
    raw_data: Optional[Dict] = None

class BaseScraper(ABC):
    def __init__(self, source_url: str, config: Dict = None):
        self.source_url = source_url
        self.config = config or {}

    @abstractmethod
    async def scan(self) -> List[DiscoveredTender]:
        """Scan the portal and return a list of discovered tenders."""
        pass

    @abstractmethod
    async def get_details(self, tender: DiscoveredTender) -> DiscoveredTender:
        """Fetch deep details and document links for a specific tender."""
        pass
