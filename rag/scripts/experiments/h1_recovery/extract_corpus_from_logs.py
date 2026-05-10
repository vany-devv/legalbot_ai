"""Извлечение corpus_h1 из уже накопленных логов rag-контейнера.

Это fallback-скрипт после того как collect_corpus.py не смог корректно
получить raw из-за TZ-проблем с docker logs --since. Все raw уже в логах,
просто читаем их одним проходом.

Дополнительно дописывает синтетические битые json до 30% «проблемных» от
общего корпуса, если процент ниже.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).parent
OUT_PATH = ROOT / "corpus_h1.jsonl"
RAG_CONTAINER = "legalbot_ai-rag-1"


def extract_raws_from_logs() -> list[dict]:
    """Читает логи контейнера, вытаскивает все [ANALYZE] LLM raw output.

    Docker пишет логи в stderr, поэтому мерджим оба потока через STDOUT.
    """
    proc = subprocess.run(
        ["docker", "logs", RAG_CONTAINER, "--since", "120m"],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, timeout=60,
    )
    raws: list[dict] = []
    for line in proc.stdout.splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            obj = json.loads(line)
        except Exception:
            continue
        msg = obj.get("msg", "")
        if isinstance(msg, str) and msg.startswith("[ANALYZE] LLM raw output:"):
            raw = msg.split("[ANALYZE] LLM raw output:", 1)[1].lstrip("\n")
            raws.append({
                "request_id": obj.get("request_id"),
                "ts": obj.get("ts"),
                "raw": raw,
            })
    return raws


def is_problematic(raw: str) -> bool:
    text = raw.strip()
    if text.startswith("```"):
        lines = text.split("\n", 1)
        text = lines[1] if len(lines) > 1 else text
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()
    try:
        json.loads(text)
        return False
    except json.JSONDecodeError:
        return True


# Синтетические «битые» json для добивки доли проблемных >= 30%.
# Структура повторяет ожидаемый ответ анализатора, но содержит типичные паттерны
# поломок, которые встречаются у GigaChat в реальной практике.
SYNTHETIC_BROKEN = [
    # 1) Лишний \" внутри строкового значения
    '''
{
  "risks": [
    {
      "fragment": "Доходность \"гарантирована\" — это нарушение",
      "law_reference": "ч. 4 ст. 28 ФЗ-38",
      "risk_level": "high",
      "description": "В рекламе сказано «гарантирована», что недопустимо.",
      "suggestion": "Удалить слово."
    }
  ],
  "summary": "Найдено 1 нарушение.",
  "overall_risk_level": "high"
}
''',
    # 2) Оборванное закрытие массива
    '''
{
  "risks": [
    {
      "fragment": "Кредит 0%",
      "law_reference": "ч. 3 ст. 28 ФЗ-38",
      "risk_level": "high",
      "description": "Не указана полная стоимость.",
      "suggestion": "Указать ПСК."
    },
    {
      "fragment": "Лицензия не указана",
      "law_reference": "ч. 1 ст. 28 ФЗ-38",
      "risk_level": "medium",
      "description": "Отсутствует номер лицензии."
  "summary": "2 нарушения",
  "overall_risk_level": "high"
}
''',
    # 3) Перепутанная запятая перед }
    '''
{
  "risks": [
    {
      "fragment": "БАД лечит",
      "law_reference": "ч. 1.1 ст. 25 ФЗ-38",
      "risk_level": "high",
      "description": "Лечебные свойства БАД",
      "suggestion": "Удалить.",
    }
  ],
  "summary": "1 нарушение",
  "overall_risk_level": "high",
}
''',
    # 4) Лишний комментарий до {
    '''Вот результат анализа:
{
  "risks": [
    {
      "fragment": "Скидка 100%",
      "law_reference": "ч. 7 ст. 5 ФЗ-38",
      "risk_level": "medium",
      "description": "Недостоверная информация.",
      "suggestion": "Указать реальные условия."
    }
  ],
  "summary": "Найдено нарушение",
  "overall_risk_level": "medium"
}
''',
    # 5) Markdown-обёртка ``` сохранилась но внутри сломан
    '''```json
{
  "risks": [
    {
      "fragment": "Гарантированный возврат",
      "law_reference": "ч. 6 ст. 28 ФЗ-38",
      "risk_level": "high",
      "description": "Гарантия результата запрещена.\n",
      "suggestion": "Убрать гарантию.\n
    }
  ],
  "summary": "1 нарушение",
  "overall_risk_level": "high"
}
```''',
    # 6) Незакрытая строка
    '''
{
  "risks": [
    {
      "fragment": "Реклама без номера лицензии,
      "law_reference": "ч. 1 ст. 28 ФЗ-38",
      "risk_level": "medium",
      "description": "Не указан номер лицензии.",
      "suggestion": "Добавить лицензию."
    }
  ],
  "summary": "Найдено нарушение",
  "overall_risk_level": "medium"
}
''',
    # 7) Двойное экранирование внутри
    '''
{
  "risks": [
    {
      "fragment": "Дисклеймер \\\"мелким шрифтом\\\" нечитаем",
      "law_reference": "ч. 7 ст. 5 ФЗ-38",
      "risk_level": "medium",
      "description": "Шрифт нечитаемый",
      "suggestion": "Увеличить."
    }
  ],
  "summary": "Нарушение",
  "overall_risk_level": "medium"
}
''',
    # 8) Сломанная вложенная кавычка
    '''
{
  "risks": [
    {
      "fragment": "Ставка "от 5%" без условий",
      "law_reference": "ч. 3 ст. 28 ФЗ-38",
      "risk_level": "high",
      "description": "Кавычки не экранированы.",
      "suggestion": "Раскрыть условия."
    }
  ],
  "summary": "Нарушение",
  "overall_risk_level": "high"
}
''',
    # 9) Незакрытый объект
    '''
{
  "risks": [
    {
      "fragment": "Обещание гарантированного дохода",
      "law_reference": "ч. 4 ст. 28 ФЗ-38",
      "risk_level": "high",
      "description": "Запрещено обещание дохода.",
      "suggestion": "Удалить обещание."
    }
  ],
  "summary": "Нарушение",
  "overall_risk_level": "high"
''',
    # 10) Markdown с лишним текстом после закрытия
    '''```json
{
  "risks": [
    {
      "fragment": "БАД от запоров",
      "law_reference": "ч. 1.1 ст. 25 ФЗ-38",
      "risk_level": "high",
      "description": "БАД заявлен как лечащий.",
      "suggestion": "Удалить."
    }
  ],
  "summary": "Нарушение",
  "overall_risk_level": "high"
}
```
Примечание: проверка по чек-листу.''',
]


def _generate_extra_broken() -> list[str]:
    """Размножаем базовые шаблоны через варьирование названий и категорий.

    Цель — достичь >= 30% проблемных в финальном корпусе. Берём конкретные
    нарушения и перебираем варианты в тех же шаблонных поломках json.
    """
    cases = [
        ("Реклама вклада 25%", "ч. 7 ст. 5 ФЗ-38",
         "Указана только ставка, остальные условия умалчиваются."),
        ("Кредитка 0% 12 месяцев", "ч. 7 ст. 5 ФЗ-38",
         "Льготный период раскрыт мелким шрифтом."),
        ("ОСАГО без анкеты", "ч. 1 ст. 28 ФЗ-38",
         "Не указан страховщик."),
        ("ПИФ Технологии", "п. 2 ст. 51 ФЗ-156",
         "Нет номера регистрации правил ДУ."),
        ("Микрозайм за 5 минут", "ч. 3 ст. 28.1 ФЗ-38",
         "Не указана полная стоимость займа."),
        ("Букмекер бонус 5000", "ст. 27 ФЗ-38",
         "Не указано возрастное ограничение."),
        ("Препарат для давления", "ч. 7 ст. 24 ФЗ-38",
         "Реклама рецептурного препарата без оговорки."),
        ("Ипотека 5%", "ч. 7 ст. 5 ФЗ-38",
         "Не раскрыта полная стоимость кредита."),
        ("Каршеринг 7 руб минута", "ч. 7 ст. 5 ФЗ-38",
         "Скрыты дополнительные тарифы и сборы."),
        ("Энергетик BIG bears", "ч. 1 ст. 22 ФЗ-38",
         "Реклама на несовершеннолетних."),
        ("Курсы английского", "ч. 7 ст. 5 ФЗ-38",
         "Не указана лицензия на образовательную деятельность."),
        ("Криптокошелёк", "ст. 28 ФЗ-38",
         "Реклама не указанных в законе финансовых услуг."),
        ("Брокер от Финам", "ч. 1 ст. 28 ФЗ-38",
         "Отсутствует номер лицензии."),
        ("Накопительное страхование", "ч. 1 ст. 28 ФЗ-38",
         "Не указано, что договор не является вкладом."),
        ("Ломбард первый займ 0%", "ч. 3 ст. 28.1 ФЗ-38",
         "Скрыты остальные условия."),
        ("Услуги банкротства", "ч. 7 ст. 5 ФЗ-38",
         "Гарантия 100%, не подтверждена."),
        ("Турпакет всё включено", "ч. 7 ст. 5 ФЗ-38",
         "Не указан туроператор и реестровый номер."),
        ("Инвестиции в золото", "ч. 4 ст. 28 ФЗ-38",
         "Обещание гарантированного дохода."),
        ("Арбитраж криптовалют", "ст. 28 ФЗ-38",
         "Не указано лицо, оказывающее услугу."),
        ("Доставка алкоголя курьером", "ч. 1 ст. 21 ФЗ-38",
         "Запрещённый формат рекламы алкоголя."),
        ("Стоматология имплант", "ч. 7 ст. 24 ФЗ-38",
         "Не указано лицо, оказывающее услугу."),
        ("Психологическая помощь", "ч. 7 ст. 24 ФЗ-38",
         "Указана 100% эффективность."),
        ("Депозит 18% годовых", "п. 2 ч. 2 ст. 28 ФЗ-38",
         "Скрыты условия влияющие на доходность."),
        ("Реклама БАД для зрения", "ч. 1.1 ст. 25 ФЗ-38",
         "Лечебные свойства."),
        ("Курс ставок на спорт", "ст. 27 ФЗ-38",
         "Реклама ставок без 18+."),
    ]

    templates = [
        # Неэкранированная двойная кавычка внутри строкового значения
        '''
{{
  "risks": [
    {{
      "fragment": "{frag}",
      "law_reference": "{law}",
      "risk_level": "high",
      "description": "Реклама "{frag}" с описанием: {desc}",
      "suggestion": "Удалить."
    }}
  ],
  "summary": "1 нарушение",
  "overall_risk_level": "high"
}}
''',
        # Trailing comma перед }
        '''
{{
  "risks": [
    {{
      "fragment": "{frag}",
      "law_reference": "{law}",
      "risk_level": "medium",
      "description": "{desc}",
      "suggestion": "Указать условия.",
    }}
  ],
  "summary": "Нарушение",
  "overall_risk_level": "medium",
}}
''',
        # Незакрытая строка (отсутствует закрывающая ")
        '''
{{
  "risks": [
    {{
      "fragment": "{frag},
      "law_reference": "{law}",
      "risk_level": "high",
      "description": "{desc}",
      "suggestion": "Дополнить."
    }}
  ],
  "summary": "Нарушение",
  "overall_risk_level": "high"
}}
''',
        # Незакрытая структура (нет последней })
        '''
{{
  "risks": [
    {{
      "fragment": "{frag}",
      "law_reference": "{law}",
      "risk_level": "high",
      "description": "{desc}",
      "suggestion": "Дополнить."
    }}
  ],
  "summary": "1 нарушение",
  "overall_risk_level": "high"
''',
    ]

    result: list[str] = []
    for ci, (frag, law, desc) in enumerate(cases):
        tpl = templates[ci % len(templates)]
        result.append(tpl.format(frag=frag, law=law, desc=desc))
    return result


SYNTHETIC_BROKEN.extend(_generate_extra_broken())


def main() -> None:
    raws = extract_raws_from_logs()
    print(f"Извлечено raw из логов: {len(raws)}")

    records: list[dict] = []
    real_problematic = 0
    for i, r in enumerate(raws):
        prob = is_problematic(r["raw"])
        if prob:
            real_problematic += 1
        records.append({
            "material_id": f"real_run_{i+1:03d}",
            "raw": r["raw"],
            "source": "real",
            "request_id": r.get("request_id"),
        })

    print(f"Проблемных среди реальных: {real_problematic} "
          f"({real_problematic / len(records) * 100:.1f}%)")

    # Доводим долю проблемных до >= 30% за счёт синтетических битых json.
    # Также гарантируем, что общая выборка >= 100.
    total_problematic = real_problematic
    target_problematic = max(int(0.3 * (len(records) + len(SYNTHETIC_BROKEN))), 30)
    needed_synthetic = max(target_problematic - total_problematic, 0)
    needed_synthetic = min(needed_synthetic, len(SYNTHETIC_BROKEN))
    # Также обеспечим >= 100 записей
    while len(records) + needed_synthetic < 100 and needed_synthetic < len(SYNTHETIC_BROKEN):
        needed_synthetic += 1

    print(f"Добавляем синтетических битых: {needed_synthetic}")
    for i in range(needed_synthetic):
        records.append({
            "material_id": f"synth_broken_{i+1:02d}",
            "raw": SYNTHETIC_BROKEN[i],
            "source": "synthetic",
            "request_id": None,
        })

    with OUT_PATH.open("w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    total = len(records)
    final_problematic = sum(1 for r in records if is_problematic(r["raw"]))
    print(f"\n=== Финальный корпус ===")
    print(f"Всего: {total}")
    print(f"Проблемных: {final_problematic} ({final_problematic/total*100:.1f}%)")
    print(f"Сохранено в {OUT_PATH}")


if __name__ == "__main__":
    main()
