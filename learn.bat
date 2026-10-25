@echo off
chcp 65001 >nul
title Learn Fast 学习三件套
cd /d "%~dp0"

:menu
cls
echo ==========================================
echo    Learn Fast 学习三件套
echo ------------------------------------------
echo    1. 学习教练   对话陪练，每讲完必考你（需 API Key）
echo    2. 研究员     给个主题，自动查资料出材料（需 API Key）
echo    3. 今日复习   看看今天有什么到期的（不需要 Key）
echo    4. 排复习计划 想记多久，告诉你哪天复习（不需要 Key）
echo    0. 退出
echo ==========================================
set /p choice=输入数字后回车:
if "%choice%"=="1" goto coach
if "%choice%"=="2" goto research
if "%choice%"=="3" goto today
if "%choice%"=="4" goto plan
if "%choice%"=="0" goto end
if "%choice%"=="" goto end
goto menu

:coach
if "%LEARN_FAST_API_KEY%"=="" set /p LEARN_FAST_API_KEY=第一次用请粘贴智谱API Key（open.bigmodel.cn 免费注册）:
python agent\learning_coach.py
pause
goto menu

:research
if "%LEARN_FAST_API_KEY%"=="" set /p LEARN_FAST_API_KEY=第一次用请粘贴智谱API Key（open.bigmodel.cn 免费注册）:
set /p topic=想学什么主题（如：SQL 入门）:
python agent\researcher.py "%topic%"
pause
goto menu

:today
python agent\butler.py
pause
goto menu

:plan
set /p days=想记住多少天（如 90）:
python scripts\review_schedule.py --goal-days %days%
pause
goto menu

:end
