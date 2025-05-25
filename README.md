# Salary Report

Salary Report — это утилита на Python 3.9+ для генерации отчётов о зарплатах сотрудников на основе данных из CSV-файлов. Поддерживает форматы вывода JSON и CSV. Подходит для бухгалтерии и автоматизации внутренней аналитики.


## Возможности

- Обработка одного или нескольких CSV-файлов с данными сотрудников.
- Генерация двух типов отчётов:
  - `payout` — расчёт итоговых выплат каждому сотруднику на основе отработанных часов и ставки.
  - `average_rate` — расчёт средней ставки по отделам.
- Поддержка вывода отчёта в JSON и CSV.
- Устойчивость к ошибкам данных: пропущенные поля и некорректные значения игнорируются.
- Полноценное покрытие тестами через `pytest`.

---

## Установка

1. Клонирование репозитория:

```bash
git clone https://github.com/mikhail-medvedev90/salary_report.git
cd salary_report
```

2. Создание виртуального окружения:

```bash
python3 -m venv venv
source venv/bin/activate  # Для Windows: venv\Scripts\activate
```

3. Установить зависимости:

```bash
pip install -r requirements.txt
```

## Запуск скрипта

1. Генерация отчёта по выплатам (payout):

```bash
python3 -m src.main examples/data.csv --report payout
python3 -m src.main examples/data.csv examples/data1.csv --report payout
python3 -m src.main examples/data.csv --report payout --output reports/result_payout.csv # Сохранение отчёта в reports/result_payout.csv
```

2. Генерация отчёта по средней ставке (average_rate):

```bash
python3 -m src.main examples/data.csv --report average_rate
python3 -m src.main examples/data.csv examples/data2.csv --report average_rate
python3 -m src.main examples/data.csv --report average_rate --output reports/result_average_rate.csv # Сохранение отчёта в reports/result_average_rate.csv
```

3. Пример CSV-файла:

```csv
id,name,department,hours_worked,hourly_rate
1,John Doe,Engineering,40,25
2,Jane Smith,Engineering,38,30
3,Bob Johnson,Sales,42,20
```

## Тестирование

```bash
pytest
```
