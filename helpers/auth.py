from functools import wraps
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from main import Config

def owner_only(func):
    """Decorator to restrict command to owner only"""
    @wraps(func)
    async def wrapper(bot, message):
        user_id = message.from_user.id
        
        if user_id != Config.OWNER_ID:
            # Create inline keyboard with owner contact button
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("👤 Owner", url=f"https://t.me/{Config.OWNER_USERNAME}")]
            ])
            
            await message.reply_text(
                "🚫 **Access Denied!**\n\n"
                "You cannot use this bot.\n"
                "For any query, contact the owner:",
                reply_markup=keyboard
            )
            return
        
        # If user is owner, execute the function
        return await func(bot, message)
    
    return wrapper

def auth_required(func):
    """Decorator to check if user is authorized (owner or in AUTH_USERS)"""
    @wraps(func)
    async def wrapper(bot, message):
        user_id = message.from_user.id
        
        # Check if user is owner or in authorized users list
        if user_id != Config.OWNER_ID and user_id not in Config.AUTH_USERS:
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("👤 Owner", url=f"https://t.me/{Config.OWNER_USERNAME}")]
            ])
            
            await message.reply_text(
                "🚫 **Access Denied!**\n\n"
                "You cannot use this bot.\n"
                "For any query, contact the owner:",
                reply_markup=keyboard
            )
            return
        
        return await func(bot, message)
    
    return wrapper
