"""Security middleware and utilities."""
import hmac
import hashlib
from typing import Optional
from fastapi import Header, HTTPException, status
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


def verify_tenant(
    x_tenant_id: str = Header(..., alias="X-Tenant-Id"),
    x_api_key: str = Header(..., alias="X-Api-Key"),
) -> str:
    """Verify tenant credentials.
    
    Args:
        x_tenant_id: Tenant identifier from header
        x_api_key: API key from header
        
    Returns:
        tenant_id if valid
        
    Raises:
        HTTPException: If authentication fails
    """
    tenant_keys = settings.tenant_keys
    
    if x_tenant_id not in tenant_keys:
        logger.warning("unknown_tenant", tenant_id=x_tenant_id)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid tenant ID"
        )
    
    expected_key = tenant_keys[x_tenant_id]
    if not hmac.compare_digest(x_api_key, expected_key):
        logger.warning("invalid_api_key", tenant_id=x_tenant_id)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    
    return x_tenant_id


def verify_signature(
    payload: bytes,
    signature: Optional[str] = None
) -> bool:
    """Verify HMAC signature of request payload.
    
    Args:
        payload: Request body as bytes
        signature: HMAC signature from X-Signature header
        
    Returns:
        True if signature is valid or not required
    """
    if not signature:
        # Signature is optional in MVP
        return True
    
    expected = hmac.new(
        settings.hmac_secret.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(signature, expected)
