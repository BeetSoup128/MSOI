from selenium import webdriver
from ebooklib import epub
import bs4
import zhconv


import time
import os
import requests
import base64
import logging
import json
import uuid
import re


def string_format(iStr: str) -> str:
    return iStr.replace("&nbsp;", '').replace("\xa0", '').replace(
        "\u3000", '').replace("\u2800", '').replace('\\n', '').strip()


class Masiro:
    if not os.path.exists("Cache"):
        os.mkdir("Cache")
        with open("./Cache/sav.json", 'w', encoding='utf-8') as f:
            json.dump({"nid=": "BookName"}, f)
    if not os.path.exists("./Cache/sav.json"):
        with open("./Cache/sav.json", 'w', encoding='utf-8') as f:
            json.dump({"nid=": "BookName"}, f)
    if not os.path.exists("Result"):
        os.mkdir("Result")
    with open("./Cache/sav.json", 'r', encoding='utf-8') as f:
        conf = dict(json.load(f))
    nid = None

    def __init__(self, debug=False) -> None:
        ops = webdriver.EdgeOptions()
        if debug:
            ops.add_argument("-headless")
        logging.debug("init browser")
        self.Web = webdriver.ChromiumEdge(options=ops)
        logging.debug("init browser done")

    def modconf(self, upd: dict = {}, remove: list = []) -> None:
        logging.debug(
            "try modeify conf:{} to update{} and remove{}".format(
                self.conf, upd, remove))
        self.conf.update(upd)
        for rm in remove:
            self.conf[rm] = None
            del self.conf[rm]
        with open("./Cache/sav.json", '2', encoding='utf-8') as f:
            json.dump(self.conf, f)

    def login(self, name: str, pwd: str, msoHOST: str = "https://masiro.me",
              loginPATH: str = "/admin/auth/login", loginOKPATH: str = "/admin") -> bool:
        logging.debug("Login in, using url:" + msoHOST + loginPATH)
        self.mso = msoHOST
        self.Web.get(msoHOST + loginPATH)
        self.Web.execute_script(
            f"document.getElementById('username').value = '{name}';document.getElementById('password').value = '{pwd}';")
        time.sleep(2)
        self.Web.execute_script(
            "document.getElementById('login-btn').click();")
        time.sleep(5)
        fph = self.Web.execute_script("return new URL(document.URL).pathname;")
        if fph == loginOKPATH:
            logging.info(f"login OK")
            logging.debug(
                f"name:{name}, password:{pwd}, using host:{msoHOST}, using loginpath and final jump2'{loginPATH}' and '{loginOKPATH}'")
            return True
        else:
            logging.info(f"login error, wrong jump path '{fph}'")
            logging.debug(
                f"name:{name}, password:{pwd}, using host:{msoHOST}, using loginpath and final jump2'{loginPATH}' and '{loginOKPATH}'")
            return False

    def NovSearch(self, nid,
                  nidpathformat: str = r"/admin/novelView?novel_id={nid}"):
        logging.debug(
            "search novel's menu using url:" +
            self.mso +
            nidpathformat.format(
                nid=nid))
        # Title Search
        if self.nid is None:
            self.nid = str(nid)
        else:
            logging.info("has nid yet while searching {}".format(nid))
            yield False
        try:
            self.Web.get(self.mso + nidpathformat.format(nid=nid))
            ####
            Tit = string_format(self.Web.execute_script(
                "return document.getElementsByClassName('novel-title')[0].innerText;"))
        except BaseException:
            logging.info("Error while searching title")
            yield False
        else:
            self.bookTit = Tit
            yield Tit  # str Title
        ####
        # meta-data Search
        try:
            metals = string_format(self.Web.execute_script(
                "return document.getElementsByClassName('n-detail')[0].innerText;")).split('\n')
            meta = {'brief': string_format(self.Web.execute_script(
                "return document.getElementsByClassName('brief')[0].innerText;"))}
            for l in metals:
                r = l.split(':', 1)
                meta[r[0].strip()] = r[1].strip()
        except BaseException:
            logging.info("Error while searching meta")
            yield False
        else:
            self.bookMeta = meta
            yield meta  # {brief:..., ...:... }
        ####
        # Chapter:Pages Search
        try:
            oHtml = self.Web.execute_script(
                "return document.getElementsByClassName('chapter-ul')[0].outerHTML;")
            sp = bs4.BeautifulSoup(oHtml,"html.parser")
            CHNames = [bTag.string.strip()
                       for bTag in sp.select("li[class='chapter-box'] b")]
            EPLists = [[{"path": als["href"], "tTitle":als.select_one("span").string.replace(
                "&nbsp;", ' ').strip()} for als in ul.select("a")] for ul in sp.select("ul[class='episode-ul']")]
            res = {}
            res.update(zip(CHNames, EPLists))
        except BaseException:
            logging.info("Error while searching cid")
            yield False
        else:
            self.booktree = res
            yield res  # {章节:[{path:,tTitle:}],...}
        ####

    def EPSearch(
            self, cid: str, epp: str = "/admin/novelReading?") -> tuple[bs4.BeautifulSoup, str]:
        'MSOPATH + epp + cid\n"https://masiro.me" + "/admin/novelReading?" + "cid=123456"'
        logging.debug("search EP using url:{}".format(self.mso + epp + cid))
        self.Web.get(self.mso + epp + cid)
        time.sleep(5)
        try:
            chTitle = str(self.Web.execute_script(
                "return document.getElementsByClassName('novel-title')[0].innerText;"))
            chHTML = str(self.Web.execute_script(
                "return document.getElementsByClassName('box-body nvl-content')[0].outerHTML;"))
        except BaseException:
            logging.info("unable to read, try to pay for reading")
            self.Web.execute_script(
                "document.getElementsByClassName('hint-btn pay')[0].click();")
            time.sleep(1)
            self.Web.execute_script(
                "document.getElementsByClassName('layui-layer-btn0')[0].click();")
            time.sleep(1)
            self.Web.execute_script(
                "document.getElementsByClassName('layui-layer-btn0')[0].click();")
            time.sleep(5)

            chTitle = str(self.Web.execute_script(
                "return document.getElementsByClassName('novel-title')[0].innerText;"))
            chHTML = str(self.Web.execute_script(
                "return document.getElementsByClassName('box-body nvl-content')[0].outerHTML;"))
        chHTML = string_format(chHTML)
        chTitle = string_format(chTitle)
        logging.debug("search OK")
        return (bs4.BeautifulSoup('\n'.join(['<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"',
                                             '"http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">',
                                             '<html xmlns="http://www.w3.org/1999/xhtml">',
                                             '<head>\n  <meta charset="utf-8">\n  <title>' + chTitle + '</title>\n</head>\n<body>\n', chHTML, '</body>\n</html>']),
                                  "html.parser"),
                chTitle)

    def EPdr(self, ep: bs4.BeautifulSoup, SavePath: str) -> None:
        for img in ep.find_all("img"):
            if img.parent.name == 'div':
                pass
            tmp = img.attrs
            url = tmp.get("src", "")
            if "base64" not in url:
                time.sleep(2)
                try:
                    res = base64.b64encode(requests.get(url).content)
                except BaseException:
                    pass
                else:
                    tmp["src"] = "data:image/jpeg;base64," + \
                        res.decode("utf-8")
            tmp["style"] = "width: auto; height: auto; max-width: 100%; max-height: 100%;"
            img.append(ep.new_tag('img', **tmp))
            img.attrs = {"style": "width:100%;"}
            img.name = 'div'
        for p in ep.select('*'):
            if p.string:
                p.string = zhconv.convert(
                    p.string, "zh-hans").replace(
                    '“', '「').replace(
                    '”', '」').replace(
                    '‘', '『').replace(
                    '’', '』')
        with open(SavePath, 'w', encoding='utf-8') as f:
            f.write(ep.prettify())


class MSOEpub:
    def __init__(self, nid: str, tit: str) -> None:
        self.nid = nid
        self.tit = tit
        with open(f"./Cache/{nid}/init.json", 'r', encoding='utf-8') as f:
            self.bktree = json.load(f)
        with open(f"./Cache/{nid}/meta.json", 'r', encoding='utf-8') as f:
            self.bkmeta = json.load(f)
        bk = epub.EpubBook()
        bk.set_language('zh')
        bk.set_title(tit)
        bk.set_identifier(str(uuid.uuid5(namespace=uuid.NAMESPACE_URL,
                                         name=f"MSOI://BeetSoup128:BeetSoup128@masiro.me/epub/nid={nid}").int))
        bk.add_author(self.bkmeta.get('作者', 'set_author_here'))
        bk.add_metadata(
            "DC", "description", self.bkmeta.get(
                'biref', 'input_brief_here'))
        for k in self.bkmeta.keys():
            bk.add_metadata("masiro", k, self.bkmeta[k])
        spine_tmp = []
        toc_tmp = []
        for ch in self.bktree.keys():
            eps = []
            for ep in self.bktree[ch]:
                with open("./Cache/{}/{}.xhtml".format(nid, ep["cid="].replace('=', '_')), 'r', encoding='utf-8') as f:
                    page = epub.EpubHtml(title=ep["Title"],
                                         file_name=ep["cid="].replace(
                                             '=', '_') + ".xhtml",
                                         lang='cn',
                                         content=re.sub(u"[\\x00-\\x08\\x0b\\x0e-\\x1f\\x7f]", '', f.read()))
                bk.add_item(page)
                spine_tmp.append(page)
                eps.append(page)
            toc_tmp.append(
                (epub.Section(
                    re.sub(
                        u"[\\x00-\\x08\\x0b\\x0e-\\x1f\\x7f]",
                        '',
                        ch)),
                    eps,
                 ))
        bk.toc = [(epub.Section(tit), toc_tmp,)]
        bk.add_item(epub.EpubNcx())
        bk.add_item(epub.EpubNav())
        bk.spine.append("nav")
        bk.spine.extend(spine_tmp)
        self.bk = bk

    def out(self):
        epub.write_epub(f"./Result/{self.tit}.ePub", self.bk)
