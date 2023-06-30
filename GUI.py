from masiro import Masiro, MSOEpub
import tkinter
import os
from tkinter import ttk
import threading
import json
import configparser
import logging


import sv_ttk

if __name__ == "__main__":
    window = tkinter.Tk(className="Masiro Installer by BeetSoup128")

class MSP(ttk.Frame):
    try:
        conf = configparser.ConfigParser()
        conf.read("GUI.ini")
        Local_nam = tkinter.Variable(value=conf['user']['name'])
        Local_pwd = tkinter.Variable(value=conf['user']['pwd'])
    except BaseException:
        Local_nam = tkinter.Variable(value="输入用户名")
        Local_pwd = tkinter.Variable(value="输入密码")
    Local_url = tkinter.Variable(value="https://masiro.me")
    Local_State = tkinter.Variable(value="未登录")

    Local_Login = False

    def __init__(self, master, MSO: Masiro) -> None:
        super().__init__(master)
        self.Local_MSO = MSO
        self.grid(column=0, row=0)
        ttk.Label(
            self,
            text="Masiro_login_page",
            font=(
                "-size",
                48)).grid(
            column=0,
            columnspan=2,
            row=0)

        ttk.Label(
            self,
            text="默认url",
            font=(
                "-size",
                24),
            width=8).grid(
            column=0,
            row=1,
            sticky='w')
        ttk.Label(
            self,
            text="用户名",
            font=(
                "-size",
                36),
            width=8).grid(
            column=0,
            row=2,
            sticky='w')
        ttk.Label(
            self,
            text="密码  ",
            font=(
                "-size",
                36),
            width=8).grid(
            column=0,
            row=3,
            sticky='w')

        ttk.Entry(
            self,
            textvariable=self.Local_url,
            font=(
                "-size",
                24)).grid(
            column=1,
            row=1,
            sticky='we')
        ttk.Entry(
            self,
            textvariable=self.Local_nam,
            font=(
                "-size",
                36)).grid(
            column=1,
            row=2,
            sticky='w')
        ttk.Entry(
            self,
            textvariable=self.Local_pwd,
            font=(
                "-size",
                36)).grid(
            column=1,
            row=3,
            sticky='w')

        ttk.Label(
            self,
            font=(
                "-size",
                36),
            textvariable=self.Local_State,
            width=8).grid(
            column=0,
            columnspan=2,
            row=4,
            sticky='w')
        ttk.Button(
            self,
            text="LOGIN",
            command=self.login,
            width=12,
            style='my.TButton').grid(
            column=0,
            columnspan=2,
            row=5)

    def login(self):
        if not self.Local_Login:
            threading.Thread(target=self.login_main).start()

    def login_main(self):
        # print(f"name    ::{ self.Local_nam.get() }\npassword::{ self.Local_pwd.get() }")
        self.Local_Login = True
        self.Local_State.set("登陆中")
        try:
            if self.Local_MSO.login(self.Local_nam.get(
            ), self.Local_pwd.get(), self.Local_url.get()):
                self.Local_State.set("已登录")
            else:
                self.Local_State.set("登录异常")
        except BaseException:
            self.Local_State.set("网络异常")
        self.Local_Login = False


class NVP(ttk.Frame):
    Local_NID = tkinter.Variable(value="输入Nid")
    Local_BTNV = tkinter.Variable(value="Download it")
    Local_searching = False
    Local_searched = False
    Local_Downloading = False
    Local_Downloaded = False

    def __init__(self, master, MSO: Masiro) -> None:
        self.MSO = MSO
        super().__init__(master)
        self.grid(column=0, row=0)
        ttk.Entry(
            self,
            textvariable=self.Local_NID,
            font=(
                "-size",
                36),
            width='16').grid(
            column=0,
            columnspan=2,
            row=0,
            sticky='we')
        ttk.Button(
            self,
            text="搜索",
            command=self.search,
            style='my.TButton').grid(
            column=2,
            row=0,
            sticky='we')

        self.t = ttk.Treeview(
            self,
            columns=('ep'),
            show='tree headings',
            displaycolumns='#all',
            selectmode='extended')
        self.t.grid(column=0, row=1, columnspan=3, sticky='we')

        ttk.Button(
            self,
            text=" Delete ",
            command=self.delbktree,
            style='my.TButton').grid(
            column=0,
            row=2)
        ttk.Button(
            self,
            text=" Clear ",
            command=self.search_clear,
            style='my.TButton').grid(
            column=1,
            row=2)
        ttk.Button(
            self,
            textvariable=self.Local_BTNV,
            command=self.download,
            style='my.TButton').grid(
            column=2,
            row=2)

    def search(self):
        if self.Local_searched:
            self.Local_NID.set("Searched")
            return
        if self.Local_searching:
            self.Local_NID.set("Searching")
            return
        threading.Thread(target=self.search_main).start()

    def search_main(self):
        self.Local_searching = True

        gen = self.MSO.NovSearch(self.Local_NID.get())
        Title = next(gen)
        meta = next(gen)
        bktree = next(gen)
        if (not Title) or (not meta) or (not bktree):
            self.Local_BTNV.set("网络异常!")
            self.Local_searching = False
            return None
        ####
        self.t.heading('#0', text="章节名", anchor='w')
        self.t.heading('ep', text="EPid", anchor='w')
        for i in bktree.keys():
            node = self.t.insert('', 'end', text=i)
            for t in bktree[i]:
                self.t.insert(
                    node, 'end', text=t['tTitle'], values=(
                        t['path'].split(
                            "?", 1)[1],))
        self.Local_searching = False
        self.Local_searched = True

    def delbktree(self):
        self.t.delete(*self.t.selection())

    def search_clear(self):
        self.t.delete(*self.t.get_children())
        self.Local_searched = False
        self.Local_Downloaded = False
        self.MSO.bookMeta = None
        self.MSO.bookTit = None
        self.MSO.booktree = None
        self.MSO.nid = None

    def download(self):
        if self.Local_Downloaded:
            self.Local_BTNV.set("Downloaded")
            return
        if self.Local_Downloading:
            self.Local_BTNV.set("Downloading")
            return
        threading.Thread(target=self.download_main).start()

    def download_main(self):
        self.Local_Downloading = True
        bkt = {}
        for ch in self.t.get_children():
            chnode = []
            for ep in self.t.get_children(ch):
                chnode.append({'cid=': str(self.t.item(ep)['values'][0])})
            bkt.update({str(self.t.item(ch)['text']): chnode})
        self.MSO.booktree = bkt
        if not os.path.exists(f"Cache/{self.MSO.nid}"):
            os.mkdir(f"Cache/{self.MSO.nid}")
        with open(f"Cache/{self.MSO.nid}/init.json", 'w', encoding='utf-8') as f:
            json.dump(bkt, f)
        with open(f"Cache/{self.MSO.nid}/meta.json", 'w', encoding='utf-8') as f:
            json.dump(self.MSO.bookMeta, f)
        tls = []
        for _ in bkt.keys():
            for ep in bkt[_]:
                cid = ep["cid="]
                epb, tit = self.MSO.EPSearch(cid=cid)
                ep["Title"] = tit
                cid = cid.replace("=", '_')
                tls.append(
                    threading.Thread(
                        target=self.MSO.EPdr,
                        kwargs={
                            'ep': epb,
                            'SavePath': f"Cache/{self.MSO.nid}/{ cid }.xhtml"}))
                tls[-1].start()
        [_.join() for _ in tls]
        with open(f"Cache/{self.MSO.nid}/init.json", 'w', encoding='utf-8') as f:
            json.dump(bkt, f)
        self.MSO.modconf(upd={self.MSO.nid: self.MSO.bookTit})
        self.Local_Downloading = False
        self.Local_Downloaded = False
        return


class HDP(ttk.Frame):
    def __init__(self, master, MSO) -> None:
        super().__init__(master)
        self.grid(column=0, row=0)
        self.t = ttk.Treeview(
            self,
            columns=(
                'nid',
                'title'),
            selectmode='browse',
            show='tree')
        self.t.grid(column=0, columnspan=3, row=0)
        self.sav = ttk.Button(
            self,
            text="Save to ./Result",
            command=self.save,
            style='my.TButton')
        self.sav.grid(column=0, columnspan=2, row=1)
        self.ref = ttk.Button(
            self,
            text="Refresh",
            command=self.refresh,
            style='my.TButton')
        self.ref.grid(column=2, columnspan=1, row=1)
        self.refresh()

    def save(self):
        if len(self.t.selection()) == 0:
            return
        r = self.t.item(self.t.selection()[0])["values"]
        threading.Thread(target=MSOEpub(
            *(self.t.item(self.t.selection()[0]))["values"]).out).start()
        print(r)

    def refresh(self):
        with open("./Cache/sav.json", 'r', encoding='utf-8') as f:
            self.sav = json.load(f)
        self.t.heading('nid', text="NovelID", anchor='w')
        self.t.heading('title', text="BookName", anchor='w')
        del self.sav["nid="]
        for nids in self.sav.keys():
            self.t.insert('', 'end', values=(nids, self.sav[nids]))


class MSOI(ttk.Notebook):
    MSO = None

    def _sty_(self, sty: ttk.Style):
        sty.configure('my.TButton', font=('-size', 36))

    def __init__(self, master, sty) -> None:
        self.MSO = Masiro()
        self._sty_(sty)
        super().__init__(master)
        self.interpagedict = {
            "登录": MSP(
                self, self.MSO), "小说选取": NVP(
                self, self.MSO), "生成器": HDP(
                self, self.MSO)}
        for att in self.interpagedict:
            self.add(
                self.interpagedict[att],
                text=att,
                padding=12,
                sticky="nsew")
        self.grid(column=0, row=0)


class app():
    def __init__(self,window:tkinter.Tk):
        self.window = window
        self.window.geometry('720x480')
        sv_ttk.set_theme("dark")
        self.Local_MSOI = MSOI(self.window, ttk.Style())

    def run(self, debug=False):
        self.window.mainloop()


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
                        datefmt='%a, %d %b %Y %H:%M:%S',
                        filename='/MSOInstaller.log',
                        filemode='w')

    app(window).run(False)
