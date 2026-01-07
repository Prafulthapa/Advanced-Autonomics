"""
Lead Enricher - Use Ollama AI to enrich lead data
Extract company info, clean data, structure output
"""
import re
import asyncio
import httpx
import logging
import json
from config import SCRAPER_CONFIG

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

OLLAMA_HOST = "http://ollama:11434"
MODEL_NAME = "llama3.2:3b"


class LeadEnricher:
    """Enrich leads using AI."""
    
    def __init__(self):
        pass
    
    async def enrich_lead(self, lead_data):
        """Enrich a single lead with AI."""
        logger.info(f"🤖 Enriching: {lead_data.get('name')}")
        
        # Create prompt for AI
        prompt = self.create_enrichment_prompt(lead_data)
        
        # Get AI response
        enriched = await self.call_ollama(prompt)
        
        if enriched:
            # Merge with original data
            lead_data.update(enriched)
            logger.info(f"✅ Enriched: {lead_data.get('name')}")
        
        return lead_data
    
    def create_enrichment_prompt(self, lead_data):
        """Create prompt for AI enrichment."""
        prompt = f"""Analyze this professional profile and extract structured information.

Profile:
Name: {lead_data.get('name', 'Unknown')}
Title: {lead_data.get('title', 'Unknown')}
Company: {lead_data.get('company', 'Unknown')}
Location: {lead_data.get('location', 'Unknown')}

Extract and return ONLY a JSON object with these fields:
- first_name: (extract from name)
- last_name: (extract from name)
- clean_company_name: (company name without Pty Ltd, Inc, etc.)
- industry: (guess industry based on company name and title)
- is_decision_maker: (true if title suggests decision-making authority like CEO, Owner, Director)

Return ONLY the JSON object, no other text.
"""
        return prompt
    
    async def call_ollama(self, prompt):
        """Call Ollama API."""
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{OLLAMA_HOST}/api/generate",
                    json={
                        "model": MODEL_NAME,
                        "prompt": prompt,
                        "stream": False
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    text = result.get("response", "")
                    
                    # Try to parse JSON from response
                    try:
                        # Extract JSON from response (might have markdown)
                        json_match = re.search(r'\{.*\}', text, re.DOTALL)
                        if json_match:
                            parsed = json.loads(json_match.group())
                            return parsed
                    except:
                        pass
                
        except Exception as e:
            logger.error(f"Ollama error: {str(e)}")
        
        return None
    
    async def enrich_all_leads(self, leads):
        """Enrich all leads."""
        logger.info(f"🤖 Enriching {len(leads)} leads with AI...")
        
        enriched_leads = []
        
        for lead in leads[:100]:  # Limit to 100 to avoid timeout
            enriched = await self.enrich_lead(lead)
            enriched_leads.append(enriched)
            await asyncio.sleep(1)  # Rate limit
        
        logger.info(f"✅ Enriched {len(enriched_leads)} leads")
        return enriched_leads


async def main():
    """Test enricher."""
    enricher = LeadEnricher()
    
    test_lead = {
        "name": "John Smith",
        "title": "CEO & Founder",
        "company": "ABC Robotics Pty Ltd",
        "location": "Sydney, Australia"
    }
    
    enriched = await enricher.enrich_lead(test_lead)
    print(json.dumps(enriched, indent=2))


if __name__ == "__main__":
    asyncio.run(main())