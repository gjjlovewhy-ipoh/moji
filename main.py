import requests
from bs4 import BeautifulSoup
import os
import re
import json
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
    image_link_list = []
    total_downloaded = 0

    def save_image(img_url, source_type="direct"):
        nonlocal total_downloaded
        if not img_url or img_url in downloaded_urls:
            return False
        if img_url.startswith(('data:', 'javascript:', 'blob:')):
            return False
        try:
            parsed = urlparse(img_url)
            abs_url = img_url
            if not parsed.netloc:
                abs_url = urljoin(url, img_url)
            
            if abs_url in downloaded_urls:
                return False
            
            # 存入链接列表
            downloaded_urls.add(abs_url)
            image_link_list.append({
                "source_type": source_type,
                "image_url": abs_url
            })

            time.sleep(0.3)
            resp = requests.get(abs_url, headers=headers, timeout=15, stream=True)
            resp.raise_for_status()
            
            fname = os.path.basename(parsed.path)
            if not fname or len(fname) < 3:
                ext = '.jpg'
                if 'png' in abs_url.lower():
                    ext = '.png'
                fname = f'{source_type}_{total_downloaded + 1}{ext}'
                
            fname = re.sub(r'[\\/*?:"<>|]', '_', fname)
            fpath = os.path.join(save_folder, fname)
            
            with open(fpath, 'wb') as f:
                for chunk in resp.iter_content(4096):
                    f.write(chunk)
                    
            total_downloaded += 1
            print(f'[{total_downloaded}] [{source_type}] {abs_url}')
            return True
            
        except Exception as e:
            print(f'图片下载失败：{str(e)}')
            return False
    
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        # 1. 常规图片、懒加载图片
        for img in soup.find_all('img'):
            src = img.get('src') or img.get('data-src') or img.get('data-original')
            save_image(src, 'img')
        
        # 2. CSS背景图
        bg_pattern = re.compile(r'background[^;]*url\(["\']?(.*?)["\']?\)', re.I)
        for tag in soup.find_all(style=True):
            for bg_url in bg_pattern.findall(tag['style']):
                save_image(bg_url, 'bg')
        
        # 3. 文本内图片链接
        link_pattern = re.compile(r'(https?://[^"\'\s]+\.(jpg|jpeg|png|gif|webp))', re.I)
        for match in link_pattern.finditer(resp.text):
            save_image(match.group(1), 'link')

        # 导出链接到JSON文件
        json_data = {
            "crawl_time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "source_url": url,
            "total_count": len(image_link_list),
            "images": image_link_list
        }
        with open("image_links.json", "w", encoding="utf-8") as f:
            json.dump(json_data, f, ensure_ascii=False, indent=2)

        print(f"\n===== 抓取完成 =====")
        print(f"总计图片数量：{len(image_link_list)} 张")
        print(f"链接已保存至：image_links.json")

    except Exception as e:
        print(f'页面请求异常：{str(e)}')

if __name__ == "__main__":
    target_url = "https://tianqi.moji.com/liveview/china/hainan/nanette-district-(spratly-islands)"
    download_images_deep(target_url)
