from typing import List, Dict, Any
from app.services.matcher import get_matcher
from app.core.supabase import get_supabase
from app.services.discovery.base import DiscoveredTender

class DiscoveryMatcher:
    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id
        self.supabase = get_supabase()
        self.matcher = get_matcher()

    async def match_tender(self, tender: DiscoveredTender) -> Dict[str, Any]:
        """
        AI-based semantic matching using both Vector Store and LLM for enterprise-level accuracy.
        """
        # 1. Fetch Discovery Config
        config_res = self.supabase.table("discovery_config") \
            .select("*") \
            .eq("tenant_id", self.tenant_id) \
            .execute()
        
        config = config_res.data[0] if config_res.data else {}
        preferred_domains = config.get("preferred_domains", [])
        keywords = config.get("keywords", [])
        
        # 2. Vector Match (Against past projects & KB)
        content_to_match = f"Title: {tender.title}\nCategory: {tender.category}\nAuthority: {tender.authority}\nDescription: {tender.description}"
        kb_matches = await self.matcher.search(tender.title, top_k=3)
        
        # 3. LLM Semantic Analysis (The 'Agent' Part)
        from app.core.config import get_settings
        settings = get_settings()
        
        prompt = f"""
        Analyze the following Tender Discovery for a company specializing in: {', '.join(preferred_domains)}.
        Keywords of interest: {', '.join(keywords)}

        TENDER DETAILS:
        Title: {tender.title}
        Authority: {tender.authority}
        Category: {tender.category}
        Description: {tender.description}

        TASK:
        1. Assign a Match Score (0-100) based on how well this aligns with their business domains.
        2. Provide a 1-2 sentence explanation of why it fits (or doesn't).
        3. Extract 3-5 relevant domain tags.

        FORMAT (JSON):
        {{
            "score": number,
            "explanation": "string",
            "tags": ["tag1", "tag2"]
        }}
        """
        
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                res = await client.post(
                    f"{settings.llm_api_url.rstrip('/')}/chat/completions",
                    headers={"Authorization": f"Bearer {settings.llm_api_key}"},
                    json={
                        "model": settings.llm_model,
                        "messages": [{"role": "system", "content": "You are an expert procurement consultant specializing in tender evaluation."}, 
                                    {"role": "user", "content": prompt}],
                        "response_format": {"type": "json_object"}
                    },
                    timeout=30.0
                )
                llm_data = res.json()["choices"][0]["message"]["content"]
                import json
                result = json.loads(llm_data)
        except Exception as e:
            print(f"LLM Match Error: {e}")
            # Fallback to simple logic if LLM fails
            result = {
                "score": 50 if any(d.lower() in tender.title.lower() for d in preferred_domains) else 20,
                "explanation": "Automated domain keyword match (LLM Unavailable).",
                "tags": [d for d in preferred_domains if d.lower() in tender.title.lower()]
            }

        # Labeling
        label = "Weak Match"
        if result["score"] > 80: label = "Highly Relevant"
        elif result["score"] > 50: label = "Related"

        return {
            "score": result["score"],
            "explanation": result["explanation"],
            "tags": result["tags"],
            "label": label
        }

    async def process_and_update_tender(self, tender_id: str):
        """Fetch tender from DB, match it, and update it."""
        tender_res = self.supabase.table("discovered_tenders") \
            .select("*") \
            .eq("id", tender_id) \
            .execute()
        
        if not tender_res.data:
            return
            
        tender_record = tender_res.data[0]
        # Convert record to DiscoveredTender object for matcher
        tender_obj = DiscoveredTender(
            external_ref_id=tender_record["external_ref_id"],
            title=tender_record["title"],
            category=tender_record["category"],
            description=tender_record["description"],
            source_portal=tender_record["source_portal"]
        )
        
        match_results = await self.match_tender(tender_obj)
        
        self.supabase.table("discovered_tenders") \
            .update({
                "match_score": match_results["score"],
                "match_explanation": match_results["explanation"],
                "domain_tags": match_results["tags"]
            }) \
            .eq("id", tender_id) \
            .execute()
        
        return match_results
