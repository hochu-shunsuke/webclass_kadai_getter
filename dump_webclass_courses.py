import os
import re
import json
import settings as s
from webclass import webclass
import requests
from bs4 import BeautifulSoup

def parse_webclass_html_from_string(html):
    soup = BeautifulSoup(html, 'html.parser')
    result = []
    for panel in soup.find_all('section', class_='panel panel-default cl-contentsList_folder'):
        heading = panel.find('div', class_='panel-heading')
        panel_title = heading.find('h4', class_='panel-title').get_text(strip=True) if heading else ""
        list_group = panel.find('div', class_='list-group')
        items = []
        if list_group:
            for item in list_group.find_all('section', class_='list-group-item cl-contentsList_listGroupItem'):
                is_new = item.find('div', class_='cl-contentsList_new') is not None
                name_tag = item.find('h4', class_='cm-contentsList_contentName')
                a_tag = name_tag.find('a') if name_tag else None
                title = name_tag.get_text(strip=True) if name_tag else ""
                url = a_tag['href'] if a_tag and a_tag.has_attr('href') else ""
                import re
                id_match = re.search(r'id=([a-f0-9]+)', url)
                share_link = f"https://rpwebcls.meijo-u.ac.jp/webclass/login.php?id={id_match.group(1)}&page=1&auth_mode=SAML" if id_match else ""
                category = item.find('div', class_='cl-contentsList_categoryLabel')
                category = category.get_text(strip=True) if category else ""
                period = ""
                for label, data in zip(item.find_all('div', class_='cm-contentsList_contentDetailListItemLabel'), item.find_all('div', class_='cm-contentsList_contentDetailListItemData')):
                    if "利用可能期間" in label.get_text():
                        period = data.get_text(strip=True)
                items.append({
                    'title': title,
                    'url': url,
                    'share_link': share_link,
                    'is_new': is_new,
                    'category': category,
                    'period': period
                })
        result.append({
            'panel_title': panel_title,
            'items': items
        })
    return result

def main():
    userdata = s.getpsw()
    wbc = webclass(userdata["userid"], userdata["password"])
    temp_dir = "temp"
    os.makedirs(temp_dir, exist_ok=True)
    top_html = requests.get(wbc.url, cookies=wbc.cookies).text
    soup = BeautifulSoup(top_html, "html.parser")
    course_links = []
    seen = set()
    for a_tag in soup.find_all('a', href=True, class_='list-group-item course'):
        name = a_tag.get_text(strip=True)
        href = a_tag.get("href")
        key = (name, href)
        if href and '/webclass/course.php/' in href and key not in seen:
            course_links.append(key)
            seen.add(key)
    print(f"科目リンク抽出数: {len(course_links)}")
    if not course_links:
        print("科目が見つかりません。HTML構造や認証状態を確認してください。")
    for i, (course_name, href) in enumerate(course_links):
        url = wbc.url.split('/webclass/')[0] + href
        res = requests.get(url, cookies=wbc.cookies)
        html = res.text
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
