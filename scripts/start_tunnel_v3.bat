@echo off
chcp 65001 >nul
title Cloudflare Tunnel -> v2rayN HTTP (10808)
echo ==========================================
echo  Cloudflare Tunnel 启动器 (调试版，绝不闪退)
echo  目标: http://localhost:10808 (v2rayN HTTP)
echo ==========================================
echo.

:: 1. 定位 cloudflared.exe
set "CF_EXE="
if exist "%~dp0cloudflared.exe" (
    set "CF_EXE=%~dp0cloudflared.exe"
    echo [OK] 使用脚本同级目录: %CF_EXE%
) else (
    where cloudflared >nul 2>&1
    if %errorlevel% equ 0 (
        set "CF_EXE=cloudflared"
        echo [OK] 使用 PATH 中的 cloudflared
    ) else (
        echo [错误] 找不到 cloudflared.exe
        echo   请把 cloudflared.exe 放到脚本同级目录: %~dp0
        echo   或放到 C:\Windows (需管理员)
        goto :ERR_END
    )
)

:: 2. 验证 cloudflared 能跑
echo [检查] 测试 cloudflared 可执行...
"%CF_EXE%" --version
if %errorlevel% neq 0 (
    echo [错误] cloudflared 运行失败 (可能是 32/64 位不匹配)
    echo   你下载的是 386 版，请改下载 amd64 版:
    echo   https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe
    goto :ERR_END
)

:: 3. 探测 v2rayN 端口
echo [检查] 探测 v2rayN HTTP 端口 %TUNNEL_PORT%...
powershell -Command "Test-NetConnection -ComputerName localhost -Port %TUNNEL_PORT% -InformationLevel Quiet" >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] %TUNNEL_PORT% 端口未监听
    echo   请在 v2rayN: 设置 -> 参数设置 -> 本地监听端口 -> HTTP 端口 = %TUNNEL_PORT%
    goto :ERR_END
)
echo [OK] 端口 %TUNNEL_PORT% 正常监听
echo.

:: 4. 启动隧道 (输出重定向到临时文件，stderr 也捕获)
set "TMPLOG=%TEMP%\cf_tunnel_%RANDOM%.log"
echo [启动] 正在建立隧道... (日志: %TMPLOG%)
echo.

start /B "" "%CF_EXE%" tunnel --url http://localhost:%TUNNEL_PORT% 2>"%TMPLOG%" >nul

:: 5. 轮询日志文件提取 URL (最多等 40 秒)
set "TUNNEL_URL="
set "WAIT=0"
:POLL
if %WAIT% geq 40 (
    echo [超时] 40 秒未捕获到地址
    echo ----- 完整日志 -----
    type "%TMPLOG%" 2>nul
    echo ---------------------
    goto :ERR_END
)

for /f "tokens=*" %%u in ('type "%TMPLOG%" 2^>nul ^| findstr /r /c:"https://.*\.trycloudflare\.com"') do (
    set "TUNNEL_URL=%%u"
    goto :GOT_URL
)

timeout /t 1 /nobreak >nul
set /a WAIT+=1
goto :POLL

:GOT_URL
if not defined TUNNEL_URL (
    echo [错误] 未捕获到 URL
    type "%TMPLOG%" 2>nul
    goto :ERR_END
)

:: 清洗 ANSI 色码
set "CLEAN_URL=%TUNNEL_URL%"
set "CLEAN_URL=%CLEAN_URL:[0m=%"
set "CLEAN_URL=%CLEAN_URL:[0;32m=%"
set "CLEAN_URL=%CLEAN_URL:[32m=%"
for /f "tokens=1" %%u in ("%CLEAN_URL%") do set "CLEAN_URL=%%u"

echo.
echo ==========================================
echo [成功] 隧道已建立！
echo 公网地址: %CLEAN_URL%
echo ==========================================
echo.
echo %CLEAN_URL% | clip
echo [已复制到剪贴板] %CLEAN_URL%
echo.
echo GitHub Secrets 填写:
echo   HTTPS_PROXY = %CLEAN_URL%
echo   HTTP_PROXY  = %CLEAN_URL%
echo.
echo ==========================================
echo 此窗口关闭即停止隧道，请保持开启
echo 按 Ctrl+C 随时停止
echo ==========================================

cmd /k "title Tunnel Running: %CLEAN_URL% & echo 隧道运行中... 关闭窗口即停止"
goto :END

:ERR_END
echo.
echo ==========================================
echo [失败] 请阅读上方错误信息，修复后重新双击
echo ==========================================
pause
:END