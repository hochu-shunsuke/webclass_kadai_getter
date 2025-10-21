def parse_webclass_html_from_string(html):
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, 'html.parser')
    import re
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
import os
from bs4 import BeautifulSoup
import json

def parse_webclass_html(filepath):
    with open(filepath, encoding='utf-8') as f:
        soup = BeautifulSoup(f, 'html.parser')

    import re
    result = []
    for panel in soup.find_all('section', class_='panel panel-default cl-contentsList_folder'):
        # 1. まとまりタイトル
        heading = panel.find('div', class_='panel-heading')
        panel_title = heading.find('h4', class_='panel-title').get_text(strip=True) if heading else ""
        # 2. 課題リスト本体
        list_group = panel.find('div', class_='list-group')
        items = []
        if list_group:
            for item in list_group.find_all('section', class_='list-group-item cl-contentsList_listGroupItem'):
                # 3. 新規課題判定
                is_new = item.find('div', class_='cl-contentsList_new') is not None
                # 4. タイトルとURL
                name_tag = item.find('h4', class_='cm-contentsList_contentName')
                a_tag = name_tag.find('a') if name_tag else None
                title = name_tag.get_text(strip=True) if name_tag else ""
                url = a_tag['href'] if a_tag and a_tag.has_attr('href') else ""
                # 7. 共有リンク生成
                id_match = re.search(r'id=([a-f0-9]+)', url)
                share_link = f"https://rpwebcls.meijo-u.ac.jp/webclass/login.php?id={id_match.group(1)}&page=1&auth_mode=SAML" if id_match else ""
                # 5. 課題タイプ
                category = item.find('div', class_='cl-contentsList_categoryLabel')
                category = category.get_text(strip=True) if category else ""
                # 6. 利用可能期間
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

