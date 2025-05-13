import httpx
import logging
from typing import Dict, Optional
from tenacity import retry, stop_after_attempt, wait_fixed

from app.core.config import settings

logger = logging.getLogger(__name__)


class ProductServiceClient:
    """Client for interacting with the Product Service."""

    def __init__(self):
        self.base_url = str(settings.PRODUCT_SERVICE_URL)
        self.timeout = 5.0  # seconds
        self.max_retries = settings.MAX_RETRIES
        self.retry_delay = settings.RETRY_DELAY

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(1))
    async def get_product(self, product_id: str) -> Optional[Dict]:
        """
        Get product details by ID.
        
        Args:
            product_id: The ID of the product
            
        Returns:
            dict: Product details or None if not found
        """
        logger.info(f"Getting product details for ID: {product_id}")
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/products/{product_id}")
                
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 404:
                    logger.warning(f"Product not found: {product_id}")
                    return None
                else:
                    logger.error(f"Error getting product: {response.text}")
                    return None
        except httpx.RequestError as e:
            logger.error(f"Request error getting product: {str(e)}")
            return None


# Create a singleton instance
product_service = ProductServiceClient()