# 翻译队列和自定义Prompt开发方案

## 项目概述

在现有QuQu语音助手系统中增加翻译功能，并开放System Prompt给用户自定义。该方案基于现有任务队列架构，采用分层配置和可插拔任务处理器设计。

## 技术目标

1. **独立翻译队列**：支持语音识别后的文本翻译
2. **配置复用机制**：翻译服务可复用AI修正配置，也可独立配置
3. **自定义Prompt**：用户可编辑AI修正和翻译的System Prompt
4. **向后兼容**：不影响现有功能，渐进式升级

## 架构设计

### 1. 配置架构重构

#### 1.1 新的配置结构
```json
{
  "ai_services": {
    "default": {
      "api_key": "xxx",
      "base_url": "http://localhost:11435/v1",
      "model_name": "jan-v1-4b"
    },
    "correction": {
      "system_prompt": "你是语音识别文本修正专家...",
      "system_prompt_file": "prompts/correction.txt"
    },
    "translation": {
      "api_key": "",  // 空则继承default
      "base_url": "", // 空则继承default
      "model_name": "qwen-turbo", // 可指定不同模型
      "target_language": "en",
      "system_prompt": "你是专业翻译助手...",
      "system_prompt_file": "prompts/translation.txt"
    }
  },
  "enable_ai_optimization": true,
  "enable_translation": false,
  "language": "zh",
  "use_vad": true,
  "use_punc": true
}
```

#### 1.2 配置继承逻辑
- 三层继承：`default → task_type → runtime`
- 空值自动继承上级配置
- 运行时可动态覆盖

### 2. 任务处理器架构

#### 2.1 抽象基类设计
```python
class BaseTaskProcessor(ABC):
    """任务处理器基类"""
    task_type: str

    @abstractmethod
    def process(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理任务核心逻辑"""
        pass

    def get_ai_config(self, base_config: Dict) -> Dict:
        """获取合并后的AI配置"""
        default_config = base_config.get("ai_services", {}).get("default", {})
        task_config = base_config.get("ai_services", {}).get(self.task_type, {})

        # 合并配置，空值使用默认值
        merged = {**default_config}
        for k, v in task_config.items():
            if v:  # 只覆盖非空值
                merged[k] = v
        return merged
```

#### 2.2 具体处理器实现
- `CorrectionProcessor`：AI文本修正处理器
- `TranslationProcessor`：文本翻译处理器

### 3. 任务队列扩展

#### 3.1 新增任务类型
```python
@dataclass
class TranslationTask:
    """翻译任务"""
    original_text: str
    source_language: str
    target_language: str
    task_id: str
    created_at: float
    priority: TaskPriority = TaskPriority.NORMAL
    status: TaskStatus = TaskStatus.PENDING
    translated_text: Optional[str] = None
    error: Optional[str] = None
    future: Optional[Future] = None
```

#### 3.2 TaskManager扩展
- 新增 `translation_queue` 优先级队列
- 新增 `translation_pool` 线程池
- 统一任务处理流程 `_process_generic_task()`
- 支持动态任务处理器注册

## 实施计划

### Phase 1: 配置系统重构 (优先级: 高)

#### 1.1 ConfigManager增强
- [ ] 修改 `DEFAULT_CONFIG` 支持新的配置结构
- [ ] 实现 `get_ai_service_config(task_type)` 方法
- [ ] 添加 `load_prompt(task_type)` 支持文件和内联Prompt
- [ ] 实现配置继承逻辑 `merge_configs(default, specific)`

#### 1.2 配置文件迁移
- [ ] 创建配置迁移逻辑，保持向后兼容
- [ ] 更新默认配置文件 `doudou_settings.json`

### Phase 2: 任务处理器架构 (优先级: 高)

#### 2.1 基础架构
- [ ] 创建 `src/core/task_processors/` 目录
- [ ] 实现 `BaseTaskProcessor` 抽象基类
- [ ] 实现 `TaskProcessorRegistry` 注册器

#### 2.2 现有功能重构
- [ ] 创建 `CorrectionProcessor` 处理器
- [ ] 将现有AI优化逻辑迁移到 `CorrectionProcessor`
- [ ] 更新 `TaskManager` 使用新的处理器架构

### Phase 3: 翻译功能实现 (优先级: 中)

#### 3.1 翻译任务处理器
- [ ] 创建 `TranslationTask` 数据类
- [ ] 实现 `TranslationProcessor` 处理器
- [ ] 添加多语言支持和翻译质量检测

#### 3.2 队列集成
- [ ] 扩展 `TaskManager` 添加翻译队列和线程池
- [ ] 实现 `submit_translation_task()` 方法
- [ ] 添加翻译任务统计信息

### Phase 4: UI界面更新 (优先级: 中)

#### 4.1 设置界面增强
- [ ] 在 `src/ui/dialogs.py` 中添加翻译配置区域
- [ ] 添加AI服务高级配置折叠面板
- [ ] 实现Prompt文本编辑器（支持多行输入）

#### 4.2 主界面集成
- [ ] 在主界面添加翻译开关和目标语言选择
- [ ] 显示翻译结果和状态
- [ ] 添加翻译任务监控显示

### Phase 5: 测试和优化 (优先级: 低)

#### 5.1 功能测试
- [ ] 单元测试：配置继承逻辑
- [ ] 集成测试：任务队列和处理流程
- [ ] 端到端测试：完整识别->修正->翻译流程

#### 5.2 性能优化
- [ ] 队列大小和线程数调优
- [ ] AI API调用优化（批量、缓存等）
- [ ] 错误处理和重试机制

## 技术细节

### 1. 配置文件位置管理
- 默认配置：`docs/config/doudou_settings.json`
- 用户配置：`项目根目录/doudou_settings.json`
- Prompt文件：`prompts/correction.txt`, `prompts/translation.txt`

### 2. 错误处理策略
- AI服务不可用时的降级处理
- 配置验证和错误提示
- 任务失败重试机制
- 队列溢出处理

### 3. 性能考虑
- 翻译队列独立线程池，不阻塞识别流程
- Prompt缓存减少重复加载
- 配置热更新支持

## 兼容性说明

1. **向后兼容**：现有配置自动迁移，无需用户重新配置
2. **渐进启用**：翻译功能默认关闭，用户手动启用
3. **配置复用**：未配置翻译服务时自动使用AI修正配置
4. **UI降级**：新增配置项对现有功能无影响

## 风险评估

### 高风险
- 配置结构变更可能导致现有配置失效
- 任务队列架构变更影响稳定性

### 中风险
- AI API调用增加可能导致性能下降
- 新功能可能引入新的bug

### 低风险
- UI界面变更影响用户体验
- 文档更新不及时

## 成功标准

1. **功能完整性**：翻译功能正常工作，配置系统稳定
2. **性能要求**：不影响现有识别性能，翻译响应时间<3秒
3. **用户体验**：配置界面友好，操作简单直观
4. **代码质量**：架构清晰，易于扩展和维护

## 交付物

1. **代码实现**：所有新增和修改的源代码文件
2. **配置文件**：更新后的默认配置和示例配置
3. **文档更新**：API文档、用户手册、开发文档
4. **测试用例**：单元测试和集成测试代码
5. **部署脚本**：配置迁移和环境更新脚本

---

*本文档将随开发进展持续更新*