import httpx
import logging
from tenacity import retry, stop_after_attempt, wait_fixed

from app.core.config import settings

logger = logging.getLogger(__name__)

class InventoryServiceClient:
    """Client for interacting with the Inventory Service."""

    def __init__(self):
        self.base_url = str(settings.INVENTORY_SERVICE_URL)
        self.timeout = 5.0  # seconds
        self.max_retries = 3
        self.retry_delay = 1  # seconds

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(1))
    async def create_inventory(self, product_id: str, initial_quantity: int = 0, 
                            reorder_threshold: int = 5) -> bool:
        """
        Create inventory for a new product.
        
        Args:
            product_id: The ID of the product
            initial_quantity: Initial quantity to set (defaults to product quantity)
            reorder_threshold: Threshold for low stock alerts
            
        Returns:
            bool: True if inventory creation was successful, False otherwise
        """
        logger.info(f"Creating inventory for product {product_id}")
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/inventory/",
                    json={
                        "product_id": product_id,
                        "available_quantity": initial_quantity,
                        "reserved_quantity": 0,
                        "reorder_threshold": reorder_threshold
                    }
                )
                
                if response.status_code in (200, 201):
                    logger.info(f"Successfully created inventory for product {product_id}")
                    return True
                else:
                    logger.error(f"Failed to create inventory: {response.text}")
                    return False
        except httpx.RequestError as e:
            logger.error(f"Error creating inventory: {str(e)}")
            return False

# Create a singleton instance
inventory_service = InventoryServiceClient()