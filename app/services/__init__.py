# app/services/__init__.py
# 服务层入口文件 - 统一导出所有服务类，便于其他模块导入

from .image_service import ImageService

# 当前导出的所有服务类（未来新增服务时在此处添加）
__all__ = [
    "ImageService",
    # 示例：未来新增其他服务时在此添加
    # "InquiryService",
    # "CartService",
    # "MailService",
]

# 可选：添加版本信息或文档字符串（便于维护）
"""
服务层（Services）设计原则：
- 所有业务逻辑封装在此层，不直接写在路由或模型中
- 每个服务类负责单一职责（Single Responsibility Principle）
- 使用依赖注入或工厂模式访问数据库/配置等资源
"""
