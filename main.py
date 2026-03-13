import requests
import re
import random
from flask import Flask, request, jsonify
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import concurrent.futures

app = Flask(__name__)

# --- قائمة الأنماط الشاملة (Regex) لكل أنواع المفاتيح ---
PATTERNS = {
    'Secret Key (SK)': r'sk_live_[a-zA-Z0-9]{24,}',
    'Publishable Key (PK)': r'pk_live_[a-zA-Z0-9]{24,}',
    'Client Secret (CS)': r'pi_[a-zA-Z0-9]{16,}_secret_[a-zA-Z0-9]{24,}',
    'Session ID (SS)': r'cs_live_[a-zA-Z0-9]{50,}',
    'Access Token': r'access_token_live_[a-zA-Z0-9]{24,}',
    'Webhook Secret': r'whsec_[a-zA-Z0-9]{24,}'
}

# دالة الفحص في النص
def extract_keys(text):
    found = {}
    for label, pattern in PATTERNS.items():
        matches = re.findall(pattern, text)
        if matches:
            found[label] = list(set(matches)) # إرجاع نتائج فريدة
    return found

def get_all_links(url, html):
    links = set()
    soup = BeautifulSoup(html, 'html.parser')
    
    # سحب ملفات الـ JS
    for script in soup.find_all('script'):
        src = script.get('src')
        if src:
            links.add(urljoin(url, src))
            
    # سحب الروابط الداخلية (ربما توجد صفحة دفع مخفية)
    for a in soup.find_all('a', href=True):
        full_url = urljoin(url, a['href'])
        if urlparse(url).netloc == urlparse(full_url).netloc:
            links.add(full_url)
            
    return links

@app.route('/deep_scan', methods=['POST'])
def deep_scan():
    base_url = request.json.get('url')
    if not base_url: return jsonify({"error": "URL missing"}), 400

    all_found_keys = {}
    scanned_urls = []
    
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/122.0.0.0'}
        # 1. فحص الصفحة الرئيسية وجلب كل الروابط والملفات
        response = requests.get(base_url, headers=headers, timeout=10)
        scanned_urls.append(base_url)
        
        initial_keys = extract_keys(response.text)
        all_found_keys.update(initial_keys)
        
        target_links = get_all_links(base_url, response.text)

        # 2. فحص الروابط والملفات بشكل متوازي (Threads) لسرعة خيالية
        def fetch_and_scan(link):
            try:
                res = requests.get(link, headers=headers, timeout=5)
                return extract_keys(res.text)
            except:
                return {}

        with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
            future_results = executor.map(fetch_and_scan, target_links)
            for result in future_results:
                for label, keys in result.items():
                    if label in all_found_keys:
                        all_found_keys[label] = list(set(all_found_keys[label] + keys))
                    else:
                        all_found_keys[label] = keys

        return jsonify({
            "status": "Success",
            "scanned_count": len(target_links) + 1,
            "keys_found": all_found_keys
        })

    except Exception as e:
        return jsonify({"status": "Error", "message": str(e)})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)
