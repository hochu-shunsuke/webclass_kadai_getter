import os
import re
import json
import settings as s
from webclass import webclass
import requests
from bs4 import BeautifulSoup
from parse_webclass_html import parse_webclass_html_from_string
from webclass import webclass

def main():
    userdata = s.getpsw()
    wbc = webclass(userdata["userid"], userdata["password"])
    temp_dir = "temp"
    os.makedirs(temp_dir, exist_ok=True)
    # 科目一覧ページからcourse_links抽出
    top_html = requests.get(wbc.url, cookies=wbc.cookies).text
    with open("top.html", "w", encoding="utf-8") as f:
        f.write(top_html)
    print("トップページHTMLをtop.htmlに保存しました。")
    soup = BeautifulSoup(top_html, "html.parser")
    course_links = []
    for a_tag in soup.find_all('a', href=True):
        name = a_tag.get_text(strip=True)
        href = a_tag.get("href")
        # 必要ならhrefやnameでフィルタリング（例: /webclass/course.php/ を含むものだけ）
        if href and '/webclass/course.php/' in href:
            course_links.append((name, href))
    print(f"科目リンク抽出数: {len(course_links)}")
    if not course_links:
        print("科目が見つかりません。HTML構造や認証状態を確認してください。")
    for i, (course_name, href) in enumerate(course_links):
        url = wbc.url.split('/webclass/')[0] + href
        res = requests.get(url, cookies=wbc.cookies)
        html = res.text
        # リダイレクト先URLがあれば再アクセス
        soup = BeautifulSoup(html, "html.parser")
        script = soup.find("script")
        redirect_url = None
        if script and "window.location.href" in script.text:
            m = re.search(r'window.location.href\s*=\s*"([^"]+)"', script.text)
            if m:
                redirect_url = m.group(1)
        if redirect_url:
            if redirect_url.startswith("/"):
                base = wbc.url.split('/webclass/')[0]
                redirect_url = base + redirect_url
            res2 = requests.get(redirect_url, cookies=wbc.cookies)
            html = res2.text
        # .txt保存は廃止し、直接HTML解析→JSON保存
            safe_name = re.sub(r'[^\w]', '_', course_name)
        json_fname = os.path.join(temp_dir, f"{safe_name}.json")
        try:
            data = parse_webclass_html_from_string(html)
            with open(json_fname, "w", encoding="utf-8") as jf:
                json.dump(data, jf, ensure_ascii=False, indent=2)
            print(f"保存: {json_fname}")
        except Exception as e:
            print(f"抽出エラー: {e}")

if __name__ == "__main__":
    main()
