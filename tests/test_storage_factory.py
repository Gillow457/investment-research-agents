from research_agents.storage import ReportStore, create_report_store


def test_storage_factory_uses_sqlite_for_file_paths(tmp_path) -> None:
    store = create_report_store(str(tmp_path / "reports.sqlite3"))

    assert isinstance(store, ReportStore)
