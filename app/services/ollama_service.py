import httpx
import logging

logger = logging.getLogger(__name__)

OLLAMA_HOST = "http://ollama:11434"
MODEL_NAME = "llama3.2:3b"


class OllamaService:

    @staticmethod
    async def generate_email(prompt: str) -> str:
        """Generate a personalised cold email."""
        payload = {
            "model": MODEL_NAME,
            "prompt": prompt,
            "stream": False
        }
        
        try:
            logger.info(f"Connecting to Ollama at {OLLAMA_HOST} with model {MODEL_NAME}")
            
            # Increased timeout from 60 to 180 seconds
            async with httpx.AsyncClient(timeout=httpx.Timeout(180.0)) as client:
                response = await client.post(f"{OLLAMA_HOST}/api/generate", json=payload)
                
                logger.info(f"Ollama response status: {response.status_code}")
                
                response.raise_for_status()
                result = response.json()
                generated_text = result.get("response", "")
                
                logger.info(f"Generated email: {len(generated_text)} characters")
                
                return generated_text
                
        except httpx.TimeoutException as e:
            logger.error(f"Timeout connecting to Ollama: {str(e)}")
            raise Exception(f"Ollama timeout - model may be loading: {str(e)}")
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error from Ollama: {e.response.status_code} - {e.response.text}")
            raise Exception(f"Ollama HTTP error: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error calling Ollama: {str(e)}", exc_info=True)
            raise

    @staticmethod
    async def classify_reply(text: str) -> str:
        """Classify reply: interested / not interested / unsubscribe / unclear."""
        classification_prompt = f"""
        Classify this email reply clearly into one category:
        - interested
        - not interested
        - unsubscribe
        - unclear

        Reply ONLY with the category.

        Email:
        {text}
        """
        payload = {
            "model": MODEL_NAME,
            "prompt": classification_prompt,
            "stream": False
        }
        
        try:
            # Increased timeout from 60 to 180 seconds
            async with httpx.AsyncClient(timeout=httpx.Timeout(180.0)) as client:
                response = await client.post(f"{OLLAMA_HOST}/api/generate", json=payload)
                response.raise_for_status()
                return response.json().get("response", "").strip().lower()
        except Exception as e:
            logger.error(f"Classification error: {str(e)}", exc_info=True)
            raise