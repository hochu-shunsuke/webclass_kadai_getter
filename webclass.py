import urllib.parse
import requests
from bs4 import BeautifulSoup
import auth_token as ath

webclassurl = "https://rpwebcls.meijo-u.ac.jp"

def getacs(source):
    soup = BeautifulSoup(source,"html.parser")
    exccode = soup.find("script").string
    acsPath = exccode.split('"')[1].replace('&amp;', "&")
    return acsPath

class webclass:
    def __init__(self, userid, password):
        tokenId = ath.getToken(userid, password)
        url = "https://rpwebcls.meijo-u.ac.jp/webclass/login.php?auth_mode=SAML"
        res = requests.get(url, allow_redirects=False)
        location = res.headers["Location"]
        cookies = res.cookies.get_dict()
        cookies["iPlanetDirectoryPro"] = tokenId
        wbres = requests.get(location, cookies=cookies)
        soup = BeautifulSoup(wbres.text, "html.parser")
        responsedatas = soup.find_all("input")
        SAMLResponse = responsedatas[0].attrs["value"]
        RelayState = responsedatas[1].attrs["value"]
        data = {
            "SAMLResponse": SAMLResponse,
            "RelayState": RelayState
        }
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        req = urllib.parse.urlencode(data)
        defaultsp = "https://rpwebcls.meijo-u.ac.jp/simplesaml/module.php/saml/sp/saml2-acs.php/default-sp"
        wbres = requests.post(defaultsp, cookies=cookies, headers=headers, data=req, allow_redirects=False)
        SimpleSAML = wbres.cookies.get_dict()['SimpleSAML']
        SimpleSAMLAuthToken = wbres.cookies.get_dict()['SimpleSAMLAuthToken']
        cookies['SimpleSAML'] = SimpleSAML
        cookies['SimpleSAMLAuthToken'] = SimpleSAMLAuthToken
        loginphp = requests.get(url, cookies=cookies, allow_redirects=False)
        acsPath = getacs(loginphp.text)
        e = loginphp.cookies.get_dict()
        cookies['WBT_Session'] = e['WBT_Session']
        cookies['SimpleSAML'] = e['SimpleSAML']
        cookies['WCAC'] = e['WCAC']
        webclassurl_ = webclassurl + acsPath
        webclasresponce = requests.get(webclassurl_, cookies=cookies)
        cookies['wcui_session_settings'] = webclasresponce.cookies.get_dict()['wcui_session_settings']
        self.url = webclassurl_
        self.cookies = cookies