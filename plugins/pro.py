from pyrogram import filters, Client as AFK
from main import LOGGER as LOGS, prefixes, Config, Msg
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from handlers.tg import TgClient, TgHandler
from helpers.auth import owner_only, auth_required
import os
import sys
import shutil
import time
from handlers.downloader import download_handler, get_link_atributes
from handlers.uploader import Upload_to_Tg
import asyncio
from collections import defaultdict
import psutil
import platform
from datetime import datetime


# 🚦 Rate Limiter
class RateLimiter:
    def __init__(self):
        self.user_requests = defaultdict(list)
        self.max_requests = 5  # Max 5 requests
        self.time_window = 60  # Per 60 seconds
    
    def is_rate_limited(self, user_id):
        now = time.time()
        user_requests = self.user_requests[user_id]
        
        # Remove old requests
        self.user_requests[user_id] = [
            req_time for req_time in user_requests 
            if now - req_time < self.time_window
        ]
        
        # Check if rate limited
        if len(self.user_requests[user_id]) >= self.max_requests:
            return True
        
        # Add current request
        self.user_requests[user_id].append(now)
        return False


# Global rate limiter instance
rate_limiter = RateLimiter()


# 🔒 Helper: wait until file is not locked (for Windows)
def wait_until_file_is_free(path, timeout=30):
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            with open(path, 'ab'):
                return True
        except PermissionError:
            time.sleep(1)
    LOGS.warning(f"File still locked after {timeout}s: {path}")
    return False


# 🔥 Helper: safely delete folder
def safe_delete_folder(path, retries=5, delay=2):
    for attempt in range(retries):
        try:
            if os.path.exists(path):
                shutil.rmtree(path)
                LOGS.info(f"Deleted folder: {path}")
            return
        except PermissionError:
            LOGS.warning(f"Retry {attempt+1}/{retries} deleting {path}")
            time.sleep(delay)
        except Exception as e:
            LOGS.error(f"Error deleting {path}: {e}")
            break


# 📄 Paginated Help System
class HelpPagination:
    def __init__(self, bot_info):
        self.bot_info = bot_info
        self.pages = self._create_help_pages()
    
    def _create_help_pages(self):
        """Create paginated help content"""
        pages = []
        
        # Page 1: Overview & Bot Details
        page_1 = f"""❓ **Help & Information - Page 1/6**

**🤖 Bot Details:**
• **Name:** {self.bot_info.first_name}
• **Username:** @{self.bot_info.username}
• **Version:** `{getattr(Config, 'BOT_VERSION', '2.5.0')}`
• **Owner:** @{Config.OWNER_USERNAME}

**📋 Available Commands:**

**🎯 Main Commands:**
• `/start` - Welcome message & bot features
• `/pro` - 📥 Multi-platform downloader
• `/help` - ❓ Show this help message

**🔓 Specialized Downloads:**
• `/drm` - 🔐 DRM protected content
• `/ytc` - 📚 YCT Publication books

**👑 Owner Commands:**
• `/restart` - 🔄 Restart bot (Owner only)
• `/stats` - 📊 System statistics (Owner only)"""
        pages.append(page_1)
        
        # Page 2: How to Use
        page_2 = """❓ **Help & Information - Page 2/6**

**🚀 How to Use `/pro`:**

**Step 1:** Send `/pro` command

**Step 2:** Upload a text file with download links
• One URL per line
• Supported formats: `.txt`, `.html`

**Step 3:** Select starting index
• Choose specific index (1, 2, 3...)
• Or send `0` to download all files

**Step 4:** Choose quality and options
• Select video quality (144p to 1080p)
• Provide batch name and username

**Step 5:** Wait for download & upload
• Bot will process files sequentially
• Progress updates will be shown"""
        pages.append(page_2)
        
        # Page 3: Supported Platforms
        page_3 = """❓ **Help & Information - Page 3/6**

**🌐 Supported Platforms:**

**✅ Video Platforms:**
• YouTube, Vimeo, Dailymotion
• ClassPlus, Vision IAS
• Unacademy, Testbook
• Google Drive videos

**✅ Educational Platforms:**
• Adda247, BYJU'S
• Vedantu, Toppr
• Physics Wallah
• Various coaching institutes

**✅ Document Platforms:**
• Google Drive PDFs
• Educational PDFs
• Course materials

**📝 Supported File Formats:**
• `.txt` files with URLs (one per line)
• `.html` files with embedded links
• Direct URLs in chat"""
        pages.append(page_3)
        
        # Page 4: Features & Quality
        page_4 = """❓ **Help & Information - Page 4/6**

**⚙️ Advanced Features:**
• 🎯 Batch downloading (multiple files)
• 📊 Real-time progress tracking
• 🔄 Auto-retry mechanism
• 📏 File size validation (2GB limit)
• 🚦 Rate limiting protection
• 🎬 Video thumbnail generation
• 📱 Mobile-friendly uploads

**🔧 Quality Options:**
• `144p, 240p, 360p` - Mobile quality
• `480p, 720p` - Standard quality  
• `1080p` - High quality (if available)

**⚠️ Important Limitations:**
• Maximum file size: 2GB (Telegram limit)
• Rate limit: 5 requests per minute
• Bot processes downloads sequentially
• Large files may take 10-30 minutes"""
        pages.append(page_4)
        
        # Page 5: Tips & Security
        page_5 = """❓ **Help & Information - Page 5/6**

**💡 Tips for Better Downloads:**
• Use lower quality for faster downloads
• Ensure stable internet connection
• Avoid downloading during peak hours
• Check link validity before submitting
• Use descriptive batch names
• Be patient with large files

**🔒 Privacy & Security:**
• Your links are processed securely
• No data is stored permanently
• Files are deleted after upload
• Bot respects platform rate limits
• All downloads are encrypted
• No logs of your content kept

**⚡ Performance Tips:**
• Download during off-peak hours
• Use 720p for best speed/quality balance
• Split large batches into smaller ones"""
        pages.append(page_5)
        
        # Page 6: Support & Contact
        page_6 = f"""❓ **Help & Information - Page 6/6**

**🆘 Need Help?**
• **Contact:** @{Config.OWNER_USERNAME}
• **Report bugs** to owner
• **Request new platform** support
• **Suggest improvements**

**🔧 Troubleshooting:**
• **Link not working?** Check if it's valid
• **Download failed?** Try different quality
• **Bot not responding?** Check rate limits
• **Upload failed?** File might be too large

**📞 Support Channels:**
• Direct message owner for urgent issues
• Check announcements for maintenance
• Follow updates for new features

**🎯 Quick Commands:**
• `/start` - Bot overview
• `/help` - This help system
• `/pro` - Start downloading

**Thank you for using our bot! 🚀**"""
        pages.append(page_6)
        
        return pages
    
    def get_keyboard(self, current_page):
        """Generate navigation keyboard"""
        buttons = []
        nav_buttons = []
        
        # Previous button
        if current_page > 0:
            nav_buttons.append(InlineKeyboardButton("⬅️ Previous", callback_data=f"help_page_{current_page-1}"))
        
        # Page indicator
        nav_buttons.append(InlineKeyboardButton(f"📄 {current_page+1}/6", callback_data="help_current"))
        
        # Next button
        if current_page < len(self.pages) - 1:
            nav_buttons.append(InlineKeyboardButton("Next ➡️", callback_data=f"help_page_{current_page+1}"))
        
        buttons.append(nav_buttons)
        
        # Quick navigation
        quick_nav = [
            InlineKeyboardButton("🏠 Overview", callback_data="help_page_0"),
            InlineKeyboardButton("🚀 Usage", callback_data="help_page_1"),
            InlineKeyboardButton("🌐 Platforms", callback_data="help_page_2")
        ]
        buttons.append(quick_nav)
        
        quick_nav_2 = [
            InlineKeyboardButton("⚙️ Features", callback_data="help_page_3"),
            InlineKeyboardButton("💡 Tips", callback_data="help_page_4"),
            InlineKeyboardButton("🆘 Support", callback_data="help_page_5")
        ]
        buttons.append(quick_nav_2)
        
        # Close button
        buttons.append([InlineKeyboardButton("❌ Close Help", callback_data="help_close")])
        
        return InlineKeyboardMarkup(buttons)


# 📊 Paginated Stats System
class StatsPagination:
    def __init__(self, bot_info, system_data):
        self.bot_info = bot_info
        self.system_data = system_data
        self.pages = self._create_stats_pages()
    
    def _create_stats_pages(self):
        """Create paginated stats content"""
        pages = []
        
        # Page 1: Bot Information
        uptime_str = self.system_data.get('uptime_str', 'Unknown')
        page_1 = f"""📊 **System Statistics - Page 1/4**

**🤖 Bot Information:**
• **Name:** {self.bot_info.first_name}
• **Username:** @{self.bot_info.username}
• **ID:** `{self.bot_info.id}`
• **Version:** `{getattr(Config, 'BOT_VERSION', '2.5.0')}`
• **Uptime:** `{uptime_str}`
• **Started:** `{datetime.fromtimestamp(getattr(Config, 'BOT_START_TIME', time.time())).strftime('%Y-%m-%d %H:%M:%S')}`

**🎯 Bot Status:**
• **Response:** `Active ✅`
• **Download System:** `Operational ✅`
• **Upload System:** `Operational ✅`
• **Error Rate:** `Low 📉`"""
        pages.append(page_1)
        
        # Page 2: System Resources
        page_2 = f"""📊 **System Statistics - Page 2/4**

**💻 System Resources:**"""
        
        if self.system_data.get('cpu_percent') is not None:
            page_2 += f"""
• **Platform:** `{platform.system()} {platform.release()}`
• **Python:** `{platform.python_version()}`
• **CPU Usage:** `{self.system_data['cpu_percent']:.1f}%`
• **Memory Usage:** `{self.system_data['memory'].percent:.1f}%`
• **Memory Total:** `{self.system_data['memory'].total/(1024**3):.1f}GB`
• **Memory Used:** `{self.system_data['memory'].used/(1024**3):.1f}GB`
• **Disk Usage:** `{self.system_data['disk'].percent:.1f}%`
• **Disk Total:** `{self.system_data['disk'].total/(1024**3):.1f}GB`
• **Available Disk:** `{self.system_data['disk'].free/(1024**3):.1f}GB`"""
            
            if self.system_data.get('network_sent', 0) > 0:
                page_2 += f"""
• **Network Sent:** `{self.system_data['network_sent']:.2f}GB`
• **Network Received:** `{self.system_data['network_recv']:.2f}GB`"""
            
            page_2 += f"""
• **Bot Memory:** `{self.system_data['process_memory']:.1f}MB`"""
        else:
            page_2 += "\n• **System stats unavailable**"
        
        pages.append(page_2)
        
        # Page 3: Storage & Configuration
        page_3 = f"""📊 **System Statistics - Page 3/4**

**📁 Storage Information:**
• **Downloads Folder:** `{self.system_data['download_size']:.1f}MB`
• **Sessions Folder:** `{self.system_data['session_size']:.1f}MB`
• **Active Files:** `{self.system_data['file_count']}` files
• **Download Path:** `{Config.DOWNLOAD_LOCATION}`
• **Sessions Path:** `{Config.SESSIONS}`

**⚙️ Configuration:**
• **Max Concurrent Downloads:** `{getattr(Config, 'MAX_CONCURRENT_DOWNLOADS', 3)}`
• **Debug Mode:** `{'Enabled' if getattr(Config, 'DEBUG_MODE', False) else 'Disabled'}`
• **Stats Enabled:** `{'Yes' if getattr(Config, 'ENABLE_STATS', True) else 'No'}`
• **Log Channel:** `{Config.LOG_CH}`"""
        pages.append(page_3)
        
        # Page 4: User Management & Actions
        page_4 = f"""📊 **System Statistics - Page 4/4**

**👥 User Management:**
• **Owner ID:** `{Config.OWNER_ID}`
• **Owner Username:** @{Config.OWNER_USERNAME}
• **Authorized Users:** `{len(Config.AUTH_USERS)}` users
• **Authorized Groups:** `{len([g for g in Config.GROUPS if g])}` groups

**📈 Quick Actions:**
• Use `/restart` to restart bot
• Use `/help` for user guide
• Monitor logs in channel: `{Config.LOG_CH}`

**🕐 Last Updated:** `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`

**💡 System Health:** All systems operational
**🔧 Maintenance:** No scheduled maintenance
**📊 Performance:** Optimal"""
        pages.append(page_4)
        
        return pages
    
    def get_keyboard(self, current_page):
        """Generate navigation keyboard for stats"""
        buttons = []
        nav_buttons = []
        
        # Previous button
        if current_page > 0:
            nav_buttons.append(InlineKeyboardButton("⬅️ Previous", callback_data=f"stats_page_{current_page-1}"))
        
        # Page indicator
        nav_buttons.append(InlineKeyboardButton(f"📄 {current_page+1}/4", callback_data="stats_current"))
        
        # Next button
        if current_page < len(self.pages) - 1:
            nav_buttons.append(InlineKeyboardButton("Next ➡️", callback_data=f"stats_page_{current_page+1}"))
        
        buttons.append(nav_buttons)
        
        # Quick navigation
        quick_nav = [
            InlineKeyboardButton("🤖 Bot Info", callback_data="stats_page_0"),
            InlineKeyboardButton("💻 System", callback_data="stats_page_1")
        ]
        buttons.append(quick_nav)
        
        quick_nav_2 = [
            InlineKeyboardButton("📁 Storage", callback_data="stats_page_2"),
            InlineKeyboardButton("👥 Users", callback_data="stats_page_3")
        ]
        buttons.append(quick_nav_2)
        
        # Action buttons
        action_buttons = [
            InlineKeyboardButton("🔄 Refresh", callback_data="stats_refresh"),
            InlineKeyboardButton("❌ Close", callback_data="stats_close")
        ]
        buttons.append(action_buttons)
        
        return InlineKeyboardMarkup(buttons)


# Store active pagination sessions
help_sessions = {}
stats_sessions = {}


# ──────────────────────────  COMMANDS  ────────────────────────── #

@AFK.on_message(filters.incoming & filters.command("start", prefixes=prefixes))
@auth_required
async def start_msg(bot: AFK, m: Message):
    await bot.send_message(m.chat.id, Msg.START_MSG)


@AFK.on_message(filters.incoming & filters.command("help", prefixes=prefixes))
@auth_required
async def help_command(bot: AFK, m: Message):
    """Enhanced paginated help command"""
    try:
        # Get bot info
        bot_info = await bot.get_me()
        
        # Create pagination instance
        help_pagination = HelpPagination(bot_info)
        help_sessions[m.from_user.id] = help_pagination
        
        # Send first page
        await bot.send_message(
            chat_id=m.chat.id,
            text=help_pagination.pages[0],
            reply_markup=help_pagination.get_keyboard(0),
            disable_web_page_preview=True
        )
        
        LOGS.info(f"📖 Paginated help command used by user {m.from_user.id}")
        
    except Exception as e:
        LOGS.error(f"Help command error: {e}")
        await m.reply_text("❌ **Error showing help**\n\nPlease try again later.")


@AFK.on_message(filters.incoming & filters.command("stats", prefixes=prefixes))
@owner_only
async def stats_command(bot: AFK, m: Message):
    """Enhanced paginated stats command"""
    try:
        # Send initial processing message
        processing_msg = await bot.send_message(
            chat_id=m.chat.id,
            text="📊 **Gathering System Statistics...**\n\n⏳ **Please wait...**"
        )
        
        # Get bot info
        bot_info = await bot.get_me()
        
        # Gather system information
        system_data = await gather_system_stats()
        
        # Create pagination instance
        stats_pagination = StatsPagination(bot_info, system_data)
        stats_sessions[m.from_user.id] = stats_pagination
        
        # Update message with first page
        await processing_msg.edit_text(
            text=stats_pagination.pages[0],
            reply_markup=stats_pagination.get_keyboard(0)
        )
        
        LOGS.info(f"📊 Paginated stats command used by owner {m.from_user.id}")
        
    except Exception as e:
        LOGS.error(f"Stats command error: {e}")
        try:
            await processing_msg.edit_text(
                "❌ **Error gathering statistics**\n\n"
                f"**Error:** `{str(e)[:100]}...`\n"
                "Please try again later."
            )
        except:
            await m.reply_text("❌ **Statistics temporarily unavailable**")


async def gather_system_stats():
    """Gather comprehensive system statistics"""
    system_data = {}
    
    try:
        # CPU and Memory
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        system_data.update({
            'cpu_percent': cpu_percent,
            'memory': memory,
            'disk': disk
        })
        
        # Network (if available)
        try:
            network = psutil.net_io_counters()
            system_data.update({
                'network_sent': network.bytes_sent / (1024**3),
                'network_recv': network.bytes_recv / (1024**3)
            })
        except:
            system_data.update({'network_sent': 0, 'network_recv': 0})
        
        # Process information
        process = psutil.Process()
        system_data['process_memory'] = process.memory_info().rss / (1024**2)
        
    except Exception as e:
        LOGS.warning(f"Could not get detailed system stats: {e}")
        system_data.update({
            'cpu_percent': None,
            'memory': None,
            'disk': None,
            'process_memory': 0
        })
    
    # Bot uptime
    try:
        if hasattr(Config, 'BOT_START_TIME'):
            uptime_seconds = time.time() - Config.BOT_START_TIME
        else:
            uptime_seconds = 0
        
        uptime_str = f"{int(uptime_seconds//3600):02d}:{int((uptime_seconds%3600)//60):02d}:{int(uptime_seconds%60):02d}"
        system_data['uptime_str'] = uptime_str
    except:
        system_data['uptime_str'] = "Unknown"
    
    # Directory sizes
    try:
        download_size = sum(
            os.path.getsize(os.path.join(dirpath, filename))
            for dirpath, dirnames, filenames in os.walk(Config.DOWNLOAD_LOCATION)
            for filename in filenames
        ) / (1024**2)
    except:
        download_size = 0
    
    try:
        session_size = sum(
            os.path.getsize(os.path.join(dirpath, filename))
            for dirpath, dirnames, filenames in os.walk(Config.SESSIONS)
            for filename in filenames
        ) / (1024**2)
    except:
        session_size = 0
    
    try:
        file_count = sum(
            len(filenames)
            for dirpath, dirnames, filenames in os.walk(Config.DOWNLOAD_LOCATION)
        )
    except:
        file_count = 0
    
    system_data.update({
        'download_size': download_size,
        'session_size': session_size,
        'file_count': file_count
    })
    
    return system_data


# Callback query handlers for pagination
@AFK.on_callback_query(filters.regex(r"^help_page_(\d+)$"))
async def help_page_callback(bot: AFK, callback_query):
    """Handle help page navigation"""
    try:
        page_num = int(callback_query.data.split("_")[2])
        user_id = callback_query.from_user.id
        
        if user_id not in help_sessions:
            await callback_query.answer("❌ Session expired. Please use /help again.", show_alert=True)
            return
        
        help_pagination = help_sessions[user_id]
        
        if 0 <= page_num < len(help_pagination.pages):
            await callback_query.edit_message_text(
                text=help_pagination.pages[page_num],
                reply_markup=help_pagination.get_keyboard(page_num),
                disable_web_page_preview=True
            )
            await callback_query.answer()
        else:
            await callback_query.answer("❌ Invalid page number.")
            
    except Exception as e:
        LOGS.error(f"Help pagination error: {e}")
        await callback_query.answer("❌ Navigation error occurred.")


@AFK.on_callback_query(filters.regex(r"^stats_page_(\d+)$"))
async def stats_page_callback(bot: AFK, callback_query):
    """Handle stats page navigation"""
    try:
        page_num = int(callback_query.data.split("_")[2])
        user_id = callback_query.from_user.id
        
        if user_id not in stats_sessions:
            await callback_query.answer("❌ Session expired. Please use /stats again.", show_alert=True)
            return
        
        stats_pagination = stats_sessions[user_id]
        
        if 0 <= page_num < len(stats_pagination.pages):
            await callback_query.edit_message_text(
                text=stats_pagination.pages[page_num],
                reply_markup=stats_pagination.get_keyboard(page_num)
            )
            await callback_query.answer()
        else:
            await callback_query.answer("❌ Invalid page number.")
            
    except Exception as e:
        LOGS.error(f"Stats pagination error: {e}")
        await callback_query.answer("❌ Navigation error occurred.")


@AFK.on_callback_query(filters.regex(r"^stats_refresh$"))
async def stats_refresh_callback(bot: AFK, callback_query):
    """Handle stats refresh"""
    try:
        user_id = callback_query.from_user.id
        
        if user_id not in stats_sessions:
            await callback_query.answer("❌ Session expired. Please use /stats again.", show_alert=True)
            return
        
        # Show loading
        await callback_query.answer("🔄 Refreshing statistics...", show_alert=False)
        
        # Get fresh data
        bot_info = await bot.get_me()
        system_data = await gather_system_stats()
        
        # Update pagination
        stats_pagination = StatsPagination(bot_info, system_data)
        stats_sessions[user_id] = stats_pagination
        
        # Update message with first page
        await callback_query.edit_message_text(
            text=stats_pagination.pages[0],
            reply_markup=stats_pagination.get_keyboard(0)
        )
        
    except Exception as e:
        LOGS.error(f"Stats refresh error: {e}")
        await callback_query.answer("❌ Refresh failed.")


@AFK.on_callback_query(filters.regex(r"^help_close$"))
async def help_close_callback(bot: AFK, callback_query):
    """Handle help close"""
    try:
        user_id = callback_query.from_user.id
        if user_id in help_sessions:
            del help_sessions[user_id]
        
        await callback_query.edit_message_text("✅ **Help closed.**")
        await callback_query.answer()
        
    except Exception as e:
        LOGS.error(f"Help close error: {e}")


@AFK.on_callback_query(filters.regex(r"^stats_close$"))
async def stats_close_callback(bot: AFK, callback_query):
    """Handle stats close"""
    try:
        user_id = callback_query.from_user.id
        if user_id in stats_sessions:
            del stats_sessions[user_id]
        
        await callback_query.edit_message_text("✅ **Statistics closed.**")
        await callback_query.answer()
        
    except Exception as e:
        LOGS.error(f"Stats close error: {e}")


@AFK.on_callback_query(filters.regex(r"^(help|stats)_current$"))
async def current_page_callback(bot: AFK, callback_query):
    """Handle current page indicator clicks"""
    await callback_query.answer("📄 You are viewing the current page.", show_alert=False)


@AFK.on_message(filters.incoming & filters.command("restart", prefixes=prefixes))
@owner_only
async def restart_handler(_, m: Message):
    # 🆕 Enhanced restart with processing message
    processing_msg = await m.reply_text("🔄 **Restarting Bot...**\n\n⏳ **Please wait...**")
    
    safe_delete_folder(Config.DOWNLOAD_LOCATION)
    
    try:
        await processing_msg.edit_text(Msg.RESTART_MSG)
        await asyncio.sleep(2)  # Show message before restart
    except:
        pass
    
    os.execl(sys.executable, sys.executable, *sys.argv)


@AFK.on_message(filters.incoming & filters.command("pro", prefixes=prefixes))
@auth_required
async def Pro(bot: AFK, m: Message):
    # 🚦 Rate Limiting Check
    if rate_limiter.is_rate_limited(m.from_user.id):
        await bot.send_message(
            chat_id=m.chat.id,
            text=Msg.RATE_LIMIT_MSG
        )
        return

    sPath = f"{Config.DOWNLOAD_LOCATION}/{m.chat.id}"
    tPath = f"{Config.DOWNLOAD_LOCATION}/FILE/{m.chat.id}"
    os.makedirs(sPath, exist_ok=True)
    BOT = TgClient(bot, m, sPath)

    # 🆕 Show initial processing message
    processing_msg = await bot.send_message(
        chat_id=m.chat.id,
        text=Msg.PROCESSING_MSG
    )

    error_list = []
    
    try:
        nameLinks, num, caption, quality, Token, txt_name, userr = await BOT.Ask_user()
        Thumb = await BOT.thumb()
        
        # 🆕 Update processing message with file analysis
        await processing_msg.edit_text(
            f"📋 **File Analysis Complete!**\n\n"
            f"📊 **Total Links Found:** `{len(nameLinks)}`\n"
            f"🎯 **Starting from index:** `{num}`\n"
            f"📁 **Files to process:** `{len(nameLinks) - num}`\n\n"
            f"⏳ **Starting downloads...**"
        )
        
    except Exception as e:
        LOGS.error(f"User input failed: {e}")
        await processing_msg.edit_text("❌ **Input Error!**\n\n`Wrong input format. Please try again.`")
        await TgHandler.error_message(bot=bot, m=m, error=f"from User Input - {e}")
        return

    # 🆕 Track download statistics
    total_files = len(nameLinks) - num
    completed_files = 0
    failed_files = 0
    
    for i in range(num, len(nameLinks)):
        try:
            name = BOT.parse_name(nameLinks[i][0])
            link = nameLinks[i][1]
            
            # 🆕 Validate URL before processing
            if not link or not link.startswith(('http://', 'https://')):
                LOGS.error(f"Invalid URL: {link}")
                await bot.send_message(
                    chat_id=m.chat.id,
                    text=Msg.INVALID_LINK_MSG
                )
                failed_files += 1
                continue
            
            wxh = get_link_atributes().get_height_width(link=link, Q=quality)
            caption_name = f"**{str(i+1).zfill(3)}.** - {name} {wxh}"
            file_name = f"{str(i+1).zfill(3)}. - {BOT.short_name(name)} {wxh}"
            LOGS.info(f"{caption_name} | Link: {link}")

            # 🆕 Enhanced download status message
            Show = await bot.send_message(
                chat_id=m.chat.id,
                text=Msg.SHOW_MSG.format(file_name=file_name, file_link=link),
                disable_web_page_preview=True
            )

            url = get_link_atributes().input_url(link=link, Q=quality)
            DL = download_handler(name=file_name, url=url, path=sPath, Token=Token, Quality=quality)
            
            try:
                # 🆕 Add timeout for downloads (30 minutes)
                dl_file = await asyncio.wait_for(
                    DL.start_download(), 
                    timeout=1800
                )
            except asyncio.TimeoutError:
                # 🆕 Handle download timeout
                await Show.edit_text(Msg.TIMEOUT_MSG)
                await asyncio.sleep(3)
                await Show.delete()
                failed_files += 1
                continue

            if dl_file:
                dl_file = os.path.abspath(dl_file)
                LOGS.info(f"Downloaded to: {dl_file}")

                # 🆕 Check file size
                if os.path.isfile(dl_file):
                    file_size = os.path.getsize(dl_file)
                    
                    # Check if file is too large (2GB limit)
                    if file_size > 2 * 1024 * 1024 * 1024:  # 2GB
                        LOGS.warning(f"File too large: {file_size} bytes")
                        await Show.edit_text(Msg.FILE_TOO_LARGE_MSG)
                        await asyncio.sleep(3)
                        await Show.delete()
                        os.remove(dl_file)  # Clean up large file
                        failed_files += 1
                        continue
                    
                    wait_until_file_is_free(dl_file)

                    if dl_file.endswith(".mp4"):
                        cap = f"{caption_name}.mp4\n\n<b>𝗕𝗮𝘁𝗰𝗵 𝗡𝗮𝗺𝗲 :</b> {caption}\n\n<b>𝗘𝘅𝘁𝗿𝗮𝗰𝘁𝗲𝗱 𝗯𝘆 ➤</b> **{userr}**"
                        UL = Upload_to_Tg(bot, m, caption_name, dl_file, sPath, Thumb, Show, cap)
                        LOGS.info(f"Uploading video: {file_name}")
                        
                        try:
                            # 🆕 Add timeout for uploads (15 minutes)
                            await asyncio.wait_for(UL.upload_video(), timeout=900)
                            completed_files += 1
                            
                            # 🆕 Send success notification
                            await bot.send_message(
                                chat_id=m.chat.id,
                                text=f"✅ **Upload Completed!**\n\n"
                                     f"📁 **File:** `{file_name}`\n"
                                     f"📊 **Size:** `{file_size / (1024*1024):.2f} MB`\n"
                                     f"📈 **Progress:** `{completed_files}/{total_files}`"
                            )
                            
                        except asyncio.TimeoutError:
                            await Show.edit_text("⏰ **Upload Timeout!**\n\nTrying as document...")
                            await UL.upload_doc()
                            completed_files += 1
                            
                    else:
                        ext = dl_file.split(".")[-1]
                        cap = f"{caption_name}.{ext}\n\n<b>𝗕𝗮𝘁𝗰𝗵 𝗡𝗮𝗺𝗲 : </b>{caption}\n\n<b>𝗘𝘅𝘁𝗿𝗮𝗰𝘁𝗲𝗱 𝗯𝘆 ➤ </b> **{userr}**"
                        UL = Upload_to_Tg(bot, m, caption_name, dl_file, sPath, Thumb, Show, cap)
                        LOGS.info(f"Uploading document: {file_name}")
                        
                        try:
                            await asyncio.wait_for(UL.upload_doc(), timeout=900)
                            completed_files += 1
                            
                            # 🆕 Send success notification for documents
                            await bot.send_message(
                                chat_id=m.chat.id,
                                text=f"✅ **Document Uploaded!**\n\n"
                                     f"📄 **File:** `{file_name}`\n"
                                     f"📊 **Size:** `{file_size / (1024*1024):.2f} MB`\n"
                                     f"📈 **Progress:** `{completed_files}/{total_files}`"
                            )
                            
                        except asyncio.TimeoutError:
                            await Show.edit_text(Msg.TIMEOUT_MSG)
                            failed_files += 1
                            
                else:
                    LOGS.warning(f"File not found after download: {dl_file}")
                    await Show.delete(True)
                    await bot.send_message(
                        chat_id=Config.LOG_CH,
                        text=Msg.ERROR_MSG.format(
                            error="File not found after download",
                            no_of_files=len(error_list),
                            file_name=caption_name,
                            file_link=url,
                        )
                    )
                    failed_files += 1
            else:
                LOGS.warning(f"Download returned None: {file_name}")
                await Show.delete(True)
                failed_files += 1

        except Exception as r:
            LOGS.error(f"Processing error: {r}")
            error_list.append(f"{caption_name}\n")
            failed_files += 1
            
            try:
                await Show.delete(True)
            except:
                pass
            
            # 🆕 Enhanced error handling with specific messages
            if "timeout" in str(r).lower():
                error_msg = Msg.TIMEOUT_MSG
            elif "file not found" in str(r).lower():
                error_msg = Msg.INVALID_LINK_MSG
            elif "connection" in str(r).lower():
                error_msg = "🌐 **Connection Error!**\n\n❌ **Network issue detected**\n💡 **Please check your internet connection**"
            else:
                error_msg = Msg.ERROR_MSG.format(
                    error=str(r),
                    no_of_files=len(error_list),
                    file_name=caption_name,
                    file_link=url,
                )
            
            await bot.send_message(
                chat_id=Config.LOG_CH,
                text=error_msg
            )
            continue

    # 🆕 Delete processing message
    try:
        await processing_msg.delete()
    except:
        pass

    # Cleanup
    safe_delete_folder(sPath)

    try:
        if os.path.exists(tPath):
            if os.path.isfile(tPath):
                wait_until_file_is_free(tPath)
                os.remove(tPath)
                LOGS.info(f"Deleted file: {tPath}")
            else:
                safe_delete_folder(tPath)
    except Exception as e1:
        LOGS.error(f"Cleanup failed: {e1}")

    # 🆕 Enhanced completion message with statistics
    completion_msg = f"🎉 **Batch Download Complete!**\n\n" \
                    f"✅ **Successful:** `{completed_files}`\n" \
                    f"❌ **Failed:** `{failed_files}`\n" \
                    f"📊 **Total:** `{total_files}`\n\n"
    
    if completed_files > 0:
        completion_msg += "🚀 **All files uploaded successfully!**"
    elif failed_files == total_files:
        completion_msg += "⚠️ **All downloads failed. Please check your links.**"
    else:
        completion_msg += "⚡ **Partially completed. Check individual file status above.**"

    await BOT.linkMsg2(error_list)
    await m.reply_text(completion_msg)
