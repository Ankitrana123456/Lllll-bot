from pyrogram import filters, Client as ace
from main import LOGGER as LOGS, prefixes
from pyrogram.types import Message
from main import Config
import os
import subprocess
import tgcrypto
import shutil
import sys
from handlers.uploader import Upload_to_Tg
from helpers.auth import auth_required  
from handlers.tg import TgClient
import requests
import wget
import img2pdf
import time

@ace.on_message(filters.incoming & filters.command("ytc", prefixes=prefixes))
@auth_required
async def ytc_handler(bot: ace, m: Message):
    path = f"{Config.DOWNLOAD_LOCATION}/{m.chat.id}"
    tPath = f"{Config.DOWNLOAD_LOCATION}/PHOTO/{m.chat.id}"
    os.makedirs(path, exist_ok=True)
    os.makedirs(tPath, exist_ok=True)

    try:
        pages_msg = await bot.ask(m.chat.id, 
            "📚 YCT Publication Downloader\n\n" +
            "Format:\n" +
            "1:50\n" +
            "Book Name\n" +
            "Book ID\n\n" +
            "Example:\n" +
            "1:100\n" +
            "Mathematics Class 12\n" +
            "2638"
        )
        
        try:
            pages, Book_Name, bid = str(pages_msg.text).split("\n")
        except ValueError:
            await m.reply_text("❌ Invalid Format!\n\nPlease provide exactly 3 lines:\n1. Page range\n2. Book name\n3. Book ID")
            return


        # Validate inputs
        try:
            page = pages.split(":")
            page_1 = int(page[0])
            last_page = int(page[1]) + 1
            
            if page_1 >= last_page or page_1 < 1:
                await m.reply_text("❌ **Invalid page range!** Start page must be less than end page and both must be positive.")
                return
                
        except (ValueError, IndexError):
            await m.reply_text("❌ **Invalid page format!** Use format: `1:50`")
            return

        # Validate Book ID
        try:
            book_id = int(bid)
        except ValueError:
            await m.reply_text("❌ **Invalid Book ID!** Must be a number.")
            return

        # Updated API URL based on your request information
        # Using the actual YCT Publication API endpoint
        api_url = "https://yctpublication.com/master/api/MasterController/getPdfPage?book_id={bid}&page_no={pag}&user_id=14593"

        Show = await bot.send_message(
            m.chat.id,
            f"📚 **Starting YCT Download**\n\n"
            f"📖 **Book:** {Book_Name}\n"
            f"📄 **Pages:** {pages}\n"
            f"🆔 **ID:** {bid}\n\n"
            f"🔍 **Testing API connection...**"
        )

        # Test API connection with first page
        test_url = api_url.format(bid=bid, pag=page_1)
        try:
            test_response = requests.get(test_url, timeout=15)
            if test_response.status_code != 200:
                await Show.edit_text(
                    f"❌ **API Connection Failed!**\n\n"
                    f"**Status Code:** {test_response.status_code}\n"
                    f"**Book ID:** {bid}\n\n"
                    f"**Possible issues:**\n"
                    f"• Book ID `{bid}` doesn't exist\n"
                    f"• Book requires authentication\n"
                    f"• Server is temporarily down\n\n"
                    f"**Solutions:**\n"
                    f"• Verify Book ID from YCT website\n"
                    f"• Try a different book ID\n"
                    f"• Contact bot owner if issue persists"
                )
                return
            
            # Check if response contains actual image data
            if len(test_response.content) < 1000:
                await Show.edit_text(
                    f"❌ **Invalid Response!**\n\n"
                    f"**Book ID `{bid}` returned empty or invalid data**\n\n"
                    f"**This usually means:**\n"
                    f"• Book doesn't exist\n"
                    f"• Page number is out of range\n"
                    f"• Book requires special access\n\n"
                    f"**Try:**\n"
                    f"• Different Book ID\n"
                    f"• Smaller page range (1:5)\n"
                    f"• Verify book exists on YCT website"
                )
                return
                
        except requests.RequestException as e:
            await Show.edit_text(
                f"❌ **Network Error!**\n\n"
                f"**Error:** `{str(e)}`\n\n"
                f"**Solutions:**\n"
                f"• Check internet connection\n"
                f"• Try again later\n"
                f"• YCT servers might be down"
            )
            return

        await Show.edit_text(f"✅ **API Connection Successful!**\n\n📚 **Downloading {Book_Name}**\n📄 **Pages:** {pages}")

        # Enhanced download function with better error handling
        def download_page_with_retry(page_url, file_path, page_num, retries=3):
            for attempt in range(retries):
                try:
                    response = requests.get(page_url, timeout=30)
                    if response.status_code == 200:
                        # Check if response contains actual image data
                        if len(response.content) > 1000:
                            with open(file_path, 'wb') as f:
                                f.write(response.content)
                            return True
                        else:
                            LOGS.warning(f"Page {page_num} returned small content: {len(response.content)} bytes")
                            return False
                    else:
                        LOGS.warning(f"Page {page_num} returned status: {response.status_code}")
                        return False
                except Exception as e:
                    LOGS.warning(f"Download attempt {attempt+1} for page {page_num} failed: {e}")
                    if attempt < retries - 1:
                        time.sleep(2)  # Wait before retry
            return False

        IMG_LIST = []
        failed_pages = []
        successful_pages = 0

        for i in range(page_1, last_page):
            try:
                page_url = api_url.format(pag=i, bid=bid)
                file_name = f"{str(i).zfill(3)}_page_{str(i)}"
                file_path = f"{tPath}/{file_name}.jpg"
                
                if download_page_with_retry(page_url, file_path, i):
                    IMG_LIST.append(file_path)
                    successful_pages += 1
                    LOGS.info(f"✅ Downloaded page {i}")
                else:
                    failed_pages.append(i)
                    LOGS.error(f"❌ Failed to download page {i}")
                
                # Update progress every 5 pages or on last page
                if i % 5 == 0 or i == last_page - 1:
                    progress = f"📚 **Downloading Pages...**\n\n"
                    progress += f"✅ **Success:** {successful_pages}\n"
                    progress += f"❌ **Failed:** {len(failed_pages)}\n"
                    progress += f"📊 **Progress:** {i-page_1+1}/{last_page-page_1}"
                    
                    if failed_pages and len(failed_pages) <= 10:
                        progress += f"\n⚠️ **Failed pages:** {', '.join(map(str, failed_pages))}"
                    elif len(failed_pages) > 10:
                        progress += f"\n⚠️ **Failed pages:** {', '.join(map(str, failed_pages[:10]))} and {len(failed_pages)-10} more..."
                    
                    await Show.edit_text(progress)
                    
            except Exception as e:
                failed_pages.append(i)
                LOGS.error(f"❌ Error processing page {i}: {e}")
                continue

        # Check if we have any successful downloads
        if not IMG_LIST:
            await Show.edit_text(
                f"❌ **Download Failed!**\n\n"
                f"**No pages were downloaded successfully.**\n\n"
                f"**Attempted:** {last_page - page_1} pages\n"
                f"**Failed:** {len(failed_pages)} pages\n\n"
                f"**Possible causes:**\n"
                f"• Book ID `{bid}` is invalid\n"
                f"• Page range `{pages}` doesn't exist\n"
                f"• Book requires authentication\n"
                f"• Server is blocking requests\n\n"
                f"**Recommendations:**\n"
                f"• Try Book ID from working YCT links\n"
                f"• Use smaller range (1:5) for testing\n"
                f"• Verify book exists on YCT website\n"
                f"• Contact support with Book ID {bid}"
            )
            return

        # Create PDF from successful downloads
        try:
            await Show.edit_text(f"📄 **Creating PDF...**\n\n⏳ **Converting {len(IMG_LIST)} images to PDF**")
            
            def create_pdf(title, imagelist):
                # Clean title for filename
                safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()
                pdf_path = f"{path}/{safe_title}.pdf"
                with open(pdf_path, "wb") as f:
                    f.write(img2pdf.convert(imagelist))
                return pdf_path

            PDF = create_pdf(Book_Name, IMG_LIST)
            
            # Create detailed caption
            caption = f"📚 **{Book_Name}**\n\n"
            caption += f"📄 **Requested Pages:** {pages}\n"
            caption += f"✅ **Downloaded:** {successful_pages} pages\n"
            caption += f"🆔 **Book ID:** {bid}\n"
            
            if failed_pages:
                caption += f"⚠️ **Failed Pages:** {len(failed_pages)}\n"
                if len(failed_pages) <= 10:
                    caption += f"📋 **Failed:** {', '.join(map(str, failed_pages))}\n"
            
            caption += f"📅 **Generated:** {time.strftime('%Y-%m-%d %H:%M')}\n"
            caption += f"🤖 **Via:** YCT Publication Downloader"
            
            # Upload PDF with corrected parameters
            UL = Upload_to_Tg(bot=bot, m=m, name=Book_Name, file_path=PDF,
                              path=path, Thumb="", show_msg=Show, caption=caption)
            await UL.upload_doc()
            
            # Send comprehensive summary
            summary = f"🎉 **YCT Download Complete!**\n\n"
            summary += f"📚 **Book:** `{Book_Name}`\n"
            summary += f"🆔 **Book ID:** `{bid}`\n"
            summary += f"📄 **Requested:** `{pages}` ({last_page - page_1} pages)\n"
            summary += f"✅ **Downloaded:** `{successful_pages}` pages\n"
            
            if failed_pages:
                summary += f"❌ **Failed:** `{len(failed_pages)}` pages\n"
                if len(failed_pages) <= 20:
                    summary += f"📋 **Failed pages:** `{', '.join(map(str, failed_pages))}`\n"
                else:
                    summary += f"📋 **Failed pages:** `{', '.join(map(str, failed_pages[:20]))}` ... and {len(failed_pages)-20} more\n"
            
            summary += f"\n💡 **Success Rate:** `{(successful_pages/(last_page-page_1)*100):.1f}%`"
            
            await m.reply_text(summary)
            
        except Exception as e:
            await Show.edit_text(f"❌ **PDF Creation Failed:** `{str(e)}`")
            LOGS.error(f"PDF creation error: {e}")
            
    except Exception as e:
        await m.reply_text(f"❌ **YTC Download Error:** `{str(e)}`")
        LOGS.error(f"YTC command error: {e}")
    finally:
        # Cleanup temporary files
        try:
            if os.path.exists(tPath):
                shutil.rmtree(tPath)
            # Don't remove main path as upload might still be in progress
        except Exception as e:
            LOGS.warning(f"Cleanup warning: {e}")
