# H2 — извлечение текста: результаты

Корпус: 30 материалов (pdf+docx+txt).

## Сводные метрики

- success_rate: **1.000** (порог ≥ 0.9)
- preservation_rate: **0.947** (порог ≥ 0.85)
- H₀ отвергается: **ДА**

## Per-format

| Формат | n | success_rate | preservation_rate |
|---|---|---|---|
| pdf | 10 | 1.0 | 0.8917 |
| docx | 10 | 1.0 | 1.0 |
| txt | 10 | 1.0 | 0.95 |

## Материалы с проблемами

| material_id | format | attr_score | error_reason |
|---|---|---|---|
| real_01 | pdf | 0.6667 | missing_attrs:object_name |
| real_02 | pdf | 0.75 | missing_attrs:object_name |
| real_03 | pdf | 0.75 | missing_attrs:object_name |
| real_04 | pdf | 0.75 | missing_attrs:object_name |
| real_26 | txt | 0.5 | missing_attrs:object_name |