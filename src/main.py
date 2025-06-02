"""
Модуль для генерации отчётов по зарплатам сотрудников на основе данных из CSV-файлов.

Основные функции:
- Парсинг CSV-файлов с информацией о сотрудниках
- Генерация отчётов:
  - Выплаты (payout): расчёт зарплаты по часам работы
  - Средняя ставка (average_rate): расчёт средней ставки по отделам
- Экспорт результатов в JSON или CSV форматы

Ключевые классы:
- BaseReport: абстрактный базовый класс для отчётов
- PayoutReport: реализация расчёта выплат
- AverageRateReport: реализация расчёта средней ставки

Требования к входным данным:
- CSV файлы должны содержать обязательные поля:
  - hours_worked: отработанные часы
  - Одно из полей ставки: hourly_rate, rate или salary
  - Дополнительные поля: id, name, department
"""

import argparse
import json
import sys
import logging
from pathlib import Path

from src.constants import REPORT_NAMES, VALID_RATE_FIELDS

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


def parse_csv(file_path: str) -> list[dict[str, str]]:
    """
    Парсит CSV-файл и преобразует его в список словарей.

    Параметры:
        file_path (str): Путь к CSV-файлу

    Возвращает:
        list[dict[str, str]]: Список записей в виде словарей

    Исключения:
        FileNotFoundError: Если файл не существует
        Exception: При общих ошибках чтения файла

    Логирует:
        Предупреждения о строках с несоответствующим количеством полей
        Ошибки при проблемах с чтением файла
    """

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
    """Абстрактный базовый класс для генерации отчётов."""

    def generate(self, records: list[dict[str, str]]) -> dict:
        """
        Абстрактный метод для генерации отчёта.

        Параметры:
            records (list[dict[str, str]]): Список записей сотрудников

        Исключения:
            NotImplementedError: При прямом вызове метода базового класса
        """

        raise NotImplementedError("Метод generate должен быть реализован в дочерних классах")


class PayoutReport(BaseReport):
    """Класс для генерации отчёта по выплатам сотрудников."""

    def generate(self, records: list[dict[str, str]]) -> dict:
        """
        Рассчитывает выплаты для каждого сотрудника.

        Параметры:
            records (list[dict[str, str]]): Список записей сотрудников

        Возвращает:
            dict: Результаты в формате:
                {
                    "report": "payout",
                    "results": [
                        {
                            "id": "сотрудника",
                            "name": "имя",
                            "department": "отдел",
                            "payout": сумма
                        }, ...
                    ]
                }

        Логирует:
            Предупреждения о записях с отсутствующими полями ставок
            Ошибки обработки записей
        """

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
    """Класс для генерации отчёта по средней ставке по отделам."""

    def generate(self, records: list[dict[str, str]]) -> dict:
        """
        Рассчитывает среднюю ставку для каждого отдела.

        Параметры:
            records (list[dict[str, str]]): Список записей сотрудников

        Возвращает:
            dict: Результаты в формате:
                {
                    "report": "average_rate",
                    "results": {
                        "отдел1": средняя_ставка,
                        ...
                    }
                }

        Логирует:
            Предупреждения о записях с отсутствующими полями ставок
            Ошибки обработки записей
        """

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
        averages = {dept: round(sum(rates) / len(rates), 2) for dept, rates in departments.items() if rates}
        return {"report": "average_rate", "results": averages}


def write_output(data: dict, output_path: str | None):
    """
    Записывает результаты отчёта в файл или выводит в stdout.

    Параметры:
        data (dict): Данные отчёта
        output_path (str | None): Путь для сохранения файла

    Поддерживаемые форматы:
        - JSON (.json)
        - CSV (.csv)

    Логирует:
        Ошибки при неверном формате файла
        Ошибки записи в файл
    """

    if output_path:
        ext = Path(output_path).suffix.lower()
        try:
            if ext == ".json":
                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=4, ensure_ascii=False)
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
        print(json.dumps(data, indent=4, ensure_ascii=False))


def main():
    """
    Основная функция для обработки аргументов командной строки и запуска генерации отчётов.

    Аргументы командной строки:
        files: Один или несколько CSV-файлов
        --report: Тип отчёта (payout | average_rate)
        --output: Путь к выходному файлу (опционально)

    Логирует:
        Информацию о выбранном отчёте и входных файлах
        Ошибки при неверных параметрах
    """

    parser = argparse.ArgumentParser(description="Генерация отчётов по зарплатам сотрудников")
    parser.add_argument("files", nargs="+", help="Один или несколько CSV-файлов")
    parser.add_argument("--report", required=True, choices=REPORT_NAMES, help="Тип отчёта: payout или average_rate")
    parser.add_argument("--output", help="Путь к выходному файлу (json или csv)")
    args = parser.parse_args()

    logging.info(f"Тип отчёта: {args.report}")
    logging.info(f"Файлы на вход: {args.files}")

    all_records = []
    for file in args.files:
        all_records.extend(parse_csv(file))

    match args.report:
        case "payout":
            report_class = PayoutReport()
        case "average_rate":
            report_class = AverageRateReport()
        case _:
            report_class = BaseReport()

    report = report_class.generate(all_records)
    write_output(report, args.output)


if __name__ == "__main__":
    main()
