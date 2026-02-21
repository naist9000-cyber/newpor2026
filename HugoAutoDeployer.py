import sys
import os
import subprocess
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QLineEdit, QPushButton, QFileDialog, QTextEdit, QMessageBox)
from PyQt6.QtCore import Qt, QThread, pyqtSignal

class Worker(QThread):
    finished = pyqtSignal(bool, str)
    progress = pyqtSignal(str)

    def __init__(self, config):
        super().__init__()
        self.config = config

    def run(self):
        try:
            path = self.config['path']
            title = self.config['title']
            subtitle = self.config['subtitle']
            repo_url = self.config['repo_url']

            if not os.path.exists(path):
                os.makedirs(path)
            
            os.chdir(path)
            self.progress.emit(f"🚀 작업을 시작합니다: {path}")

            # 1. Hugo 사이트 생성
            self.progress.emit("1. Hugo 사이트 초기화 중...")
            subprocess.run(["hugo", "new", "site", ".", "--force"], check=True, shell=True)

            # 2. Git 초기화 및 테마 추가
            self.progress.emit("2. Git 설정 및 테마 다운로드 중 (시간이 소요될 수 있습니다)...")
            subprocess.run(["git", "init"], check=True, shell=True)
            subprocess.run(["git", "submodule", "add", "https://github.com/CaiJimmy/hugo-theme-stack.git", "themes/hugo-theme-stack"], check=True, shell=True)

            # 3. 설정 파일 생성 (통합형 hugo.toml)
            self.progress.emit("3. 한국어 최적화 설정 적용 중...")
            hugo_toml = f'''baseURL = "{repo_url.replace('.git', '/')}"
languageCode = "ko-kr"
title = "{title}"
defaultContentLanguage = "ko"
hasCJKLanguage = true

[[module.imports]]
    path = "github.com/CaiJimmy/hugo-theme-stack/v3"

[pagination]
    pagerSize = 5

[permalinks]
    post = "/p/:slug/"
    page = "/:slug/"

[params]
    mainSections = ["post"]
    rssFullContent = true
    
    [params.footer]
        since = 2026
        customText = "{title} - {subtitle}"

    [params.sidebar]
        emoji = "✏️"
        subtitle = "{subtitle}"

    [params.article]
        [params.article.license]
            enabled = false
        
    [params.comments]
        enabled = false

    [params.widgets]
        homepage = [
            {{ type = "search" }},
            {{ type = "archives", params = {{ limit = 5 }} }},
            {{ type = "categories", params = {{ limit = 10 }} }},
            {{ type = "tag-cloud", params = {{ limit = 10 }} }},
        ]
        page = [{{ type = "toc" }}]

[menu]
    [[menu.main]]
        identifier = "home"
        name = "홈"
        url = "/"
        weight = 1
        [menu.main.params]
            icon = "home"

    [[menu.main]]
        identifier = "archives"
        name = "아카이브"
        url = "/archives/"
        weight = 2
        [menu.main.params]
            icon = "archives"

    [[menu.main]]
        identifier = "search"
        name = "검색"
        url = "/search/"
        weight = 3
        [menu.main.params]
            icon = "search"
'''
            os.makedirs("config/_default", exist_ok=True)
            with open("config/_default/hugo.toml", "w", encoding="utf-8") as f:
                f.write(hugo_toml)

            # 4. 초기 포스팅 생성
            self.progress.emit("4. 환영 인사 포스트 생성 중...")
            os.makedirs("content/post/welcome", exist_ok=True)
            with open("content/post/welcome/index.md", "w", encoding="utf-8") as f:
                f.write(f'''---
title: "{title} 블로그에 오신 것을 환영합니다!"
description: "{subtitle}"
date: 2026-02-22T00:00:00+09:00
---
안녕하세요! **{title}** 블로그를 방문해 주셔서 감사합니다.
''')

            # 5. GitHub Actions 설정
            self.progress.emit("5. 자동 배포 기능(GitHub Actions) 설정 중...")
            os.makedirs(".github/workflows", exist_ok=True)
            with open(".github/workflows/hugo.yml", "w", encoding="utf-8") as f:
                f.write('''name: Deploy Hugo site to Pages
on:
  push:
    branches: ["main"]
  workflow_dispatch:
permissions:
  contents: read
  pages: write
  id-token: write
concurrency:
  group: "pages"
  cancel-in-progress: false
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4
        with:
          submodules: recursive
          fetch-depth: 0
      - name: Setup Pages
        uses: actions/configure-pages@v4
      - name: Install Hugo
        run: sudo apt-get install hugo
      - name: Build with Hugo
        run: hugo --minify --baseURL "${{ steps.pages.outputs.base_url }}/"
      - name: Upload artifact
        uses: actions/upload-pages-artifact@v3
        with:
          path: ./public
  deploy:
    needs: build
    runs-on: ubuntu-latest
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    steps:
      - name: Deploy to GitHub Pages
        id: deployment
        uses: actions/deploy-pages@v4
''')

            # 6. 배포
            self.progress.emit("6. GitHub에 업로드 및 배포 중...")
            subprocess.run(["git", "add", "."], check=True, shell=True)
            subprocess.run(["git", "commit", "-m", "Initial commit: Hugo Stack Theme Optimized"], check=True, shell=True)
            subprocess.run(["git", "branch", "-M", "main"], check=True, shell=True)
            subprocess.run(["git", "remote", "add", "origin", repo_url], check=True, shell=True)
            subprocess.run(["git", "push", "-u", "origin", "main", "--force"], check=True, shell=True)

            self.finished.emit(True, "✅ 모든 작업이 성공적으로 완료되었습니다!")
        except Exception as e:
            self.finished.emit(False, f"❌ 에러 발생: {str(e)}")

class HugoApp(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('🚀 Hugo 블로그 자동 배포 툴 (PyQt6 버전)')
        self.setGeometry(300, 300, 500, 600)

        layout = QVBoxLayout()

        # 사이트 정보
        layout.addWidget(QLabel('📝 블로그 제목 (닉네임):'))
        self.edit_title = QLineEdit('정보톡톡')
        layout.addWidget(self.edit_title)

        layout.addWidget(QLabel('💡 블로그 한 줄 설명:'))
        self.edit_subtitle = QLineEdit('세상의 정보를 한번 알아보자')
        layout.addWidget(self.edit_subtitle)

        # 깃허브 정보
        layout.addWidget(QLabel('🔗 GitHub 저장소 URL:'))
        self.edit_repo = QLineEdit('https://github.com/[ID]/[REPO_NAME].git')
        layout.addWidget(self.edit_repo)

        # 경로 설정
        layout.addWidget(QLabel('📂 로컬 저장 경로:'))
        h_layout = QHBoxLayout()
        self.edit_path = QLineEdit(os.getcwd())
        btn_path = QPushButton('폴더 선택')
        btn_path.clicked.connect(self.selectFolder)
        h_layout.addWidget(self.edit_path)
        h_layout.addWidget(btn_path)
        layout.addLayout(h_layout)

        # 로그 출력창
        layout.addWidget(QLabel('🖥️ 작업 로그:'))
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        layout.addWidget(self.log_output)

        # 실행 버튼
        self.btn_run = QPushButton('🎨 블로그 생성 및 배포 시작')
        self.btn_run.setFixedHeight(50)
        self.btn_run.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; font-size: 16px;")
        self.btn_run.clicked.connect(self.startTask)
        layout.addWidget(self.btn_run)

        self.setLayout(layout)

    def selectFolder(self):
        folder = QFileDialog.getExistingDirectory(self, "설치할 폴더 선택")
        if folder:
            self.edit_path.setText(folder)

    def startTask(self):
        config = {
            'title': self.edit_title.text(),
            'subtitle': self.edit_subtitle.text(),
            'repo_url': self.edit_repo.text(),
            'path': self.edit_path.text()
        }

        if 'github.com' not in config['repo_url']:
            QMessageBox.warning(self, '경고', '올바른 GitHub URL을 입력해주세요.')
            return

        self.btn_run.setEnabled(False)
        self.log_output.clear()
        
        self.worker = Worker(config)
        self.worker.progress.connect(self.updateLog)
        self.worker.finished.connect(self.onFinished)
        self.worker.start()

    def updateLog(self, text):
        self.log_output.append(text)

    def onFinished(self, success, message):
        self.btn_run.setEnabled(True)
        if success:
            QMessageBox.information(self, '완료', message)
        else:
            QMessageBox.critical(self, '에러', message)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = HugoApp()
    ex.show()
    sys.exit(app.exec())
