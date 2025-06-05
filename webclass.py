import urllib.parse
import requests
import json
import urllib
from bs4 import BeautifulSoup
import os
import general as g
import filedownload
import auth_token as ath

defaultpath = "class"
webclassurl = "https://rpwebcls.meijo-u.ac.jp"

def getacs(source):
    soup = BeautifulSoup(source,"html.parser")
    exccode = soup.find("script").string
    acsPath = exccode.split('"')[1].replace('&amp;',"&")
    return acsPath

class webclass:
    def __init__(self,userid,password):
        tokenId = ath.getToken(userid,password)
        url = "https://rpwebcls.meijo-u.ac.jp/webclass/login.php?auth_mode=SAML"
        res = requests.get(url,allow_redirects=False)
        #truetatuscode(res.status_code,302)#statuscode確認
        #print("location")
        #print(res.headers)
        #kugiri()
        location = res.headers["Location"]
        cookies = res.cookies.get_dict()
        cookies["iPlanetDirectoryPro"]= tokenId
        #print("cookies:")
        #print(cookies)
        #kugiri()
        wbres = requests.get(location,cookies=cookies)
        g.truetatuscode(wbres.status_code,200)
        #print(wbres.text)
        #kugiri()
        soup = BeautifulSoup(wbres.text,"html.parser")
        responsedatas =soup.find_all("input")
        SAMLResponse=responsedatas[0].attrs["value"]
        RelayState = responsedatas[1].attrs["value"]
        data = {
            "SAMLResponse" :SAMLResponse,
            "RelayState":RelayState
        }
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        req = urllib.parse.urlencode(data)
        defaultsp = "https://rpwebcls.meijo-u.ac.jp/simplesaml/module.php/saml/sp/saml2-acs.php/default-sp"
        wbres = requests.post(defaultsp,cookies=cookies,headers=headers,data=req,allow_redirects=False)
        #truetatuscode(wbres.status_code,303)
        #print(data)
        g.kugiri()
        print("SAMLAuthToken")
        SimpleSAML = wbres.cookies.get_dict()['SimpleSAML']
        SimpleSAMLAuthToken = wbres.cookies.get_dict()['SimpleSAMLAuthToken']
        cookies['SimpleSAML'] = SimpleSAML
        cookies['SimpleSAMLAuthToken'] = SimpleSAMLAuthToken
        print(cookies)
        g.kugiri()
        loginphp = requests.get(url,cookies=cookies,allow_redirects=False)
        #truetatuscode(wbres.status_code,303)
        acsPath = getacs(loginphp.text)
        g.kugiri()
        e = loginphp.cookies.get_dict()
        cookies['WBT_Session'] =e['WBT_Session']
        cookies['SimpleSAML'] = e['SimpleSAML']
        cookies['WCAC'] = e['WCAC']
        print(cookies)
        g.kugiri()
        webclassurl_ = webclassurl + acsPath
        webclasresponce = requests.get(webclassurl_,cookies=cookies)
        g.truetatuscode(webclasresponce.status_code,200)
        cookies['wcui_session_settings'] = webclasresponce.cookies.get_dict()['wcui_session_settings']
        #print(requests.get(webclassurl_,cookies=cookies).headers)
        self.url = webclassurl_
        self.cookies = cookies



def responceacspath(url,cookies):
    source = requests.get(url,cookies=cookies)
    #print(source.text)
    acspath = getacs(source.text)
    responce = requests.get(webclassurl+acspath,cookies=cookies)
    g.truetatuscode(responce.status_code,200)
    #print(responce.text)
    return responce

def getshowinfopagecontent(soup:BeautifulSoup,cookies):
    g.putlog("GGGAAA2")#識別するやつ
    g.putlog(soup.prettify)
    path = soup.find("frame",{"name":"contentsInfo"})["src"].replace('&amp;',"&")
    url = webclassurl+"/webclass/"+path
    header ={
        "content-type":"application/x-www-form-urlencoded"
    }
    data = {
        "next":"%E9%96%8B%E5%A7%8B"
    }
    req =urllib.parse.urlencode(data)
    responce = requests.post(url,headers=header,data=req,cookies=cookies)
    soup = BeautifulSoup(responce.text,"html.parser")
    g.putlog("GGGAAA23")
    g.putlog(soup.prettify)
    execode = soup.find("script").string
    execode = execode.split('"')[1].replace('&amp;',"&")
    url = webclassurl+execode
    source = requests.get(url,cookies=cookies)
    
    g.putlog("GGGAAA234")
    g.putlog(source.text)
    soup = BeautifulSoup(source.text,"html.parser")
    execode = soup.find("script").string
    execode = execode.split('"')[1].replace('&amp;',"&")
    url = webclassurl+"/webclass/"+execode
    source = requests.get(url,cookies=cookies)
    g.putlog("GGGAAA2345")
    g.putlog(source.text)
    return source

def getcontents(sectionelement:BeautifulSoup,cookies,classname):
    title = sectionelement.find("h4",class_="panel-title").get_text()
    print(f"コース名,{title}")
    g.putlog(f"コース名,{title}" )
    courcename = title
    no_courcename = False 
    if courcename == "" or courcename == " " :#もしcourcenameが空だったら(味文みたいなやつの場合)
        no_courcename = True #no_courcenameフラグを立てる 
        #<input type='hidden' name='question_url' value='/webclass/loadit.php?lang=JAPANESE&amp;file=%2Fwebclass%2Ftext%2F20%2F2025016424060%2Faf459037367d3198fc86f2b2088bc141%2F971c7e050499c2dd.pdf'>

    contentselements = sectionelement.find(class_="list-group").find_all("section",class_="cl-contentsList_listGroupItem")#授業内容のグループを取得
    for j in range(len(contentselements)):
        try:
            contenttitle = contentselements[j].find("h4",class_="cm-contentsList_contentName").find("a")#授業内容のグループのタイトルを取得
            contenturl = contenttitle['href']
            session_qs = urllib.parse.urlparse(contenturl).query#クエリパラメータを取得
            session_qd = urllib.parse.parse_qs(session_qs)#クエリパラメータを辞書型に変換
            contenturl = "https://rpwebcls.meijo-u.ac.jp/webclass/do_contents.php?reset_status=1&"+"set_contents_id="+session_qd["set_contents_id"][0]
            print(f"コンテンツ,{contenttitle.get_text()}")
            contentname = contenttitle.get_text()
            
            if no_courcename and j == 0:
                courcename = contentname #content最初のやつを名前にする
            
            #print(f"URL,{contenturl}")
            source = requests.get(contenturl,cookies=cookies)
            acspath = getacs(source.text)
            url = webclassurl+"/webclass/"+acspath
            source = requests.get(url,cookies=cookies)
            soup = BeautifulSoup(source.text,"html.parser")
            if "show_frame.php" in acspath:#移動先が確認画面の場合
                source = getshowinfopagecontent(soup,cookies)#確認画面後に上書き
                url = source.url
                soup = BeautifulSoup(source.text)
            #g.putlog(f"{source.text}")
            
            g.putlog(f"content:{contenttitle.get_text()}")
            g.putlog(f"url:{url}")

            uri = urllib.parse.urlparse(url)
            g.putlog(f"path:{uri.path}")
            if(uri.path == "/webclass/qstn_frame.php"):#パスが課題の場合
                print("qtn selected")
                #question frame
                anserpath = soup.find("frame",{"name":"answer"})["src"]#<FRAME src='dqstn_answer.php?rnd=c4d7c&amp;set_contents_id=59e541e4f288e80ed9303de98ad069f0&amp;language=JAPANESE&amp;content_mode=i&amp;start_from_show_info=true&amp;content_mode=q&amp;acs_=4c8bb7ee' Name = 'answer'>
                g.putlog(f"anser path:{anserpath}")
                ansurl = webclassurl+"/webclass/"+ anserpath
                g.putlog(f"anser path:{ansurl}")
                source_ans = requests.get(ansurl,cookies=cookies)
                soup = BeautifulSoup(source_ans.text,"html.parser")
                g.putlog(soup.prettify())
                print("soup seeing")
                question_path = soup.find("input",{"name":"question_url"})["value"]
                g.putlog(f"question_path:{question_path}")
                query = question_path
                g.putlog(f"query:{query}")
                
                filepath = f"{defaultpath}/{classname}/{courcename}/{contentname}"
                print(filepath)
                os.makedirs(filepath,exist_ok=True)
                filepath = f"{filepath}/work.pdf"
                filedownload.getfiles(query,cookies,filepath)
                
            if(uri.path == "/webclass/txtbk_frame.php"):
                print("txtbk selected")
                chapterpath = soup.find("frame",{"name":"webclass_chapter"}).attrs["src"].replace("&amp;","&")
                g.putlog(f"chapterpath:{chapterpath}")
                chapterurl = webclassurl+"/webclass/"+chapterpath
                source_chapter = requests.get(chapterurl,cookies=cookies)
                soup_chapter = BeautifulSoup(source_chapter.text,"html.parser")#チャプターのhtml取得
                #g.putlog(f"{soup_chapter.prettify}")
                json_str= soup_chapter.find("script",id = "json-data").get_text()
                #g.putlog(f"str:{json_str}")
                pagedata = json.loads(json_str)#資料の情報をjson形式で保存
                #g.putlog(json.dumps(pagedata,indent=2))
                text_urls = pagedata["text_urls"]
                g.putlog(f"text_urls:{text_urls}")
                chapternames = getchapternames(soup_chapter,len(text_urls.values()))
                g.putlog(f"chapternames:{chapternames}")
                    
                for i in range(len(chapternames)):#chapterごとの操作
                    filepath = f"{defaultpath}/{classname}/{courcename}/{contentname}"
                    print(filepath)
                    os.makedirs(filepath,exist_ok=True)
                    filepath = f"{filepath}/{chapternames[i]}.pdf"
                    filedownload.getfiles(text_urls[f"{i+1}"],cookies,filepath)
            
        except:
            print("コンテンツ,閉鎖もしくは予期せぬエラー")

def getchapternames(soup,page):
    TOC = soup.find("table",{"id":"TOCLayout"})
    chapters = soup.find_all("span",{"class":"size2 darkslategray"})
    n = page
    chapternames = []
    for i in  range(int(n)):
        chaptername = chapters[i*2].get_text()+","+chapters[i*2+1].get_text()
        chapternames.append(chaptername)
    return chapternames

def getsections(page,cookies):
    divs = page.find_all("div")  # divタグを持つ要素を取得
    for n in divs:
        n.extract()
    name = page.get_text()
    classname = name[9:]  # "授業名"の部分を取得
    print(f"授業名:{classname}")  # 各リンクのURLを表示
    g.putlog(f"授業名:{classname}")
    classurl = webclassurl+page['href']
    #print(f"URL:{classurl}")
    os.makedirs(defaultpath+"/"+classname, exist_ok=True)
    
    source = responceacspath(classurl,cookies)#偽リダイレクトの時のアクセス方法
    soup = BeautifulSoup(source.text,"html.parser")
    sectionelements = soup.find_all("section",class_="cl-contentsList_folder")#授業内容の部分を取得
    for i in range(len(sectionelements)):
        getcontents(sectionelements[i],cookies,classname)
    g.kugiri()

def getClasses(page,cookies):
    soup = BeautifulSoup(page, "html.parser")

    ##print("ページのHTMLを取得中")

    schedule_element = soup.find(id = "schedule-table")
    hrefs = schedule_element.find_all("a", href=True)
    for href in hrefs:
        getsections(href,cookies)
