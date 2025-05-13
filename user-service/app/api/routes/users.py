from fastapi import APIRouter, Depends, HTTPException, status, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update, delete
from typing import List, Any, Dict, Optional

from app.db.postgresql import get_db
from app.models.user import (
    User, UserUpdate, UserResponse, UserChangePassword,
    Address, AddressCreate, AddressUpdate, AddressResponse
)
from app.api.dependencies import (
    get_current_active_user, get_current_verified_user,
    get_current_admin, get_user_by_id
)
from app.core.security import get_password_hash, verify_password

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Get current user profile.
    """
    return current_user


@router.put("/me", response_model=UserResponse)
async def update_current_user_profile(
    user_update: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Update current user profile.
    """
    # Update only provided fields
    update_data = user_update.dict(exclude_unset=True)
    
    if update_data:
        for key, value in update_data.items():
            setattr(current_user, key, value)
        
        await db.commit()
        await db.refresh(current_user)
    
    return current_user


@router.put("/me/password", status_code=status.HTTP_200_OK)
async def change_password(
    password_change: UserChangePassword,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Dict[str, str]:
    """
    Change user password.
    """
    # Verify current password
    if not verify_password(password_change.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect current password",
        )
    
    # Update password
    current_user.hashed_password = get_password_hash(password_change.new_password)
    await db.commit()
    
    return {"message": "Password changed successfully"}


@router.get("/{user_id}", response_model=UserResponse)
async def get_user_by_id_api(
    user_id: int = Path(..., title="The ID of the user to get"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin),  # Only admins can access other users
) -> Any:
    """
    Get user by ID (admin only).
    """
    user = await get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found",
        )
    
    return user


@router.put("/{user_id}", response_model=UserResponse)
async def update_user_by_admin(
    user_id: int,
    user_update: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin),  # Only admins can update other users
) -> Any:
    """
    Update user (admin only).
    """
    user = await get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found",
        )
    
    # Update only provided fields
    update_data = user_update.dict(exclude_unset=True)
    
    if update_data:
        for key, value in update_data.items():
            setattr(user, key, value)
        
        await db.commit()
        await db.refresh(user)
    
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin),  # Only admins can delete users
) -> None:
    """
    Delete user (admin only).
    """
    user = await get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found",
        )
    
    # Don't allow deleting yourself
    if current_user.id == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account",
        )
    
    await db.delete(user)
    await db.commit()


@router.get("/me/addresses", response_model=List[AddressResponse])
async def get_user_addresses(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_verified_user),
) -> Any:
    """
    Get all addresses for the current user.
    """
    result = await db.execute(select(Address).where(Address.user_id == current_user.id))
    addresses = result.scalars().all()
    
    return addresses


@router.post("/me/addresses", response_model=AddressResponse, status_code=status.HTTP_201_CREATED)
async def create_user_address(
    address: AddressCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_verified_user),
) -> Any:
    """
    Create a new address for the current user.
    """
    # If this is the first address or it's set as default
    is_first_address = False
    if address.is_default:
        # Check if the user already has a default address
        result = await db.execute(
            select(Address).where(
                Address.user_id == current_user.id,
                Address.is_default == True
            )
        )
        current_default = result.scalars().first()
        
        if current_default:
            # Remove default flag from the current default address
            current_default.is_default = False
    else:
        # Check if this is the first address (make it default automatically)
        result = await db.execute(
            select(Address).where(Address.user_id == current_user.id)
        )
        if not result.scalars().first():
            is_first_address = True
    
    # Create the new address
    db_address = Address(
        user_id=current_user.id,
        line1=address.line1,
        line2=address.line2,
        city=address.city,
        state=address.state,
        postal_code=address.postal_code,
        country=address.country,
        is_default=address.is_default or is_first_address
    )
    
    db.add(db_address)
    await db.commit()
    await db.refresh(db_address)
    
    return db_address


@router.get("/me/addresses/{address_id}", response_model=AddressResponse)
async def get_user_address(
    address_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_verified_user),
) -> Any:
    """
    Get a specific address for the current user.
    """
    result = await db.execute(
        select(Address).where(
            Address.id == address_id,
            Address.user_id == current_user.id
        )
    )
    address = result.scalars().first()
    
    if not address:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Address with ID {address_id} not found",
        )
    
    return address


@router.put("/me/addresses/{address_id}", response_model=AddressResponse)
async def update_user_address(
    address_id: int,
    address_update: AddressUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_verified_user),
) -> Any:
    """
    Update a specific address for the current user.
    """
    result = await db.execute(
        select(Address).where(
            Address.id == address_id,
            Address.user_id == current_user.id
        )
    )
    address = result.scalars().first()
    
    if not address:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Address with ID {address_id} not found",
        )
    
    # Update only provided fields
    update_data = address_update.dict(exclude_unset=True)
    
    # If setting this address as default
    if update_data.get("is_default") is True and not address.is_default:
        # Find and update current default address
        result = await db.execute(
            select(Address).where(
                Address.user_id == current_user.id,
                Address.is_default == True
            )
        )
        current_default = result.scalars().first()
        
        if current_default:
            current_default.is_default = False
    
    # Apply updates
    if update_data:
        for key, value in update_data.items():
            setattr(address, key, value)
        
        await db.commit()
        await db.refresh(address)
    
    return address


@router.delete("/me/addresses/{address_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_address(
    address_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_verified_user),
) -> None:
    """
    Delete a specific address for the current user.
    """
    result = await db.execute(
        select(Address).where(
            Address.id == address_id,
            Address.user_id == current_user.id
        )
    )
    address = result.scalars().first()
    
    if not address:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Address with ID {address_id} not found",
        )
    
    # Check if this is the default address and there are other addresses
    if address.is_default:
        # Count other addresses
        result = await db.execute(
            select(Address).where(
                Address.user_id == current_user.id,
                Address.id != address_id
            )
        )
        other_addresses = result.scalars().all()
        
        if other_addresses:
            # Make the first one the new default
            other_addresses[0].is_default = True
    
    await db.delete(address)
    await db.commit()


@router.put("/me/addresses/{address_id}/default", response_model=AddressResponse)
async def set_default_address(
    address_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_verified_user),
) -> Any:
    """
    Set an address as the default for the current user.
    """
    # Verify address exists and belongs to user
    result = await db.execute(
        select(Address).where(
            Address.id == address_id,
            Address.user_id == current_user.id
        )
    )
    address = result.scalars().first()
    
    if not address:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Address with ID {address_id} not found",
        )
    
    # If already default, no changes needed
    if address.is_default:
        return address
    
    # Find and update current default address
    result = await db.execute(
        select(Address).where(
            Address.user_id == current_user.id,
            Address.is_default == True
        )
    )
    current_default = result.scalars().first()
    
    if current_default:
        current_default.is_default = False
    
    # Set the new default
    address.is_default = True
    await db.commit()
    await db.refresh(address)
    
    return address


@router.get("/{user_id}/verify", response_model=Dict[str, Any])
async def verify_user_exists(
    user_id: int,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    Verify if a user exists and is active.
    This endpoint is used by other services to validate users.
    """
    user = await get_user_by_id(db, user_id)
    
    if not user or not user.is_active:
        return {"valid": False}
    
    return {
        "valid": True,
        "user_id": user.id,
        "email": user.email,
        "full_name": f"{user.first_name} {user.last_name}",
        "is_verified": user.is_email_verified
    }