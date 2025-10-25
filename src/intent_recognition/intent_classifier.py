"""
意图识别分类器模块
基于Qwen3-32B SFT的意图识别和实体抽取
"""

import json
import logging
from typing import Dict, List, Optional
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
import yaml

from .intent_config import (
    IntentType, EntityType, Entity, IntentResult,
    validate_intent_result, get_intent_by_name, get_entity_by_name
)

logger = logging.getLogger(__name__)


class IntentClassifier:
    """
    意图识别分类器
    使用Qwen3-32B SFT模型进行意图识别和实体抽取
    """

    def __init__(self, config_path: str = "config/config.yaml"):
        """
        初始化意图分类器

        Args:
            config_path: 配置文件路径
        """
        # 加载配置
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)

        self.model_config = self.config['models']['intent_recognition']

        # 加载Prompt配置
        with open('config/prompt_config.yaml', 'r', encoding='utf-8') as f:
            self.prompt_config = yaml.safe_load(f)

        self.system_prompt = self.prompt_config['intent_recognition_system']

        # 加载模型和分词器
        self.device = self.model_config['device']
        self.tokenizer = None
        self.model = None

        logger.info(f"初始化意图识别分类器，设备: {self.device}")

    def load_model(self):
        """加载模型（延迟加载）"""
        if self.model is not None:
            return

        logger.info(f"正在加载模型: {self.model_config['model_name']}")

        try:
            # 加载分词器
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_config['model_path'],
                trust_remote_code=True
            )

            # 加载模型
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_config['model_path'],
                device_map="auto",
                torch_dtype=torch.float16,
                trust_remote_code=True
            )

            self.model.eval()
            logger.info("模型加载成功")

        except Exception as e:
            logger.error(f"模型加载失败: {str(e)}")
            raise

    def _build_messages(self, user_query: str) -> List[Dict]:
        """
        构建输入消息

        Args:
            user_query: 用户查询

        Returns:
            消息列表
        """
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_query}
        ]
        return messages

    def _parse_output(self, output_text: str) -> Dict:
        """
        解析模型输出的JSON

        Args:
            output_text: 模型输出文本

        Returns:
            解析后的字典
        """
        try:
            # 尝试直接解析JSON
            result = json.loads(output_text)
            return result
        except json.JSONDecodeError:
            # 如果失败，尝试提取JSON部分
            try:
                # 查找第一个 { 和最后一个 }
                start_idx = output_text.find('{')
                end_idx = output_text.rfind('}')

                if start_idx != -1 and end_idx != -1:
                    json_str = output_text[start_idx:end_idx + 1]
                    result = json.loads(json_str)
                    return result
            except Exception as e:
                logger.error(f"JSON解析失败: {str(e)}")

            # 如果仍然失败，返回OOD
            logger.warning(f"无法解析输出，返回OOD: {output_text}")
            return {"intent": "OOD", "entities": []}

    def predict(self, user_query: str) -> IntentResult:
        """
        预测用户查询的意图和实体

        Args:
            user_query: 用户查询

        Returns:
            IntentResult对象
        """
        # 确保模型已加载
        self.load_model()

        # 构建输入
        messages = self._build_messages(user_query)

        # 应用聊天模板
        text = self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )

        # 编码输入
        model_inputs = self.tokenizer([text], return_tensors="pt").to(self.device)

        # 生成输出（关闭CoT模式）
        with torch.no_grad():
            generated_ids = self.model.generate(
                model_inputs.input_ids,
                max_new_tokens=self.model_config['max_length'],
                temperature=self.model_config['temperature'],
                top_p=self.model_config['top_p'],
                do_sample=True if self.model_config['temperature'] > 0 else False,
                pad_token_id=self.tokenizer.eos_token_id
            )

        # 解码输出
        generated_ids = [
            output_ids[len(input_ids):]
            for input_ids, output_ids in zip(model_inputs.input_ids, generated_ids)
        ]

        output_text = self.tokenizer.batch_decode(
            generated_ids,
            skip_special_tokens=True
        )[0]

        logger.info(f"模型原始输出: {output_text}")

        # 解析输出
        result_dict = self._parse_output(output_text)

        # 验证格式
        if not validate_intent_result(result_dict):
            logger.warning(f"输出格式验证失败，返回OOD: {result_dict}")
            result_dict = {"intent": "OOD", "entities": []}

        # 构建IntentResult对象
        intent = get_intent_by_name(result_dict['intent'])

        entities = []
        for entity_dict in result_dict.get('entities', []):
            try:
                entity = Entity(
                    type=get_entity_by_name(entity_dict['type']),
                    value=entity_dict['value'],
                    confidence=entity_dict.get('confidence', 1.0)
                )
                entities.append(entity)
            except Exception as e:
                logger.warning(f"实体解析失败: {entity_dict}, 错误: {str(e)}")
                continue

        intent_result = IntentResult(
            intent=intent,
            entities=entities,
            confidence=result_dict.get('confidence', 1.0),
            raw_output=output_text
        )

        return intent_result

    def batch_predict(self, queries: List[str]) -> List[IntentResult]:
        """
        批量预测

        Args:
            queries: 查询列表

        Returns:
            IntentResult列表
        """
        results = []
        for query in queries:
            result = self.predict(query)
            results.append(result)
        return results


if __name__ == "__main__":
    # 测试代码
    logging.basicConfig(level=logging.INFO)

    # 初始化分类器
    classifier = IntentClassifier()

    # 测试查询
    test_queries = [
        "XX系统的负责人是谁？",
        "新员工入职流程怎么走？",
        "最近的数据安全法更新了什么？",
        "客户管理系统应用在哪些场景？",
        "今天天气怎么样？"
    ]

    for query in test_queries:
        print(f"\n查询: {query}")
        result = classifier.predict(query)
        print(f"意图: {result.intent}")
        print(f"实体: {[(e.type, e.value) for e in result.entities]}")
        print(f"置信度: {result.confidence}")
