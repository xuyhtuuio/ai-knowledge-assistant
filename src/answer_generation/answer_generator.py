"""
答案生成器模块
基于Qwen3-14B的RAG答案生成
关闭CoT模式，确保忠实于知识库上下文
"""

import logging
from typing import Dict, List, Optional
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
import yaml

logger = logging.getLogger(__name__)


class AnswerGenerator:
    """
    答案生成器
    使用Qwen3-14B模型基于GraphRAG检索到的上下文生成答案
    """

    def __init__(self, config_path: str = "config/config.yaml"):
        """
        初始化答案生成器

        Args:
            config_path: 配置文件路径
        """
        # 加载配置
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)

        self.model_config = self.config['models']['answer_generation']

        # 加载Prompt配置
        with open('config/prompt_config.yaml', 'r', encoding='utf-8') as f:
            self.prompt_config = yaml.safe_load(f)

        self.system_prompt = self.prompt_config['answer_generation_system']

        # 加载模型和分词器
        self.device = self.model_config['device']
        self.tokenizer = None
        self.model = None

        logger.info(f"初始化答案生成器，设备: {self.device}")

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

    def _build_rag_prompt(self, 
                         user_query: str, 
                         context: str, 
                         intent: str = "") -> List[Dict]:
        """
        构建RAG提示词

        Args:
            user_query: 用户查询
            context: 知识库上下文
            intent: 意图类型（可选，用于更精准的提示）

        Returns:
            消息列表
        """
        # 根据上下文是否为空，调整system prompt
        if context and context != "知识库中暂无相关信息。":
            # 有上下文：严格要求基于上下文回答
            full_system_prompt = f"""{self.system_prompt}

【知识库上下文】
{context}

请严格根据上述知识库上下文回答用户问题。如果上下文中没有相关信息，请明确告知用户。"""
        else:
            # 无上下文：告知用户知识库暂无信息
            full_system_prompt = f"""{self.system_prompt}

【知识库上下文】
知识库中暂无相关信息。

请礼貌地告知用户，当前知识库中暂无该问题的相关信息。"""

        messages = [
            {"role": "system", "content": full_system_prompt},
            {"role": "user", "content": user_query}
        ]

        return messages

    def generate_answer(self, 
                       user_query: str, 
                       context: str, 
                       intent: str = "",
                       max_length: Optional[int] = None,
                       temperature: Optional[float] = None) -> Dict[str, str]:
        """
        生成答案

        Args:
            user_query: 用户查询
            context: 知识库上下文
            intent: 意图类型
            max_length: 最大生成长度（覆盖配置）
            temperature: 温度参数（覆盖配置）

        Returns:
            包含答案和元信息的字典
        """
        # 确保模型已加载
        self.load_model()

        # 构建提示词
        messages = self._build_rag_prompt(user_query, context, intent)

        # 应用聊天模板
        text = self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )

        # 编码输入
        model_inputs = self.tokenizer([text], return_tensors="pt").to(self.device)

        # 生成参数
        gen_max_length = max_length if max_length else self.model_config['max_length']
        gen_temperature = temperature if temperature else self.model_config['temperature']

        # 生成输出（关闭CoT模式）
        with torch.no_grad():
            generated_ids = self.model.generate(
                model_inputs.input_ids,
                max_new_tokens=gen_max_length,
                temperature=gen_temperature,
                top_p=self.model_config['top_p'],
                do_sample=True if gen_temperature > 0 else False,
                pad_token_id=self.tokenizer.eos_token_id,
                repetition_penalty=self.model_config.get('repetition_penalty', 1.1)
            )

        # 解码输出
        generated_ids = [
            output_ids[len(input_ids):]
            for input_ids, output_ids in zip(model_inputs.input_ids, generated_ids)
        ]

        answer = self.tokenizer.batch_decode(
            generated_ids,
            skip_special_tokens=True
        )[0]

        logger.info(f"生成答案: {answer[:100]}...")

        result = {
            "answer": answer.strip(),
            "context_used": context,
            "has_context": bool(context and context != "知识库中暂无相关信息。"),
            "query": user_query
        }

        return result

    def generate_ood_response(self, user_query: str) -> Dict[str, str]:
        """
        生成OOD（域外）问题的回答

        Args:
            user_query: 用户查询

        Returns:
            包含答案的字典
        """
        # OOD问题使用通用对话模式
        messages = [
            {
                "role": "system",
                "content": "你是一个友好的AI助手。用户的问题不在你的专业领域范围内，请礼貌地告知用户，并引导用户提问关于资产、场景、热点的问题。"
            },
            {
                "role": "user",
                "content": user_query
            }
        ]

        # 确保模型已加载
        self.load_model()

        # 应用聊天模板
        text = self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )

        # 编码输入
        model_inputs = self.tokenizer([text], return_tensors="pt").to(self.device)

        # 生成
        with torch.no_grad():
            generated_ids = self.model.generate(
                model_inputs.input_ids,
                max_new_tokens=256,
                temperature=0.7,
                top_p=0.9,
                do_sample=True,
                pad_token_id=self.tokenizer.eos_token_id
            )

        # 解码
        generated_ids = [
            output_ids[len(input_ids):]
            for input_ids, output_ids in zip(model_inputs.input_ids, generated_ids)
        ]

        answer = self.tokenizer.batch_decode(
            generated_ids,
            skip_special_tokens=True
        )[0]

        result = {
            "answer": answer.strip(),
            "context_used": "",
            "has_context": False,
            "query": user_query,
            "is_ood": True
        }

        return result

    def batch_generate(self, 
                      queries_with_context: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """
        批量生成答案

        Args:
            queries_with_context: 包含query和context的字典列表

        Returns:
            答案列表
        """
        results = []
        for item in queries_with_context:
            query = item['query']
            context = item['context']
            intent = item.get('intent', '')
            
            result = self.generate_answer(query, context, intent)
            results.append(result)
        
        return results


if __name__ == "__main__":
    # 测试代码
    logging.basicConfig(level=logging.INFO)

    # 初始化生成器
    generator = AnswerGenerator()

    # 测试查询
    test_query = "新员工入职场景需要哪些核心资产？"
    test_context = """
关系 1:
  asset_name: HR系统
  asset_description: 人力资源管理系统，负责员工信息管理
  role: 核心依赖
  status: 已上线

关系 2:
  asset_name: OA系统
  asset_description: 办公自动化系统
  role: 核心依赖
  status: 已上线

关系 3:
  asset_name: 统一认证系统
  asset_description: 企业统一身份认证平台
  role: 辅助支持
  status: 已上线
"""

    # 生成答案
    result = generator.generate_answer(test_query, test_context)
    
    print(f"\n问题: {test_query}")
    print(f"\n答案: {result['answer']}")
    print(f"\n是否使用了上下文: {result['has_context']}")

    # 测试OOD问题
    ood_query = "今天天气怎么样？"
    ood_result = generator.generate_ood_response(ood_query)
    
    print(f"\n\nOOD问题: {ood_query}")
    print(f"答案: {ood_result['answer']}")

