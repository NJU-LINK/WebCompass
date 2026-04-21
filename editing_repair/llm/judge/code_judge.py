from typing import Union, List, Dict, Any, Optional, Tuple
import os
import json
import re
import time

from pathlib import Path
from utils.config import CODE_EXTENSIONS, IMAGE_EXTENSIONS
from utils.utils import encode_image, get_image_mime_type
from openai import OpenAI

# Task-specific judge dimensions (paper §F.5).
JUDGE_DIMS: Dict[str, Tuple[str, str, str]] = {
    "edit":   ("instruction_targeting", "feature_integrity",    "style_conformance"),
    "repair": ("root_cause_targeting",  "interaction_integrity", "reference_fidelity"),
}


class CodeJudge:
    DEFAULT_MAX_TOKENS = 8192 * 2
    DEFAULT_TEMPERATURE = 0
    # DEFAULT_SEED = 42
    
    def __init__(self, model_name: str, client: Optional[OpenAI] = None, api_key: Optional[str] = None, base_url: Optional[str] = None, **kwargs) -> None:
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
        
        # 将prompt作为实例变量
        self.edit_judge_prompt = kwargs.get("edit_judge_prompt", "")
        self.repair_judge_prompt = kwargs.get("repair_judge_prompt", "")
        
        print(f"Model: {self.model_name}, Temperature: {self.temperature}, Max Tokens: {self.max_tokens}, Max Retry: {self.max_retry}")
    
    def load_label_data(self, data_folder: Path) -> Dict[str, Any]:
        """
        加载 edit/repair 任务的 info.json 数据
        
        Args:
            data_folder: edit/repair 任务的数据文件夹路径
        
        Returns:
            Dict[str, Any]: 包含任务信息的字典
        """
        info_path = data_folder / "info.json"
        
        with open(info_path, 'r', encoding='utf-8') as f:
            info = json.load(f)
        
        # 获取 src_screenshot 路径
        src_screenshots_data = info.get("src_screenshot", [])
        info["src_screenshot"] = [str(data_folder / "src" / screenshot) for screenshot in src_screenshots_data]
        
        # 获取 dst_screenshot 路径
        dst_screenshots_data = info.get("dst_screenshot", [])
        info["dst_screenshot"] = [str(data_folder / "dst" / screenshot) for screenshot in dst_screenshots_data]
        
        return info
    
    def load_generated_data(self, generated_folder: Path) -> Dict[str, Any]:
        """
        加载生成的答案数据
        
        Args:
            generated_folder: 生成的答案文件夹路径
        
        Returns:
            Dict[str, Any]: 包含生成答案信息的字典
        """
        info_path = generated_folder / "info.json"
        
        with open(info_path, 'r', encoding='utf-8') as f:
            info = json.load(f)
        
        ans_screenshot_data = info.get("ans_screenshot", [])
        info["ans_screenshot"] = [str(generated_folder / "ans" / screenshot) for screenshot in ans_screenshot_data]
        return info
    
    def construct_edit_judge_messages(self,
                                      description: List[Dict[str, str]],
                                      generated_modifications: List[Dict[str, str]],
                                      src_screenshots: List[str],
                                      generated_screenshots: List[str]) -> List[Dict[str, Any]]:
        """
        构建 Edit 任务的评分 messages
        
        Args:
            description: 任务描述列表
            generated_modifications: 生成的修改块列表
            src_screenshots: 源截图路径列表
            generated_screenshots: 生成的截图路径列表
        
        Returns:
            List[Dict[str, Any]]: OpenAI 格式的 messages 列表
        """
        messages = []
        
        # 添加系统提示
        messages.append({
            "role": "system",
            "content": self.edit_judge_prompt
        })
        
        user_content = []
        
        # 1. 添加任务描述
        description_list = [f"Task {idx} - {task['task_type']}: {task['description']}\n" 
                           for idx, task in enumerate(description)]
        task_description = "\n".join(description_list)
        
        user_content.append({
            "type": "text",
            "text": f"## Task Instructions\n{task_description}"
        })
        
        # 2. 添加生成的修改块
        generated_mods_text = "\n## Generated Code Modifications\n"
        if generated_modifications:
            for mod in generated_modifications:
                generated_mods_text += f'<search_replace path="{mod["path"]}">\n'
                generated_mods_text += f'<search>\n{mod["search"]}\n</search>\n'
                generated_mods_text += f'<replace>\n{mod["replace"]}\n</replace>\n'
                generated_mods_text += '</search_replace>\n\n'
        else:
            generated_mods_text += "No modifications were made.\n"
        
        user_content.append({
            "type": "text",
            "text": generated_mods_text
        })
        
        # 3. 添加源截图 (Original UI)
        if src_screenshots:
            user_content.append({
                "type": "text",
                "text": "\n## Original UI Screenshot (Before Modification)\n"
            })
            
            for screenshot_path in src_screenshots:
                screenshot_file = Path(screenshot_path)
                if screenshot_file.exists():
                    try:
                        img_base64 = encode_image(str(screenshot_file))
                        mime_type = get_image_mime_type(str(screenshot_file))
                        user_content.append({
                            "type": "text",
                            "text": f"Original Screenshot: {screenshot_file.name}"
                        })
                        user_content.append({
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{mime_type};base64,{img_base64}"
                            }
                        })
                    except Exception as e:
                        print(f"Warning: Failed to encode screenshot {screenshot_path}: {e}")
        
        # 4. 添加生成的截图 (Modified UI)
        if generated_screenshots:
            user_content.append({
                "type": "text",
                "text": "\n## Modified UI Screenshot (After Modification)\n"
            })
            
            for screenshot_path in generated_screenshots:
                screenshot_file = Path(screenshot_path)
                if screenshot_file.exists():
                    try:
                        img_base64 = encode_image(str(screenshot_file))
                        mime_type = get_image_mime_type(str(screenshot_file))
                        user_content.append(
                            {
                                "type": "text",
                                "text": f"\n[Modified Screenshot: {screenshot_file.name}]",
                            }
                        )
                            
                        user_content.append({
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{mime_type};base64,{img_base64}"
                            }
                        })
                    except Exception as e:
                        print(f"Warning: Failed to encode screenshot {screenshot_path}: {e}")
        
        messages.append({
            "role": "user",
            "content": user_content
        })
        
        return messages
    
    def construct_repair_judge_messages(self,
                                        description: List[Dict[str, str]],
                                        label_modifications: List[Dict[str, str]],
                                        generated_modifications: List[Dict[str, str]],
                                        src_screenshots: List[str],
                                        generated_screenshots: List[str],
                                        dst_screenshots: List[str]) -> List[Dict[str, Any]]:
        """
        构建 Repair 任务的评分 messages
        
        Args:
            description: 任务描述列表
            label_modifications: 标注的修改块列表 (Ground-Truth)
            generated_modifications: 生成的修改块列表
            src_screenshots: 源截图路径列表 - 显示缺陷的红框
            generated_screenshots: 生成的截图路径列表 - 修复后的结果
            dst_screenshots: 目标截图路径列表 - Ground-truth参考
        
        Returns:
            List[Dict[str, Any]]: OpenAI 格式的 messages 列表
        """
        messages = []
        
        # 添加系统提示
        messages.append({
            "role": "system",
            "content": self.repair_judge_prompt
        })
        
        user_content = []
        
        # 1. 添加缺陷描述
        description_list = [f"Defect {idx} - {task['task_type']}: {task['description']}\n" 
                           for idx, task in enumerate(description)]
        defect_description = "\n".join(description_list)
        
        user_content.append({
            "type": "text",
            "text": f"## Defect Description\n{defect_description}"
        })
        
        # 2. 添加标注的修改快和生成的修改块
        label_mods_text = "\n## Ground-Truth Code Modifications (Reference Solution)\n"
        if label_modifications:
            for mod in label_modifications:
                label_mods_text += f'<search_replace path="{mod["path"]}">\n'
                label_mods_text += f'<search>\n{mod["search"]}\n</search>\n'
                label_mods_text += f'<replace>\n{mod["replace"]}\n</replace>\n'
                label_mods_text += '</search_replace>\n\n'
        else:
            label_mods_text += "No modifications were made.\n"
        generated_mods_text = "\n## Generated Code Modifications (Repair Attempt)\n"
        if generated_modifications:
            for mod in generated_modifications:
                generated_mods_text += f'<search_replace path="{mod["path"]}">\n'
                generated_mods_text += f'<search>\n{mod["search"]}\n</search>\n'
                generated_mods_text += f'<replace>\n{mod["replace"]}\n</replace>\n'
                generated_mods_text += '</search_replace>\n\n'
        else:
            generated_mods_text += "No modifications were made.\n"
        
        user_content.append({
            "type": "text",
            "text": label_mods_text
        })
        user_content.append({
            "type": "text",
            "text": generated_mods_text
        })
        # 
        # 3. 添加源截图 (Before-Fix with red boxes)
        if src_screenshots:
            user_content.append({
                "type": "text",
                "text": "\n## Before-Fix UI Screenshot (Defective State with Red Boxes)\n"
            })
            
            for screenshot_path in src_screenshots:
                screenshot_file = Path(screenshot_path)
                if screenshot_file.exists():
                    try:
                        img_base64 = encode_image(str(screenshot_file))
                        mime_type = get_image_mime_type(str(screenshot_file))
                        
                        user_content.append({
                            "type": "text",
                            "text": f"Original Screenshot: {screenshot_file.name}"
                        })
                        user_content.append({
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{mime_type};base64,{img_base64}"
                            }
                        })
                    except Exception as e:
                        print(f"Warning: Failed to encode screenshot {screenshot_path}: {e}")
        
        # 4. 添加生成的截图 (After-Fix result)
        if generated_screenshots:
            user_content.append({
                "type": "text",
                "text": "\n## After-Fix UI Screenshot (Actual Repair Result)\n"
            })
            
            for screenshot_path in generated_screenshots:
                screenshot_file = Path(screenshot_path)
                if screenshot_file.exists():
                    try:
                        img_base64 = encode_image(str(screenshot_file))
                        mime_type = get_image_mime_type(str(screenshot_file))
                        
                        user_content.append({
                            "type": "text",
                            "text": f"After-Fix Screenshot: {screenshot_file.name}"
                        })
                        user_content.append({
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{mime_type};base64,{img_base64}"
                            }
                        })
                    except Exception as e:
                        print(f"Warning: Failed to encode screenshot {screenshot_path}: {e}")
        
        # 5. 添加目标截图 (Ground-Truth reference)
        
        if dst_screenshots:
            user_content.append({
                "type": "text",
                "text": "\n## Ground-Truth Fixed UI Screenshot (Reference Solution)\n"
            })
            
            for screenshot_path in dst_screenshots:
                screenshot_file = Path(screenshot_path)
                if screenshot_file.exists():
                    try:
                        img_base64 = encode_image(str(screenshot_file))
                        mime_type = get_image_mime_type(str(screenshot_file))
                        
                        user_content.append({
                            "type": "text",
                            "text": f"Ground-Truth Screenshot: {screenshot_file.name}"
                        })
                        
                        user_content.append({
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{mime_type};base64,{img_base64}"
                            }
                        })
                    except Exception as e:
                        print(f"Warning: Failed to encode screenshot {screenshot_path}: {e}")
        
        messages.append({
            "role": "user",
            "content": user_content
        })
        
        return messages
    
    def parse_judge_response(self, response: str) -> Dict[str, Any]:
        """
        解析评分响应,提取 JSON 结果
        
        Args:
            response: LLM 的评分响应
        
        Returns:
            Dict[str, Any]: 解析后的评分结果
        """
        # 尝试直接解析 JSON
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            pass
        
        # 尝试提取 JSON 代码块
        json_pattern = r'```json\s*(.*?)\s*```'
        matches = re.findall(json_pattern, response, re.DOTALL)
        
        if matches:
            try:
                return json.loads(matches[0])
            except json.JSONDecodeError:
                pass
        
        # 尝试提取任何 JSON 对象
        json_obj_pattern = r'\{.*\}'
        matches = re.findall(json_obj_pattern, response, re.DOTALL)
        
        if matches:
            try:
                return json.loads(matches[0])
            except json.JSONDecodeError:
                raise ValueError("Failed to parse JSON from judge response")
        
        raise ValueError("No JSON content found in judge response")
        
    def ignore_error_blocks(self,
                            generated_modifications: List[Dict[str, str]],
                            apply_errors: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """
        忽略那些应用时出错的修改块
        
        Args:
            generated_modifications: 生成的修改块列表
            apply_errors: 应用时出错的修改块列表,每个错误包含 {"path": str, "block_index": int, "error": str}
        
        Returns:
            过滤后的修改块列表
        """
        if not apply_errors:
            return generated_modifications
        
        # 创建错误块的索引集合,用于快速查找
        # 格式: {(path, block_index_in_that_path)}
        error_blocks = set()
        
        # 按路径分组计算每个文件中的块索引
        blocks_by_path = {}
        for idx, block in enumerate(generated_modifications):
            path = block["path"]
            if path not in blocks_by_path:
                blocks_by_path[path] = []
            blocks_by_path[path].append(idx)
        
        # 将错误信息转换为全局索引
        for error in apply_errors:
            if isinstance(error, dict) and "path" in error and "block_index" in error:
                path = error["path"]
                block_index_in_path = error["block_index"]
                
                # 找到该路径下第 block_index_in_path 个块在全局列表中的索引
                if path in blocks_by_path and block_index_in_path < len(blocks_by_path[path]):
                    global_index = blocks_by_path[path][block_index_in_path]
                    error_blocks.add(global_index)
        
        # 过滤掉错误的块
        filtered_modifications = [
            block for idx, block in enumerate(generated_modifications)
            if idx not in error_blocks
        ]
        
        if error_blocks:
            print(f"⚠️  已忽略 {len(error_blocks)} 个应用失败的修改块")
            print(f"✓  保留 {len(filtered_modifications)}/{len(generated_modifications)} 个有效修改块")
        
        return filtered_modifications
       
    def _validate_judge_task_types(
        self,
        description: List[Dict[str, str]],
        judge_result: Dict[str, Any],
        task: str,
    ) -> None:
        """
        校验 judge_result 中 task_scores 的 task_type 是否与 description 对应一致
        """
        if task not in JUDGE_DIMS:
            raise ValueError(f"Unknown task '{task}'; expected 'edit' or 'repair'")
        dims = JUDGE_DIMS[task]
        if not isinstance(judge_result, dict):
            raise ValueError("Judge result is not a dict.")

        task_scores = judge_result.get("task_scores")
        if not isinstance(task_scores, list):
            raise ValueError("Judge result missing or invalid task_scores.")

        if len(task_scores) != len(description):
            raise ValueError(
                f"Task score count mismatch: got {len(task_scores)}, expected {len(description)}"
            )

        for idx, task in enumerate(description):
            expected_type = task.get("task_type")
            if expected_type is None:
                raise ValueError(f"Missing task_type in description at index {idx}")

            score_item = task_scores[idx]
            if not isinstance(score_item, dict):
                raise ValueError(f"task_scores[{idx}] is not a dict")

            actual_type = score_item.get("task_type")
            if actual_type != expected_type:
                raise ValueError(
                    f"task_type mismatch at index {idx}: got '{actual_type}', expected '{expected_type}'"
                )

            task_idx = score_item.get("task_idx")
            if task_idx is not None and task_idx != idx:
                raise ValueError(
                    f"task_idx mismatch at index {idx}: got {task_idx}, expected {idx}"
                )

            # 校验三维度分数是否存在且为 0-10 的数值
            for dim in dims:
                if dim not in score_item:
                    raise ValueError(f"Missing '{dim}' score in task_scores[{idx}]")
                dim_value = score_item.get(dim)
                if not isinstance(dim_value, (int, float)):
                    raise ValueError(f"Invalid '{dim}' score type in task_scores[{idx}]")
                if not (0 <= dim_value <= 10):
                    raise ValueError(f"'{dim}' score out of range in task_scores[{idx}]")

    def _judge_with_retry(
        self,
        messages: List[Dict[str, Any]],
        description: List[Dict[str, str]],
        task: str,
        max_retries: int = 3,
        backoff_base: int = 2,
    ) -> Tuple[Dict[str, Any], str]:
        """
        带重试的评分流程：LLM调用 -> 解析 -> 校验 task_type 一致性
        """
        if task not in JUDGE_DIMS:
            raise ValueError(f"Unknown task '{task}'; expected 'edit' or 'repair'")
        d1, d2, d3 = JUDGE_DIMS[task]
        last_error = None

        for attempt in range(1, max_retries + 1):
            try:
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=messages,
                    max_tokens=self.max_tokens,
                    temperature=self.temperature,
                    # seed=self.seed,
                )

                response_text = (
                    response.choices[0].message.content
                    if response and response.choices
                    else None
                )
                if not response_text:
                    raise ValueError("Empty response content from LLM.")

                judge_result = self.parse_judge_response(response_text)

                self._validate_judge_task_types(description, judge_result, task)

                return judge_result, response_text

            except Exception as exc:
                last_error = exc
                wait_time = backoff_base ** attempt
                if attempt == max_retries:
                    raise Exception(
                        f"Judge failed after {max_retries} attempts. Last error: {exc}"
                    ) from last_error

                print(
                    f"Attempt {attempt}/{max_retries} failed: {exc}. "
                    f"Retrying in {wait_time}s..."
                )
                time.sleep(wait_time)

        raise last_error

    def judge_task(self,
                   data_folder: Union[str, Path],
                   generated_folder: Union[str, Path],
                   task: str,
                   output_filename: str = "judge.json") -> Dict[str, Any]:
        """
        对单个任务进行评分

        Args:
            data_folder: 原始数据文件夹路径
            generated_folder: 生成的答案文件夹路径
            task: 任务类型 ("edit" 或 "repair")
            output_filename: 保存评分结果的文件名 (默认: judge.json)

        Returns:
            Dict[str, Any]: 评分结果
        """
        data_folder = Path(data_folder)
        generated_folder = Path(generated_folder)
        
        # 验证任务类型
        if task not in ["edit", "repair"]:
            raise ValueError(f"Invalid task: {task}. Must be 'edit' or 'repair'")
        
        output_path = generated_folder
        
        # 1. 加载原始数据
        info = self.load_label_data(data_folder)
        description = info["description"]
        src_code = info["src_code"]
        label_modifications = info["label_modified_files"]
        src_screenshots = info["src_screenshot"]
        dst_screenshots = info["dst_screenshot"]
        
        # 2. 加载生成的修改块和截图
        generated_info = self.load_generated_data(generated_folder)
        generated_modifications = self.ignore_error_blocks(
            generated_info["modified_files"],
            generated_info["apply_errors"]
        )
        generated_screenshots = generated_info["ans_screenshot"]
        
        print(f"Task Type: {task}")
        print(f"Loaded {len(generated_modifications)} generated modification blocks")
        print(f"Loaded {len(generated_screenshots)} generated screenshots")
        print(f"Label has {len(label_modifications)} modification blocks")
        
        # 3. 根据任务类型构建不同的评分 messages
        if task == "edit":
            messages = self.construct_edit_judge_messages(
                description=description,
                generated_modifications=generated_modifications,
                src_screenshots=src_screenshots,
                generated_screenshots=generated_screenshots
            )
        elif task == "repair":
            messages = self.construct_repair_judge_messages(
                description=description,
                label_modifications=label_modifications,
                generated_modifications=generated_modifications,
                src_screenshots=src_screenshots,
                generated_screenshots=generated_screenshots,
                dst_screenshots=dst_screenshots
            )
        else:
            raise ValueError(f"Unknown task type: {task}")
        
        # 4. 调用 LLM 进行评分（带重试与校验）
        judge_result, response = self._judge_with_retry(
            messages=messages,
            description=description,
            task=task,
            max_retries=self.max_retry,
        )
        print("Judge response received")
        
        # 5. 保存评分结果
        result = {
            "judge_model": self.model_name,
            "task": task,
            "task_type": info.get("task_type", []),
            "description": description,
            "judge_result": judge_result,
            "generated_modifications": generated_modifications,
            "label_modifications": label_modifications,
            # "judge_messages": messages,
            "judge_response": response,
            "data_folder": str(data_folder),
            "generated_folder": str(generated_folder)
        }
        
        with open(output_path / output_filename, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=4)
        
        print(f"Judge result saved to: {output_path}")
        
        return result


if __name__ == "__main__":
    import os
    from llm.judge.prompt import EDIT_JUDGE_SYSTEM_PROMPT, REPAIR_JUDGE_SYSTEM_PROMPT

    api_key = os.environ.get("OPENAI_API_KEY")
    base_url = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable is required.")
    
    judge = CodeJudge(
        model_name="gemini-3-pro-preview",
        api_key=api_key,
        base_url=base_url,
        max_tokens=32 * 1024,
        max_retry=3,
        edit_judge_prompt=EDIT_JUDGE_SYSTEM_PROMPT,
        repair_judge_prompt=REPAIR_JUDGE_SYSTEM_PROMPT
    )
    
    # 测试评分
    ## edit test multi
    data_folder = "/Users/pedestrian/Desktop/web_coding_output/data/data_demo_renderbench_3_6_9/edit_test_multi/2930611_www.fieldsquared.com_L9_2"
    generated_folder = "/Users/pedestrian/Desktop/web_coding_output/results_test/gemini-3-pro-preview_text_20260116_232556/edit_test_multi/2930611_www.fieldsquared.com_L9_2"
    result = judge.judge_task(
        data_folder=data_folder,
        generated_folder=generated_folder,
        task="edit"
    )
    print("\n=== Judge Result ===")
    print(json.dumps(result["judge_result"], indent=2, ensure_ascii=False))
    task_scores = result["judge_result"].get("task_scores", [])
    d1, d2, d3 = JUDGE_DIMS["edit"]
    if task_scores:
        per_task_hm = [
            3 / (1 / max(t[d1], 1) + 1 / max(t[d2], 1) + 1 / max(t[d3], 1))
            for t in task_scores
        ]
        print(f"\nHarmonic mean across {len(task_scores)} tasks: "
              f"{sum(per_task_hm) / len(per_task_hm):.2f} / 10.0")
    # # repair test multi
    # data_folder = "/Users/pedestrian/Desktop/web_coding_output/data/data_demo_renderbench_10/repair_test_multi/1009769_www.kccworld.co.kr_english__L8_0"
    # generated_folder = "/Users/pedestrian/Desktop/web_coding_output/results_new/gpt-5-codex/image/repair_test_multi/1009769_www.kccworld.co.kr_english__L8_0"
    # result = judge.judge_task(
    #     data_folder=data_folder,
    #     generated_folder=generated_folder,
    #     task="repair"
    # )
    
    print("\n=== Judge Result ===")
    print(json.dumps(result["judge_result"], indent=2, ensure_ascii=False))
