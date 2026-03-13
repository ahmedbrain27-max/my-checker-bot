import requests
import re
import concurrent.futures
from flask import Flask, request, jsonify
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup

app = Flask(__name__)

# قائمة الأنماط الشاملة (Regex) لقنص كافة أنواع المفاتيح
PATTERNS = {
    'Secret Key (SK)': r'sk_live_[a-zA-Z0-9]{24,}',
    'Publishable Key (PK)': r'pk_live_[a-zA-Z0-9]{24,}',
    'Client Secret (CS)': r'pi_[a-zA-Z0-9]{16,}_secret_[a-zA-Z0-9]{24,}',
    'Session ID (SS)': r'cs_live_[a-zA-Z0-9]{50,}',
    'Access Token': r'access_token_live_[a-zA-Z0-9]{24,}',
    'Webhook Secret': r'whsec_[a-zA-Z0-9]{24,}'
}

def extract_keys(text):
    found = {}
    for label, pattern in PATTERNS.items():
        matches = re.findall(pattern, text)
        if matches:
            found[label] = list(set(matches))
    return found

def get_assets(url, html):
    assets = set()
    try:
        soup = BeautifulSoup(html, 'html.parser')
        # سحب ملفات الـ JS
        for script in soup.find_all('script'):
            src = script.get('src')
            if src: assets.add(urljoin(url, src))
        
        # سحب الروابط الداخلية (صفحات الدفع المحتملة)
        for a in soup.find_all('a', href=True):
            full_url = urljoin(url, a['href'])
            if urlparse(url).netloc == urlparse(full_url).netloc:
                assets.add(full_url)
    except: pass
    return assets

@app.route('/')
def home():
    return "Server is Running - LYNIX ELITE SNIPER"

@app.route('/scan', methods=['POST'])
def scan():
    data = request.json
    base_url = data.get('url')
    if not base_url:
        return jsonify({"status": "Error", "message": "URL missing"}), 400

    all_found_keys = {}
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/122.0.0.0'}

    try:
        # 1. فحص الصفحة الأساسية
        response = requests.get(base_url, headers=headers, timeout=10)
        initial_keys = extract_keys(response.text)
        all_found_keys.update(initial_keys)
        
        # 2. جمع الأصول (JS وروابط داخلية)
        target_assets = get_assets(base_url, response.text)

        # 3. الفحص المتوازي (Threading) - قوة Pro Ultra
        def fetch_and_scan(link):
            try:
                res = requests.get(link, headers=headers, timeout=5)
                return extract_keys(res.text)
            except: return {}

        with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
            future_results = executor.map(fetch_and_scan, target_assets)
            for result in future_results:
                for label, keys in result.items():
                    if label in all_found_keys:
                        all_found_keys[label] = list(set(all_found_keys[label] + keys))
                    else:
                        all_found_keys[label] = keys

        return jsonify({
            "status": "Success",
            "scanned_assets_count": len(target_assets),
            "keys_found": all_found_keys
        })

    except Exception as e:
        return jsonify({"status": "Error", "message": str(e)}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)
