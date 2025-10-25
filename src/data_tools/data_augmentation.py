"""
数据增强模块
实现三种数据扩充策略：
1. 基于LLM的同义改写 (Paraphrasing)
2. 基于目录的实体置换 (Entity Permutation)
3. 系统性的负样本与边界样本生成 (Negative Sampling)
"""

import json
import logging
import random
from typing import List, Dict, Any, Optional
from pathlib import Path
import pandas as pd
import yaml
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

logger = logging.getLogger(__name__)


class DataAugmentation:
    """数据增强器"""

    def __init__(self, config_path: str = "config/config.yaml"):
        """
        初始化数据增强器

        Args:
            config_path: 配置文件路径
        """
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)

        self.data_config = self.config['data']
        self.tokenizer = None
        self.model = None

        logger.info("数据增强器初始化完成")

    def load_llm_model(self, model_path: str):
        """
        加载LLM模型（用于同义改写）

        Args:
            model_path: 模型路径
        """
        logger.info(f"加载LLM模型: {model_path}")

        self.tokenizer = AutoTokenizer.from_pretrained(
            model_path,
            trust_remote_code=True
        )

        self.model = AutoModelForCausalLM.from_pretrained(
            model_path,
            device_map="auto",
            torch_dtype=torch.float16,
            trust_remote_code=True
        )

        self.model.eval()
        logger.info("LLM模型加载成功")

    def paraphrase_sample(self, 
                         original_query: str, 
                         intent: str, 
                         entities: List[Dict],
                         num_variations: int = 10) -> List[Dict]:
        """
        策略一：基于LLM的同义改写

        Args:
            original_query: 原始查询
            intent: 意图标签
            entities: 实体列表
            num_variations: 生成变体数量

        Returns:
            增强后的样本列表
        """
        if self.model is None:
            logger.warning("LLM模型未加载，跳过同义改写")
            return []

        system_prompt = """你是一个专业的数据增强助手。请对给定的用户查询进行同义改写，生成多个语义相同但表达方式不同的变体。
要求：
1. 保持原意不变
2. 改变表达方式（口语化、书面化、简洁、详细等）
3. 保留实体名称（用[]标记的部分）
4. 每行一个变体
"""

        user_prompt = f"""原始查询: {original_query}

请生成{num_variations}个同义改写变体："""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        # 应用聊天模板
        text = self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )

        # 编码
        model_inputs = self.tokenizer([text], return_tensors="pt").to(self.model.device)

        # 生成
        with torch.no_grad():
            generated_ids = self.model.generate(
                model_inputs.input_ids,
                max_new_tokens=512,
                temperature=0.8,
                top_p=0.9,
                do_sample=True
            )

        # 解码
        generated_ids = [
            output_ids[len(input_ids):]
            for input_ids, output_ids in zip(model_inputs.input_ids, generated_ids)
        ]

        output_text = self.tokenizer.batch_decode(
            generated_ids,
            skip_special_tokens=True
        )[0]

        # 解析生成的变体
        variations = []
        lines = output_text.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if line and len(line) > 5:  # 过滤空行和过短的行
                # 移除行首的数字序号
                line = line.lstrip('0123456789.、 ')
                
                sample = {
                    "messages": [
                        {
                            "role": "system",
                            "content": "你是一个意图识别和实体抽取专家。请分析用户输入，并以JSON格式返回意图和实体。"
                        },
                        {
                            "role": "user",
                            "content": line
                        },
                        {
                            "role": "assistant",
                            "content": json.dumps({
                                "intent": intent,
                                "entities": entities
                            }, ensure_ascii=False)
                        }
                    ]
                }
                variations.append(sample)

        logger.info(f"生成了 {len(variations)} 个同义改写变体")
        return variations[:num_variations]

    def permutate_entities(self,
                          template_samples: List[Dict],
                          entity_catalog: Dict[str, List[str]]) -> List[Dict]:
        """
        策略二：基于目录的实体置换

        Args:
            template_samples: 模板样本列表
            entity_catalog: 实体目录 {"Asset": [...], "Scenario": [...], "Hotspot": [...]}

        Returns:
            增强后的样本列表
        """
        augmented_samples = []

        for template in template_samples:
            original_query = template['messages'][1]['content']
            original_response = json.loads(template['messages'][2]['content'])
            
            intent = original_response['intent']
            entities = original_response['entities']

            # 对每个实体类型进行置换
            for entity_info in entities:
                entity_type = entity_info['type']
                
                if entity_type in entity_catalog:
                    available_entities = entity_catalog[entity_type]
                    
                    # 为每个可用实体生成一个新样本
                    for new_entity_value in available_entities:
                        # 替换查询中的实体
                        new_query = original_query.replace(
                            entity_info['value'],
                            new_entity_value
                        )
                        
                        # 替换实体列表中的值
                        new_entities = []
                        for e in entities:
                            new_e = e.copy()
                            if e['type'] == entity_type:
                                new_e['value'] = new_entity_value
                            new_entities.append(new_e)
                        
                        # 创建新样本
                        new_sample = {
                            "messages": [
                                {
                                    "role": "system",
                                    "content": "你是一个意图识别和实体抽取专家。请分析用户输入，并以JSON格式返回意图和实体。"
                                },
                                {
                                    "role": "user",
                                    "content": new_query
                                },
                                {
                                    "role": "assistant",
                                    "content": json.dumps({
                                        "intent": intent,
                                        "entities": new_entities
                                    }, ensure_ascii=False)
                                }
                            ]
                        }
                        augmented_samples.append(new_sample)

        logger.info(f"通过实体置换生成了 {len(augmented_samples)} 个样本")
        return augmented_samples

    def generate_negative_samples(self, num_ood: int = 100, num_hard: int = 50) -> List[Dict]:
        """
        策略三：生成负样本

        Args:
            num_ood: OOD负样本数量
            num_hard: 边界负样本数量

        Returns:
            负样本列表
        """
        negative_samples = []

        # OOD负样本（闲聊、常识问答）
        ood_queries = [
            "今天天气怎么样？",
            "帮我写个笑话",
            "你叫什么名字？",
            "1+1等于几？",
            "推荐一首歌",
            "明天会下雨吗？",
            "讲个故事",
            "你好",
            "谢谢",
            "帮我翻译一下",
            "什么是人工智能？",
            "推荐一部电影",
            "怎么做红烧肉？",
            "Python怎么安装？",
            "股票今天涨了吗？",
            "最近有什么新闻？",
            "给我讲个冷笑话",
            "你能做什么？",
            "北京在哪里？",
            "帮我算个数学题",
        ]

        # 扩充到num_ood个
        while len(ood_queries) < num_ood:
            ood_queries.extend(ood_queries[:min(20, num_ood - len(ood_queries))])

        for query in ood_queries[:num_ood]:
            sample = {
                "messages": [
                    {
                        "role": "system",
                        "content": "你是一个意图识别和实体抽取专家。请分析用户输入，并以JSON格式返回意图和实体。"
                    },
                    {
                        "role": "user",
                        "content": query
                    },
                    {
                        "role": "assistant",
                        "content": json.dumps({
                            "intent": "OOD",
                            "entities": []
                        }, ensure_ascii=False)
                    }
                ]
            }
            negative_samples.append(sample)

        # 边界负样本（Hard Negatives）
        hard_negative_queries = [
            "查询不存在的资产XYZ的信息",
            "那个系统和那个场景",
            "帮我查一下",
            "这个怎么办？",
            "告诉我",
            "资产",
            "场景是什么",
            "最近的",
            "XXX",
            "查询一下某某某",
            "那个东西的负责人",
            "这个系统在哪些",
            "怎么查",
            "给我看看",
            "有哪些",
        ]

        # 扩充到num_hard个
        while len(hard_negative_queries) < num_hard:
            hard_negative_queries.extend(
                hard_negative_queries[:min(15, num_hard - len(hard_negative_queries))]
            )

        for query in hard_negative_queries[:num_hard]:
            sample = {
                "messages": [
                    {
                        "role": "system",
                        "content": "你是一个意图识别和实体抽取专家。请分析用户输入，并以JSON格式返回意图和实体。"
                    },
                    {
                        "role": "user",
                        "content": query
                    },
                    {
                        "role": "assistant",
                        "content": json.dumps({
                            "intent": "OOD",
                            "entities": []
                        }, ensure_ascii=False)
                    }
                ]
            }
            negative_samples.append(sample)

        logger.info(f"生成了 {len(negative_samples)} 个负样本 (OOD: {num_ood}, Hard: {num_hard})")
        return negative_samples

    def augment_dataset(self,
                       original_samples: List[Dict],
                       entity_catalog_file: Optional[str] = None,
                       output_file: str = "data/processed/training/augmented_train.jsonl",
                       use_paraphrase: bool = True,
                       use_permutation: bool = True,
                       use_negative: bool = True,
                       paraphrase_count: int = 10) -> List[Dict]:
        """
        完整数据增强流程

        Args:
            original_samples: 原始样本列表
            entity_catalog_file: 实体目录文件路径
            output_file: 输出文件路径
            use_paraphrase: 是否使用同义改写
            use_permutation: 是否使用实体置换
            use_negative: 是否使用负样本
            paraphrase_count: 每个样本的改写数量

        Returns:
            增强后的完整数据集
        """
        all_samples = []

        # 添加原始样本
        all_samples.extend(original_samples)
        logger.info(f"原始样本数: {len(original_samples)}")

        # 策略一：同义改写
        if use_paraphrase and self.model is not None:
            logger.info("开始同义改写...")
            for sample in original_samples:
                query = sample['messages'][1]['content']
                response = json.loads(sample['messages'][2]['content'])
                
                intent = response['intent']
                entities = response['entities']
                
                # 只对正样本进行改写（不对OOD改写）
                if intent != "OOD":
                    paraphrased = self.paraphrase_sample(
                        query, intent, entities, paraphrase_count
                    )
                    all_samples.extend(paraphrased)

        # 策略二：实体置换
        if use_permutation and entity_catalog_file:
            logger.info("开始实体置换...")
            
            # 加载实体目录
            with open(entity_catalog_file, 'r', encoding='utf-8') as f:
                entity_catalog = json.load(f)
            
            # 只选择有实体的样本作为模板
            template_samples = [
                s for s in original_samples
                if json.loads(s['messages'][2]['content']).get('entities')
            ]
            
            permutated = self.permutate_entities(template_samples, entity_catalog)
            all_samples.extend(permutated)

        # 策略三：负样本生成
        if use_negative:
            logger.info("开始生成负样本...")
            negative = self.generate_negative_samples(num_ood=100, num_hard=50)
            all_samples.extend(negative)

        # 打乱顺序
        random.shuffle(all_samples)

        # 保存到文件
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w', encoding='utf-8') as f:
            for sample in all_samples:
                f.write(json.dumps(sample, ensure_ascii=False) + '\n')

        logger.info(f"数据增强完成！总样本数: {len(all_samples)}")
        logger.info(f"增强后的数据已保存到: {output_file}")

        return all_samples


def load_entity_catalog_from_csv(asset_file: str,
                                 scenario_file: str,
                                 hotspot_file: str,
                                 output_file: str = "data/processed/entity_catalog.json"):
    """
    从CSV文件加载实体目录

    Args:
        asset_file: 资产CSV文件
        scenario_file: 场景CSV文件
        hotspot_file: 热点CSV文件
        output_file: 输出JSON文件路径
    """
    catalog = {
        "Asset": [],
        "Scenario": [],
        "Hotspot": []
    }

    # 加载资产
    if Path(asset_file).exists():
        df = pd.read_csv(asset_file)
        catalog["Asset"] = df['name'].dropna().unique().tolist()
        logger.info(f"加载了 {len(catalog['Asset'])} 个资产实体")

    # 加载场景
    if Path(scenario_file).exists():
        df = pd.read_csv(scenario_file)
        catalog["Scenario"] = df['name'].dropna().unique().tolist()
        logger.info(f"加载了 {len(catalog['Scenario'])} 个场景实体")

    # 加载热点
    if Path(hotspot_file).exists():
        df = pd.read_csv(hotspot_file)
        catalog["Hotspot"] = df['title'].dropna().unique().tolist()
        logger.info(f"加载了 {len(catalog['Hotspot'])} 个热点实体")

    # 保存
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(catalog, f, ensure_ascii=False, indent=2)

    logger.info(f"实体目录已保存到: {output_file}")
    return catalog


if __name__ == "__main__":
    # 测试代码
    logging.basicConfig(level=logging.INFO)

    # 创建数据增强器
    augmentor = DataAugmentation()

    # 示例：加载实体目录
    entity_catalog = load_entity_catalog_from_csv(
        asset_file="data/raw/assets/assets.csv",
        scenario_file="data/raw/scenarios/scenarios.csv",
        hotspot_file="data/raw/hotspots/hotspots.csv",
        output_file="data/processed/entity_catalog.json"
    )

    # 示例：原始样本
    original_samples = [
        {
            "messages": [
                {"role": "system", "content": "你是一个意图识别和实体抽取专家。请分析用户输入，并以JSON格式返回意图和实体。"},
                {"role": "user", "content": "XX系统的负责人是谁？"},
                {"role": "assistant", "content": json.dumps({
                    "intent": "Query_Asset",
                    "entities": [
                        {"type": "Asset", "value": "XX系统"},
                        {"type": "Attribute", "value": "负责人"}
                    ]
                }, ensure_ascii=False)}
            ]
        }
    ]

    # 执行数据增强
    augmented = augmentor.augment_dataset(
        original_samples=original_samples,
        entity_catalog_file="data/processed/entity_catalog.json",
        output_file="data/processed/training/augmented_train.jsonl",
        use_paraphrase=False,  # 如果没有加载LLM模型，设为False
        use_permutation=True,
        use_negative=True
    )

    print(f"\n数据增强完成，共生成 {len(augmented)} 个样本")

