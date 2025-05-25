import argparse
import json
import sys
import logging
from typing import List, Dict, Optional
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

VALID_RATE_FIELDS = {"hourly_rate", "rate", "salary"}


def parse_csv(file_path: str) -> List[Dict[str, str]]:
    logging.info(f"Чтение файла: {file_path}")
    records = []
    try:
        with open(file_path, encoding="utf-8") as f:
            header = [h.strip() for h in f.readline().strip().split(",")]
            for line in f:
                values = [v.strip() for v in line.strip().split(",")]
                if len(values) != len(header):
                    logging.warning(f"Пропущена строка с несоответствием количества полей: {line.strip()}")
                    continue
                record = dict(zip(header, values))
                records.append(record)
    except FileNotFoundError:
        logging.error(f"Файл не найден: {file_path}")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Ошибка чтения файла {file_path}: {e}")
        sys.exit(1)
    return records


class BaseReport:
    def generate(self, records: List[Dict[str, str]]) -> Dict:
        raise NotImplementedError


class PayoutReport(BaseReport):
    def generate(self, records: List[Dict[str, str]]) -> Dict:
        logging.info("Формируется отчёт payout")
        result = []
        for r in records:
            try:
                hours = float(r.get("hours_worked", 0))
                rate_field = next((f for f in VALID_RATE_FIELDS if f in r), None)
                if not rate_field:
                    logging.warning(f"Пропущена запись (отсутствует поле ставки): {r}")
                    continue
                rate = float(r[rate_field])
                payout = hours * rate
                result.append({
                    "id": r.get("id", ""),
                    "name": r.get("name", ""),
                    "department": r.get("department", ""),
                    "payout": round(payout, 2)
                })
            except Exception as e:
                logging.warning(f"Ошибка обработки записи: {r} — {e}")
        return {"report": "payout", "results": result}


class AverageRateReport(BaseReport):
    def generate(self, records: List[Dict[str, str]]) -> Dict:
        logging.info("Формируется отчёт average_rate")
        departments = {}
        for r in records:
            try:
                rate_field = next((f for f in VALID_RATE_FIELDS if f in r), None)
                if not rate_field:
                    logging.warning(f"Пропущена запись (отсутствует поле ставки): {r}")
                    continue
                dept = r.get("department", "")
                rate = float(r[rate_field])
                departments.setdefault(dept, []).append(rate)
            except Exception as e:
                logging.warning(f"Ошибка обработки записи: {r} — {e}")
        averages = {
            dept: round(sum(rates) / len(rates), 2)
            for dept, rates in departments.items()
            if rates
        }
        return {"report": "average_rate", "results": averages}


def write_output(data: Dict, output_path: Optional[str]):
    if output_path:
        ext = Path(output_path).suffix.lower()
        try:
            if ext == ".json":
                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
            elif ext == ".csv":
                with open(output_path, "w", encoding="utf-8") as f:
                    if data["report"] == "payout":
                        f.write("id,name,department,payout\n")
                        for r in data["results"]:
                            f.write(f'{r["id"]},{r["name"]},{r["department"]},{r["payout"]}\n')
                    elif data["report"] == "average_rate":
                        f.write("department,average_rate\n")
                        for dept, avg in data["results"].items():
                            f.write(f"{dept},{avg}\n")
                    else:
                        logging.error("Неподдерживаемый формат отчета для CSV")
                        sys.exit(1)
            else:
                logging.error("Неподдерживаемый формат файла вывода")
                sys.exit(1)
            logging.info(f"Отчёт успешно сохранён в {output_path}")
        except Exception as e:
            logging.error(f"Ошибка записи в файл {output_path}: {e}")
            sys.exit(1)
    else:
        print(json.dumps(data, indent=2, ensure_ascii=False))


def main():
    parser = argparse.ArgumentParser(description="Генерация отчётов по зарплатам сотрудников")
    parser.add_argument("files", nargs="+", help="Один или несколько CSV-файлов")
    parser.add_argument("--report", required=True, help="Тип отчёта: payout или average_rate")
    parser.add_argument("--output", help="Путь к выходному файлу (json или csv)")
    args = parser.parse_args()

    logging.info(f"Тип отчёта: {args.report}")
    logging.info(f"Файлы на вход: {args.files}")

    all_records = []
    for file in args.files:
        all_records.extend(parse_csv(file))

    reports = {
        "payout": PayoutReport(),
        "average_rate": AverageRateReport(),
    }

    if args.report not in reports:
        logging.error("Неподдерживаемый тип отчёта. Доступные типы: payout, average_rate")
        sys.exit(1)

    report = reports[args.report].generate(all_records)
    write_output(report, args.output)


if __name__ == "__main__":
    main()
