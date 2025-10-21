# webclass_client.py

import urllib.parse
import requests
import time
import json
from bs4 import BeautifulSoup

# --- auth_token.pyから移植したロジック ---

SSO_URL = 'https://slbsso.meijo-u.ac.jp/opensso/json/authenticate'
MAX_RETRIES = 5
RETRY_DELAY = 1

def _get_sso_token(userid, password):
    """SSOサーバーから認証トークンを取得する"""
    headers = {'Content-Type': 'application/json'}
    
    try:
        # 1. 認証テンプレートの取得
        source_res = requests.post(SSO_URL, headers=headers)
        source_res.raise_for_status()
        jsn = source_res.json()
        
        # 2. テンプレートに資格情報を設定
        jsn["callbacks"][0]["input"][0]["value"] = userid
        jsn["callbacks"][1]["input"][0]["value"] = password
        
        # 3. 資格情報を送信
        for attempt in range(MAX_RETRIES):
            token_res = requests.post(SSO_URL, headers=headers, json=jsn)
            if token_res.status_code == 200:
                token_data = token_res.json()
                print(f"SSOトークン取得成功。")
                return token_data["tokenId"]
            
            print(f"認証試行 {attempt + 1}/{MAX_RETRIES} 失敗 (Status: {token_res.status_code}). {RETRY_DELAY}秒後リトライ...")
            time.sleep(RETRY_DELAY)
            
        raise Exception(f"トークン取得失敗 (Status: {token_res.status_code})")

    except requests.exceptions.RequestException as e:
        print(f"SSOサーバーへの接続に失敗しました: {e}")
        raise
    except (KeyError, IndexError, json.JSONDecodeError) as e:
        print(f"SSOサーバーの応答形式が予期したものではありません: {e}")
        raise

# --- webclass.pyのロジック ---

WEBCLASS_BASE_URL = "https://rpwebcls.meijo-u.ac.jp"

def _get_acs_path(source):
    """HTMLソースからJavaScript内のリダイレクトパスを抽出する"""
    soup = BeautifulSoup(source, "html.parser")
    script_tag = soup.find("script")
    if script_tag and script_tag.string and '"' in script_tag.string:
        exccode = script_tag.string
        parts = exccode.split('"')
        if len(parts) > 1:
            return parts[1].replace('&amp;', "&")
    return None

class WebClassClient:
    def __init__(self, userid, password):
        print("認証セッションを開始します...")
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'
        })
        self.base_url = WEBCLASS_BASE_URL
        self.dashboard_url = None
        self._login(userid, password)

    def _login(self, userid, password):
        try:
            # 1. SSOトークンを取得
            token_id = _get_sso_token(userid, password)
            
            # 2. WebClassのSAMLログインページにアクセス
            login_url = f"{self.base_url}/webclass/login.php?auth_mode=SAML"
            res = self.session.get(login_url, allow_redirects=False)
            sso_location = res.headers["Location"]
            
            # 3. SSOのページにトークンをCookieとして送信
            sso_cookies = {"iPlanetDirectoryPro": token_id}
            sso_res = self.session.get(sso_location, cookies=sso_cookies)
            sso_res.raise_for_status()

            # 4. SAML認証情報をパース
            soup = BeautifulSoup(sso_res.text, "html.parser")
            inputs = soup.find_all("input")
            data = {
                "SAMLResponse": inputs[0].attrs["value"],
                "RelayState": inputs[1].attrs["value"]
            }
            
            # 5. SAML認証情報をWebClassのACSにPOST
            acs_url = f"{self.base_url}/simplesaml/module.php/saml/sp/saml2-acs.php/default-sp"
            self.session.post(acs_url, data=data, allow_redirects=False)
            
            # 6. 再度ログインページにアクセス (SAML Cookieで認証される)
            login_php_res = self.session.get(login_url, allow_redirects=False)
            
            # 7. 最終的なダッシュボードのURLを取得
            acs_path = _get_acs_path(login_php_res.text)
            if not acs_path:
                raise Exception("最終的なリダイレクトパス(acsPath)の取得に失敗しました。")
                
            self.dashboard_url = urllib.parse.urljoin(self.base_url, acs_path)
            
            # 8. 最終ページにアクセスしてセッションを確定
            self.session.get(self.dashboard_url).raise_for_status()
            
            print(f"ログイン成功！")
        
        except Exception as e:
            print(f"ログイン処理中にエラーが発生しました: {e}")
            raise

    def get(self, url, **kwargs):
        """認証済みセッションでGETリクエストを送信する"""
        return self.session.get(url, **kwargs)