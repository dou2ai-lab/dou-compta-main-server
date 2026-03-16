FROM python:3.11-slim as base

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    tesseract-ocr \
    tesseract-ocr-fra \
    tesseract-ocr-eng \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Service-specific targets
FROM base as auth-service
ENV PYTHONPATH=/app
CMD ["uvicorn", "services.auth.main:app", "--host", "0.0.0.0", "--port", "8000"]

FROM base as expense-service
ENV PYTHONPATH=/app
CMD ["uvicorn", "services.expense.main:app", "--host", "0.0.0.0", "--port", "8000"]

FROM base as admin-service
ENV PYTHONPATH=/app
CMD ["uvicorn", "services.admin.main:app", "--host", "0.0.0.0", "--port", "8000"]

FROM base as audit-service
ENV PYTHONPATH=/app
CMD ["uvicorn", "services.audit.main:app", "--host", "0.0.0.0", "--port", "8000"]

FROM base as anomaly-service
ENV PYTHONPATH=/app
CMD ["uvicorn", "services.anomaly_service.main:app", "--host", "0.0.0.0", "--port", "8000"]

FROM base as rag-service
ENV PYTHONPATH=/app
CMD ["uvicorn", "services.rag_service.main:app", "--host", "0.0.0.0", "--port", "8000"]

FROM base as erp-service
ENV PYTHONPATH=/app
CMD ["uvicorn", "services.erp_service.main:app", "--host", "0.0.0.0", "--port", "8000"]

FROM base as gdpr-service
ENV PYTHONPATH=/app
CMD ["uvicorn", "services.gdpr_service.main:app", "--host", "0.0.0.0", "--port", "8000"]

FROM base as performance-service
ENV PYTHONPATH=/app
CMD ["uvicorn", "services.performance.main:app", "--host", "0.0.0.0", "--port", "8000"]

FROM base as security-service
ENV PYTHONPATH=/app
CMD ["uvicorn", "services.security.main:app", "--host", "0.0.0.0", "--port", "8000"]

FROM base as monitoring-service
ENV PYTHONPATH=/app
CMD ["uvicorn", "services.monitoring.main:app", "--host", "0.0.0.0", "--port", "8000"]

FROM base as file-service
ENV PYTHONPATH=/app
CMD ["uvicorn", "services.file_service.main:app", "--host", "0.0.0.0", "--port", "8000"]

FROM base as ocr-service
ENV PYTHONPATH=/app
CMD ["uvicorn", "services.ocr_service.main:app", "--host", "0.0.0.0", "--port", "8000"]

FROM base as llm-service
ENV PYTHONPATH=/app
CMD ["uvicorn", "services.llm_service.main:app", "--host", "0.0.0.0", "--port", "8000"]

FROM base as llm-worker
ENV PYTHONPATH=/app
CMD ["python", "-m", "services.llm_service.worker"]

FROM base as policy-service
ENV PYTHONPATH=/app
CMD ["uvicorn", "services.policy_service.main:app", "--host", "0.0.0.0", "--port", "8000"]

FROM base as report-service
ENV PYTHONPATH=/app
CMD ["uvicorn", "services.report_service.main:app", "--host", "0.0.0.0", "--port", "8000"]

FROM base as urssaf-service
ENV PYTHONPATH=/app
CMD ["uvicorn", "services.urssaf_service.main:app", "--host", "0.0.0.0", "--port", "8000"]

FROM base as vat-service
ENV PYTHONPATH=/app
CMD ["uvicorn", "services.vat_service.main:app", "--host", "0.0.0.0", "--port", "8000"]

FROM base as accounting-service
ENV PYTHONPATH=/app
CMD ["uvicorn", "services.accounting_service.main:app", "--host", "0.0.0.0", "--port", "8000"]

FROM base as dossier-service
ENV PYTHONPATH=/app
CMD ["uvicorn", "services.dossier_service.main:app", "--host", "0.0.0.0", "--port", "8000"]

FROM base as notification-service
ENV PYTHONPATH=/app
CMD ["uvicorn", "services.notification_service.main:app", "--host", "0.0.0.0", "--port", "8000"]

FROM base as banking-service
ENV PYTHONPATH=/app
CMD ["uvicorn", "services.banking_service.main:app", "--host", "0.0.0.0", "--port", "8000"]

FROM base as tax-service
ENV PYTHONPATH=/app
CMD ["uvicorn", "services.tax_service.main:app", "--host", "0.0.0.0", "--port", "8000"]

FROM base as analysis-service
ENV PYTHONPATH=/app
CMD ["uvicorn", "services.analysis_service.main:app", "--host", "0.0.0.0", "--port", "8000"]

FROM base as einvoice-service
ENV PYTHONPATH=/app
CMD ["uvicorn", "services.einvoice_service.main:app", "--host", "0.0.0.0", "--port", "8000"]

FROM base as payroll-service
ENV PYTHONPATH=/app
CMD ["uvicorn", "services.payroll_service.main:app", "--host", "0.0.0.0", "--port", "8000"]

FROM base as collection-service
ENV PYTHONPATH=/app
CMD ["uvicorn", "services.collection_service.main:app", "--host", "0.0.0.0", "--port", "8000"]

FROM base as agents-service
ENV PYTHONPATH=/app
CMD ["uvicorn", "services.agents_service.main:app", "--host", "0.0.0.0", "--port", "8000"]














