import os
from pyrogram import Client as AFK, idle
from pyrogram.enums import ChatMemberStatus, ChatMembersFilter
from pyrogram import enums
from pyrogram.types import ChatMember
import asyncio
import logging
import tgcrypto
from pyromod import listen
import logging
from tglogging import TelegramLogHandler
import time
import platform
import psutil
from datetime import datetime


# 🔧 Enhanced Config with monitoring capabilities
class Config(object):
    BOT_TOKEN = os.environ.get("BOT_TOKEN", "7767901658:AAEQ_6jOYQVZwq3STmolGceYhLfHZc-WEFY")
    API_ID = int(os.environ.get("API_ID",  "23075295"))
    API_HASH = os.environ.get("API_HASH", "93b13e8efb0c24e00458be3f734d7e41")
    DOWNLOAD_LOCATION = "./DOWNLOADS"
    SESSIONS = "./SESSIONS"
    
    # ─── OWNER SETTINGS ───
    OWNER_ID = int(os.environ.get("OWNER_ID", "1970647198"))
    OWNER_USERNAME = os.environ.get("OWNER_USERNAME", "Contact_xbot")
    
    # ─── USER MANAGEMENT ───
    AUTH_USERS = os.environ.get('AUTH_USERS', str(OWNER_ID)).split(',')
    AUTH_USERS = list(map(int, AUTH_USERS))
    
    GROUPS = os.environ.get('GROUPS', '').split(',')
    GROUPS = [int(x) for x in GROUPS if x]
    
    LOG_CH = os.environ.get("LOG_CH", "-1002324493310")
    
    # 🆕 BOT SETTINGS
    BOT_VERSION = "2.5.0"
    BOT_START_TIME = time.time()
    MAX_CONCURRENT_DOWNLOADS = int(os.environ.get("MAX_CONCURRENT_DOWNLOADS", "3"))
    ENABLE_STATS = os.environ.get("ENABLE_STATS", "True").lower() == "true"
    DEBUG_MODE = os.environ.get("DEBUG_MODE", "False").lower() == "true"


# 🆕 Enhanced Logging with better formatting
logging.basicConfig(
    level=logging.DEBUG if Config.DEBUG_MODE else logging.INFO,
    format="[%(asctime)s - %(levelname)s] - %(name)s - %(message)s",
    datefmt='%d-%b-%y %H:%M:%S',
    handlers=[
        TelegramLogHandler(
            token=Config.BOT_TOKEN, 
            log_chat_id=Config.LOG_CH, 
            update_interval=2, 
            minimum_lines=1, 
            pending_logs=200000
        ),
        logging.StreamHandler()
    ]
)

LOGGER = logging.getLogger(__name__)


# 🆕 System Information Helper
class SystemInfo:
    @staticmethod
    def get_system_stats():
        """Get detailed system information"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            uptime = time.time() - Config.BOT_START_TIME
            uptime_str = f"{int(uptime//3600):02d}:{int((uptime%3600)//60):02d}:{int(uptime%60):02d}"
            
            return {
                "cpu": cpu_percent,
                "memory_used": memory.percent,
                "memory_total": memory.total / (1024**3),  # GB
                "disk_used": disk.percent,
                "disk_free": disk.free / (1024**3),  # GB
                "uptime": uptime_str,
                "platform": platform.system(),
                "python_version": platform.python_version()
            }
        except Exception as e:
            LOGGER.warning(f"Could not get system stats: {e}")
            return None

    @staticmethod
    def format_system_stats(stats):
        """Format system stats for display"""
        if not stats:
            return "📊 **System stats unavailable**"
            
        return f"""📊 **System Statistics:**

💻 **Platform:** `{stats['platform']}`
🐍 **Python:** `{stats['python_version']}`
⏱️ **Uptime:** `{stats['uptime']}`

🖥️ **CPU Usage:** `{stats['cpu']:.1f}%`
🧠 **Memory:** `{stats['memory_used']:.1f}%` of `{stats['memory_total']:.1f}GB`
💾 **Disk:** `{stats['disk_used']:.1f}%` used, `{stats['disk_free']:.1f}GB` free"""


# Store
class Store(object):
    CPTOKEN = "eyJhbGciOiJIUzM4NCIsInR5cCI6IkpXVCJ9.eyJpZCI6MzgzNjkyMTIsIm9yZ0lkIjoyNjA1LCJ0eXBlIjoxLCJtb2JpbGUiOiI5MTcwODI3NzQyODkiLCJuYW1lIjoiQWNlIiwiZW1haWwiOm51bGwsImlzRmlyc3RMb2dpbiI6dHJ1ZSwiZGVmYXVsdExhbmd1YWdlIjpudWxsLCJjb3VudHJ5Q29kZSI6IklOIiwiaXNJbnRlcm5hdGlvbmFsIjowLCJpYXQiOjE2NDMyODE4NzcsImV4cCI6MTY0Mzg4NjY3N30.hM33P2ai6ivdzxPPfm01LAd4JWv-vnrSxGXqvCirCSpUfhhofpeqyeHPxtstXwe0"
    SPROUT_URL = "https://discuss.oliveboard.in/"
    ADDA_TOKEN = ""
    THUMB_URL = "https://telegra.ph/file/84870d6d89b893e59c5f0.jpg"


# 🚀 Enhanced Message Templates
class Msg(object):
    # 🆕 Enhanced start message with system info
    START_MSG = f"""🚀 **Welcome to Premium Downloader Bot v{Config.BOT_VERSION}!**

📌 **Available Commands:**
• `/pro` - 📥 Download from multiple platforms
• `/drm` - 🔓 DRM protected content downloader  
• `/ytc` - 📚 YCT Publication downloader
• `/stats` - 📊 System statistics (Owner only)
• `/help` - ❓ Get detailed help

🎯 **Features:**
✅ Multi-platform support
✅ DRM content handling
✅ Batch downloading
✅ Auto-retry mechanism
✅ Progress tracking
✅ File size validation

💡 **Ready to download? Use** `/pro` **to get started!**

🤖 **Bot Version:** `{Config.BOT_VERSION}`
⚡ **Status:** `Online & Ready`"""

    TXT_MSG = "👋 **Hey** <b>{user}</b>**!**\n\n" \
              "🤖 `I'm your Multi-Talented Download Assistant!`\n" \
              "💪 `I can download content from various platforms.`\n\n" \
              "📄 **Please send a TXT or HTML file to proceed:**\n\n" \
              "📝 **Supported formats:**\n" \
              "• `.txt` files with download links\n" \
              "• `.html` files with embedded links\n" \
              "• Direct URLs (one per line)"

    ERROR_MSG = "❌ **Download Failed ({no_of_files} errors)**\n\n" \
                "📂 **File:** `{file_name}`\n" \
                "🔗 **Link:** `{file_link}`\n\n" \
                "⚠️ **Error Details:**\n`{error}`\n\n" \
                "💡 **Possible solutions:**\n" \
                "• Check if the link is still valid\n" \
                "• Try a different quality setting\n" \
                "• Contact support if issue persists"

    SHOW_MSG = "⏬ **Download Started...**\n\n" \
               "📁 **File:** `{file_name}`\n" \
               "🌐 **Source:** `{file_link}`\n\n" \
               "⏳ **Please wait while I fetch your content...**\n" \
               "🔄 **This may take several minutes for large files**"

    CMD_MSG_1 = "📋 **File Analysis Complete!**\n\n" \
                "📊 **Total Links Found:** `{no_of_links}`\n\n" \
                "🔢 **Send Index Number:** `[1 - {no_of_links}]`\n" \
                "💡 **Or send** `0` **to download all files**\n\n" \
                "⚠️ **Note:** Batch downloads may take longer"

    CMD_MSG_2 = "📤 **Uploading to Telegram...**\n\n" \
                "📁 **File:** `{file_name}`\n" \
                "⚡ **Processing your request...**\n\n" \
                "🕐 **Average upload time:** `1-5 minutes`"

    RESTART_MSG = f"""🔄 **Bot Restarted Successfully!**

✅ **System Status:** `Online`
🗂️ **Storage:** `Cleared`
🚀 **Version:** `{Config.BOT_VERSION}`
⏰ **Restart Time:** `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`

🎯 **Ready for new downloads!**
💡 **All previous sessions have been cleared**"""

    # Enhanced additional messages
    SUCCESS_MSG = "🎉 **Upload Completed Successfully!**\n\n" \
                  "✅ **Your file has been uploaded to Telegram**\n" \
                  "📱 **Check your chat above** ⬆️\n\n" \
                  "🚀 **Ready for your next download!**"

    PROCESSING_MSG = "🔄 **Processing Your Request...**\n\n" \
                     "⏳ **This may take a few moments**\n" \
                     "☕ **Grab a coffee while you wait!**\n\n" \
                     "📊 **Queue position will be shown if busy**"

    CANCELLED_MSG = "🛑 **Operation Cancelled!**\n\n" \
                    "❌ **Download/Upload stopped by user**\n" \
                    "🔄 **You can start a new request anytime**\n\n" \
                    "💡 **No charges apply for cancelled operations**"

    TIMEOUT_MSG = "⏰ **Request Timeout!**\n\n" \
                  "🚫 **Operation took too long to complete**\n" \
                  "🔄 **Please try again with a smaller file**\n\n" \
                  "💡 **Recommended:** Files under 1GB for faster processing"

    FILE_TOO_LARGE_MSG = "📏 **File Too Large!**\n\n" \
                         "⚠️ **Maximum file size:** `2GB` (Telegram limit)\n" \
                         "💡 **Try downloading a smaller quality version**\n\n" \
                         "🎯 **Recommended qualities:**\n" \
                         "• `720p` for videos\n" \
                         "• `480p` for mobile viewing"

    INVALID_LINK_MSG = "🔗 **Invalid Link Detected!**\n\n" \
                       "❌ **Unable to process this URL**\n" \
                       "💡 **Please check the link and try again**\n\n" \
                       "✅ **Supported platforms:**\n" \
                       "• YouTube, Vimeo, ClassPlus\n" \
                       "• Vision IAS, Adda247\n" \
                       "• Google Drive, and more!"

    MAINTENANCE_MSG = f"""🔧 **Under Maintenance**

⚠️ **Bot is currently being updated**
⏰ **Estimated downtime:** `5-15 minutes`
🔄 **Please try again shortly**

📢 **What's being updated:**
• Performance improvements
• New platform support
• Bug fixes and stability

💡 **Follow updates:** @{Config.OWNER_USERNAME}"""

    RATE_LIMIT_MSG = "🚦 **Rate Limited!**\n\n" \
                     "⏳ **Too many requests. Please wait**\n" \
                     "🕐 **Try again in 30 seconds**\n\n" \
                     "📊 **Current limits:**\n" \
                     "• 5 requests per minute\n" \
                     "• 20 requests per hour"

    # 🆕 New system messages
    SYSTEM_STATS_MSG = """📊 **System Statistics**

{system_info}

📈 **Bot Statistics:**
🏃 **Active Downloads:** `{active_downloads}`
📥 **Total Downloads:** `{total_downloads}`
👥 **Active Users:** `{active_users}`"""

    HELP_MSG = f"""❓ **Help & Information**

**🤖 Bot Version:** `{Config.BOT_VERSION}`
**👑 Owner:** @{Config.OWNER_USERNAME}

**📋 Available Commands:**

**General Commands:**
• `/start` - Show welcome message
• `/pro` - Start download process
• `/help` - Show this help message

**Download Commands:**
• `/drm` - Download DRM protected content
• `/ytc` - Download YCT publications

**Owner Commands:**
• `/restart` - Restart the bot
• `/stats` - View system statistics

**🎯 How to Use:**
1. Use `/pro` to start downloading
2. Send a text file with links or direct URLs
3. Choose quality and options
4. Wait for download and upload

**🔧 Supported Platforms:**
• YouTube, Vimeo, Dailymotion
• ClassPlus, Vision IAS, Unacademy
• Google Drive, Adda247
• And many more!

**⚠️ Important Notes:**
• Max file size: 2GB
• Supported formats: MP4, PDF, etc.
• Bot respects rate limits

**🆘 Need Help?**
Contact: @{Config.OWNER_USERNAME}"""

    UNAUTHORIZED_MSG = f"""🚫 **Access Denied!**

You are not authorized to use this bot.

**🔐 This is a private bot**
**👑 Owner:** @{Config.OWNER_USERNAME}

**💡 Want access?**
Contact the owner for authorization."""


# Prefixes
prefixes = ["/", "~", "?", "!", "."]


# 🆕 Bot Statistics Tracker
class BotStats:
    def __init__(self):
        self.total_downloads = 0
        self.active_downloads = 0
        self.active_users = set()
        self.start_time = time.time()
    
    def add_download(self):
        self.total_downloads += 1
        self.active_downloads += 1
    
    def complete_download(self):
        self.active_downloads = max(0, self.active_downloads - 1)
    
    def add_user(self, user_id):
        self.active_users.add(user_id)
    
    def get_stats(self):
        return {
            "total_downloads": self.total_downloads,
            "active_downloads": self.active_downloads,
            "active_users": len(self.active_users),
            "uptime": time.time() - self.start_time
        }

# Global stats instance
bot_stats = BotStats()


# 🆕 Enhanced startup function
async def send_startup_notification(client, chat_ids):
    """Send enhanced startup notification with system info"""
    try:
        system_stats = SystemInfo.get_system_stats()
        bot_info = await client.get_me()
        
        startup_msg = f"""🚀 **Bot Started Successfully!**

🤖 **Bot:** @{bot_info.username}
📅 **Started:** `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`
🔧 **Version:** `{Config.BOT_VERSION}`

{SystemInfo.format_system_stats(system_stats) if system_stats else '📊 System stats unavailable'}

✅ **All systems operational**
🎯 **Ready to serve downloads**

💡 **Use** `/pro` **to start downloading!**"""

        successful_sends = 0
        for chat_id in chat_ids:
            try:
                await client.send_message(chat_id=chat_id, text=startup_msg)
                successful_sends += 1
                LOGGER.info(f"✅ Startup notification sent to {chat_id}")
            except Exception as e:
                LOGGER.warning(f"⚠️ Failed to send startup notification to {chat_id}: {e}")
                
        LOGGER.info(f"📤 Startup notifications sent to {successful_sends}/{len(chat_ids)} chats")
        
    except Exception as e:
        LOGGER.error(f"❌ Error sending startup notifications: {e}")


# Client setup
plugins = dict(root="plugins")

if __name__ == "__main__":
    # 🆕 Enhanced directory setup with logging
    for directory in [Config.DOWNLOAD_LOCATION, Config.SESSIONS]:
        if not os.path.isdir(directory):
            os.makedirs(directory)
            LOGGER.info(f"📁 Created directory: {directory}")
        else:
            LOGGER.info(f"📁 Directory exists: {directory}")

    # 🆕 Log initial configuration
    LOGGER.info("🔧 Bot Configuration:")
    LOGGER.info(f"   • Version: {Config.BOT_VERSION}")
    LOGGER.info(f"   • Owner: {Config.OWNER_ID} (@{Config.OWNER_USERNAME})")
    LOGGER.info(f"   • Auth Users: {len(Config.AUTH_USERS)}")
    LOGGER.info(f"   • Groups: {len(Config.GROUPS)}")
    LOGGER.info(f"   • Debug Mode: {Config.DEBUG_MODE}")
    LOGGER.info(f"   • Max Concurrent Downloads: {Config.MAX_CONCURRENT_DOWNLOADS}")

    PRO = AFK(
        "AFK-DL",
        bot_token=Config.BOT_TOKEN,
        api_id=Config.API_ID,
        api_hash=Config.API_HASH,
        sleep_threshold=120,
        plugins=plugins,
        workdir=f"{Config.SESSIONS}/",
        workers=4,  # 🆕 Increased workers for better performance
    )

    # 🆕 Enhanced chat ID collection
    chat_id = []
    
    # Add groups
    for group in Config.GROUPS:
        if group:  # Only add non-empty groups
            chat_id.append(group)
    
    # Add auth users
    for user in Config.AUTH_USERS:
        if user and user not in chat_id:  # Avoid duplicates
            chat_id.append(user)
    
    LOGGER.info(f"📤 Will send startup notifications to {len(chat_id)} chats")

    async def main():
        """Enhanced main function with better error handling and monitoring"""
        try:
            LOGGER.info("🚀 Starting bot initialization...")
            
            # Start the client
            await PRO.start()
            bot_info = await PRO.get_me()
            
            LOGGER.info(f"✅ Bot initialized successfully:")
            LOGGER.info(f"   • Username: @{bot_info.username}")
            LOGGER.info(f"   • ID: {bot_info.id}")
            LOGGER.info(f"   • Name: {bot_info.first_name}")
            
            # 🆕 Enhanced startup notification
            if chat_id:
                await send_startup_notification(PRO, chat_id)
            else:
                LOGGER.warning("⚠️ No chat IDs configured for startup notifications")
            
            # 🆕 Log system information
            system_stats = SystemInfo.get_system_stats()
            if system_stats:
                LOGGER.info("💻 System Information:")
                LOGGER.info(f"   • Platform: {system_stats['platform']}")
                LOGGER.info(f"   • Python: {system_stats['python_version']}")
                LOGGER.info(f"   • CPU: {system_stats['cpu']:.1f}%")
                LOGGER.info(f"   • Memory: {system_stats['memory_used']:.1f}%")
            
            LOGGER.info("🎯 Bot is now ready and waiting for commands...")
            LOGGER.info("=" * 50)
            
            # Start the idle loop
            await idle()
            
        except Exception as e:
            LOGGER.error(f"❌ Critical error in main function: {e}")
            raise
        finally:
            LOGGER.info("🛑 Bot shutdown initiated...")

    # 🆕 Enhanced event loop handling
    try:
        LOGGER.info("live log streaming to telegram.")
        asyncio.get_event_loop().run_until_complete(main())
    except KeyboardInterrupt:
        LOGGER.info("🛑 Bot stopped by user (Ctrl+C)")
    except Exception as e:
        LOGGER.error(f"❌ Fatal error: {e}")
    finally:
        LOGGER.info("🔚 Bot stopped gracefully")
        LOGGER.info("=" * 50)
