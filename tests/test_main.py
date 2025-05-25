import os
import subprocess
# import json
import sys
from pathlib import Path
from io import StringIO
from src.main import main


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
