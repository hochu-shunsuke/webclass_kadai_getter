import json
import re
import urllib.parse
from pathlib import Path
from bs4 import BeautifulSoup
import settings
from webclass_client import WebClassClient
from parser import parse_course_contents

# --- 定数 ---
TEMP_DIR = Path("temp")
# MAX_WORKERS = 10  # 削除
REDIRECT_REGEX = re.compile(r'window.location.href\s*=\s*"([^"]+)"')

def get_course_links(client: WebClassClient):
    """ダッシュボードから科目一覧のリンクを取得する"""
    print("ダッシュボードから科目リンクを取得中...")
    try:
        # クライアントの既存セッションを使用
        top_html = client.get(client.dashboard_url).text
        soup = BeautifulSoup(top_html, "html.parser")
        
        course_links = set()
        for a_tag in soup.find_all('a', href=True, class_='list-group-item course'):
            name = a_tag.get_text(strip=True)
            href = a_tag.get("href")
            if href and '/webclass/course.php/' in href:
                course_links.add((name, href))
                
        print(f"科目リンク抽出数: {len(course_links)}")
        if not course_links:
            print("警告: 科目が見つかりません．")
        return list(course_links)
        
    except Exception as e:
        print(f"科目リンクの取得に失敗しました: {e}")
        return []

def fetch_and_parse_course(course_info, client: WebClassClient):
    """
    単一の科目のページを取得，解析し，JSONファイルに保存する (直列処理用)
    """
    course_name, href = course_info
    
    # クライアントの既存セッションを使用
    session = client.session 
    base_url = client.base_url
    
    try:
        url = urllib.parse.urljoin(base_url, href)
        
        res = session.get(url)
        html = res.text
        
        # JavaScriptリダイレクト処理
        soup = BeautifulSoup(html, "html.parser")
        script = soup.find("script")
        if script and script.string and "window.location.href" in script.string:
            m = REDIRECT_REGEX.search(script.string)
            if m:
                redirect_url = urllib.parse.urljoin(base_url, m.group(1))
                res = session.get(redirect_url)
                html = res.text

        # ファイル名を安全なものに（改善後のロジック）
        # 1. '»' とそれに続く空白を削除し，前後の空白を削除
        cleaned_name = re.sub(r'»\s*', '', course_name).strip()
        
        # 2. 連続する空白(全角/半角)を単一の半角スペースに正規化
        cleaned_name = re.sub(r'\s+', ' ', cleaned_name)
        
        # 3. OSで禁止されている文字を '_' に置換
        safe_name = re.sub(r'[\\/*?:"<>|]', '_', cleaned_name)
        
        json_fname = TEMP_DIR / f"{safe_name}.json"

        # HTMLを解析
        data = parse_course_contents(html)
        
        # JSONとして保存
        with open(json_fname, "w", encoding="utf-8") as jf:
            json.dump(data, jf, ensure_ascii=False, indent=2)
            
        return (course_name, "成功")

    except Exception as e:
        return (course_name, f"失敗: {e}")

def main():
    # 1. 出力ディレクトリ作成
    TEMP_DIR.mkdir(exist_ok=True)
    
    # 2. 資格情報取得
    try:
        userdata = settings.load_or_create_credentials()
    except Exception as e:
        print(f"資格情報の読み込みに失敗しました: {e}")
        return

    # 3. WebClassログイン
    try:
        client = WebClassClient(userdata["userid"], userdata["password"])
    except Exception as e:
        print(f"ログインに失敗しました: {e}")
        return

    # 4. 科目一覧を取得
    course_links = get_course_links(client)
    if not course_links:
        print("処理する科目がありません．終了します．")
        return

    # 5. 直列処理で全科目を処理
    print(f"{len(course_links)}件の科目を直列処理します...")
    
    for i, course in enumerate(course_links):
        name, result = fetch_and_parse_course(course, client)
        print(f"  ({i+1}/{len(course_links)}) [{result}] - {name}")

    print("すべての処理が完了しました．")

if __name__ == "__main__":
    main()