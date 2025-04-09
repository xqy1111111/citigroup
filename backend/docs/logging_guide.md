# 日志系统使用指南

本文档详细说明了项目的日志系统设计、使用方法和生产环境的最佳实践。

## 1. 系统概述

我们的日志系统提供以下核心功能：

- **多级别日志记录**：DEBUG、INFO、WARNING、ERROR、CRITICAL
- **日志轮转**：基于时间和大小的日志文件轮转
- **请求追踪**：为每个 HTTP 请求分配唯一的追踪 ID
- **结构化输出**：支持 JSON 格式的结构化日志
- **异常捕获**：全局异常处理和记录
- **性能监控**：记录请求处理时间

## 2. 基本用法

### 2.1 获取日志记录器

```python
import logging

# 获取模块专用记录器
logger = logging.getLogger(__name__)  # 推荐，使用模块名作为记录器名

# 或者获取功能专用记录器
db_logger = logging.getLogger('db')  # 数据库操作专用
api_logger = logging.getLogger('api')  # API调用专用
access_logger = logging.getLogger('access')  # 访问日志专用
```

### 2.2 记录不同级别的日志

```python
# 调试信息（开发环境）
logger.debug("详细的调试信息，包含变量: %s", variable_name)

# 一般信息
logger.info("一般操作信息，如用户登录")

# 警告信息
logger.warning("警告信息，如配置不推荐使用")

# 错误信息
logger.error("错误信息，如数据库连接失败")

# 异常信息（包含堆栈跟踪）
try:
    # 一些可能引发异常的代码
    result = 1 / 0
except Exception as e:
    logger.exception("出现异常，详细信息: %s", str(e))
    # 注意: logger.exception() 自动包含堆栈跟踪

# 严重错误
logger.critical("严重错误，系统无法正常运行")
```

### 2.3 使用请求追踪 ID

```python
from core.logging import set_trace_id

# 手动设置追踪ID
set_trace_id("your-custom-trace-id")

# 使用中间件时，无需手动设置，系统会自动为每个请求生成
# 记录的日志会自动包含当前上下文的追踪ID
logger.info("这条日志会包含当前上下文的追踪ID")
```

## 3. 高级用法

### 3.1 结构化日志记录

```python
# 推荐使用关键字参数的方式记录结构化数据
logger.info("用户操作", user_id=user_id, action="login", ip_address=client_ip)

# 这样在启用JSON格式输出时，这些字段会被正确地结构化
```

### 3.2 自定义日志过滤器

```python
from logging import Filter

class MyCustomFilter(Filter):
    def filter(self, record):
        # 添加自定义字段
        record.custom_field = "自定义值"
        return True

# 获取记录器并添加过滤器
logger = logging.getLogger(__name__)
logger.addFilter(MyCustomFilter())
```

## 4. 生产环境配置

在生产环境中，我们推荐以下配置：

### 4.1 环境变量设置

```bash
# 设置应用环境
export APP_ENV=production

# 日志级别
export LOG_LEVEL=INFO

# 日志目录路径（可选）
export LOG_DIR=/var/log/myapp
```

### 4.2 日志收集与聚合

在生产环境中，建议设置一个集中的日志管理系统，如 ELK Stack (Elasticsearch, Logstash, Kibana) 或 Graylog。

**使用 Filebeat 收集日志**:

```yaml
# filebeat.yml 示例配置
filebeat.inputs:
  - type: log
    enabled: true
    paths:
      - /var/log/myapp/*.log
    json.keys_under_root: true
    json.add_error_key: true

output.elasticsearch:
  hosts: ["elasticsearch:9200"]
```

### 4.3 容器环境配置

在 Docker 或 Kubernetes 环境中，我们建议将日志输出到标准输出/错误流，然后由容器运行时收集：

```python
# 配置日志输出到标准输出
import logging
import sys

handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
root = logging.getLogger()
root.addHandler(handler)
```

### 4.4 性能考虑

- 在高流量环境中，考虑使用异步日志记录
- 调整日志级别，生产环境通常使用 INFO 级别
- 定期清理旧日志文件，避免磁盘空间耗尽
- 考虑使用日志采样技术，仅记录一部分请求的详细信息

## 5. 安全考虑

日志中应避免记录以下敏感信息：

- 用户密码或私钥
- 访问令牌或会话标识符
- 个人身份信息(PII)
- 信用卡号码或其他财务信息
- 健康医疗信息

如需记录包含敏感信息的请求，应进行适当的信息脱敏：

```python
# 脱敏示例
def mask_sensitive_data(data, field_name):
    if field_name in data and data[field_name]:
        if isinstance(data[field_name], str):
            if len(data[field_name]) > 6:
                data[field_name] = data[field_name][:3] + "****" + data[field_name][-3:]
            else:
                data[field_name] = "******"
    return data
```

## 6. 从开发到生产的区别

| 特性       | 开发环境       | 生产环境                 |
| ---------- | -------------- | ------------------------ |
| 日志级别   | DEBUG          | INFO                     |
| 日志格式   | 文本格式       | JSON 格式                |
| 日志输出   | 控制台 + 文件  | 文件 + 日志收集系统      |
| 轮转策略   | 较小的日志文件 | 更大的文件，更长的保留期 |
| 追踪详细度 | 全面追踪       | 采样追踪                 |
| 监控集成   | 可选           | 必需（告警和监控）       |

## 7. 监控与告警

在生产环境中，建议将日志系统与监控和告警系统集成，以便及时发现和响应问题：

1. 配置基于日志内容的告警规则
2. 监控 ERROR 和 CRITICAL 级别的日志数量
3. 设置 API 响应时间阈值告警
4. 监控日志文件大小和磁盘空间

## 8. 故障排查

常见的日志相关问题和解决方案：

1. **日志文件过大**：调整轮转策略，减少保留时间
2. **日志记录影响性能**：使用异步日志，调整日志级别
3. **无法找到特定请求的日志**：使用 trace_id 进行过滤
4. **敏感信息泄露**：实施数据脱敏，审核日志内容

## 9. 最佳实践

1. 使用模块级别的记录器 (`logging.getLogger(__name__)`)
2. 为每个环境使用适当的日志级别
3. 始终包含上下文信息（用户 ID、操作类型等）
4. 定期审查和清理日志
5. 将错误和异常信息记录为结构化数据
6. 在 API 边界和关键组件处记录性能指标

## 10. 与其他系统集成

### 10.1 与 APM 工具集成

我们的日志系统可以与 APM (Application Performance Monitoring) 工具集成，如 New Relic、Datadog 或 Elastic APM，提供更全面的应用监控：

```python
# 需要添加相应的APM库
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

# 设置追踪提供者
provider = TracerProvider()
processor = BatchSpanProcessor(OTLPSpanExporter())
provider.add_span_processor(processor)
trace.set_tracer_provider(provider)

# 获取追踪器
tracer = trace.get_tracer(__name__)
```

### 10.2 与业务指标集成

日志系统可以与业务指标监控系统集成，帮助跟踪关键业务指标：

```python
# 示例：记录业务操作并包含指标
def process_payment(payment_amount, user_id):
    try:
        # 处理支付
        result = payment_service.process(payment_amount, user_id)

        # 记录业务指标
        logger.info(
            "支付处理完成",
            user_id=user_id,
            payment_amount=payment_amount,
            processing_time=result.processing_time,
            status=result.status,
            metric="payment_processed"  # 标记为业务指标
        )

        return result
    except Exception as e:
        logger.exception(
            "支付处理失败",
            user_id=user_id,
            payment_amount=payment_amount,
            error=str(e),
            metric="payment_failed"  # 标记为业务指标
        )
        raise
```
