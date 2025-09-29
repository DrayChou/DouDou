#!/bin/bash
echo "🧹 清理 Flet 项目多余文件"
echo "================================"

# 删除过时的启动脚本
if [ -f "run.bat" ]; then
    echo "🗑️ 删除过时的启动脚本: run.bat"
    rm "run.bat"
fi

# 删除临时测试文件
if [ -f "test_simple.py" ]; then
    echo "🗑️ 删除临时测试文件: test_simple.py"
    rm "test_simple.py"
fi

# 删除过时的修复日志
if [ -f "BUGFIX_LOG.md" ]; then
    echo "🗑️ 删除过时的修复日志: BUGFIX_LOG.md"
    rm "BUGFIX_LOG.md"
fi

# 删除 Electron 时代的环境配置
if [ -f ".env" ]; then
    echo "🗑️ 删除 Electron 环境配置: .env"
    rm ".env"
fi

if [ -f ".env.example" ]; then
    echo "🗑️ 删除 Electron 环境配置模板: .env.example"
    rm ".env.example"
fi

# 删除 uv 相关配置
if [ -f ".python-version" ]; then
    echo "🗑️ 删除 uv Python 版本配置: .python-version"
    rm ".python-version"
fi

# 删除 FunASR 性能测试（可选）
if [ -f "test_funasr_timing.py" ]; then
    echo "🗑️ 删除 FunASR 性能测试: test_funasr_timing.py"
    rm "test_funasr_timing.py"
fi

# 删除 Claude 配置目录（可选）
if [ -d ".claude" ]; then
    echo "🗑️ 删除 Claude 配置目录: .claude/"
    rm -rf ".claude"
fi

echo ""
echo "✅ 清理完成！保留的核心文件:"
echo "   - flet_app.py (主应用)"
echo "   - funasr_server.py (语音识别服务)"
echo "   - download_models.py (模型下载)"
echo "   - requirements.txt (依赖配置)"
echo "   - run_flet_simple.bat (启动脚本)"
echo "   - SETUP_GUIDE.md (设置指南)"
echo "   - FLET_THREAD_SAFETY_FIX.md (技术文档)"
echo "   - simple_test.py (基础测试)"
echo "   - test_startup.py (启动测试)"
echo ""
echo "🎯 项目现在更简洁，只保留 Flet 版本必需的文件！"