import os
import sys
import time
import socket
import subprocess
import signal
import shutil
import random
import json
import threading
from pathlib import Path
from playwright.sync_api import sync_playwright

# --- 全局配置 ---
TIMEOUT_SECONDS = 120   # 等待服务启动的最大时间
VIEWPORT_WIDTH = 1280   # 视口宽度
VIEWPORT_HEIGHT = 720   # 视口高度
npm_cmd = 'npm.cmd' if os.name == 'nt' else 'npm'
PROJECT_ROOT = Path(__file__).resolve().parents[1]
NODE_MODULES_CACHE_ROOT = PROJECT_ROOT / "web_node_modules_cache"

# --- 依赖安装锁（防止多线程同时下载同一 framework 的依赖） ---
_install_locks: dict[str, threading.Lock] = {}
_install_locks_guard = threading.Lock()

def _get_install_lock(framework: str) -> threading.Lock:
    with _install_locks_guard:
        if framework not in _install_locks:
            _install_locks[framework] = threading.Lock()
        return _install_locks[framework]

# --- 工具函数 ---

def get_free_port():
    """获取随机空闲端口"""
    while True:
        port = random.randint(10000, 60000)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(('127.0.0.1', port)) != 0:
                return port

def check_port_open(port):
    """检测端口是否开启"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(1)
        return s.connect_ex(('127.0.0.1', port)) == 0

def kill_process_tree(pid):
    """终止进程树"""
    try:
        if os.name == 'nt':
            subprocess.call(['taskkill', '/F', '/T', '/PID', str(pid)], 
                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            os.killpg(os.getpgid(pid), signal.SIGTERM)
    except:
        pass

def install_dependencies(path, framework):
    """安装 npm 依赖（线程安全：同一 framework 的安装互斥）"""
    path = Path(path)
    project_nm = path / "node_modules"
    if project_nm.exists():
        return

    lock = _get_install_lock(framework)
    with lock:
        # 获取锁后重新检查（其他线程可能已完成安装并缓存）
        if project_nm.exists():
            return

        cached_nm = NODE_MODULES_CACHE_ROOT / framework / "node_modules"

        # 缓存已存在（可能是等待期间其他线程创建的），直接 symlink
        if cached_nm.exists():
            try:
                project_nm.symlink_to(cached_nm, target_is_directory=True)
                return
            except Exception as e:
                print(f"⚠️ Symlink failed:{e}")

        # 缓存不存在，安装并写入缓存
        print(f"📦 Cache miss for {framework}, installing dependencies...")
        cmd = [npm_cmd, "install"]
        if framework == "angular":
            cmd.append("--legacy-peer-deps")

        subprocess.run(
            cmd,
            cwd=str(path),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            timeout=3600,
            shell=(os.name == "nt"),
            check=True,
        )

        if not project_nm.exists():
            raise FileNotFoundError(
                f"❌ npm install finished but node_modules not found: {project_nm}"
            )

        cached_nm.parent.mkdir(parents=True, exist_ok=True)
        if not cached_nm.exists():
            shutil.copytree(project_nm, cached_nm)

        shutil.rmtree(project_nm)
        project_nm.symlink_to(cached_nm, target_is_directory=True)


# --- 处理器基类 ---

class ProjectHandler:
    def __init__(self, path):
        self.path = Path(path).resolve()
        self.process = None
        self.port = None
        self.base_url = None
        self.log_file = None

    def setup(self):
        """安装依赖"""
        pass

    def start(self):
        """启动服务，返回 Base URL"""
        return None

    def get_routes(self):
        """返回路由列表 [{'name': 'index', 'route': '/...'}, ...]"""
        return []

    def get_root_selector(self):
        """返回主要容器 ID，用于 CSS 修复"""
        return "body"

    def stop(self):
        """清理资源"""
        if self.log_file:
            self.log_file.close()
        if self.process:
            # print(f"🧹 Stopping server...")
            kill_process_tree(self.process.pid)
            if self.port and os.name != "nt":
                os.system(
                    f"lsof -ti:{self.port} | xargs kill -9 >/dev/null 2>&1"
                )
        # 清理项目下的 node_modules 软连接（仅软连接）
        project_nm = self.path / "node_modules"
        try:
            if project_nm.is_symlink():
                project_nm.unlink()
                # print(f"🧹 Removed symlink: {project_nm}")
        except Exception as e:
            print(f"⚠️ Failed to remove symlink {project_nm}: {e}")


# --- 具体实现 ---


class HtmlHandler(ProjectHandler):
    def setup(self):
        pass  # 无需安装

    def start(self):
        # 静态文件使用 file:// 协议
        self.base_url = self.path.as_uri()
        return self.base_url

    def get_routes(self):
        routes = []
        for file in self.path.glob("*.html"):
            stem = file.stem
            # file:// URL 需要完整文件名
            routes.append(
                {"name": stem, "route": f"/{file.name}", "is_file": True}
            )
        return routes

    def get_root_selector(self):
        return "body"


class AngularHandler(ProjectHandler):
    def setup(self):
        install_dependencies(self.path, "angular")

    def start(self):
        self.port = get_free_port()
        print(f"🚀 Starting Angular on port {self.port}...")
        self.log_file = open(self.path / "angular_run.log", "w")

        cmd = [
            npm_cmd,
            "start",
            "--",
            "--port",
            str(self.port),
            "--host",
            "127.0.0.1",
            "--disable-host-check",
        ]
        cmd_str = " ".join(cmd) if os.name == "nt" else cmd
        shell_mode = os.name == "nt"

        self.process = subprocess.Popen(
            cmd_str,
            cwd=str(self.path),
            stdout=self.log_file,
            stderr=subprocess.STDOUT,
            preexec_fn=None if os.name == "nt" else os.setsid,
            shell=shell_mode,
        )

        self._wait_for_port()
        self.base_url = f"http://127.0.0.1:{self.port}"
        return self.base_url

    def get_routes(self):
        pages_dir = self.path / "src" / "app" / "pages"
        routes = []
        # 默认路由
        routes.append({"name": "index", "route": "/#/"})

        if pages_dir.exists():
            for file in pages_dir.glob("*.component.ts"):
                stem = file.stem.replace(".component", "")
                lower = stem.lower()
                if lower not in ["index", "home", "main"]:
                    routes.append({"name": lower, "route": f"/#/{lower}"})
        return routes

    def get_root_selector(self):
        return "app-root"

    def _wait_for_port(self):
        print("   Waiting for server...", end="", flush=True)
        for _ in range(TIMEOUT_SECONDS):
            if check_port_open(self.port):
                print(" Ready.")
                return
            time.sleep(1)
            print(".", end="", flush=True)
        raise TimeoutError("Server failed to start")


class ReactHandler(ProjectHandler):
    def setup(self):
        install_dependencies(self.path, "react")

    def start(self):
        self.port = get_free_port()
        print(f"🚀 Starting React on port {self.port}...")
        self.log_file = open(self.path / "react_run.log", "w")

        env = os.environ.copy()
        env["PORT"] = str(self.port)
        env["BROWSER"] = "none"

        self.process = subprocess.Popen(
            [npm_cmd, "start"],
            cwd=str(self.path),
            env=env,
            stdout=self.log_file,
            stderr=subprocess.STDOUT,
            preexec_fn=None if os.name == "nt" else os.setsid,
            shell=(os.name == "nt"),
            creationflags=(
                subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0
            ),
        )

        self._wait_for_port()
        self.base_url = f"http://localhost:{self.port}"
        return self.base_url

    def get_routes(self):
        pages_dir = self.path / "src" / "pages"
        routes = [{"name": "index", "route": "/"}]
        if pages_dir.exists():
            for file in pages_dir.glob("*.js*"):  # match .js, .jsx
                stem = file.stem.lower()
                if stem not in ["index", "home", "main", "app"]:
                    # React 尝试 .html 后缀，失败会回退
                    routes.append(
                        {
                            "name": stem,
                            "route": f"/{stem}.html",
                            "try_clean": True,
                        }
                    )
        return routes

    def get_root_selector(self):
        return "#root"

    def _wait_for_port(self):
        # React 启动同 Angular
        AngularHandler._wait_for_port(self)


class VueHandler(ProjectHandler):
    def setup(self):
        install_dependencies(self.path, "vue")

    def start(self):
        self.port = get_free_port()
        print(f"🚀 Starting Vue on port {self.port}...")
        self.log_file = open(self.path / "vue_run.log", "w")

        if os.name == "nt":
            cmd = f'"{npm_cmd}" start -- --port {self.port} --host 127.0.0.1'
            shell_mode = True
        else:
            cmd = [
                npm_cmd,
                "start",
                "--",
                "--port",
                str(self.port),
                "--host",
                "127.0.0.1",
            ]
            shell_mode = False

        self.process = subprocess.Popen(
            cmd,
            cwd=str(self.path),
            stdout=self.log_file,
            stderr=subprocess.STDOUT,
            preexec_fn=None if os.name == "nt" else os.setsid,
            shell=shell_mode,
        )

        self._wait_for_port()
        self.base_url = f"http://localhost:{self.port}"
        return self.base_url

    def get_routes(self):
        pages_dir = self.path / "src" / "pages"
        routes = [{"name": "index", "route": "/"}]
        if pages_dir.exists():
            for file in pages_dir.glob("*.vue"):
                stem = file.stem.lower()
                if stem not in ["index", "home", "main", "app"]:
                    routes.append(
                        {
                            "name": stem,
                            "route": f"/{stem}.html",
                            "try_clean": True,
                        }
                    )
        return routes

    def get_root_selector(self):
        return "#app"

    def _wait_for_port(self):
        AngularHandler._wait_for_port(self)


# --- 工厂与主逻辑 ---


def detect_project_type(path):
    path = Path(path)
    if (path / "angular.json").exists():
        return AngularHandler(path), "Angular"
    elif (path / "vite.config.js").exists() or (
        path / "src" / "App.vue"
    ).exists():
        return VueHandler(path), "Vue"
    elif (path / "src" / "index.js").exists() or (
        path / "src" / "App.js"
    ).exists():
        return ReactHandler(path), "React"
    else:
        # 默认为静态 HTML
        return HtmlHandler(path), "HTML"


def capture_screenshots(handler, project_type):
    save_dir = handler.path
    routes = handler.get_routes()
    root_selector = handler.get_root_selector()
    screenshot_paths = []
    # print(f"📸 Scanning {len(routes)} pages for {project_type} project...")

    with sync_playwright() as p:
        browser = p.chromium.launch()
        # 使用较大的视口，但在截图时 full_page 会自动扩展
        context = browser.new_context(
            viewport={"width": VIEWPORT_WIDTH, "height": VIEWPORT_HEIGHT}
        )
        page = context.new_page()

        for info in routes:
            # 构造 URL
            if project_type == "HTML":
                url = f"{handler.base_url}/{info['route'].lstrip('/')}"
            else:
                url = f"{handler.base_url}{info['route']}"

            # 与 save_screenshots 保持一致：jpeg + quality=70
            final_filename = f"screenshot_{info['name']}.jpg"
            final_path = save_dir / final_filename

            # print(f"   --> {info['name']}: {url}")

            try:
                # 1) 分级回退加载策略: load -> domcontentloaded -> commit
                wait_time_after_load = 500

                for wait_state in ["load", "domcontentloaded", "commit"]:
                    try:
                        response = page.goto(
                            url, wait_until=wait_state, timeout=60000
                        )

                        # React/Vue 404 回退机制（尝试去掉 .html）
                        if project_type in ["React", "Vue"] and info.get(
                            "try_clean"
                        ):
                            if response and response.status == 404:
                                alt_url = url.replace(".html", "")
                                print(f"       (404, retrying: {alt_url})")
                                page.goto(
                                    alt_url,
                                    wait_until=wait_state,
                                    timeout=60000,
                                )

                        if wait_state == "commit":
                            wait_time_after_load = 2000
                        elif wait_state == "domcontentloaded":
                            wait_time_after_load = 500

                        break
                    except Exception as e:
                        if wait_state != "commit":
                            print(
                                f"       Load failed with '{wait_state}': {e}. Retrying with next strategy..."
                            )
                        else:
                            raise

                page.wait_for_timeout(wait_time_after_load)

                # 2) 模拟滚动（触发懒加载）
                page.evaluate(
                    """
                    async () => {
                        const delay = ms => new Promise(resolve => setTimeout(resolve, ms));
                        const step = 400;
                        const wait = 100;
                        const docHeight = Math.max(document.body.scrollHeight, document.documentElement.scrollHeight);
                        let currentPos = 0;
                        while (currentPos < docHeight) {
                            window.scrollTo(0, currentPos);
                            await delay(wait);
                            currentPos += step;
                        }
                        window.scrollTo(0, docHeight);
                        await delay(500);
                        window.scrollTo(0, 0); // 滚回顶部
                        await delay(500);
                    }
                """
                )

                # 3) CSS 修复（防止容器高度塌陷）
                page.evaluate(
                    f"""() => {{
                    const root = document.querySelector('{root_selector}');
                    const tags = [document.body, document.documentElement];
                    if (root) tags.push(root);

                    tags.forEach(el => {{
                        if (el) {{
                            el.style.height = 'auto';
                            el.style.minHeight = '100vh';
                            el.style.overflow = 'visible';
                            if (el.tagName === 'APP-ROOT') el.style.display = 'block';
                        }}
                    }});
                }}"""
                )

                # 4) 截图（与 save_screenshots 一致）
                page.screenshot(
                    path=str(final_path),
                    full_page=True,
                    animations="disabled",
                    timeout=60000,
                    type="jpeg",
                    quality=70,
                )
                screenshot_paths.append(final_filename)
                # print(f"✅ Saved to {final_filename}")

            except Exception as e:
                print(f"   ⚠️ {save_dir} Failed to capture {info['name']}: {e}")

        browser.close()
    return screenshot_paths


def save_screenshots(dictionary):
    if not os.path.exists(dictionary):
        print(f"❌ Path not found: {dictionary}")
        return []

    handler, p_type = detect_project_type(dictionary)
    print(f"🔍 Detected Project Type: {p_type}")

    try:
        handler.setup()
        base_url = handler.start()
        if not base_url:
            print("❌ Failed to start server or resolve base URL.")
            return []

        screenshot_paths = capture_screenshots(handler, p_type)
        return screenshot_paths

    except Exception as e:
        print(f"❌ {handler.path} Unexpected error: {e}")
        import traceback

        traceback.print_exc()
    finally:
        handler.stop()


if __name__ == "__main__":
    dictionary = "/root/bayes-tmp/data/webcoding_framework_dataset_test/html/mp/generation/985175_www.fbimmigration.com/dst"
    save_screenshots(dictionary)
