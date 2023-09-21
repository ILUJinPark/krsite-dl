import requests
import os
import re
import time
import pytz
import subprocess
from rich.progress import Progress
from urllib.parse import unquote
import krsite_dl as kr

class DownloadHandler():
    def __init__(self):
        self.args = kr.args
        self.reserved_pattern = r'[\\/:*?"<>|]'

    
    # sanitize string to remove windows reserved characters
    def __sanitize_string(self, string):
        if not self.args.no_windows_filenames:
            string = re.sub(self.reserved_pattern, '', string)
        return string
    

    # location list for timezone
    def _location(self, loc):
        # list country codes here as json so i can call them by matching its keys
        country_codes = {
            "KR": "Asia/Seoul", "JP": "Asia/Tokyo", "SG": "Asia/Singapore"
        }

        return country_codes.get(loc, "UTC")
        

    # korean filename encoder
    def _encode_kr(self, img_name):
        img = img_name.split('/')[-1]
        decoded = unquote(img).strip()

        if '%EC' in decoded or '%EB' in decoded:
            korean_filename = decoded.encode('utf-8')
        else:
            try:
                korean_filename = decoded.encode('euc-kr')
            except UnicodeDecodeError:
                korean_filename = decoded.encode('euc-kr', errors='ignore')
        
        img = self.__sanitize_string(korean_filename.decode('euc-kr'))

        return img
    
    def _download_logic(self, filename, uri, dirs, post_date, loc):
        try:
            with Progress() as progress:
                process = subprocess.Popen([
                            'aria2c', '-d', dirs, 
                            '-c', 
                            '-j', '2', 
                            '-o', filename, uri,
                            '--continue',
                            '--download-result=hide',
                            '-U', 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:87.0) Gecko/20100101 Firefox/87.0'],
                            stdout=subprocess.PIPE,
                            encoding='utf-8',
                            text=True)
                
                task = progress.add_task("Downloading...", total=100)
                
                for line in process.stdout:
                    parts = line.split()
                    if len(parts) >=3 and parts[1].endswith('%)'):
                        progress.update(task, advance=int(re.search(r'\((\d+)%\)', parts[1]).group(1)))
                    if 'Download complete' in line:
                        progress.update(task, completed=100)

            if os.path.exists(dirs + '/' + filename):
                utc = pytz.timezone(self._location(loc))
                dt = post_date
                dt = utc.localize(dt)
                timestamp = int(dt.timestamp())
                os.utime(dirs + '/' + filename, (timestamp, timestamp))
                os.utime(dirs, (timestamp, timestamp))
        except requests.exceptions.SSLError:
            print("[Status] SSL Error. Skipping...")
        except requests.exceptions.HTTPError:
            print("[Status] HTTP Error. Skipping...")
        except requests.exceptions.ConnectionError:
            print("[Status] Connection Error. Skipping...")

    def downloader(self, img_list, dirs, post_date, loc):
        for img in img_list:
            img_name = self._encode_kr(img)

            print("[Source URL] %s" % img)
            print("[Image Name] %s" % img_name)

            if os.path.exists(dirs + '/' + img_name) and not os.path.exists(dirs + '/' + img_name + '.aria2'):
                print("[Status] This file already exists. Skipping...")
                continue

            self._download_logic(img_name, img, dirs, post_date, loc)


    def downloader_naver(self, img_list, dirs, post_date):
        for img in img_list:
            img_name = self._encode_kr(img)

            print("[Source URL] %s" % img)
            print("[Image Name] %s" % img_name)

            if os.path.exists(dirs + '/' + img_name) and not os.path.exists(dirs + '/' + img_name + '.aria2'):
                print("[Status] This file already exists. Skipping...")
                continue

            self._download_logic(img_name, img, dirs, post_date, "KR")


    def downloader_combine(self, img_list, dirs, post_date, post_date_short, title, loc):
        for img in img_list:
            img_name = self._encode_kr(img)
            img_ext = img.split('.')[-1]

            if len(img_list) > 1:
                img_name = f'{post_date_short} {title} ({img_list.index(img)+1}).{img_ext}'
            else:
                img_name = f'{post_date_short} {title}.{img_ext}'

            print("[Source URL] %s" % img)
            print("[Image Name] %s" % img_name)

            if os.path.exists(dirs + '/' + img_name) and not os.path.exists(dirs + '/' + img_name + '.aria2'):
                print("[Status] This file already exists. Skipping...")
                continue

            self._download_logic(img_name, img, dirs, post_date, loc)


# def download_handler(img_list, dirs, post_date, loc):
#     print("Downloading image(s) to folder: ", dirs)
#     for img in img_list:
#         img_name = img.split('/')[-1]

#         decoded = unquote(img_name).strip()

#         if '%EC' in decoded or '%EB' in decoded:
#             korean_filename = decoded.encode('utf-8')
#         else:
#             try:
#                 korean_filename = decoded.encode('euc-kr')
#             except UnicodeDecodeError:
#                 korean_filename = decoded.encode('euc-kr', errors='ignore')
        
#         img_name = korean_filename

#         img_name = img_name.decode('euc-kr')

#         print("[Source URL] %s" % img)
#         print("[Image Name] %s" % img_name)

#         if os.path.exists(dirs + '/' + img_name) and not os.path.exists(dirs + '/' + img_name + '.aria2'):
#             print("[Status] This file already exists. Skipping...")
#             continue
        
#         try:
#             with Progress() as progress:
#                 process = subprocess.Popen(['aria2c', '-d', dirs, 
#                             '-c', 
#                             '-j', '2', 
#                             '-o', img_name, img,
#                             '--continue',
#                             '--download-result=hide',
#                             '-U', 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:87.0) Gecko/20100101 Firefox/87.0'],
#                             stdout=subprocess.PIPE,
#                             encoding='utf-8',
#                             text=True)
                
#                 task = progress.add_task("Downloading...", total=100)
                
#                 for line in process.stdout:
#                     parts = line.split()
#                     if len(parts) >=3 and parts[1].endswith('%)'):
#                         progress.update(task, advance=int(re.search(r'\((\d+)%\)', parts[1]).group(1)))
#                     if 'Download complete' in line:
#                         progress.update(task, completed=100)

#             if os.path.exists(dirs + '/' + img_name):
#                 # Set file and folders modification time
#                 if loc == "KR":
#                     utc = pytz.timezone("Asia/Seoul")
#                 elif loc == "JP":
#                     utc = pytz.timezone("Asia/Tokyo")
#                 elif loc == "SG":
#                     utc = pytz.timezone("Asia/Singapore")
                
#                 dt = post_date
#                 dt = utc.localize(dt)
#                 timestamp = int(dt.timestamp())
                
#                 # print(timestamp)
#                 # print(dt)

#                 os.utime(dirs + '/' + img_name, (timestamp, timestamp))
#                 os.utime(dirs, (timestamp, timestamp))
#         except requests.exceptions.SSLError:
#             print("[Status] SSL Error. Skipping...")
#             continue
#         except requests.exceptions.HTTPError:
#             print("[Status] HTTP Error. Skipping...")
#             continue
#         except requests.exceptions.ConnectionError:
#             print("[Status] Connection Error. Skipping...")
#             continue


# def download_handler_naver(img_list, dirs, post_date):
#     print("Downloading image(s) to folder: ", dirs)
#     for img in img_list:
#         img_name = img.split('/')[-1]

#         decoded = unquote(img_name).strip()

#         if '%EC' in decoded or '%EB' in decoded:
#             korean_filename = decoded.encode('utf-8')
#         else:
#             try:
#                 korean_filename = decoded.encode('euc-kr')
#             except UnicodeDecodeError:
#                 korean_filename = decoded.encode('euc-kr', errors='ignore')
        
#         img_name = korean_filename

#         img_name = img_name.decode('euc-kr')

#         print("[Source URL] %s" % img)
#         print("[Image Name] %s" % img_name)


#         if os.path.exists(dirs + '/' + img_name) and not os.path.exists(dirs + '/' + img_name + '.aria2'):
#             print("[Status] This file already exists. Skipping...")
#             continue
        
#         try:
#             with Progress() as progress:
#                 task = progress.add_task("Downloading...", total=100)

#                 process = subprocess.Popen(['aria2c', '-d', dirs, 
#                             '-c', 
#                             '-j', '2', 
#                             '-o', img_name, img,
#                             '--continue',
#                             '--download-result=hide',
#                             '-U', 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:87.0) Gecko/20100101 Firefox/87.0'],
#                             stdout=subprocess.PIPE,
#                             encoding='utf-8',
#                             text=True)
                
#                 for line in process.stdout:
#                     parts = line.split()
#                     if len(parts) >=3 and parts[1].endswith('%)'):
#                         progress.update(task, advance=int(re.search(r'\((\d+)%\)', parts[1]).group(1)))
#                     if 'Download complete' in line:
#                         progress.update(task, completed=100)
            
#             if os.path.exists(dirs + '/' + img_name):
#                 # Set file and folders modification time
#                 utc = pytz.timezone("Asia/Seoul")
#                 dt = post_date
#                 dt = utc.localize(dt)
                
#                 timestamp = int(dt.timestamp())
#                 # print(timestamp)
#                 # print(dt)

#                 os.utime(dirs + '/' + img_name, (timestamp, timestamp))
#                 os.utime(dirs, (timestamp, timestamp))
#         except requests.exceptions.SSLError:
#             print("[Status] SSL Error. Skipping...")
#             continue
#         except requests.exceptions.HTTPError:
#             print("[Status] HTTP Error. Skipping...")
#             continue
#         except requests.exceptions.ConnectionError:
#             print("[Status] Connection Error. Skipping...")
#             continue


# def download_handler_no_folder(img_list, dirs, post_date, post_date_short, title, loc):
#     print("Downloading image(s) to folder: ", dirs)
#     for img in img_list:
#         img_ext = img.split('.')[-1]

#         # set image name based on the number of images
#         if len(img_list) > 1:
#             img_name = f'{post_date_short} {title} ({img_list.index(img)+1}).{img_ext}'
#         else:
#             img_name = f'{post_date_short} {title}.{img_ext}'

#         print("[Source URL] %s" % img)
#         print("[Image Name] %s" % img_name)

#         if os.path.exists(dirs + '/' + img_name) and not os.path.exists(dirs + '/' + img_name + '.aria2'):
#             print("[Status] This file already exists. Skipping...")
#             continue
        
#         try:
#             with Progress() as progress:
#                 process = subprocess.Popen(['aria2c', '-d', dirs, 
#                             '-c', 
#                             '-j', '2', 
#                             '-o', img_name, img,
#                             '--continue',
#                             '--download-result=hide',
#                             '--check-certificate=false',
#                             '-U', 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:87.0) Gecko/20100101 Firefox/87.0'],
#                             stdout=subprocess.PIPE,
#                             encoding='utf-8',
#                             text=True)
                
#                 task = progress.add_task("Downloading...", total=100)
                
#                 for line in process.stdout:
#                     parts = line.split()
#                     if len(parts) >=3 and parts[1].endswith('%)'):
#                         progress.update(task, advance=int(re.search(r'\((\d+)%\)', parts[1]).group(1)))
#                     if 'Download complete' in line:
#                         progress.update(task, completed=100)

#             if os.path.exists(dirs + '/' + img_name):
#                 # Set file and folders modification time
#                 if loc == "KR":
#                     utc = pytz.timezone("Asia/Seoul")
#                 elif loc == "JP":
#                     utc = pytz.timezone("Asia/Tokyo")
#                 elif loc == "SG":
#                     utc = pytz.timezone("Asia/Singapore")
                
#                 dt = post_date
#                 dt = utc.localize(dt)
#                 timestamp = int(dt.timestamp())

#                 os.utime(dirs + '/' + img_name, (timestamp, timestamp))
#                 os.utime(dirs, (timestamp, timestamp))
#         except requests.exceptions.SSLError:
#             print("[Status] SSL Error. Skipping...")
#             continue
#         except requests.exceptions.HTTPError:
#             print("[Status] HTTP Error. Skipping...")
#             continue
#         except requests.exceptions.ConnectionError:
#             print("[Status] Connection Error. Skipping...")
#             continue


# def download_handler_alt(img, dirs):
#     print("Downloading image(s) to folder: ", dirs)
#     try:
#         response = requests.head(img, timeout=60)
#     except requests.exceptions.Timeout:
#         print("Request timeout. Skipping...")
#     content_length = int(response.headers.get('Content-Length', 0))

#     img_name = img.split('/')[-1]

#     decoded = unquote(img_name).strip()

#     if '%EC' in decoded or '%EB' in decoded:
#         korean_filename = decoded.encode('utf-8')
#     else:
#         try:
#             korean_filename = decoded.encode('euc-kr')
#         except UnicodeDecodeError:
#             korean_filename = decoded.encode('euc-kr', errors='ignore')
    
#     img_name = korean_filename

#     img_name = img_name.decode('euc-kr')

#     print("\n[Image Name] %s" % img_name)
    
#     url_mod_time = response.headers.get('Last-Modified')

#     with Progress() as progress:
#         task = progress.add_task("Downloading...", total=100)

#         process = subprocess.Popen(['aria2c', '-d', dirs, 
#                     '-V', '-c', 
#                     '-j', '2', 
#                     '-o', img_name, img,
#                     '--continue',
#                     '--download-result=hide',
#                     '-U', 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:87.0) Gecko/20100101 Firefox/87.0'],
#                     stdout=subprocess.PIPE,
#                     encoding='utf-8',
#                     text=True)
        
#         for line in process.stdout:
#             parts = line.split()
#             if len(parts) >=3 and parts[1].endswith('%)'):
#                 progress.update(task, advance=int(re.search(r'\((\d+)%\)', parts[1]).group(1)))
#             if 'Download complete' in line:
#                 progress.update(task, completed=100)
        
#     if os.path.exists(dirs + '/' + img_name):
#         # Set file and folders modification time
#         if url_mod_time:
#             print("[Metadata] Embedding metadata to %s" % img_name)
#             mod_time = time.strptime(url_mod_time, '%a, %d %b %Y %H:%M:%S %Z')
#             os.utime(dirs + '/' + img_name, (time.time(), time.mktime(mod_time)))
        
#         if url_mod_time:
#             os.utime(dirs, (time.time(), time.mktime(mod_time)))