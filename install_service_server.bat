@echo off
echo Installing Streamlit Service on Windows Server...

REM Check if running as administrator
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo This script must be run as Administrator!
    pause
    exit /b 1
)

REM Download NSSM
if not exist "nssm.exe" (
    echo Downloading NSSM...
    powershell -ExecutionPolicy Bypass -Command "Invoke-WebRequest -Uri 'https://nssm.cc/release/nssm-2.24.zip' -OutFile 'nssm.zip'; Expand-Archive -Path 'nssm.zip' -DestinationPath '.'; Copy-Item 'nssm-2.24\win64\nssm.exe' 'nssm.exe'; Remove-Item 'nssm-2.24' -Recurse -Force; Remove-Item 'nssm.zip'"
)

REM Install and configure service
nssm install StreamlitWaitingList "d:\waiting_list_contracts_app\start_streamlit_server.bat"
nssm set StreamlitWaitingList DisplayName "Streamlit Waiting List Service"
nssm set StreamlitWaitingList Description "Streamlit application for hospital waiting list contracts management"
nssm set StreamlitWaitingList Start SERVICE_AUTO_START
nssm set StreamlitWaitingList AppDirectory "d:\waiting_list_contracts_app"
nssm set StreamlitWaitingList AppStdout "d:\waiting_list_contracts_app\logs\service.log"
nssm set StreamlitWaitingList AppStderr "d:\waiting_list_contracts_app\logs\error.log"
nssm set StreamlitWaitingList AppRotateFiles 1
nssm set StreamlitWaitingList AppRotateOnline 1
nssm set StreamlitWaitingList AppRotateBytes 1048576

REM Configure auto-restart on failure
nssm set StreamlitWaitingList AppExit Default Restart
nssm set StreamlitWaitingList AppRestartDelay 5000
nssm set StreamlitWaitingList AppThrottle 1500

REM Create logs directory
if not exist "logs" mkdir logs

REM Configure firewall
netsh advfirewall firewall add rule name="Streamlit App" dir=in action=allow protocol=TCP localport=8501

REM Start service
nssm start StreamlitWaitingList

echo Service installed successfully!
echo Access: http://localhost:8501 or http://[server-ip]:8501
pause