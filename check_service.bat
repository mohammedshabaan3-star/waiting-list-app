@echo off
powershell -ExecutionPolicy Bypass -File "d:\waiting_list_contracts_app\service_monitor.ps1" -Action status
pause