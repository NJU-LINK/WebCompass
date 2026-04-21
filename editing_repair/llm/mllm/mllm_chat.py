from typing import Union, List, Dict, Any, Optional, Tuple
import os
import shutil
import json
import re
from pathlib import Path
from datetime import datetime
from utils.config import CODE_EXTENSIONS, IMAGE_EXTENSIONS
from utils.utils import (
    encode_image,
    save_screenshots,
    apply_search_replace,
    get_image_mime_type,
    chat_with_retry,
)
from openai import OpenAI
from utils import copy_resources

class MLLMChat:
    DEFAULT_MAX_TOKENS = 8192 * 2
    DEFAULT_TEMPERATURE = 0
    # DEFAULT_SEED = 42

    def __init__(
        self,
        model_name: str,
        client: Optional[OpenAI] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        **kwargs,
    ) -> None:
        # 如果提供了client就使用client,否则创建新的client
        if client:
            self.client = client
        else:
            # 优先使用传入的参数,其次使用环境变量
            api_key = api_key or os.getenv("OPENAI_API_KEY")
            client_kwargs = {"api_key": api_key}
            if base_url:
                client_kwargs["base_url"] = base_url
            self.client = OpenAI(**client_kwargs)
        self.model_name = model_name
        self.max_tokens = kwargs.get("max_tokens", self.DEFAULT_MAX_TOKENS)
        self.temperature = kwargs.get("temperature", self.DEFAULT_TEMPERATURE)
        # self.seed = kwargs.get("seed", self.DEFAULT_SEED)
        self.max_retry = kwargs.get("max_retry", 3)

        # 添加 prompt 实例变量
        self.generation_prompt = kwargs.get("generation_prompt", "")
        self.edit_prompt = kwargs.get("edit_prompt", "")
        self.repair_prompt = kwargs.get("repair_prompt", "")

        # 添加时间戳,用于标识同一次测试
        # 若外部传入 timestamp，则优先使用
        self.timestamp = kwargs.get("timestamp") or datetime.now().strftime("%Y%m%d_%H%M%S")

        print(
            f"Model: {self.model_name}, Temperature: {self.temperature}, Max Tokens: {self.max_tokens}, Max Retry: {self.max_retry}"
        )
        print(f"Test Session: {self.timestamp}")

    def chat(self, messages: List[dict]) -> str:
        """
        发送消息到OpenAI并获取响应
        Args:
            messages: OpenAI格式的消息列表
        Returns:
            LLM的响应内容字符串
        """
        response = chat_with_retry(
            client=self.client,
            messages=messages,
            model=self.model_name,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            max_retries=self.max_retry,
        )

        return response

    def load_data(self, data_folder: Path) -> Dict[str, Any]:
        """
        加载 edit/repair 任务的 info.json 数据

        Args:
            data_folder: edit/repair 任务的数据文件夹路径

        Returns:
            Tuple[str, List[Dict[str, str]], List[str], List[str]]: (description, src_code, src_screenshots, dst_screenshots)
            - description: 任务描述
            - src_code: 源代码文件列表,格式为 [{"path": "...", "code": "..."}]
            - src_screenshots: 源截图的完整路径列表
            - dst_screenshots: 目标截图的完整路径列表
            - resources_info: 资源文件信息列表,包含路径、类型和描述
        """
        info_path = data_folder / "info.json"

        with open(info_path, "r", encoding="utf-8") as f:
            info = json.load(f)

        # 3. 获取 src_screenshot 路径
        src_screenshots_data = info.get("src_screenshot", [])
        info["src_screenshot"] = [
            str(data_folder / "src" / screenshot)
            for screenshot in src_screenshots_data
        ]

        # 4. 获取 dst_screenshot 路径
        dst_screenshots_data = info.get("dst_screenshot", [])
        info["dst_screenshot"] = [
            str(data_folder / "dst" / screenshot)
            for screenshot in dst_screenshots_data
        ]

        return info

    def create_workspace(
        self,
        data_folder: Path,
        workspace_path: Path,
        resources_info: List[Dict[str, Any]],
    ) -> None:
        """
        创建工作空间,根据 resources_info 从 src 中复制资源文件

        Args:
            data_folder: generation任务的数据文件夹路径
            workspace_path: 工作空间路径
            resources_info: 资源文件信息列表
        """
        origin_path = data_folder / "src"
        copy_resources(origin_path, workspace_path, resources_info)
        

    def construct_messages_for_generation(
        self,
        description: str,
        screenshot_paths: List[str],
        resources_info: List[Dict[str, Any]],
        instruction_prompt: str,
        mode: str = "text",
        workspace_path: Optional[Path] = None,
    ) -> List[Dict[str, Any]]:
        """
        根据不同模态组装 generation 任务的 messages

        Args:
            description: 任务描述
            screenshot_paths: 目标截图的完整路径列表
            resources_info: 资源文件信息列表
            instruction_prompt: 任务提示词
            mode: 模态类型,"text" 或 "image"
            workspace_path: 工作空间路径(image模式需要)

        Returns:
            List[Dict[str, Any]]: OpenAI 格式的 messages 列表
        """
        messages = []

        # 构建 user message 的 content
        user_content = []

        # 1. 首先添加任务指令
        task_instruction = (
            instruction_prompt
            + "\n"
            + f"## Website Description\n{description}\n"
        )

        # 2. 添加目标截图说明(仅在 image 模式下)
        if mode == "image" and screenshot_paths:
            task_instruction += "\n## Target Screenshots\n"
            task_instruction += (
                "The following screenshots show the expected result:\n\n"
            )

        # 添加任务指令文本
        user_content.append({"type": "text", "text": task_instruction})

        # 3. 添加目标截图(仅在 image 模式下)
        if mode == "image" and screenshot_paths:
            for screenshot_path in screenshot_paths:
                screenshot_file = Path(screenshot_path)

                if screenshot_file.exists():
                    try:
                        img_base64 = encode_image(str(screenshot_file))

                        # 使用工具函数获取MIME类型
                        mime_type = get_image_mime_type(str(screenshot_file))

                        # 添加截图说明文本
                        user_content.append(
                            {
                                "type": "text",
                                "text": f"\n[Target Screenshot: {screenshot_file.name}]",
                            }
                        )

                        # 添加截图本体
                        user_content.append(
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{mime_type};base64,{img_base64}"
                                },
                            }
                        )

                    except Exception as e:
                        print(
                            f"Warning: Failed to encode screenshot {screenshot_path}: {e}"
                        )

        # 4. 添加资源信息
        if resources_info:
            resource_instruction = "\n## Available Resources\n"
            resource_instruction += (
                "The following resources are available in your workspace:\n\n"
            )

            for resource in resources_info:
                resource_type = resource.get("type", "")
                resource_path = resource.get("path", "")

                # text模式: 添加路径和描述(如果是图片)
                resource_instruction += f"- `{resource_path}`"
                if resource_type == "image" and resource.get("description"):
                    resource_instruction += (
                        f"\n  - Description: {resource['description']}"
                    )
                resource_instruction += "\n"

            user_content.append({"type": "text", "text": resource_instruction})

        # 构建 user message
        messages.append({"role": "user", "content": user_content})

        return messages

    def construct_messages_for_edit(self,
                                description: List[Dict[str, str]],
                                src_code: List[Dict[str, str]],
                                src_screenshots: List[str],
                                instruction_prompt: str,
                                mode: str = "text") -> List[Dict[str, Any]]:
        """
        根据不同模态组装 edit 任务的 messages
        """
        messages = []
        user_content = []

        # edit 任务显示完整描述
        description_list = [
            f"Task{idx}- {task_item['task_type']}: {task_item['description']}"
            for idx, task_item in enumerate(description)
        ]
        task_description = "\n".join(description_list)

        # 1. 添加任务指令
        task_instruction = (
            instruction_prompt
            + "\n"
            + f"## Task Description\n{task_description}"
        )
        # 2. 添加源代码 (使用XML格式)
        task_instruction += "\n## Source Code\n"
        task_instruction += (
            "The following is the current code that needs to be modified:\n\n"
        )
        task_instruction += "<code_context>\n"

        for file_info in src_code:
            file_path = file_info.get("path", "")
            file_code = file_info.get("code", "")
            task_instruction += (
                f'<file path="{file_path}">\n{file_code}\n</file>\n'
            )

        task_instruction += "</code_context>\n"

        user_content.append({"type": "text", "text": task_instruction})

        # 3. 添加源截图(仅在 image 模式下)
        if mode == "image" and src_screenshots:
            user_content.append(
                {
                    "type": "text",
                    "text": "\n## Current State Screenshots\nThe following screenshots show the current state:\n\n",
                }
            )

            for screenshot_path in src_screenshots:
                screenshot_file = Path(screenshot_path)

                if screenshot_file.exists():
                    try:
                        img_base64 = encode_image(str(screenshot_file))
                        mime_type = get_image_mime_type(str(screenshot_file))

                        user_content.append(
                            {
                                "type": "text",
                                "text": f"\n[Current Screenshot: {screenshot_file.name}]",
                            }
                        )

                        user_content.append(
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{mime_type};base64,{img_base64}"
                                },
                            }
                        )

                    except Exception as e:
                        print(
                            f"Warning: Failed to encode screenshot {screenshot_path}: {e}"
                        )

        messages.append({"role": "user", "content": user_content})

        return messages

    def construct_messages_for_repair(
        self,
        description: List[Dict[str, str]],
        src_code: List[Dict[str, str]],
        src_screenshots: List[str],
        dst_screenshots: List[str],
        instruction_prompt: str,
        mode: str = "text",
    ) -> List[Dict[str, Any]]:
        """
        根据不同模态组装 repair 任务的 messages
        """
        messages = []
        user_content = []

        # repair 任务只显示 defect 类型
        # description_list = [
        #     f"Task{idx}- Fix issue:{task_item['task_type']}"
        #     for idx, task_item in enumerate(description)
        # ]
        # task_instruction = "\n".join(description_list)

        # 1. 添加任务指令
        # task_instruction = (
        #     instruction_prompt
        #     + "\n"
        #     + f"## Task Description\n{task_description}"
        # )
        task_instruction = instruction_prompt + "\n" + f"You have only {len(description)} issues to fix, and you can not fix more than {len(description)} issues."
        # 2. 添加源代码 (使用XML格式)
        task_instruction += "\n## Source Code\n"
        task_instruction += (
            "The following is the current code that needs to be modified:\n\n"
        )
        task_instruction += "<code_context>\n"

        for file_info in src_code:
            file_path = file_info.get("path", "")
            file_code = file_info.get("code", "")
            task_instruction += (
                f'<file path="{file_path}">\n{file_code}\n</file>\n'
            )

        task_instruction += "</code_context>\n"

        user_content.append({"type": "text", "text": task_instruction})

        # 3. 添加源截图(仅在 image 模式下)
        if mode == "image" and src_screenshots:
            user_content.append(
                {
                    "type": "text",
                    "text": "\n## Current State Screenshots\nThe following screenshots show the current state:\n\n",
                }
            )

            for screenshot_path in src_screenshots:
                screenshot_file = Path(screenshot_path)

                if screenshot_file.exists():
                    try:
                        img_base64 = encode_image(str(screenshot_file))
                        mime_type = get_image_mime_type(str(screenshot_file))

                        user_content.append(
                            {
                                "type": "text",
                                "text": f"\n[Current Screenshot: {screenshot_file.name}]",
                            }
                        )

                        user_content.append(
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{mime_type};base64,{img_base64}"
                                },
                            }
                        )

                    except Exception as e:
                        print(
                            f"Warning: Failed to encode screenshot {screenshot_path}: {e}"
                        )

        # 4. 添加目标截图(仅在 image 模式下)
        if mode == "image" and dst_screenshots:
            user_content.append(
                {
                    "type": "text",
                    "text": "\n## Target State Screenshots\nThe following screenshots show the expected result:\n\n",
                }
            )

            for screenshot_path in dst_screenshots:
                screenshot_file = Path(screenshot_path)

                if screenshot_file.exists():
                    try:
                        img_base64 = encode_image(str(screenshot_file))
                        mime_type = get_image_mime_type(str(screenshot_file))

                        user_content.append(
                            {
                                "type": "text",
                                "text": f"\n[Target Screenshot: {screenshot_file.name}]",
                            }
                        )

                        user_content.append(
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{mime_type};base64,{img_base64}"
                                },
                            }
                        )

                    except Exception as e:
                        print(
                            f"Warning: Failed to encode screenshot {screenshot_path}: {e}"
                        )

        messages.append({"role": "user", "content": user_content})

        return messages

    def parse_and_save_code(
        self, response: str, workspace_path: Path
    ) -> List[Dict[str, str]]:
        """
        解析 LLM 生成的代码(使用 <file path="..."></file> 格式)并保存到 workspace

        Args:
            response: LLM 生成的响应内容
            workspace_path: 工作空间路径

        Returns:
            List[Dict[str, str]]: 保存的代码文件列表,格式为 [{"path": "...", "code": "..."}]
        """
        saved_files = []

        # 匹配 <file path="...">...</file> 格式
        pattern = r'<file\s+path=["\']([^"\']+)["\']>\s*(.*?)\s*</file>'
        matches = re.findall(pattern, response, re.DOTALL)

        if matches:
            for file_path_str, code in matches:
                # 清理路径和代码
                file_path_str = file_path_str.strip()
                code = code.strip()

                # 移除代码块标记(如果存在)
                code = re.sub(r"^```\w*\n?", "", code)
                code = re.sub(r"\n?```$", "", code)
                code = code.strip()

                # 构建完整路径
                file_path = workspace_path / file_path_str

                # 创建目录
                file_path.parent.mkdir(parents=True, exist_ok=True)

                # 保存文件
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(code)

                saved_files.append({"path": file_path_str, "code": code})
                print(f"Saved: {file_path_str}")

        return saved_files

    def run_generation_task(
        self,
        data_folder: Union[str, Path],
        output_dir: str = "results/",
        mode: str = "text",
    ):
        """
        运行完整的 generation 任务流程

        Args:
            data_folder: generation 任务的数据文件夹路径
            mode: 模态类型,"text" 或 "image"

        """
        data_folder = Path(data_folder)
        web_name = data_folder.name
        task_type = data_folder.parent.name

        # 修改路径格式: output_dir/model_mode_timestamp/task_type/web_name/ans
        session_name = f"{self.model_name}_{mode}_{self.timestamp}"
        workspace_path = (
            Path(output_dir) / session_name / task_type / web_name / "ans"
        )
        workspace_path = workspace_path.resolve()

        instruction_prompt = self.generation_prompt
        # 1. 加载 generation 任务数据
        info = self.load_data(data_folder)
        description = info["description"]
        screenshot_paths = info["dst_screenshot"]
        resources_info = info["resources"]
        print(f"Target screenshots: {len(screenshot_paths)} items")
        print(f"Resources: {len(resources_info)} items")

        # 2. 创建 workspace (根据 resources_info 复制资源)
        self.create_workspace(data_folder, workspace_path, resources_info)
        print(f"Workspace created at: {workspace_path}")

        # 3. 组装 messages
        messages = self.construct_messages_for_generation(
            description=description,
            screenshot_paths=screenshot_paths,
            resources_info=resources_info,
            instruction_prompt=instruction_prompt,
            mode=mode,
            workspace_path=workspace_path,
        )
        print(f"Messages constructed with mode: {mode}")

        # 4. 调用 LLM 生成代码
        response = self.chat(messages)
        print("LLM response received")

        # 5. 解析并保存代码到 workspace
        saved_files = self.parse_and_save_code(response, workspace_path)
        print(f"Saved {len(saved_files)} files")

        # 6. 截图
        screenshot_files = save_screenshots(str(workspace_path))
        print(f"Screenshots: {screenshot_files}")

        llm_log = {
            "task_type": info["task_type"],
            "description": description,
            "ans_screenshot": screenshot_files,
            "workspace_path": str(workspace_path),
            "llm_input_messages": messages,
            "llm_response": response,
            "label_code": info["dst_code"],
            "generated_code": saved_files,
        }

        with open(
            workspace_path.parent / "info.json", "w", encoding="utf-8"
        ) as f:
            json.dump(llm_log, f, ensure_ascii=False, indent=4)

    def parse_and_apply_search_replace(
        self,
        response: str,
        src_code: List[Dict[str, str]],
        workspace_path: Path,
    ) -> Tuple[List[Dict[str, str]], List[str]]:
        """
        解析 LLM 生成的 search_replace 块并应用到源代码

        Args:
            response: LLM 生成的响应内容
            src_code: 源代码文件列表,格式为 [{"path": "...", "code": "..."}]
            workspace_path: 工作空间路径

        Returns:
            Tuple[List[Dict[str, str]], List[str]]:
                - 修改后的代码文件列表,格式为 [{"path": "...", "code": "..."}]
                - 错误信息列表
        """
        # 解析 search_replace 块
        modified_files = []
        if not response:
            print("Warning: LLM response is empty or null")
            for file_info in src_code:
                file_path = workspace_path / file_info["path"]
                file_path.parent.mkdir(parents=True, exist_ok=True)
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(file_info["code"])
            return modified_files, ["LLM response is empty or null"]
        pattern = r'<search_replace\s+path=["\']([^"\']+)["\']>\s*<search>(.*?)</search>\s*<replace>(.*?)</replace>\s*</search_replace>'
        matches = re.findall(pattern, response, re.DOTALL)

        for file_path, search_text, replace_text in matches:
            search_stripped = search_text.strip()
            replace_stripped = replace_text.strip()

            modified_files.append(
                {
                    "path": file_path.strip(),
                    "search": search_stripped,
                    "replace": replace_stripped,
                }
            )

        if not modified_files:
            print("Warning: No valid search_replace blocks found in response")
            # 仍然保存原始代码到 workspace
            for file_info in src_code:
                file_path = workspace_path / file_info["path"]
                file_path.parent.mkdir(parents=True, exist_ok=True)
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(file_info["code"])
            return modified_files, ["No valid search_replace blocks found"]

        # 使用软匹配模式应用 search_replace
        ans_code, errors = apply_search_replace(
            src_code, modified_files, strict_mode=False  # 使用软匹配模式
        )

        if errors:
            print(
                f"⚠️  部分代码块替换失败: {len(errors)}/{len(modified_files)} 个块失败"
            )
            print(
                f"✓ 成功应用: {len(modified_files) - len(errors)}/{len(modified_files)} 个代码块"
            )
        else:
            print(
                f"✓ 所有代码块替换成功: {len(modified_files)}/{len(modified_files)}"
            )

        # 保存修改后的代码到 workspace
        for file_info in ans_code:
            file_path = workspace_path / file_info["path"]
            file_path.parent.mkdir(parents=True, exist_ok=True)

            with open(file_path, "w", encoding="utf-8") as f:
                f.write(file_info["code"])

            print(f"Saved: {file_info['path']}")

        return modified_files, errors

    def run_edit_repair_task(
        self,
        data_folder: Union[str, Path],
        output_dir: str = "results/",
        mode: str = "text",
        task: str = "edit",
    ):
        """
        运行完整的 edit/repair 任务流程

        Args:
            data_folder: edit/repair 任务的数据文件夹路径
            output_dir: 输出目录
            mode: 模态类型,"text" 或 "image"
            task: 任务类型,"edit" 或 "repair"

        Returns:
            Dict[str, Any]: 包含任务执行结果的字典
        """
        data_folder = Path(data_folder)
        task_type = data_folder.parent.name
        web_name = data_folder.name

        # 修改路径格式: output_dir/model_mode_timestamp/task_type/web_name/ans
        session_name = f"{self.model_name}_{mode}_{self.timestamp}"
        workspace_path = (
            Path(output_dir) / session_name / task_type / web_name / "ans"
        )
        workspace_path = workspace_path.resolve()

        # 根据任务类型选择 prompt
        if task == "repair":
            instruction_prompt = self.repair_prompt
        else:
            instruction_prompt = self.edit_prompt

        # 1. 加载 edit/repair 任务数据
        info = self.load_data(data_folder)
        description = info["description"]
        src_code = info["src_code"]
        src_screenshots = info["src_screenshot"]
        dst_screenshots = info["dst_screenshot"]
        resources_info = info["resources"]
        print(f"Source code files: {len(src_code)} items")
        print(f"Source screenshots: {len(src_screenshots)} items")
        print(f"Target screenshots: {len(dst_screenshots)} items")

        # 2. 创建 workspace 并复制源代码
        self.create_workspace(data_folder, workspace_path, resources_info)
        print(f"Workspace created at: {workspace_path}")

        # 3. 组装 messages
        if task == "repair":
            messages = self.construct_messages_for_repair(
                description=description,
                src_code=src_code,
                src_screenshots=src_screenshots,
                dst_screenshots=dst_screenshots,
                instruction_prompt=instruction_prompt,
                mode=mode
            )
        else:
            messages = self.construct_messages_for_edit(
                description=description,
                src_code=src_code,
                src_screenshots=src_screenshots,
                instruction_prompt=instruction_prompt,
                mode=mode
            )
        print(f"Messages constructed with mode: {mode}, task: {task}")

        # 4. 调用 LLM 生成修改指令
        response = self.chat(messages)
        print("LLM response received")

        # 5. 解析并应用 search_replace 到 workspace (使用软匹配)
        modified_files, apply_errors = self.parse_and_apply_search_replace(
            response, src_code, workspace_path
        )
        print(f"Modified {len(modified_files)} files")

        # 6. 截图
        screenshot_files = save_screenshots(str(workspace_path))
        print(f"Screenshots: {screenshot_files}")

        llm_log = {
            "task_type": info["task_type"],
            "description": description,
            "ans_screenshot": screenshot_files,
            "workspace_path": str(workspace_path),
            "llm_input_messages": messages,
            "llm_response": response,
            "label_modified_files": info["label_modified_files"],
            "modified_files": modified_files,
            "apply_errors": apply_errors,
        }

        with open(
            workspace_path.parent / "info.json", "w", encoding="utf-8"
        ) as f:
            json.dump(llm_log, f, ensure_ascii=False, indent=4)


if __name__ == "__main__":
    import os
    from llm.mllm.prompt import *

    api_key = os.environ.get("OPENAI_API_KEY")
    base_url = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable is required.")
    # model = "gpt-5-codex"
    model = "gemini-3-pro-preview"
    # model = "deepseek-v3"
    client = MLLMChat(
        model_name=model,
        api_key=api_key,
        base_url=base_url,
        max_tokens=32 * 1024,
        max_retry=6,
        generation_prompt=Generation_Instruction_Prompt,
        edit_prompt=Edit_Instruction_Prompt,
        repair_prompt=Repair_Instruction_Prompt,
    )
    # 测试单个generation文件夹
    # data_folder = "/Users/pedestrian/Desktop/web_case/data/data_demo_renderbench_1_5_9/generation/2931255_www.testing.com"
    # client.run_generation_task(
    #     data_folder=data_folder,
    #     mode="text",
    #     output_dir="/Users/pedestrian/Desktop/web_coding_output/results/"
    # )

    # 测试edit 任务
    data_folder = "/Users/pedestrian/Desktop/web_coding_output/data/data_demo_renderbench_3_6_9/edit_test_multi/2930611_www.fieldsquared.com_L9_2"
    client.run_edit_repair_task(
        data_folder=data_folder,
        output_dir="/Users/pedestrian/Desktop/web_coding_output/results_test/",
        mode="text",
        task="edit",
    )
    # 测试repair 任务
    # data_folder = "/Users/pedestrian/Desktop/web_coding_output/data/data_demo_renderbench_1_5_9/repair/948729_www.crystalriverspas.com_L9_2"
    # client.run_edit_repair_task(
    #     data_folder=data_folder,
    #     output_dir="/Users/pedestrian/Desktop/web_coding_output/results_test/",
    #     mode="image",
    #     task="repair",
    # )
