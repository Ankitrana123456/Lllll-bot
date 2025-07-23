import ctypes
import subprocess
from subprocess import getoutput
from handlers.url_scripts import ParseLink
from main import LOGGER as LOGS, Msg
import asyncio
import requests
import aiohttp
import aiofiles
import os
import time
from handlers.tg import TgHandler

cc = 0

EXTRA_LINKS = {
    "CP_VIMEO_TYPE": ("https://videos.classplusapp.com/", "https://api.edukemy.com/videodetails/", "https://tencdn.classplusapp.com", "https://covod.testbook.com/"),
    "GUIDELY_LINK": ("https://guidely.prepdesk.in/api/", "https://ibpsguide.prepdesk.in/api/"),
    "SET3": ("https://ply-404.herokuapp.com/"),
    "EDU_PDF": ("https://edukemy-v2-assets.s3.ap-south-1.amazonaws.com/course_content/"),
    "VISION_PDF": ("http://www.visionias.in/student/pt/video_student/handout", "http://www.visionias.in/student/3.php?"),
    "TOPRANKER": ("https://live.anytimelearning.in/", "https://onlinetest.sure60.com/"),
}

class get_link_atributes:
    @staticmethod
    def get_wxh(ytdlp):
        try:
            widthXheight = str(
                getoutput(f"{ytdlp}  -e --get-filename -R 25")).split("\n")[1].strip()
            LOGS.info(widthXheight)
            return widthXheight
        except Exception as e1:
            LOGS.info(str(e1))
            widthXheight = ".N.A"
            return widthXheight

    @staticmethod
    def get_height_width(link: str, Q: str):
        # 🆕 Enhanced validation and error handling
        if not link or not isinstance(link, str):
            LOGS.warning("Invalid link provided for resolution detection")
            return ".N.A"
            
        try:
            url = get_link_atributes().input_url(link=link, Q=Q)
            if not url:
                return ".N.A"
                
            YTF = f"bv[height<=?{Q}]+ba/[height<=?{Q}]+ba/[height>=?{Q}]+ba/[height<=?{Q}]/[height>=?{Q}]/b"
            
            if link.endswith("ankul60"):
                url = ParseLink.topranker_link(link)
                if "m3u8" in url:
                    rout = ParseLink.rout(url=link, m3u8=url)
                    os.system(f'curl "{rout}" -c "cooks.txt"')
                    cook = "cooks.txt"
                    YTDLP = f'yt-dlp -i --no-check-certificate -f "{YTF}" --no-warning "{url}" --cookies "{cook}" -o "%(resolution)s"'
                    wXh = get_link_atributes().get_wxh(YTDLP)
                    return wXh
                elif "youtu" in url:
                    YTDLP = f'yt-dlp -i --no-check-certificate -f "{YTF}" --no-warning "{url}" --progress -o "%(resolution)s"'
                    wXh = get_link_atributes().get_wxh(YTDLP)
                    return wXh
            else:
                YTDLP = f'yt-dlp -i --no-check-certificate -f "{YTF}" --no-warning "{url}" --progress --remux-video mp4 -o "%(resolution)s"'
                wXh = get_link_atributes().get_wxh(YTDLP)
                return wXh
        except Exception as e:
            LOGS.error(f"Error getting resolution: {e}")
            return ".N.A"

    @staticmethod
    def input_url(link: str, Q: str):
        # 🆕 Enhanced URL validation
        if not link:
            LOGS.error("Empty link provided")
            return None
            
        if not link.startswith(('http://', 'https://')) and not link.endswith('ankul60'):
            LOGS.warning(f"Potentially invalid URL format: {link}")
        
        try:
            if link.startswith("https://videos.classplusapp.com/"):
                if link.split("?")[-1].startswith("auth_key="):
                    url = link
                    return url
                else:
                    url = ParseLink.classplus_link(link=link)
                    return url
            elif link.startswith(("https://vod.visionias.in/player/index.php", "https://vod.visionias.in/player_v2/index.php")):
                url = ParseLink.vision_m3u8_link(link, Q)
                return url
            elif link.startswith(("https://covod.testbook.com/")):
                url = ParseLink.classplus_link(link=link)
                return url
            elif link.startswith(("https://tencdn.classplusapp.com")):
                url = ParseLink.classplus_link(link=link)
                return url
            elif link.startswith("http://www.visionias.in/student/videoplayer_v2/?"):
                url = ParseLink.vision_mpd_link(link)
                return url
            elif link.startswith("https://d1d34p8vz63oiq.cloudfront.net/"):
                url = ParseLink.is_pw(link)
                return url
            elif "drive" in link:
                url = ParseLink.is_drive_pdf(url=link)
                return url
            elif link.startswith("https://videotest.adda247.com/"):
                if link.split("/")[3] != "demo":
                    url = f'https://videotest.adda247.com/demo/{link.split("https://videotest.adda247.com/")[1]}'
                    return url
                else:
                    return link
            elif not link.startswith("http"):
                url = ParseLink.cw_url2(link.split("*")[0]) + link.split("*")[1]
                print(url)
                return url
            else:
                url = link
                return url
        except Exception as e:
            LOGS.error(f"Error processing URL {link}: {e}")
            return None

class Download_Methods:
    def __init__(self, name: str, url: str, path, Token: str, Quality: str) -> None:
        self.url = url
        self.name = name
        self.Q = Quality
        self.path = path
        self.token = Token
        self.temp_dir = f"{path}/{name}"

    # 🆕 Enhanced file size checker
    async def check_file_size(self, url):
        """Check if file size is within limits before downloading"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.head(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    content_length = response.headers.get('content-length')
                    if content_length:
                        file_size = int(content_length)
                        # 2GB limit
                        if file_size > 2 * 1024 * 1024 * 1024:
                            LOGS.warning(f"File too large: {file_size / (1024*1024*1024):.2f}GB")
                            return False, file_size
                        return True, file_size
            return True, 0  # If can't determine size, allow download
        except Exception as e:
            LOGS.warning(f"Could not check file size: {e}")
            return True, 0

    # 🆕 Enhanced network connectivity checker
    async def check_connectivity(self, url):
        """Check if URL is accessible before downloading"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.head(url, timeout=aiohttp.ClientTimeout(total=15)) as response:
                    if response.status in [200, 206, 302, 301]:
                        return True
                    else:
                        LOGS.warning(f"URL returned status {response.status}")
                        return False
        except asyncio.TimeoutError:
            LOGS.error("Connection timeout - URL not accessible")
            return False
        except Exception as e:
            LOGS.error(f"Connectivity check failed: {e}")
            return False

    async def m3u82mp4(self, file):
        """Convert M3U8 to MP4 with enhanced error handling"""
        try:
            LOGS.info("🔄 Converting M3U8 to MP4...")
            process = await asyncio.create_subprocess_exec(
                "ffmpeg", "-hide_banner", "-loglevel", "error", 
                "-protocol_whitelist", "file,http,https,tcp,tls,crypto",
                "-i", file, "-c", "copy", "-bsf:a", "aac_adtstoasc", 
                f"{self.temp_dir}.mp4",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                os.remove(file)
                if os.path.isfile(f"{self.temp_dir}.mp4"):
                    LOGS.info("✅ M3U8 conversion successful")
                    return f"{self.temp_dir}.mp4"
            else:
                LOGS.error(f"FFmpeg conversion failed: {stderr.decode()}")
                return None
        except Exception as e:
            LOGS.error(f"M3U8 conversion error: {e}")
            return None

    def addapdf(self):
        """Download Adda247 PDF with enhanced error handling"""
        try:
            LOGS.info("📄 Downloading Adda247 PDF...")
            cookies = {
                'cp_token': f'{self.token}',
            }
            headers = {
                'Host': 'store.adda247.com',
                'user-agent': 'Mozilla/5.0 (Linux; Android 11; moto g(40) fusion Build/RRI31.Q1-42-51-8; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/97.0.4692.98 Mobile Safari/537.36',
                'accept': '*/*',
                'x-requested-with': 'com.adda247.app',
                'sec-fetch-site': 'same-origin',
                'sec-fetch-mode': 'cors',
                'sec-fetch-dest': 'empty',
                'referer': 'https://store.adda247.com/build/pdf.worker.js',
                'accept-language': 'en-US,en;q=0.9',
            }
            
            response = requests.get(f'{self.url}', cookies=cookies, headers=headers, timeout=30)
            
            if response.status_code == 200:
                with open(f'{self.temp_dir}.pdf', 'wb') as f:
                    f.write(response.content)
                LOGS.info("✅ Adda247 PDF downloaded successfully")
                return f'{self.temp_dir}.pdf'
            else:
                LOGS.error(f"Adda247 PDF download failed: HTTP {response.status_code}")
                return None
        except Exception as e:
            LOGS.error(f"Adda247 PDF download error: {e}")
            return None

    async def aio(self):
        """Async download with progress tracking and enhanced error handling"""
        try:
            LOGS.info("📥 Starting async download...")
            k = f"{self.temp_dir}.pdf"
            
            # Check connectivity first
            if not await self.check_connectivity(self.url):
                LOGS.error("❌ URL not accessible")
                return None
            
            # Check file size
            size_ok, file_size = await self.check_file_size(self.url)
            if not size_ok:
                LOGS.error("❌ File too large for download")
                return None
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=1800)) as session:
                async with session.get(self.url) as resp:
                    if resp.status == 200:
                        total_size = int(resp.headers.get('content-length', 0))
                        downloaded = 0
                        
                        f = await aiofiles.open(k, mode='wb')
                        async for chunk in resp.content.iter_chunked(8192):
                            await f.write(chunk)
                            downloaded += len(chunk)
                            
                            # Log progress every 10MB
                            if downloaded % (10 * 1024 * 1024) == 0 and total_size > 0:
                                progress = (downloaded / total_size) * 100
                                LOGS.info(f"📊 Download progress: {progress:.1f}%")
                        
                        await f.close()
                        LOGS.info("✅ Async download completed successfully")
                        return k
                    else:
                        LOGS.error(f"❌ HTTP error: {resp.status}")
                        return None
        except asyncio.TimeoutError:
            LOGS.error("⏰ Download timeout")
            return None
        except Exception as e:
            LOGS.error(f"❌ Async download error: {e}")
            return None

    def cwpdf(self):
        """Download CW PDF with enhanced error handling"""
        try:
            LOGS.info("📄 Downloading CW PDF...")
            headers = {
                'User-Agent': 'Dalvik/2.1.0 (Linux; U; Android 9; Redmi Note 5 Pro MIUI/V11.0.5.0.PEIMIXM)',
                'Host': 'elearn.crwilladmin.com',
                'Connection': 'Keep-Alive',
            }
            
            r_pdf = requests.get(self.url, headers=headers, timeout=30)
            
            if r_pdf.status_code == 200:
                with open(f'{self.temp_dir}.pdf', 'wb') as f:
                    f.write(r_pdf.content)
                pdf = f'{self.temp_dir}.pdf'
                if os.path.isfile(pdf):
                    LOGS.info("✅ CW PDF downloaded successfully")
                    return pdf
            else:
                LOGS.error(f"CW PDF download failed: HTTP {r_pdf.status_code}")
                return None
        except Exception as e:
            LOGS.error(f"CW PDF download error: {e}")
            return None

    def visionpdf(self):
        """Download Vision PDF with enhanced error handling"""
        try:
            LOGS.info("📄 Downloading Vision PDF...")
            cookies = {
                'PHPSESSID': self.token,
            }
            headers = {
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
                'Accept-Language': 'en-US,en;q=0.9',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36',
            }
            
            response = requests.get(self.url, cookies=cookies, headers=headers, verify=False, timeout=30)
            
            if response.status_code == 200:
                with open(f"{self.temp_dir}.pdf", "wb") as f:
                    f.write(response.content)
                if os.path.isfile(f"{self.temp_dir}.pdf"):
                    LOGS.info("✅ Vision PDF downloaded successfully")
                    return f"{self.temp_dir}.pdf"
            else:
                LOGS.error(f"Vision PDF download failed: HTTP {response.status_code}")
                return None
        except Exception as e:
            LOGS.error(f"Vision PDF download error: {e}")
            return None

    async def Guidely(self):
        """Download Guidely content with enhanced error handling"""
        try:
            LOGS.info("🔓 Processing Guidely content...")
            
            # Get decryption keys and file URL
            response = requests.get(self.url, timeout=30)
            if response.status_code != 200:
                LOGS.error(f"Failed to get Guidely data: HTTP {response.status_code}")
                return None
                
            data = response.json()
            z = data['item']['data']['key']
            mpd = data['item']['data']['file']
            
            LOGS.info(f"🔑 Decryption key: {z}")
            LOGS.info(f"📺 MPD URL: {mpd}")
            
            # Download encrypted content
            cmd1 = f'yt-dlp -o "{self.path}/Name.%(ext)s" -f "bestvideo[height<={self.Q}]+bestaudio" --allow-unplayable-format --external-downloader aria2c "{mpd}"'
            process = await asyncio.create_subprocess_shell(cmd1)
            await process.communicate()
            
            if process.returncode != 0:
                LOGS.error("Failed to download encrypted content")
                return None
            
            AV = os.listdir(self.path)
            LOGS.info(f"📁 Downloaded files: {AV}")
            
            # Decrypt files
            for d in AV:
                if d.endswith("mp4"):
                    cmd2 = f'mp4decrypt --key 1:{z} "{self.path}/{d}" "{self.path}/video.mp4"'
                    os.system(cmd2)
                    os.remove(f"{self.path}/{d}")
                elif d.endswith("m4a"):
                    cmd3 = f'mp4decrypt --key 1:{z} "{self.path}/{d}" "{self.path}/audio.m4a"'
                    os.system(cmd3)
                    os.remove(f"{self.path}/{d}")
            
            # Merge video and audio
            cmd4 = f'ffmpeg -i "{self.path}/video.mp4" -i "{self.path}/audio.m4a" -c copy "{self.temp_dir}.mp4"'
            merge_process = await asyncio.create_subprocess_shell(cmd4)
            await merge_process.communicate()
            
            # Cleanup temporary files
            for temp_file in [f"{self.path}/video.mp4", f"{self.path}/audio.m4a"]:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            
            if os.path.isfile(f"{self.temp_dir}.mp4"):
                LOGS.info("✅ Guidely content processed successfully")
                return f"{self.temp_dir}.mp4"
            else:
                LOGS.error("❌ Failed to create final video file")
                return None
                
        except Exception as e:
            LOGS.error(f"❌ Guidely processing error: {e}")
            return None

    def get_drive_link_type(self):
        """Get Google Drive file type with enhanced error handling"""
        try:
            response = requests.get(self.url, timeout=15)
            c_type = response.headers.get('Content-Type', '').lower()
            LOGS.info(f"📄 Drive file type: {c_type}")
            return c_type
        except Exception as e2:
            LOGS.error(f"Drive type detection error: {e2}")
            return None

    def dot_ws_link(self):
        """Download .ws files with enhanced error handling"""
        try:
            LOGS.info("🌐 Downloading .ws content...")
            response = requests.get(self.url, stream=True, timeout=30)
            
            if response.status_code == 200:
                with open(f"{self.temp_dir}.html", "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                if os.path.isfile(f"{self.temp_dir}.html"):
                    LOGS.info("✅ .ws content downloaded successfully")
                    return f"{self.temp_dir}.html"
            else:
                LOGS.error(f".ws download failed: HTTP {response.status_code}")
                return None
        except Exception as e:
            LOGS.error(f".ws download error: {e}")
            return None

class download_handler(Download_Methods):
    def run_cmd(self, cmd):
        """Run command with enhanced logging"""
        LOGS.info(f"🚀 Executing: {cmd}")
        try:
            start_time = time.time()
            dl = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            duration = time.time() - start_time
            
            if dl.returncode == 0:
                LOGS.info(f"✅ Command completed in {duration:.1f}s")
            else:
                LOGS.error(f"❌ Command failed after {duration:.1f}s: {dl.stderr}")
                
        except Exception as e_:
            LOGS.error(f"Command execution error: {e_}")
            
        file_path = f"{self.temp_dir}.mp4"
        return file_path

    def recursive(self, cmd):
        """Recursive download with enhanced retry logic"""
        LOGS.info(f"🔄 Starting recursive download: {cmd}")
        global cc
        max_retries = 3  # Reduced from 5 for faster failure detection
        
        if cc >= max_retries:
            LOGS.error(f"❌ Max retries ({max_retries}) reached")
            return None
            
        start_time = time.time()
        dl = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        duration = time.time() - start_time
        
        if dl.returncode != 0:
            cc += 1
            LOGS.warning(f"⚠️ Retry {cc}/{max_retries} after {duration:.1f}s failure")
            if cc < max_retries:
                time.sleep(2 * cc)  # Progressive delay
                return download_handler.recursive(self, cmd=cmd)
        else:
            LOGS.info(f"✅ Download completed in {duration:.1f}s")
            
        cc = 0
        file_path = f"{self.temp_dir}.mp4"
        
        if os.path.isfile(file_path):
            LOGS.info(f"📁 File created: {file_path}")
            return file_path
        else:
            LOGS.error("❌ Expected output file not found")
            return None

    async def recursive_asyno(self, cmd):
        """Async recursive download with enhanced monitoring"""
        LOGS.info(f"🚀 Starting async download: {cmd}")
        global cc
        max_retries = 3
        
        if cc >= max_retries:
            LOGS.error(f"❌ Max async retries ({max_retries}) reached")
            return None
            
        try:
            # Create subprocess with timeout
            process = await asyncio.wait_for(
                asyncio.create_subprocess_shell(
                    cmd=cmd, 
                    stdout=asyncio.subprocess.PIPE, 
                    stderr=asyncio.subprocess.PIPE
                ),
                timeout=5
            )
            
            LOGS.info(f"📊 Process started (PID: {process.pid})")
            start_time = time.time()
            
            # Wait for completion with timeout
            stdout, stderr = await asyncio.wait_for(
                process.communicate(), 
                timeout=1800  # 30 minutes max
            )
            
            duration = time.time() - start_time
            
            if process.returncode != 0:
                cc += 1
                LOGS.warning(f"⚠️ Async retry {cc}/{max_retries} after {duration:.1f}s")
                if cc < max_retries:
                    await asyncio.sleep(2 * cc)
                    return await download_handler.recursive_asyno(self, cmd=cmd)
                else:
                    LOGS.error(f"❌ All async retries failed. Last error: {stderr.decode()}")
                    return None
            else:
                LOGS.info(f"✅ Async download completed in {duration:.1f}s")
                
        except asyncio.TimeoutError:
            LOGS.error("⏰ Async download timeout")
            return None
        except Exception as e:
            LOGS.error(f"❌ Async download error: {e}")
            return None
            
        cc = 0
        file_path = f"{self.temp_dir}.mp4"
        
        if os.path.isfile(file_path):
            file_size = os.path.getsize(file_path)
            LOGS.info(f"📁 File created: {file_path} ({file_size / (1024*1024):.2f} MB)")
            return file_path
        else:
            LOGS.error("❌ Expected output file not found")
            return None

    async def start_download(self):
        """Enhanced main download method with comprehensive error handling"""
        try:
            LOGS.info(f"🎯 Starting download: {self.name}")
            LOGS.info(f"🔗 URL: {self.url}")
            LOGS.info(f"📊 Quality: {self.Q}")
            
            # 🆕 Pre-download validation
            if not self.url:
                LOGS.error("❌ Empty URL provided")
                return None
                
            # 🆕 URL accessibility check for HTTP(S) URLs
            if self.url.startswith(('http://', 'https://')):
                if not await self.check_connectivity(self.url):
                    LOGS.error("❌ URL not accessible")
                    return None
            
            YTF = f"bv[height<=?{self.Q}]+ba/[height<=?{self.Q}]+ba/[height>=?{self.Q}]+ba/[height<=?{self.Q}]/[height>=?{self.Q}]/b"
            YTDLP = f'yt-dlp -i --no-check-certificate -f "{YTF}" --no-warning "{self.url}" --merge-output-format mp4 --remux-video mp4 -o "{self.temp_dir}.%(ext)s"'
            CMD = f'{YTDLP} -R 25 --fragment-retries 25 --external-downloader aria2c --downloader-args "aria2c:-x 16 -j 32"'

            # 🆕 Route to appropriate download method with enhanced logging
            if self.url.startswith('https://elearn.crwilladmin.com/') and self.url.endswith('.pdf'):
                LOGS.info("📄 Routing to CW PDF downloader")
                file_name = download_handler.cwpdf(self)
                return file_name

            if self.url.endswith(".pdf") or ".pdf" in self.url or self.url.startswith(EXTRA_LINKS['EDU_PDF']):
                LOGS.info("📄 Routing to async PDF downloader")
                file_name = await download_handler.aio(self)
                return file_name

            if self.url.startswith("https://store.adda247.com/"):
                LOGS.info("📄 Routing to Adda247 PDF downloader")
                file_name = download_handler.addapdf(self)
                return file_name
                
            if self.url.startswith(EXTRA_LINKS['VISION_PDF']):
                LOGS.info("📄 Routing to Vision PDF downloader")
                file_name = download_handler.visionpdf(self)
                return file_name

            if self.url.startswith(EXTRA_LINKS['GUIDELY_LINK']):
                LOGS.info("🔓 Routing to Guidely DRM downloader")
                file_name = await download_handler.Guidely(self)
                return file_name

            if self.url.startswith("https://videos.sproutvideo.com/"):
                LOGS.info("🌱 Routing to Sprout Video downloader")
                file = ParseLink.olive(self.Q, self.url, self.path)
                file_name = await download_handler.m3u82mp4(self, file)
                return file_name
                
            if "drive" in self.url:
                LOGS.info("☁️ Routing to Google Drive downloader")
                c_type = download_handler.get_drive_link_type(self)
                if c_type and "pdf" in c_type:
                    file_name = await download_handler.aio(self)
                    return file_name
                elif c_type and "video" in c_type:
                    file_name = await download_handler.recursive_asyno(self, cmd=CMD)
                    return file_name
                else:
                    file_name = await download_handler.aio(self)
                    return file_name

            if self.url.endswith("ankul60"):
                LOGS.info("🏆 Routing to TopRanker downloader")
                m3u8url = ParseLink.topranker_link(self.url)
                if "m3u8" in m3u8url:
                    rout = ParseLink.rout(url=self.url, m3u8=m3u8url)
                    os.system(f'curl "{rout}" -c "cooks.txt"')
                    cook = "cooks.txt"
                    YTDLP = f'yt-dlp -i --no-check-certificate -f "{YTF}" --no-warning "{m3u8url}" --cookies "{cook}" --remux-video mp4 -o "{self.temp_dir}.%(ext)s"'
                    CMD = f"{YTDLP} -R 25 --fragment-retries 25 --external-downloader aria2c --downloader-args 'aria2c: -x 16 -j 32'"
                    file_name = await download_handler.recursive_asyno(self, cmd=CMD)
                    if os.path.exists(cook):
                        os.remove(cook)
                    return file_name
                elif "youtu" in m3u8url:
                    self.url = m3u8url
                    file_name = await download_handler.recursive_asyno(self, cmd=CMD)
                    return file_name
                    
            if self.url.endswith(".ws"):
                LOGS.info("🌐 Routing to .ws downloader")
                file_name = download_handler.dot_ws_link(self)
                return file_name

            # 🆕 Default yt-dlp download with enhanced monitoring
            LOGS.info("📺 Routing to generic yt-dlp downloader")
            file_name = download_handler.recursive(self, cmd=CMD)
            return file_name
            
        except Exception as e:
            LOGS.error(f"❌ Download handler error: {e}")
            return None
        finally:
            # 🆕 Cleanup any temporary files
            temp_files = ["cooks.txt"]
            for temp_file in temp_files:
                if os.path.exists(temp_file):
                    try:
                        os.remove(temp_file)
                        LOGS.info(f"🧹 Cleaned up: {temp_file}")
                    except:
                        pass
