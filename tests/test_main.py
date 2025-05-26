import logging
import os
import subprocess
import json
import sys
from pathlib import Path
from io import StringIO

import pytest

from src.main import main, parse_csv, PayoutReport, write_output, AverageRateReport


def test_script_runs(tmp_path):
    """Тестирует генерацию JSON-отчета типа 'payout' через subprocess."""
    csv_file = tmp_path / "data.csv"
    csv_file.write_text("id,email,name,department,hours_worked,hourly_rate\n1,a@test.com,Alice,HR,160,50\n")
    result_file = tmp_path / "result.json"

    env = os.environ.copy()
    env["PYTHONPATH"] = str(Path(__file__).parent.parent.resolve())

    subprocess.run([
        "python3", "-m", "src.main",
        str(csv_file),
        "--report", "payout",
        "--output", str(result_file)
    ], check=True, env=env)

    assert result_file.exists()

def test_average_rate_report(monkeypatch, tmp_path):
    """Тестирует генерацию отчета 'average_rate' без указания output-файла."""
    test_csv = tmp_path / "data.csv"
    test_csv.write_text("id,email,name,department,hours_worked,salary\n"
                        "1,a@example.com,A,A,100,30\n"
                        "2,b@example.com,B,A,150,60\n"
                        "3,c@example.com,C,B,120,45\n")

    monkeypatch.setattr(sys, "argv", ["main.py", str(test_csv), "--report", "average_rate"])
    captured = StringIO()
    monkeypatch.setattr("sys.stdout", captured)
    main()
    output = captured.getvalue()
    assert "average_rate" in output
    assert '"A": 45.0' in output
    assert '"B": 45.0' in output

def test_csv_output_payout(monkeypatch, tmp_path):
    """Тестирует генерацию payout-отчета с сохранением в формате CSV."""
    test_csv = tmp_path / "data.csv"
    out_file = tmp_path / "report.csv"
    test_csv.write_text("id,email,name,department,hours_worked,salary\n1,a@example.com,A,A,100,30\n")
    monkeypatch.setattr(sys, "argv", ["main.py", str(test_csv), "--report", "payout", "--output", str(out_file)])
    main()
    assert out_file.exists()
    content = out_file.read_text()
    assert "id,name,department,payout" in content
    assert "1,A,A,3000" in content

def test_csv_output_average_rate(monkeypatch, tmp_path):
    """Тестирует генерацию average_rate-отчета с сохранением в формате CSV."""
    test_csv = tmp_path / "data.csv"
    out_file = tmp_path / "report.csv"
    test_csv.write_text("id,email,name,department,hours_worked,salary\n"
                        "1,a@example.com,A,A,100,30\n"
                        "2,b@example.com,B,A,150,60\n")
    monkeypatch.setattr(sys, "argv", ["main.py", str(test_csv), "--report", "average_rate", "--output", str(out_file)])
    main()
    assert out_file.exists()
    content = out_file.read_text()
    assert "department,average_rate" in content
    assert "A,45.0" in content

def test_parse_csv_invalid_file(caplog):
    """Тестирует обработку отсутствующего файла в parse_csv."""
    with pytest.raises(SystemExit) as exc_info:
        parse_csv("nonexistent.csv")
    assert exc_info.value.code == 1
    assert "Файл не найден: nonexistent.csv" in caplog.text

def test_parse_csv_malformed_lines(tmp_path, caplog):
    """Тестирует обработку строк с неверным количеством полей."""
    csv_file = tmp_path / "bad.csv"
    # Добавляем 1 валидную строку и 2 невалидные
    csv_file.write_text("header1,header2\nvalue1\nvalue1,value2,value3\nvalid1,valid2")
    records = parse_csv(str(csv_file))

    assert len(records) == 1  # Обработана только последняя строка
    assert "несоответствием количества полей" in caplog.text
    assert caplog.text.count("WARNING") == 2  # Два предупреждения

def test_parse_csv_empty_file(tmp_path, caplog):
    """Тестирует обработку пустого CSV-файла."""
    csv_file = tmp_path / "empty.csv"
    csv_file.write_text("")
    records = parse_csv(str(csv_file))

    assert len(records) == 0
    assert "Ошибка чтения файла" not in caplog.text  # Пустой файл не вызывает ошибок
    assert "header" not in caplog.text  # Должен корректно обработать отсутствие данных

def test_payout_zero_hours(monkeypatch):
    """Тестирует расчёт выплат при нулевом количестве часов."""
    records = [{"id": "1", "hourly_rate": "100"}]
    report = PayoutReport().generate(records)
    assert report["results"][0]["payout"] == 0.0

def test_average_rate_missing_fields(caplog):
    """Тестирует AverageRateReport с записями без полей ставки"""
    records = [
        {"department": "IT"},
        {"department": "HR", "hours_worked": "160"}
    ]
    report = AverageRateReport().generate(records)

    assert report["results"] == {}  # Покрывает строки 212-213
    assert "отсутствует поле ставки" in caplog.text

def test_payout_report_data_processing_error(caplog):
    """Тестирует обработку исключений в PayoutReport.generate"""
    records = [{"id": "1", "hours_worked": "invalid", "hourly_rate": "50"}]
    report = PayoutReport().generate(records)

    assert len(report["results"]) == 0  # Покрывает строку 94
    assert "Ошибка обработки записи" in caplog.text
