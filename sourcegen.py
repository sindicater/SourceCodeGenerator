import sys
import os
from urllib.parse import urljoin
import requests
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEnginePage
from bs4 import BeautifulSoup
import jsbeautifier

class MainWindow(QMainWindow):
    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        self.setWindowTitle("Scrapper")
        icon_path = "scrapper.png"  # Replace "path_to_your_icon" with the actual path
        self.setWindowIcon(QIcon(icon_path))

        self.browser = QWebEngineView()
        self.browser.urlChanged.connect(self.update_urlbar)
        self.browser.loadFinished.connect(self.update_title)
        self.browser.loadProgress.connect(self.update_progress)

        self.setCentralWidget(self.browser)

        self.status = QStatusBar()
        self.setStatusBar(self.status)

        navtb = QToolBar("Navigation")
        navtb.setIconSize(QSize(24, 24))
        self.addToolBar(navtb)

        back_btn = QAction("Back", self)
        back_btn.setStatusTip("Back to previous page")
        back_btn.triggered.connect(self.browser.back)
        navtb.addAction(back_btn)

        next_btn = QAction("Forward", self)
        next_btn.setStatusTip("Forward to next page")
        next_btn.triggered.connect(self.browser.forward)
        navtb.addAction(next_btn)

        reload_btn = QAction("Reload", self)
        reload_btn.setStatusTip("Reload page")
        reload_btn.triggered.connect(self.browser.reload)
        navtb.addAction(reload_btn)

        home_btn = QAction("Home", self)
        home_btn.setStatusTip("Go home")
        home_btn.triggered.connect(self.navigate_home)
        navtb.addAction(home_btn)

        navtb.addSeparator()

        self.urlbar = QLineEdit()
        self.urlbar.setPlaceholderText("Enter URL")
        self.urlbar.returnPressed.connect(self.navigate_to_url)
        navtb.addWidget(self.urlbar)

        search_btn = QAction("Search", self)
        search_btn.setStatusTip("Search for a URL")
        search_btn.triggered.connect(self.search_url)
        navtb.addAction(search_btn)

        generate_btn = QAction("Generate Source Code", self)
        generate_btn.setStatusTip("Generate source code for the website")
        generate_btn.triggered.connect(self.generate_source_code)
        navtb.addAction(generate_btn)

        self.progress = QProgressBar()
        self.progress.setMaximum(100)
        self.progress.setValue(0)
        self.progress.setTextVisible(False)
        self.progress.setFixedSize(100, 16)
        navtb.addWidget(self.progress)

        self.setWindowTitle("Modern Web Browser")
        self.setGeometry(100, 100, 1200, 800)

        self.apply_styles()

        self.show()

        self.browser.setUrl(QUrl("https://www.google.com"))

    def apply_styles(self):
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2c3e50;
            }
            QToolBar {
                background: #34495e;
                spacing: 6px;
            }
            QToolBar QToolButton {
                background: #2980b9;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 6px 12px;
                margin: 4px;
                font-weight: bold;
            }
            QToolBar QToolButton:hover {
                background: #3498db;
            }
            QToolBar QToolButton:pressed {
                background: #1c6691;
            }
            QLineEdit {border: 2px solid #2980b9;
                border-radius: 8px;
                padding: 6px;
                margin: 4px;
                background: white;
                color: #34495e;
                font-size: 14px;
            }
            QProgressBar {
                background: #ecf0f1;
                border: 2px solid #2980b9;
                border-radius: 8px;
            }
            QProgressBar::chunk {
                background: #27ae60;
                border-radius: 8px;
            }
            QStatusBar {
                background: #34495e;
                color: white;
            }
        """)

    def navigate_home(self):
        self.browser.setUrl(QUrl("https://www.google.com"))

    def search_url(self):
        url = self.urlbar.text()
        if not url.startswith("http"):
            url = "http://" + url
        self.browser.setUrl(QUrl(url))
    def navigate_to_url(self):
        url = self.urlbar.text()
        if not url.startswith("http"):
            url = "http://" + url
        self.browser.setUrl(QUrl(url))

    def update_urlbar(self, q):
        self.urlbar.setText(q.toString())

    def update_title(self):
        self.setWindowTitle(self.browser.page().title())

    def update_progress(self, progress):
        self.progress.setValue(progress)

    def extract_links_recursively(self, base_url, urls_to_scan):
        all_links = set()

        for url in urls_to_scan:
            try:
                response = requests.get(url)
                soup = BeautifulSoup(response.content, 'html.parser')
                all_links.update(self.extract_links(soup, base_url))
            except Exception as e:
                print(f"Error while scanning {url}: {e}")

        return list(all_links)

    def extract_links(self, soup, base_url):
        links = []

        for img in soup.find_all('img'):
            img_src = img.get('src')
            if img_src:
                links.append(urljoin(base_url, img_src))

        for video in soup.find_all('video'):
            video_src = video.get('src')
            if video_src:
                links.append(urljoin(base_url, video_src))

        for link in soup.find_all('a', href=True):
            href = link['href']
            if not href.startswith('#') and (href.endswith('.html') or href.endswith('/')):
                linked_url = urljoin(base_url, href)
                links.append(linked_url)

        for script in soup.find_all('script', src=True):
            src = script['src']
            if src.endswith('.js'):
                linked_url = urljoin(base_url, src)
                links.append(linked_url)

        for style in soup.find_all('link', href=True):
            href = style['href']
            if href.endswith('.css'):
                linked_url = urljoin(base_url, href)
                links.append(linked_url)

        for div in soup.find_all('div', class_='skill-card'):
            onclick = div.get('onclick')
            if onclick:
                linked_url = urljoin(base_url, onclick[13:-2])
                links.append(linked_url)

        return links

    def download_images_and_videos(self, directory, links, base_url):
        for link in links:
            if link.endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg')):
                # Download image
                img_response = requests.get(link)
                img_filename = os.path.basename(link)
                with open(os.path.join(directory, img_filename), "wb") as f:
                    f.write(img_response.content)

            elif link.endswith(('.mp4', '.webm', '.ogg', '.avi', '.mov')):
                # Download video
                video_response = requests.get(link)
                video_filename = os.path.basename(link)
                with open(os.path.join(directory, video_filename), "wb") as f:
                    f.write(video_response.content)

    def generate_files_for_links(self, directory, links, base_url):
        for link in links:
            if link.endswith('.html'):  # Handle HTML files
                response = requests.get(link)
                soup = BeautifulSoup(response.content, 'html.parser')
                html_code = soup.prettify()
                css_code = ''
                for style in soup.find_all('style'):
                    css_code += style.prettify() + '\n'
                js_code = ''
                for script in soup.find_all('script'):
                    if script.has_attr('src'):
                        src = script['src']
                        if src.startswith('//'):
                            src = 'http:' + src
                        elif not src.startswith('http'):
                            src = base_url + '/' + src
                        ext_js = requests.get(src).text
                        js_code += jsbeautifier.beautify(ext_js) + '\n'
                    else:
                        js_code += jsbeautifier.beautify(script.string) + '\n'

                filename = os.path.basename(link)
                with open(os.path.join(directory, filename), "w") as f:
                    f.write(html_code)
                with open(os.path.join(directory, filename[:-5] + '.css'), "w") as f:
                    f.write(css_code)
                with open(os.path.join(directory, filename[:-5] + '.js'), "w") as f:
                    f.write(js_code)

            elif link.endswith('.css'):  # Handle CSS files
                response = requests.get(link)
                css_code = response.text
                with open(os.path.join(directory, os.path.basename(link)), "w") as f:
                    f.write(css_code)

            elif link.endswith('.js'):  # Handle JavaScript files
                response = requests.get(link)
                js_code = response.text
                with open(os.path.join(directory, os.path.basename(link)), "w") as f:
                    f.write(js_code)

            elif link.endswith('.ts'):  # Handle TypeScript files
                response = requests.get(link)
                ts_code = response.text
                with open(os.path.join(directory, os.path.basename(link)), "w") as f:
                    f.write(ts_code)

            elif link.endswith('.php'):  # Handle PHP files
                response = requests.get(link)
                php_code = response.text
                with open(os.path.join(directory, os.path.basename(link)), "w") as f:
                    f.write(php_code)

            elif link.endswith('.py'):  # Handle Python files
                response = requests.get(link)
                py_code = response.text
                with open(os.path.join(directory, os.path.basename(link)), "w") as f:
                    f.write(py_code)

            elif link.endswith('.rb'):  # Handle Ruby files
                response = requests.get(link)
                rb_code = response.text
                with open(os.path.join(directory, os.path.basename(link)), "w") as f:
                    f.write(rb_code)

            elif link.endswith('.java'):  # Handle Java files
                response = requests.get(link)
                java_code = response.text
                with open(os.path.join(directory, os.path.basename(link)), "w") as f:
                    f.write(java_code)

            elif link.endswith('.go'):  # Handle Go files
                response = requests.get(link)
                go_code = response.text
                with open(os.path.join(directory, os.path.basename(link)), "w") as f:
                    f.write(go_code)

            elif link.endswith('.cs'):  # Handle C# files
                response = requests.get(link)
                cs_code = response.text
                with open(os.path.join(directory, os.path.basename(link)), "w") as f:
                    f.write(cs_code)

            elif link.endswith('.fs'):  # Handle F# files
                response = requests.get(link)
                fs_code = response.text
                with open(os.path.join(directory, os.path.basename(link)), "w") as f:
                    f.write(fs_code)

            elif link.endswith('.dart'):  # Handle Dart files (Flutter)
                response = requests.get(link)
                dart_code = response.text
                with open(os.path.join(directory, os.path.basename(link)), "w") as f:
                    f.write(dart_code)
            self.download_images_and_videos(directory, links, base_url)
            # Add more file type handlers as needed

    def generate_source_code(self):
        url = self.urlbar.text()
        if not url.startswith("http"):
            url = "http://" + url

        base_url = url
        if not url.endswith('/'):
            base_url += '/'

        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')
        initial_links = self.extract_links(soup, base_url)

        links_to_scan = self.extract_links_recursively(base_url, initial_links)

        directory = QFileDialog.getExistingDirectory(self, "Select Directory")
        if directory:
            self.generate_files_for_links(directory, links_to_scan, base_url)
            QMessageBox.information(self, "Success", "Source code generated successfully!")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec_())