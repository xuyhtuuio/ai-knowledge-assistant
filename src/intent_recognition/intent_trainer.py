"""
意图识别模型训练模块
使用QLoRA对Qwen3-32B进行SFT训练
"""

import os
import json
import logging
from typing import List, Dict
from dataclasses import dataclass
import torch
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    TrainingArguments,
    Trainer,
    DataCollatorForSeq2Seq
)
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from datasets import Dataset
import yaml

logger = logging.getLogger(__name__)


@dataclass
class TrainingConfig:
    """训练配置"""
    model_name: str
    output_dir: str
    train_data_path: str
    eval_data_path: str = None
    num_epochs: int = 10
    batch_size: int = 4
    learning_rate: float = 2e-5
    warmup_steps: int = 100
    save_steps: int = 500
    eval_steps: int = 100
    use_qlora: bool = True
    lora_r: int = 64
    lora_alpha: int = 16
    lora_dropout: float = 0.1
    target_modules: List[str] = None


class IntentTrainer:
    """意图识别模型训练器"""

    def __init__(self, config_path: str = "config/config.yaml"):
        """
        初始化训练器

        Args:
            config_path: 配置文件路径
        """
        # 加载配置
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)

        self.training_config = self.config['training']['intent_recognition']
        self.model_config = self.config['models']['intent_recognition']

        # 加载Prompt配置
        with open('config/prompt_config.yaml', 'r', encoding='utf-8') as f:
            self.prompt_config = yaml.safe_load(f)

        self.system_prompt = self.prompt_config['intent_recognition_system']

        self.tokenizer = None
        self.model = None

        logger.info("意图识别训练器初始化完成")

    def load_data(self, data_path: str) -> Dataset:
        """
        加载训练数据

        Args:
            data_path: 数据文件路径（JSON Lines格式）

        Returns:
            Hugging Face Dataset对象
        """
        logger.info(f"加载数据: {data_path}")

        data_list = []
        with open(data_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    data_list.append(json.loads(line))

        logger.info(f"加载了 {len(data_list)} 条训练样本")

        # 转换为Dataset
        dataset = Dataset.from_list(data_list)

        return dataset

    def preprocess_data(self, examples):
        """
        预处理数据

        Args:
            examples: 数据样本

        Returns:
            处理后的数据
        """
        model_inputs = {
            "input_ids": [],
            "attention_mask": [],
            "labels": []
        }

        for messages in examples['messages']:
            # 应用聊天模板
            text = self.tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=False
            )

            # 编码
            tokenized = self.tokenizer(
                text,
                truncation=True,
                max_length=self.model_config['max_length'],
                padding="max_length"
            )

            model_inputs["input_ids"].append(tokenized["input_ids"])
            model_inputs["attention_mask"].append(tokenized["attention_mask"])
            model_inputs["labels"].append(tokenized["input_ids"])

        return model_inputs

    def setup_model(self):
        """设置模型和分词器"""
        logger.info(f"加载模型: {self.model_config['model_name']}")

        # 加载分词器
        self.tokenizer = AutoTokenizer.from_pretrained(
            self.model_config['model_name'],
            trust_remote_code=True
        )

        # 加载模型
        if self.training_config['use_qlora']:
            
            from transformers import BitsAndBytesConfig



            # 4-bit量化, 量化类型为nf4, 计算类型为float16, 使用double量化
            bnb_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_compute_dtype=torch.float16,
                bnb_4bit_use_double_quant=True
            )

            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_config['model_name'],
                quantization_config=bnb_config,
                device_map="auto",
                trust_remote_code=True
            )

            # 准备模型用于kbit训练
            self.model = prepare_model_for_kbit_training(self.model)

            # 配置LoRA
            lora_config = LoraConfig(
                r=self.training_config['lora_r'],
                lora_alpha=self.training_config['lora_alpha'],
                target_modules=self.training_config['target_modules'],
                lora_dropout=self.training_config['lora_dropout'],
                bias="none",
                task_type="CAUSAL_LM"
            )

            # 应用LoRA
            self.model = get_peft_model(self.model, lora_config)
            self.model.print_trainable_parameters()

        else:
            # 全参数微调
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_config['model_name'],
                device_map="auto",
                torch_dtype=torch.float16,
                trust_remote_code=True
            )

        logger.info("模型加载完成")

    def train(self, train_data_path: str, eval_data_path: str = None):
        """
        开始训练

        Args:
            train_data_path: 训练数据路径
            eval_data_path: 验证数据路径（可选）
        """
        # 设置模型
        self.setup_model()

        # 加载数据
        train_dataset = self.load_data(train_data_path)

        eval_dataset = None
        if eval_data_path:
            eval_dataset = self.load_data(eval_data_path)

        # 预处理数据
        train_dataset = train_dataset.map(
            self.preprocess_data,
            batched=True,
            remove_columns=train_dataset.column_names
        )

        if eval_dataset:
            eval_dataset = eval_dataset.map(
                self.preprocess_data,
                batched=True,
                remove_columns=eval_dataset.column_names
            )

        # 训练参数
        training_args = TrainingArguments(
            output_dir=self.training_config['output_dir'],  # 模型检查点和日志的输出目录
            num_train_epochs=self.training_config['num_epochs'],  # 训练的总轮数
            per_device_train_batch_size=self.training_config['batch_size'],  # 每个设备(GPU)的训练批次大小
            per_device_eval_batch_size=self.training_config['batch_size'],  # 每个设备(GPU)的验证批次大小
            learning_rate=self.training_config['learning_rate'],  # 优化器的学习率
            
            warmup_steps=self.training_config['warmup_steps'],  # 学习率预热步数,逐步增加学习率以稳定训练
            save_steps=self.training_config['save_steps'],  # 每隔多少步保存一次模型检查点
            eval_steps=self.training_config['eval_steps'],  # 每隔多少步在验证集上评估一次
            logging_steps=50,  # 每隔多少步记录一次训练日志(loss等指标)
            save_total_limit=3,  # 最多保留3个检查点,自动删除旧的以节省磁盘空间
            load_best_model_at_end=True if eval_dataset else False,  # 训练结束后是否加载验证集上表现最好的模型
            evaluation_strategy="steps" if eval_dataset else "no",  # 评估策略:有验证集时按步数评估,否则不评估
            fp16=True,  # 启用混合精度训练(FP16),可加速训练并减少显存占用
            gradient_accumulation_steps=4,  # 梯度累积步数,每4步更新一次参数,等效于扩大4倍batch_size
            gradient_checkpointing=True,  # 启用梯度检查点,以时间换空间,显著降低显存占用
            
            
            # 这里因为是transfermer模型,所以需要使用8bit优化器节省显存,否则用标准AdamW
            optim="paged_adamw_8bit" if self.training_config['use_qlora'] else "adamw_torch",  # 优化器选择:QLoRA用8bit优化器节省显存,否则用标准AdamW
            report_to=["tensorboard"]  # 将训练指标报告到TensorBoard进行可视化
        )

        # 数据整理器
        data_collator = DataCollatorForSeq2Seq(
            tokenizer=self.tokenizer,
            model=self.model,
            padding=True
        )

        # 训练器
        trainer = Trainer(
            model=self.model,
            args=training_args,
            train_dataset=train_dataset,
            eval_dataset=eval_dataset,
            data_collator=data_collator
        )

        # 开始训练
        logger.info("开始训练...")
        trainer.train()

        # 保存最终模型
        logger.info("保存模型...")
        trainer.save_model(self.training_config['output_dir'])
        self.tokenizer.save_pretrained(self.training_config['output_dir'])

        logger.info("训练完成！")


if __name__ == "__main__":
    # 训练脚本
    logging.basicConfig(level=logging.INFO)

    import argparse

    parser = argparse.ArgumentParser(description="训练意图识别模型")
    parser.add_argument("--config", type=str, default="config/config.yaml", help="配置文件路径")
    parser.add_argument("--train_data", type=str, required=True, help="训练数据路径")
    parser.add_argument("--eval_data", type=str, default=None, help="验证数据路径")

    args = parser.parse_args()

    # 初始化训练器
    trainer = IntentTrainer(config_path=args.config)

    # 开始训练
    trainer.train(
        train_data_path=args.train_data,
        eval_data_path=args.eval_data
    )
