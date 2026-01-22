import sys, json, os
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QToolBar, QLineEdit, QAction,
    QFileDialog, QMessageBox, QMenu
)
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineProfile
from PyQt5.QtCore import QUrl, Qt
# Attempt to import pyinstaller_splash dynamically to avoid static import errors in editors/linters.
# If unavailable, provide a no-op close_splash() so it can be called unconditionally later.
try:
    import importlib
    import importlib.util
    if importlib.util.find_spec("pyinstaller_splash") is not None:
        mod = importlib.import_module("pyinstaller_splash")
        close_splash = getattr(mod, "close_splash", lambda: None)
    else:
        def close_splash():
            pass
except Exception:
    # Splash handling will be performed after the main window is created and shown.
    # Provide a no-op so close_splash() can be called unconditionally later.
    def close_splash():
        pass

import time


BOOKMARKS_FILE = "bookmarks.json"


class Browser(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Andor")
        self.setGeometry(100, 100, 1200, 800)

        # ---- Tabs ----
        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.currentChanged.connect(self.update_urlbar)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.setCentralWidget(self.tabs)

        # ---- Navigation Toolbar ----
        nav = QToolBar("Navigation")
        nav.setMovable(False)
        self.addToolBar(nav)

        back_btn = QAction("⟵", self)
        back_btn.triggered.connect(self.safe_back)
        nav.addAction(back_btn)

        fwd_btn = QAction("⟶", self)
        def go_forward():
            b = self.current()
            if b:
                try:
                    b.forward()
                except AttributeError:
                    pass
        fwd_btn.triggered.connect(go_forward)
        nav.addAction(fwd_btn)

        reload_btn = QAction("⟳", self)
        reload_btn.triggered.connect(self.safe_reload)
        nav.addAction(reload_btn)

        # Create the add button ONCE here
        add_btn = QAction("➕", self)
        add_btn.triggered.connect(self.safe_add)
        nav.addAction(add_btn)

        # Home button
        home_btn = QAction("🏠", self)
        home_btn.triggered.connect(self.go_home)
        nav.addAction(home_btn)

        # ---- URL Bar ----
        self.urlbar = QLineEdit()
        self.urlbar.returnPressed.connect(self.navigate_to_url)
        nav.addWidget(self.urlbar)

        # ---- Bookmarks Menu ----
        bookmarks_menu = QMenu("Bookmarks", self)
        bookmark_btn = QAction("⭐ Add Bookmark", self)
        bookmark_btn.triggered.connect(self.add_bookmark)
        bookmarks_menu.addAction(bookmark_btn)

        load_bookmarks_btn = QAction("📁 Show Bookmarks", self)
        load_bookmarks_btn.triggered.connect(self.show_bookmarks)
        bookmarks_menu.addAction(load_bookmarks_btn)

        nav.addAction(bookmarks_menu.menuAction())

        # ---- Shortcuts ----
        new_tab = QAction("New Tab", self)
        new_tab.setShortcut("Ctrl+T")
        new_tab.triggered.connect(lambda: self.add_tab("https://google.com"))
        self.addAction(new_tab)

        close_tab = QAction("Close Tab", self)
        close_tab.setShortcut("Ctrl+W")
        close_tab.triggered.connect(lambda: self.close_tab(self.tabs.currentIndex()))
        self.addAction(close_tab)

        # ---- Downloads ----
        profile = QWebEngineProfile.defaultProfile()
        if profile is not None:
            try:
                profile.downloadRequested.connect(self.on_download)
            except AttributeError:
                # Profile does not provide downloadRequested in this environment
                pass

        # ---- Create Startup Tab ----
        self.add_tab("https://google.com")

        self.apply_theme()

    def go_home(self):
        b = self.current()
        if b:
            try:
                b.setUrl(QUrl("https://google.com"))
            except AttributeError:
                # current widget does not support setUrl()
                pass

    def safe_add(self):
        browser = QWebEngineView()
        browser.setUrl(QUrl("https://www.google.com"))
        i = self.tabs.addTab(browser, "New Tab")
        self.tabs.setCurrentIndex(i)
        browser.urlChanged.connect(self.update_urlbar)
        browser.titleChanged.connect(lambda t: self.tabs.setTabText(self.tabs.indexOf(browser), t))

    # ------------------- UTILITIES -------------------

    def current(self):
        return self.tabs.currentWidget()

    def safe_back(self):
        b = self.current()
        if b:
            try:
                b.back()
            except AttributeError:
                # In case the current widget doesn't implement back()
                pass

    def safe_reload(self):
        b = self.current()
        if b:
            try:
                b.reload()
            except AttributeError:
                # In case the current widget doesn't implement reload()
                pass

    def add_tab(self, url, label="New Tab"):
        browser = QWebEngineView()
        browser.setUrl(QUrl(url))
        i = self.tabs.addTab(browser, label)
        self.tabs.setCurrentIndex(i)
        browser.urlChanged.connect(self.update_urlbar)
        browser.titleChanged.connect(lambda t: self.tabs.setTabText(i, t))

    def close_tab(self, i):
        if self.tabs.count() > 1:
            self.tabs.removeTab(i)

    def navigate_to_url(self):
        url = self.urlbar.text()
        if not url.startswith("http"):
            url = "https://" + url
        b = self.current()
        if b:
            try:
                b.setUrl(QUrl(url))
            except AttributeError:
                # In case the current widget doesn't implement setUrl()
                pass
        else:
            QMessageBox.warning(self, "No Tab", "There is no active tab to navigate to.")

    def update_urlbar(self, q=None):
        browser = self.current()
        if browser:
            self.urlbar.setText(browser.url().toString())

    # ------------------- DOWNLOADS -------------------

    def on_download(self, download):
        path, _ = QFileDialog.getSaveFileName(self, "Save File", download.suggestedFileName())
        if path:
            download.setPath(path)
            download.accept()

    # ------------------- BOOKMARKS -------------------

    def add_bookmark(self):
        b = self.current()
        if not b:
            QMessageBox.warning(self, "No Tab", "There is no active tab to bookmark.")
            return

        url = b.url().toString()
        title = b.title()
        data = {"title": title, "url": url}

        bookmarks = self.load_bookmarks()
        bookmarks.append(data)
        self.save_bookmarks(bookmarks)

        QMessageBox.information(self, "Bookmark Added", f"Saved: {title}")

    def show_bookmarks(self):
        bookmarks = self.load_bookmarks()
        menu = QMenu(self)

        for b in bookmarks:
            act = QAction(b["title"], self)
            act.triggered.connect(lambda _, url=b["url"]: self.add_tab(url, b["title"]))
            menu.addAction(act)

        menu.exec_(self.mapToGlobal(self.urlbar.pos()))

    def load_bookmarks(self):
        if not os.path.exists(BOOKMARKS_FILE):
            return []
        return json.load(open(BOOKMARKS_FILE, "r"))

        def save_bookmarks(self, data):
            json.dump(data, open(BOOKMARKS_FILE, "w"), indent=2)
    
        # ------------------- THEME -------------------
    def apply_theme(self):
            # Apply a simple light theme to the main widgets
            self.setStyleSheet("""
            
            QToolBar {
                background: #f1f3f4;
                padding: 6px;
                border-bottom: 1px solid #ccc;
            }
            QLineEdit {
                padding: 6px;
                border-radius: 6px;
                background: white;
            }
            QTabWidget::pane {
                border: none;
            }
            """)
    
if __name__ == "__main__":
        app = QApplication(sys.argv)
        window = Browser()
        window.show()
        time.sleep(0.3)  # short delay to ensure the window appears before closing the splash
        try:
            close_splash()
        except Exception:
            pass
        sys.exit(app.exec_())