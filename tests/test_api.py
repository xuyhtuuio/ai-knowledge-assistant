"""
API接口测试
"""

import requests
import json
import time


class APITester:
    """API测试类"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.test_cases = []
        self.passed = 0
        self.failed = 0
    
    def test_health(self):
        """测试健康检查接口"""
        print("\n[测试] 健康检查接口")
        print("-" * 60)
        
        try:
            response = requests.get(f"{self.base_url}/health")
            
            if response.status_code == 200:
                print("✓ 状态码: 200")
                data = response.json()
                print(f"✓ 响应: {json.dumps(data, ensure_ascii=False)}")
                self.passed += 1
                return True
            else:
                print(f"✗ 状态码错误: {response.status_code}")
                self.failed += 1
                return False
                
        except Exception as e:
            print(f"✗ 请求失败: {str(e)}")
            self.failed += 1
            return False
    
    def test_query(self, query: str, expected_intent: str = None):
        """测试单个查询接口"""
        print(f"\n[测试] 查询: {query}")
        print("-" * 60)
        
        try:
            start_time = time.time()
            
            response = requests.post(
                f"{self.base_url}/api/v1/query",
                json={"query": query},
                headers={"Content-Type": "application/json"}
            )
            
            elapsed = time.time() - start_time
            
            if response.status_code == 200:
                print("✓ 状态码: 200")
                data = response.json()
                
                if data.get('success'):
                    result = data['data']
                    print(f"✓ 意图: {result['intent']}")
                    print(f"✓ 实体: {result['entities']}")
                    print(f"✓ 答案: {result['answer'][:100]}...")
                    print(f"✓ 耗时: {elapsed:.2f}s")
                    
                    # 验证意图
                    if expected_intent and result['intent'] != expected_intent:
                        print(f"✗ 意图不匹配！预期: {expected_intent}, 实际: {result['intent']}")
                        self.failed += 1
                        return False
                    
                    self.passed += 1
                    return True
                else:
                    print(f"✗ 请求失败: {data.get('error')}")
                    self.failed += 1
                    return False
            else:
                print(f"✗ 状态码错误: {response.status_code}")
                print(f"✗ 响应: {response.text}")
                self.failed += 1
                return False
                
        except Exception as e:
            print(f"✗ 请求异常: {str(e)}")
            self.failed += 1
            return False
    
    def test_batch_query(self, queries: list):
        """测试批量查询接口"""
        print(f"\n[测试] 批量查询 ({len(queries)}个)")
        print("-" * 60)
        
        try:
            start_time = time.time()
            
            response = requests.post(
                f"{self.base_url}/api/v1/batch_query",
                json={"queries": queries},
                headers={"Content-Type": "application/json"}
            )
            
            elapsed = time.time() - start_time
            
            if response.status_code == 200:
                print("✓ 状态码: 200")
                data = response.json()
                
                if data.get('success'):
                    results = data['data']['results']
                    print(f"✓ 返回结果数: {len(results)}")
                    print(f"✓ 总耗时: {elapsed:.2f}s")
                    print(f"✓ 平均耗时: {elapsed/len(queries):.2f}s/query")
                    
                    self.passed += 1
                    return True
                else:
                    print(f"✗ 请求失败: {data.get('error')}")
                    self.failed += 1
                    return False
            else:
                print(f"✗ 状态码错误: {response.status_code}")
                self.failed += 1
                return False
                
        except Exception as e:
            print(f"✗ 请求异常: {str(e)}")
            self.failed += 1
            return False
    
    def test_stats(self):
        """测试统计接口"""
        print("\n[测试] 服务统计接口")
        print("-" * 60)
        
        try:
            response = requests.get(f"{self.base_url}/api/v1/stats")
            
            if response.status_code == 200:
                print("✓ 状态码: 200")
                data = response.json()
                
                if data.get('success'):
                    stats = data['data']
                    print(f"✓ 总请求数: {stats['request_count']}")
                    print(f"✓ 运行时间: {stats['uptime_formatted']}")
                    print(f"✓ 平均QPS: {stats['avg_requests_per_minute']:.2f} req/min")
                    
                    self.passed += 1
                    return True
                else:
                    print(f"✗ 请求失败: {data.get('error')}")
                    self.failed += 1
                    return False
            else:
                print(f"✗ 状态码错误: {response.status_code}")
                self.failed += 1
                return False
                
        except Exception as e:
            print(f"✗ 请求异常: {str(e)}")
            self.failed += 1
            return False
    
    def run_all_tests(self):
        """运行所有测试"""
        print("\n" + "=" * 60)
        print("开始API测试")
        print("=" * 60)
        
        # 1. 健康检查
        self.test_health()
        
        # 2. 单个查询测试
        test_queries = [
            ("XX系统的负责人是谁？", "Query_Asset"),
            ("新员工入职流程怎么走？", "Query_Scenario"),
            ("最近的数据安全法更新了什么？", "Query_Hotspot"),
            ("客户管理系统应用在哪些场景？", "Find_Relationship"),
            ("今天天气怎么样？", "OOD"),
        ]
        
        for query, expected_intent in test_queries:
            self.test_query(query, expected_intent)
            time.sleep(0.5)  # 避免请求过快
        
        # 3. 批量查询测试
        batch_queries = [q for q, _ in test_queries[:3]]
        self.test_batch_query(batch_queries)
        
        # 4. 统计接口测试
        self.test_stats()
        
        # 输出测试结果
        print("\n" + "=" * 60)
        print("测试结果汇总")
        print("=" * 60)
        print(f"✓ 通过: {self.passed}")
        print(f"✗ 失败: {self.failed}")
        print(f"总计: {self.passed + self.failed}")
        print(f"通过率: {self.passed/(self.passed+self.failed)*100:.1f}%")
        print("=" * 60)


if __name__ == "__main__":
    # 运行测试
    tester = APITester("http://localhost:8000")
    tester.run_all_tests()

