@echo off
cd /d "d:\waiting_list_contracts_app"
python -m streamlit run waiting_list_contracts_app.py --server.port 8501 --server.address 0.0.0.0 --server.headless true --server.enableCORS false --server.enableXsrfProtection true --browser.gatherUsageStats false --server.maxUploadSize 50