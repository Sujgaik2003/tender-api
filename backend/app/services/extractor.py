import re
import json
import httpx
from typing import List, Dict, Optional
from dataclasses import dataclass
from enum import Enum
from langdetect import detect, DetectorFactory
DetectorFactory.seed = 0
from app.core.config import get_settings


class RequirementCategory(str, Enum):
    ELIGIBILITY = "ELIGIBILITY"
    TECHNICAL = "TECHNICAL"
    COMPLIANCE = "COMPLIANCE"


@dataclass
class ExtractedRequirement:
    text: str
    category: RequirementCategory
    subcategory: str | None
    confidence: float
    page_number: int | None
    order: int
    priority: str = "Optional"


class RequirementExtractor:
    """Extract and categorize requirements from document text."""
    
    def __init__(self):
        settings = get_settings()
        self.llm_url = settings.llm_api_url
        self.llm_key = settings.llm_api_key
        
        # Eligibility patterns
        self.eligibility_patterns = [
            r"must have.*(?:certification|certificate|license)",
            r"minimum.*(?:\d+\s*)?years?.*experience",
            r"registered.*(?:company|firm|entity)",
            r"turnover.*(?:crore|lakh|million|billion)",
            r"iso\s*\d+.*certified",
            r"annual.*revenue",
            r"net\s*worth",
            r"valid.*registration",
            r"(?:should|must|shall)\s+be\s+(?:a\s+)?registered",
            r"empaneled\s+with",
            r"financial.*(?:standing|capability|capacity)",
            r"past.*(?:performance|experience)",
            r"similar.*(?:work|project|contract)",
        ]
        
        # Technical patterns
        self.technical_patterns = [
            r"(?:shall|must|should)\s+provide",
            r"(?:shall|must|should)\s+implement",
            r"system\s+(?:must|shall|should)",
            r"technical.*specification",
            r"deliverables?.*(?:include|consist)",
            r"solution\s+(?:must|shall|should)",
            r"(?:hardware|software)\s+requirement",
            r"platform\s+(?:must|shall|should)",
            r"integration\s+with",
            r"support.*(?:24x7|round.*clock)",
            r"uptime.*(?:\d+%|\d+\s*percent)",
            r"performance.*requirement",
            r"scalability",
            r"security.*(?:feature|requirement|standard)",
        ]
        
        # Compliance patterns
        self.compliance_patterns = [
            r"attach.*(?:certificate|document|proof)",
            r"provide.*(?:evidence|proof|documentation)",
            r"submit.*(?:document|certificate|declaration)",
            r"confirm.*compliance",
            r"undertaking.*(?:that|stating)",
            r"declaration.*(?:that|stating)",
            r"affidavit",
            r"self.*certification",
            r"duly.*signed",
            r"notarized",
            r"comply\s+with",
            r"adherence\s+to",
            r"in\s+accordance\s+with",
        ]
        
        # Requirement indicators
        self.requirement_indicators = [
            r"(?:shall|must|should|will|need\s+to|required\s+to)",
            r"mandatory",
            r"essential",
            r"prerequisite",
            r"minimum.*requirement",
            r"eligibility.*criteria",
            r"\?$", # Ends with question mark
            r"^(?:Q|Question|Sl\.?\s*No\.?)\s*[\.\d]*\s*[:\.\-]", # Q1:, Q.1:, Question 1.
            r"^Q\s*\d+[:\s\.]", # Q 1: or Q 1.
            r"^Q[A-Z]?\s*\d+[:\s\.]", # QA 1:
            r"^\d+\s*[\.\)]\s*\d*[\.\)]\s+", # Fuzzy numbering like 1 . 1
            r"^[a-z]\s*[\.\)]\s+", # a )
            r"^[A-Z]\s*[\.\)]\s+", # A .
            r"Requirement\s*[\.\d]*\s*[:\.]", # Requirement 1:
            r"Bidder\s*(?:shall|must|to)\s+", # Bidder shall...
        ]
        
        # Compile patterns for efficiency
        self._compile_patterns()
    
    def _compile_patterns(self):
        """Compile regex patterns."""
        self.eligibility_re = [re.compile(p, re.IGNORECASE) for p in self.eligibility_patterns]
        self.technical_re = [re.compile(p, re.IGNORECASE) for p in self.technical_patterns]
        self.compliance_re = [re.compile(p, re.IGNORECASE) for p in self.compliance_patterns]
        self.indicator_re = [re.compile(p, re.IGNORECASE) for p in self.requirement_indicators]
    
    async def extract(self, text: str, pages: List[Dict] = None) -> List[ExtractedRequirement]:
        """Extract requirements from document text."""
        
        # Detect language
        try:
            lang = detect(text[:2000]) # Scan first 2k chars
            print(f"[EXTRACTOR] Detected language: {lang}")
        except:
            lang = "en"
            
        # If not English and Mistral is available, use LLM extraction
        if lang != "en" and self.llm_key:
            print(f"[EXTRACTOR] User non-English detection, switching to LLM extraction")
            return await self._extract_llm(text, lang, pages)
        
        requirements = []
        seen_texts = set()
        order = 0
        
        # Split into sentences
        sentences = self._split_sentences(text)
        print(f"[EXTRACTOR] Total sentences found: {len(sentences)}")
        
        for sentence in sentences:
            sentence = sentence.strip()
            
            # Skip short or duplicate sentences
            if len(sentence) < 10 or sentence.lower() in seen_texts:
                continue
            
            # Check if this is a requirement or a question
            is_req = self._is_requirement(sentence)
            
            # DEBUG: Print only if it looks like a question but failed matching or vice versa
            if "Q" in sentence[:10] or "?" in sentence:
                 print(f"[EXTRACTOR] Testing line: '{sentence[:50]}...' -> Is Requirement: {is_req}")

            if not is_req:
                continue
            
            # Categorize the requirement
            category, confidence, subcategory, priority = self._categorize(sentence)
            
            # Find page number if pages provided
            page_num = self._find_page_number(sentence, pages) if pages else None
            
            requirements.append(ExtractedRequirement(
                text=sentence,
                category=category,
                subcategory=subcategory,
                confidence=confidence,
                page_number=page_num,
                order=order,
                priority=priority
            ))
            
            seen_texts.add(sentence.lower())
            order += 1
            
            if order >= 100: # Increased limit to capture more questions
                break
        
        # If no requirements found by regex OR we have Very Large Text, try LLM for better accuracy
        if (not requirements or len(text) > 10000) and self.llm_key:
             llm_reqs = await self._extract_llm(text, lang, pages)
             if llm_reqs:
                 return llm_reqs
              
        return requirements

    async def _extract_llm(self, text: str, lang: str, pages: List[Dict] = None) -> List[ExtractedRequirement]:
        """Use LLM to extract requirements from non-English text."""
        
        # Segment text to avoid tokens limit
        sample_text = text[:15000] # Take a large chunk
        
        prompt = f"""You are a tender analyst. Your task is to extract ALL questions and requirements from the provided document.
Language: {lang}

GENERAL RULES:
1. Questions may be explicitly numbered (Q1, Q2, 1., 2., a., b.) or may appear as sentences ending with a question mark (?).
2. Treat each logically independent question as a separate question.
3. A question may span multiple lines and may include sub-questions or bullet points.
4. Do NOT merge multiple questions into one.
5. Ignore answer placeholders, response sections, tables, headers, footers, and metadata.
6. Do NOT stop early — scan the entire document segment provided.

BOUNDARY RULES:
- A question ends immediately before the start of the next question or at the end of the document.
- If a section heading is followed by one or more interrogative sentences, treat each interrogative sentence as a question.

ID ASSIGNMENT:
- If the document provides an ID (e.g., Q3, 2.1), preserve it by prepending it to the 'text' field.
- If no ID exists, leave the text as is.

Text:
{sample_text}

Extract the top 30 requirements/questions. 
For each, provide:
1. text: The exact text (including original ID if present).
2. category: Exactly one of: ELIGIBILITY, TECHNICAL, COMPLIANCE.
3. subcategory: Short description.

Format: JSON list only.
[
  {{"text": "Q1. How do you handle X?", "category": "TECHNICAL", "subcategory": "Security"}},
  ...
]
"""
        settings = get_settings()
        try:
            headers = {"Authorization": f"Bearer {settings.llm_api_key}"}
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{settings.llm_api_url.rstrip('/')}/chat/completions",
                    headers=headers,
                    json={
                        "model": settings.llm_model,
                        "messages": [{"role": "user", "content": prompt}],
                        "response_format": {"type": "json_object"}
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    content = data["choices"][0]["message"]["content"]
                    # If Mistral returned a wrapped object, extract the list
                    parsed_data = json.loads(content)
                    items = parsed_data if isinstance(parsed_data, list) else parsed_data.get("requirements", [])
                    
                    extracted = []
                    for i, item in enumerate(items):
                        best_text = item.get("text", "")
                        if not best_text: continue
                        
                        page_num = self._find_page_number(best_text, pages) if pages else None
                        
                        extracted.append(ExtractedRequirement(
                            text=best_text,
                            category=RequirementCategory(item.get("category", "TECHNICAL")),
                            subcategory=item.get("subcategory"),
                            confidence=0.95,
                            page_number=page_num,
                            order=i
                        ))
                    return extracted
        except Exception as e:
            print(f"[EXTRACTOR] LLM extraction failed: {e}")
            
        return []

    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences."""
        # Handle common abbreviations
        text = re.sub(r'\b(Mr|Mrs|Ms|Dr|Prof|Inc|Ltd|Co|etc)\.\s', r'\1<PERIOD> ', text)
        sentences = re.split(r'(?<=[.!?])\s+', text)
        sentences = [s.replace('<PERIOD>', '.') for s in sentences]
        expanded = []
        for sentence in sentences:
            items = re.split(r'\n\s*(?:\d+[\.\)]\s*|\•\s*|\-\s*)', sentence)
            expanded.extend(items)
        return [s.strip() for s in expanded if s.strip()]
    
    def _is_requirement(self, sentence: str) -> bool:
        """Check if sentence is likely a requirement."""
        for pattern in self.indicator_re:
            if pattern.search(sentence):
                return True
        for patterns in [self.eligibility_re, self.technical_re, self.compliance_re]:
            for pattern in patterns:
                if pattern.search(sentence):
                    return True
        return False
    
    def _categorize(self, sentence: str) -> tuple[RequirementCategory, float, str | None, str]:
        """Categorize a requirement sentence and determine priority."""
        scores = {RequirementCategory.ELIGIBILITY: 0, RequirementCategory.TECHNICAL: 0, RequirementCategory.COMPLIANCE: 0}
        subcategory = None
        
        # Priority detection
        priority = "Optional"
        mandatory_keywords = ["must", "shall", "mandatory", "essential", "required", "prerequisite", "critical"]
        if any(w in sentence.lower() for w in mandatory_keywords):
            priority = "Mandatory"
            
        for pattern in self.eligibility_re:
            if pattern.search(sentence):
                scores[RequirementCategory.ELIGIBILITY] += 1
                if "certification" in sentence.lower() or "iso" in sentence.lower(): subcategory = "Certifications"
                elif "experience" in sentence.lower() or "years" in sentence.lower(): subcategory = "Experience"
                elif "turnover" in sentence.lower() or "revenue" in sentence.lower(): subcategory = "Financial"
        for pattern in self.technical_re:
            if pattern.search(sentence):
                scores[RequirementCategory.TECHNICAL] += 1
                if "security" in sentence.lower(): subcategory = "Security"
                elif "performance" in sentence.lower(): subcategory = "Performance"
                elif "integration" in sentence.lower(): subcategory = "Integration"
        for pattern in self.compliance_re:
            if pattern.search(sentence):
                scores[RequirementCategory.COMPLIANCE] += 1
                if "certificate" in sentence.lower(): subcategory = "Documentation"
                elif "declaration" in sentence.lower() or "undertaking" in sentence.lower(): subcategory = "Declarations"
        
        max_score = max(scores.values())
        if max_score == 0: return RequirementCategory.TECHNICAL, 0.5, None, priority
        category = max(scores, key=scores.get)
        total = sum(scores.values())
        return category, min(max_score / total, 0.99), subcategory, priority
    
    def _find_page_number(self, sentence: str, pages: List[Dict]) -> int | None:
        """Find which page contains the sentence."""
        sentence_lower = sentence.lower()[:50]
        for page in pages:
            if sentence_lower in page.get("content", "").lower():
                return page.get("page_num")
        return None


import json

# Singleton instance
_extractor: Optional[RequirementExtractor] = None

def get_extractor() -> RequirementExtractor:
    global _extractor
    if _extractor is None:
        _extractor = RequirementExtractor()
    return _extractor
