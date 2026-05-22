from research_agents.storage.postgres import PostgresReportStore
from research_agents.storage.sqlite import BatchItemRecord, BatchRecord, ReportRecord, ReportStore


def create_report_store(database_url: str):
    if database_url.startswith(("postgres://", "postgresql://", "postgresql+psycopg://")):
        normalized = database_url.replace("postgres://", "postgresql+psycopg://", 1)
        if normalized.startswith("postgresql://"):
            normalized = normalized.replace("postgresql://", "postgresql+psycopg://", 1)
        return PostgresReportStore(normalized)
    return ReportStore(database_url)


__all__ = ["BatchItemRecord", "BatchRecord", "PostgresReportStore", "ReportRecord", "ReportStore", "create_report_store"]
