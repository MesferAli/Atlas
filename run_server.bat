@echo off
cd /d "C:\Users\m_alm\Documents\Atlas\Pasted-Enterprise-AI\Pasted-Enterprise-AI"
set PYTHONPATH=C:\Users\m_alm\Documents\Atlas\Pasted-Enterprise-AI\Pasted-Enterprise-AI\src
echo PYTHONPATH=%PYTHONPATH%
echo Starting Atlas API server on http://localhost:8080
python -m uvicorn atlas.api.main:app --host 0.0.0.0 --port 8081
