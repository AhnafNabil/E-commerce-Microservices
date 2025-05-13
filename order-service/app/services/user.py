import httpx
import logging
from tenacity import retry, stop_after_attempt, wait_fixed

from app.core.config import settings

logger = logging.getLogger(__name__)


class UserServiceClient:
    """Client for interacting with the User Service."""

    def __init__(self):
        self.base_url = str(settings.USER_SERVICE_URL)
        self.timeout = 5.0  # seconds
        self.max_retries = settings.MAX_RETRIES
        self.retry_delay = settings.RETRY_DELAY

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(1))
    async def verify_user(self, user_id: str) -> bool:
        """
        Verify that a user exists and is active.
        
        Args:
            user_id: The ID of the user to check
            
        Returns:
            bool: True if user exists and is active, False otherwise
        """
        logger.info(f"Verifying user: {user_id}")
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/users/{user_id}/verify")
                
                if response.status_code == 200:
                    result = response.json()
                    return result.get("valid", False)
                else:
                    logger.error(f"User verification failed: {response.text}")
                    return False
        except httpx.RequestError as e:
            logger.error(f"Error verifying user: {str(e)}")
            return False

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(1))
    async def get_user_address(self, user_id: str, address_id: str = None):
        """
        Get the shipping address for a user.
        
        Args:
            user_id: The ID of the user
            address_id: Optional specific address ID
            
        Returns:
            dict: The user's address or None if not found
        """
        logger.info(f"Getting address for user: {user_id}")
        try:
            url = f"{self.base_url}/users/{user_id}/addresses"
            if address_id:
                url += f"/{address_id}"
                
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url)
                
                if response.status_code == 200:
                    if address_id:
                        return response.json()
                    else:
                        addresses = response.json()
                        # Return the default address or the first one
                        for address in addresses:
                            if address.get("is_default", False):
                                return address
                        return addresses[0] if addresses else None
                else:
                    logger.error(f"Getting user address failed: {response.text}")
                    return None
        except httpx.RequestError as e:
            logger.error(f"Error getting user address: {str(e)}")
            return None


# Create a singleton instance
user_service = UserServiceClient()