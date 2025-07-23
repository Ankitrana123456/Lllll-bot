#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# (c) AFK

from hachoir.metadata import extractMetadata
from hachoir.parser import createParser
import subprocess
import wget
import os
import time
import requests
import asyncio
import datetime
from helpers.toolkit import Tools, Vidtools
from main import Config, Msg, Store, LOGGER as LOGS
from helpers.prog_bar import progress_for_pyrogram
from pyrogram import Client as AFK
from pyrogram.types import Message


class Upload_to_Tg:
    def __init__(self, bot: AFK, m: Message, name: str, file_path, path, Thumb, show_msg: Message, caption: str) -> None:
        self.bot = bot
        self.m = m
        self.name = name
        self.file_path = file_path
        self.path = path
        self.thumb = Thumb
        self.temp_dir = f"{path}/{name}"
        self.show_msg = show_msg
        self.caption = caption
        self.upload_start_time = time.time()

    # 🆕 Enhanced file validation
    async def validate_file(self):
        """Comprehensive file validation before upload"""
        try:
            if not os.path.exists(self.file_path):
                LOGS.error(f"❌ File not found: {self.file_path}")
                await self.show_msg.edit_text("❌ **File Not Found!**\n\n`The file was not found for upload.`")
                return False

            file_size = os.path.getsize(self.file_path)
            
            # Check if file is empty
            if file_size == 0:
                LOGS.error(f"❌ Empty file detected: {self.file_path}")
                await self.show_msg.edit_text("❌ **Empty File!**\n\n`The file appears to be empty.`")
                return False
            
            # Check file size limits (2GB for Telegram)
            max_size = 2 * 1024 * 1024 * 1024  # 2GB
            if file_size > max_size:
                LOGS.error(f"❌ File too large: {file_size / (1024*1024*1024):.2f}GB")
                await self.show_msg.edit_text(Msg.FILE_TOO_LARGE_MSG)
                return False
            
            # Log file info
            LOGS.info(f"✅ File validation passed: {file_size / (1024*1024):.2f} MB")
            return True
            
        except Exception as e:
            LOGS.error(f"File validation error: {e}")
            await self.show_msg.edit_text("❌ **Validation Error!**\n\n`Could not validate file.`")
            return False

    async def get_thumb_duration(self):
        """Enhanced thumbnail and duration extraction"""
        duration = 0
        thumbnail = None
        
        # 🆕 Show processing status
        try:
            await self.show_msg.edit_text(
                "🔍 **Analyzing Video...**\n\n"
                "⏳ **Extracting metadata and generating thumbnail**"
            )
        except:
            pass
        
        # Wait a moment to ensure file is completely written
        await asyncio.sleep(1)
        
        # Check if file exists and is accessible
        if not os.path.exists(self.file_path):
            LOGS.error(f"❌ File not found: {self.file_path}")
            return 0, None
            
        # 🆕 Enhanced duration extraction with multiple fallbacks
        try:
            duration = Vidtools.get_duration(self.file_path)
            if duration:
                LOGS.info(f"✅ Duration from hachoir: {duration}s ({duration//60}:{duration%60:02d})")
        except Exception as e:
            LOGS.warning(f"⚠️ Hachoir duration failed: {e}")
            try:
                duration = int(Tools.duration(self.file_path))
                LOGS.info(f"✅ Duration from ffprobe: {duration}s ({duration//60}:{duration%60:02d})")
            except Exception as e2:
                LOGS.warning(f"⚠️ FFprobe duration failed: {e2}")
                # 🆕 Fallback duration estimation based on file size
                try:
                    file_size = os.path.getsize(self.file_path)
                    # Rough estimate: 1MB = ~8 seconds for average quality video
                    estimated_duration = max(1, int(file_size / (1024 * 1024) * 8))
                    duration = min(estimated_duration, 7200)  # Cap at 2 hours
                    LOGS.info(f"📊 Estimated duration: {duration}s (based on file size)")
                except:
                    duration = 0

        # 🆕 Enhanced thumbnail generation with multiple methods
        try:
            # Method 1: Download from URL
            if self.thumb and self.thumb.startswith(("http://", "https://")):
                try:
                    thumbnail_path = f"{self.temp_dir}.jpg"
                    LOGS.info("🌐 Downloading thumbnail from URL...")
                    
                    # Use requests instead of wget for better error handling
                    response = requests.get(self.thumb, timeout=30, stream=True)
                    if response.status_code == 200:
                        with open(thumbnail_path, 'wb') as f:
                            for chunk in response.iter_content(chunk_size=8192):
                                f.write(chunk)
                        
                        if os.path.exists(thumbnail_path) and os.path.getsize(thumbnail_path) > 0:
                            thumbnail = thumbnail_path
                            LOGS.info(f"✅ Downloaded thumbnail from URL: {thumbnail}")
                        else:
                            LOGS.warning("⚠️ Downloaded thumbnail is empty")
                    else:
                        LOGS.warning(f"⚠️ Thumbnail download failed: HTTP {response.status_code}")
                        
                except Exception as e:
                    LOGS.warning(f"⚠️ Failed to download thumbnail from URL: {e}")
                    
            # Method 2: Use existing file
            elif self.thumb and os.path.isfile(self.thumb):
                if os.path.getsize(self.thumb) > 0:
                    thumbnail = self.thumb
                    LOGS.info(f"✅ Using existing thumbnail: {thumbnail}")
                else:
                    LOGS.warning("⚠️ Existing thumbnail file is empty")
                    
            # Method 3: Generate from video
            if not thumbnail and duration > 0:
                try:
                    LOGS.info("📸 Generating thumbnail from video...")
                    # Try at multiple timestamps for better thumbnail
                    timestamps = [duration // 4, duration // 2, duration * 3 // 4]
                    
                    for timestamp in timestamps:
                        try:
                            thumbnail = await Vidtools.take_screen_shot(
                                self.file_path, self.name, self.path, timestamp
                            )
                            if thumbnail and os.path.exists(thumbnail) and os.path.getsize(thumbnail) > 0:
                                LOGS.info(f"✅ Generated thumbnail at {timestamp}s: {thumbnail}")
                                break
                        except Exception as e:
                            LOGS.warning(f"⚠️ Screenshot at {timestamp}s failed: {e}")
                            continue
                            
                except Exception as e:
                    LOGS.warning(f"⚠️ Screenshot generation failed: {e}")
            
            # Method 4: FFmpeg fallback
            if not thumbnail:
                try:
                    LOGS.info("🎬 Trying FFmpeg thumbnail generation...")
                    thumbnail_path = f"{self.temp_dir}.jpg"
                    
                    # Try multiple timestamps with FFmpeg
                    timestamps = ["00:00:01", "00:00:05", "00:00:10"] if duration > 10 else ["00:00:01"]
                    
                    for ts in timestamps:
                        cmd = f'ffmpeg -i "{self.file_path}" -ss {ts} -vframes 1 -vf scale=320:240 -y "{thumbnail_path}"'
                        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
                        
                        if result.returncode == 0 and os.path.exists(thumbnail_path) and os.path.getsize(thumbnail_path) > 0:
                            thumbnail = thumbnail_path
                            LOGS.info(f"✅ FFmpeg thumbnail created at {ts}: {thumbnail}")
                            break
                        else:
                            LOGS.warning(f"⚠️ FFmpeg thumbnail failed at {ts}")
                            
                except Exception as e:
                    LOGS.error(f"❌ FFmpeg fallback failed: {e}")
                    
            # 🆕 Thumbnail validation
            if thumbnail:
                try:
                    thumb_size = os.path.getsize(thumbnail)
                    if thumb_size < 100:  # Suspiciously small thumbnail
                        LOGS.warning(f"⚠️ Thumbnail suspiciously small ({thumb_size} bytes), removing")
                        os.remove(thumbnail)
                        thumbnail = None
                    else:
                        LOGS.info(f"📸 Thumbnail ready: {thumb_size / 1024:.1f} KB")
                except:
                    pass
                    
        except Exception as e:
            LOGS.error(f"❌ Thumbnail generation error: {e}")
            thumbnail = None
            
        return duration, thumbnail

    async def get_doc_thumb(self):
        """Enhanced document thumbnail handling"""
        try:
            LOGS.info("🖼️ Processing document thumbnail...")
            
            if self.thumb and self.thumb.startswith(("http://", "https://")):
                try:
                    doc_thumbnail_path = f"{self.temp_dir}.jpg"
                    response = requests.get(self.thumb, timeout=30, stream=True)
                    
                    if response.status_code == 200:
                        with open(doc_thumbnail_path, 'wb') as f:
                            for chunk in response.iter_content(chunk_size=8192):
                                f.write(chunk)
                        
                        if os.path.exists(doc_thumbnail_path) and os.path.getsize(doc_thumbnail_path) > 0:
                            LOGS.info(f"✅ Document thumbnail downloaded: {doc_thumbnail_path}")
                            return doc_thumbnail_path
                        else:
                            LOGS.warning("⚠️ Downloaded document thumbnail is empty")
                            
                except Exception as e:
                    LOGS.warning(f"⚠️ Failed to download document thumbnail: {e}")
                    
            elif self.thumb and os.path.isfile(self.thumb):
                if os.path.getsize(self.thumb) > 0:
                    LOGS.info(f"✅ Using existing document thumbnail: {self.thumb}")
                    return self.thumb
                else:
                    LOGS.warning("⚠️ Existing document thumbnail file is empty")
                
            # 🆕 Generate default document thumbnail
            try:
                default_thumb_path = f"{self.temp_dir}_doc.jpg"
                # Create a simple colored thumbnail for documents
                cmd = f'ffmpeg -f lavfi -i color=c=blue:size=320x240:d=1 -vframes 1 "{default_thumb_path}"'
                result = subprocess.run(cmd, shell=True, capture_output=True, timeout=10)
                
                if result.returncode == 0 and os.path.exists(default_thumb_path):
                    LOGS.info("✅ Generated default document thumbnail")
                    return default_thumb_path
            except:
                pass
                
            return None
            
        except Exception as e:
            LOGS.error(f"❌ Document thumbnail error: {e}")
            return None

    # 🆕 Enhanced upload statistics
    async def log_upload_stats(self, upload_type="video", success=True):
        """Log detailed upload statistics"""
        try:
            file_size = os.path.getsize(self.file_path)
            upload_duration = time.time() - self.upload_start_time
            
            stats_msg = f"📊 **Upload Statistics:**\n" \
                       f"📁 **Type:** `{upload_type.upper()}`\n" \
                       f"📏 **Size:** `{file_size / (1024*1024):.2f} MB`\n" \
                       f"⏱️ **Duration:** `{upload_duration:.1f}s`\n" \
                       f"🚀 **Speed:** `{(file_size / (1024*1024)) / max(upload_duration, 1):.2f} MB/s`\n" \
                       f"✅ **Status:** `{'SUCCESS' if success else 'FAILED'}`"
            
            LOGS.info(stats_msg.replace('*', '').replace('`', ''))
            
            # Send stats to user
            if success:
                await self.bot.send_message(
                    chat_id=self.m.chat.id,
                    text=f"🎉 **Upload Complete!**\n\n{stats_msg}"
                )
                
        except Exception as e:
            LOGS.warning(f"Could not log upload stats: {e}")

    async def upload_video(self):
        """Enhanced video upload with comprehensive error handling and user feedback"""
        try:
            LOGS.info(f"🎬 Starting video upload for: {self.file_path}")
            self.upload_start_time = time.time()
            
            # 🆕 File validation
            if not await self.validate_file():
                return
                
            file_size = os.path.getsize(self.file_path)
            
            # 🆕 Update progress message
            await self.show_msg.edit_text(
                f"🎬 **Preparing Video Upload...**\n\n"
                f"📁 **File:** `{self.name}`\n"
                f"📊 **Size:** `{file_size / (1024*1024):.2f} MB`\n\n"
                f"🔍 **Analyzing video metadata...**"
            )
                
            duration, thumbnail = await self.get_thumb_duration()
            
            # Try to get video dimensions
            try:
                w, h = Vidtools.get_width_height(self.file_path)
                LOGS.info(f"📺 Video dimensions: {w}x{h}")
            except Exception as e:
                LOGS.warning(f"⚠️ Could not get dimensions: {e}")
                w, h = 1280, 720
            
            # 🆕 Update progress with metadata info
            try:
                await self.show_msg.edit_text(
                    f"📤 **Starting Video Upload...**\n\n"
                    f"📁 **File:** `{self.name}`\n"
                    f"📊 **Size:** `{file_size / (1024*1024):.2f} MB`\n"
                    f"⏱️ **Duration:** `{duration//60}:{duration%60:02d}`\n"
                    f"📺 **Resolution:** `{w}x{h}`\n\n"
                    f"🚀 **Uploading to Telegram...**"
                )
            except:
                pass
            
            start_time = time.time()
            
            try:
                await self.bot.send_video(
                    chat_id=self.m.chat.id,
                    video=self.file_path,
                    supports_streaming=True,
                    caption=self.caption,
                    duration=duration if duration > 0 else None,
                    thumb=thumbnail,
                    width=w,
                    height=h,
                    progress=progress_for_pyrogram,
                    progress_args=(
                        Msg.CMD_MSG_2.format(file_name=f"{self.name}"), 
                        self.show_msg, 
                        start_time
                    )
                )
                
                LOGS.info("✅ Video uploaded successfully")
                await self.log_upload_stats("video", True)
                
            except Exception as e:
                LOGS.error(f"❌ Video upload failed, trying as document: {e}")
                
                # 🆕 Enhanced fallback message
                try:
                    await self.show_msg.edit_text(
                        "⚠️ **Video Upload Failed!**\n\n"
                        "🔄 **Trying as document...**\n"
                        "📄 **This may take a moment**"
                    )
                except:
                    pass
                
                try:
                    await self.bot.send_document(
                        chat_id=self.m.chat.id,
                        document=self.file_path,
                        caption=f"📄 **Uploaded as Document**\n\n{self.caption}",
                        thumb=thumbnail,
                        progress=progress_for_pyrogram,
                        progress_args=(
                            Msg.CMD_MSG_2.format(file_name=f"{self.name}"), 
                            self.show_msg, 
                            start_time
                        )
                    )
                    LOGS.info("✅ File uploaded as document successfully")
                    await self.log_upload_stats("document", True)
                    
                except Exception as e2:
                    LOGS.error(f"❌ Document upload also failed: {e2}")
                    await self.show_msg.edit_text(
                        "❌ **Upload Failed!**\n\n"
                        "⚠️ **Both video and document upload failed**\n"
                        "💡 **The file might be corrupted or too large**\n\n"
                        "🔄 **Please try again with a different file**"
                    )
                    await self.log_upload_stats("video", False)
                    raise e2
            
        except Exception as e:
            LOGS.error(f"❌ Upload process error: {e}")
            try:
                # 🆕 Enhanced error message based on error type
                if "timeout" in str(e).lower():
                    await self.show_msg.edit_text(Msg.TIMEOUT_MSG)
                elif "network" in str(e).lower() or "connection" in str(e).lower():
                    await self.show_msg.edit_text(
                        "🌐 **Network Error!**\n\n"
                        "❌ **Upload failed due to network issues**\n"
                        "💡 **Please check your internet connection**"
                    )
                elif "file" in str(e).lower():
                    await self.show_msg.edit_text(
                        "📁 **File Error!**\n\n"
                        "❌ **There was an issue with the file**\n"
                        "💡 **The file might be corrupted**"
                    )
                else:
                    await self.show_msg.edit_text(
                        "❌ **Upload Error!**\n\n"
                        f"⚠️ **Error:** `{str(e)[:100]}...`\n"
                        "💡 **Please try again later**"
                    )
            except:
                pass
            raise e
        finally:
            # Cleanup
            await self.cleanup_files()

    async def upload_doc(self):
        """Enhanced document upload with comprehensive features"""
        try:
            LOGS.info(f"📄 Starting document upload for: {self.file_path}")
            self.upload_start_time = time.time()
            
            # 🆕 File validation
            if not await self.validate_file():
                return
                
            file_size = os.path.getsize(self.file_path)
            file_ext = os.path.splitext(self.file_path)[1].upper()
            
            # 🆕 Update progress message with file info
            await self.show_msg.edit_text(
                f"📄 **Preparing Document Upload...**\n\n"
                f"📁 **File:** `{self.name}`\n"
                f"📊 **Size:** `{file_size / (1024*1024):.2f} MB`\n"
                f"📋 **Type:** `{file_ext or 'Unknown'}`\n\n"
                f"🔍 **Processing thumbnail...**"
            )
                
            start_time = time.time()
            doc_thumb = await self.get_doc_thumb()
            
            # 🆕 Enhanced upload message
            try:
                await self.show_msg.edit_text(
                    f"📤 **Uploading Document...**\n\n"
                    f"📁 **File:** `{self.name}`\n"
                    f"📊 **Size:** `{file_size / (1024*1024):.2f} MB`\n"
                    f"📋 **Type:** `{file_ext or 'Unknown'}`\n\n"
                    f"🚀 **Uploading to Telegram...**"
                )
            except:
                pass
            
            await self.bot.send_document(
                chat_id=self.m.chat.id,
                document=self.file_path,
                caption=self.caption,
                thumb=doc_thumb,
                progress=progress_for_pyrogram,
                progress_args=(
                    Msg.CMD_MSG_2.format(file_name=f"{self.name}"), 
                    self.show_msg, 
                    start_time
                )
            )
            
            LOGS.info("✅ Document uploaded successfully")
            await self.log_upload_stats("document", True)
            
        except Exception as e:
            LOGS.error(f"❌ Document upload error: {e}")
            
            try:
                # 🆕 Enhanced error messages
                if "timeout" in str(e).lower():
                    await self.show_msg.edit_text(Msg.TIMEOUT_MSG)
                elif "too large" in str(e).lower():
                    await self.show_msg.edit_text(Msg.FILE_TOO_LARGE_MSG)
                else:
                    await self.show_msg.edit_text(
                        "❌ **Document Upload Failed!**\n\n"
                        f"⚠️ **Error:** `{str(e)[:100]}...`\n"
                        "💡 **Please try again or contact support**"
                    )
            except:
                pass
                
            await self.log_upload_stats("document", False)
            raise e
        finally:
            await self.cleanup_files()

    async def cleanup_files(self):
        """Enhanced cleanup with detailed logging and error handling"""
        LOGS.info("🧹 Starting file cleanup...")
        
        # 🆕 Enhanced thumbnail cleanup
        thumbnail_files = [
            f"{self.temp_dir}.jpg",
            f"{self.path}/{self.name}.jpg",
            f"{self.temp_dir}_doc.jpg",  # Default doc thumbnail
        ]
        
        cleaned_thumbs = 0
        for thumb_file in thumbnail_files:
            try:
                if os.path.exists(thumb_file):
                    file_size = os.path.getsize(thumb_file)
                    os.remove(thumb_file)
                    cleaned_thumbs += 1
                    LOGS.info(f"🗑️ Removed thumbnail: {thumb_file} ({file_size / 1024:.1f} KB)")
            except Exception as e:
                LOGS.warning(f"⚠️ Could not remove thumbnail {thumb_file}: {e}")
        
        # 🆕 Enhanced main file cleanup
        try:
            if os.path.exists(self.file_path):
                file_size = os.path.getsize(self.file_path)
                os.remove(self.file_path)
                LOGS.info(f"🗑️ Removed main file: {self.file_path} ({file_size / (1024*1024):.2f} MB)")
            else:
                LOGS.warning(f"⚠️ Main file not found for cleanup: {self.file_path}")
        except Exception as e:
            LOGS.error(f"❌ Error removing main file {self.file_path}: {e}")
        
        # 🆕 Enhanced progress message cleanup
        try:
            await self.show_msg.delete(True)
            LOGS.info("🗑️ Deleted progress message")
        except Exception as e:
            LOGS.error(f"❌ Error deleting show message: {e}")
        
        # 🆕 Cleanup summary
        total_cleanup_time = time.time() - self.upload_start_time
        LOGS.info(f"✅ Cleanup completed - Removed {cleaned_thumbs} thumbnails in {total_cleanup_time:.1f}s total")

    # 🆕 Additional utility methods
    async def send_success_notification(self, upload_type="video"):
        """Send a beautiful success notification"""
        try:
            file_size = os.path.getsize(self.file_path)
            upload_duration = time.time() - self.upload_start_time
            
            success_msg = f"🎉 **Upload Successful!**\n\n" \
                         f"✅ **{upload_type.title()} uploaded successfully**\n" \
                         f"📁 **File:** `{self.name}`\n" \
                         f"📊 **Size:** `{file_size / (1024*1024):.2f} MB`\n" \
                         f"⏱️ **Time:** `{upload_duration:.1f}s`\n\n" \
                         f"📱 **Check your chat above** ⬆️"
            
            await self.bot.send_message(
                chat_id=self.m.chat.id,
                text=success_msg
            )
        except Exception as e:
            LOGS.warning(f"Could not send success notification: {e}")
