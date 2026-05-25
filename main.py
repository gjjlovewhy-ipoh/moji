import requests
from bs4 import BeautifulSoup
import os
import re
from urllib.parse import urljoin, urlparse
import time

def download_images_deep(url, save_folder='spratly_images_full'):
    if not os.path.exists(save_folder):
        os.makedirs(save_folder)
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': 'https://tianqi.moji.com/',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8'
    }
    
    downloaded_urls = set()
    total_downloaded = 0

    def save_image(img_url, source_type="direct"):
        nonlocal total_downloaded
        if not img_url or img_url in downloaded_urls:
            return False
        if img_url.startswith(('data:', 'javascript:', 'blob:')):
            return False
        try:
            parsed = urlparse(img_url)
            if not parsed.netloc:
                img_url = urljoin(url, img_url)
            
            time.sleep(0.3)
            resp = requests.get(img_url, headers=headers, timeout=15, stream=True)
            resp.raise_for_status()
            
            fname = os.path.basename(parsed.path)
            if not fname or len(fname) < 3:
                ext = '.jpg'
                if 'png' in img_url.lower():
                    ext = '.png'
                fname = f'{source_type}_{total_downloaded + 1}{ext}'
                
            fname = re.sub(r'[\\/*?:"<>|]', '_', fname)
            fpath = os.path.join(save_folder, fname)
            
            with open(fpath, 'wb') as f:
                for chunk in resp.iter_content(4096):
                    f.write(chunk)
                    
            downloaded_urls.add(img_url)
            total_downloaded += 1
            print(f'[{total_downloaded}] [{source_type}] {img_url}')
            return True
            
        except Exception as e:
            print(f'图片下载失败：', str(e))
            return False
    
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        # 抓取普通img、懒加载图片
        for img in soup.find_all('img'):
            src = img.get('src') or img.get('data-src') or img.get('data-original')
            save_image(src, 'img')
        
        # 抓取css背景图片
        bg_pattern = re.compile(r'background[^;]*url\(["\']?(.*?)["\']?\)', re.I)
        for tag in soup.find_all(style=True):
            for bg_url in bg_pattern.findall(tag['style']):
                save_image(bg_url, 'bg')
        
        # 正则匹配页面内所有图片链接
        link_pattern = re.compile(r'(https?://[^"\'\s]+\.(jpg|jpeg|png|gif|webp))', re.I)
        for match in link_pattern.finditer(resp.text):
            save_image(match.group(1), 'link')
        
        print(f"\n===== 抓取完成 =====\n共获取图片：{total_downloaded} 张")
    except Exception as e:
        print(f'页面请求异常：{str(e)}')

if __name__ == "__main__":
    target_url = "https://tianqi.moji.com/liveview/china/hainan/nanette-district-(spratly-islands)"
    download_images_deep(target_url)
