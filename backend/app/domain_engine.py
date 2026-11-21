from __future__ import annotations

from typing import Any, Optional

from .drawio_generator import generate_drawio_xml
from .schemas import (
    ClarificationQuestion,
    FileProtocolSide,
    FileUsersRange,
    NetworkNode,
    ProjectResult,
    QuestionAnswerPayload,
    QuestionOption,
    RuleItem,
    SessionStatus,
    SourceRef,
)

INDUSTRIAL_PROTOCOLS = {"MQTT", "MODBUS TCP", "МЭК 104", "МЭК 60870-5-104", "IEC 104"}

SYSTEM_PROMPT = """Ты — инженерный ИИ-ассистент по продукту СКИО «Синоникс» версии 1.9 («АйТи Бастион»).
Твоя задача:
1) Понять намерение пользователя:
   - "design": проектирование или уточнение обмена между 2 сетями;
   - "question_about_scheme": вопрос по уже построенной схеме (без изменения конфигурации);
   - "edit_scheme": просьба изменить существующую схему;
   - "fact_question": фактический вопрос о возможностях/ограничениях «Синоникса»;
   - "out_of_scope": запрос на 3+ сети или неподдерживаемую архитектуру.
2) Извлечь из диалога параметры потоков и НЕ выдумывать неизвестные IP, порты, протоколы, способы передачи файлов и проверки.
3) Учитывать контекст базы знаний (synonyx_base) и в ответах на фактические вопросы опираться только на него.

Верни строго JSON следующей структуры:
{
  "intent": "design | question_about_scheme | edit_scheme | fact_question | out_of_scope",
  "assistant_text": "Понятный ответ пользователю на русском языке",
  "edit_ambiguous": false,
  "edit_invalid_reason": null,
  "networks": {
    "open_name": "Офисная сеть или null",
    "closed_name": "Закрытая сеть цеха или null",
    "both_open": false,
    "protected_side_confirmed": false
  },
  "flows": [
    {
      "type": "data | file",
      "from": "open | closed",
      "to": "open | closed",
      "mode": "one-way | two-way | unknown",
      "protocol": "TCP | UDP | MQTT | Modbus TCP | МЭК 104 | NTP | SFTP | FTP | SMB | USB | unknown",
      "port": 514,
      "receiver_id": "уникальное имя получателя для объединения правил",
      "description": "краткое описание потока",
      "file_open_method": "manual SFTP | PULL SFTP/FTP/SMB | PUSH SFTP/FTP/SMB | USB | unknown",
      "file_closed_method": "manual SFTP | PULL SFTP/FTP/SMB | PUSH SFTP/FTP/SMB | USB | unknown",
      "checks_open": ["маска имени", "размер", "ICAP: внешний антивирус"],
      "checks_closed": [],
      "separate_visibility": false,
      "manual_users_count": 1,
      "manual_users_range": {"min": 1, "max": 10}
    }
  ],
  "missing_fields": ["trust_open_closed", "file_methods", "file_checks", "file_users", "reverse_direction"],
  "unsupported_requests": ["встроенный антивирус"]
}"""


def build_clarification_questions(missing: list[str]) -> list[ClarificationQuestion]:
    questions: list[ClarificationQuestion] = []
    seen: set[str] = set()

    for m in missing:
        if m in seen:
            continue
        seen.add(m)

        if m == "trust_open_closed":
            questions.append(
                ClarificationQuestion(
                    question_id="q_trust",
                    text="Какая из сетей является более защищаемой (закрытым сегментом)?",
                    options=[
                        QuestionOption(id="first", label="Первая сеть"),
                        QuestionOption(id="second", label="Вторая сеть"),
                        QuestionOption(id="both_open", label="Обе открытые"),
                    ],
                )
            )
        elif m == "reverse_direction":
            questions.append(
                ClarificationQuestion(
                    question_id="q_reverse",
                    text="Нужна ли передача данных в обратную сторону?",
                    options=[
                        QuestionOption(id="one_way", label="Нет, только в одну сторону"),
                        QuestionOption(id="two_way", label="Да, нужна (ответ на запрос или обмен)"),
                    ],
                )
            )
        elif m == "file_methods":
            questions.append(
                ClarificationQuestion(
                    question_id="q_file_open",
                    text="Как файлы будут отправляться со стороны отправителя?",
                    options=[
                        QuestionOption(id="manual_sftp", label="Вручную по SFTP"),
                        QuestionOption(id="pull", label="Автоматически по расписанию (PULL)"),
                        QuestionOption(id="usb", label="С флешки (USB-носитель на Узле А)"),
                    ],
                )
            )
            questions.append(
                ClarificationQuestion(
                    question_id="q_file_closed",
                    text="Куда и как файлы должны попасть на принимающей стороне?",
                    options=[
                        QuestionOption(id="manual_sftp", label="Заберёт человек вручную (SFTP)"),
                        QuestionOption(id="push_smb", label="Автоматически в хранилище по SMB (PUSH)"),
                        QuestionOption(id="usb", label="На флешку (только на Узле А)"),
                    ],
                )
            )
        elif m == "file_checks":
            questions.append(
                ClarificationQuestion(
                    question_id="q_file_checks",
                    text="Какие проверки файлов требуются?",
                    multi_select=True,
                    options=[
                        QuestionOption(id="name_mask", label="Маска имени"),
                        QuestionOption(id="type_ext", label="Тип и расширение"),
                        QuestionOption(id="size", label="Размер"),
                        QuestionOption(id="integrity", label="Контроль целостности (подпись)"),
                        QuestionOption(id="icap", label="Внешний антивирус / песочница / DLP (ICAP)"),
                    ],
                )
            )
        elif m == "file_users":
            questions.append(
                ClarificationQuestion(
                    question_id="q_file_users",
                    text="Сколько пользователей будут вручную передавать или забирать файлы?",
                    options=[
                        QuestionOption(id="1_10", label="1–10"),
                        QuestionOption(id="11_50", label="11–50"),
                        QuestionOption(id="51_100", label="51–100"),
                        QuestionOption(id="gt_100", label="Больше 100"),
                    ],
                )
            )
    return questions


def compute_project_result(
    llm_data: dict[str, Any],
    prev_result: Optional[ProjectResult],
    kb_sources: list[SourceRef],
    answers: list[QuestionAnswerPayload],
    vendor_requests_history: list[str],
) -> tuple[SessionStatus, Optional[ProjectResult], list[ClarificationQuestion]]:
    intent = llm_data.get("intent", "design")

    # Вопрос по существующей схеме или фактологический вопрос — не меняем схему
    if intent == "question_about_scheme" and prev_result is not None:
        return "completed", prev_result, []

    if intent == "fact_question" and prev_result is None:
        return "completed", None, []

    # Неоднозначная или недопустимая правка — сохраняем последнее корректное состояние
    if llm_data.get("edit_ambiguous") or llm_data.get("edit_invalid_reason"):
        if prev_result is not None:
            return "completed", prev_result, []

    if intent == "out_of_scope" and not llm_data.get("flows"):
        return "unsupported", prev_result, []

    # Обработка ответов "Не знаю"
    any_unknown_answer = any(a.is_unknown for a in answers)
    missing = list(llm_data.get("missing_fields") or [])
    questions = [] if any_unknown_answer else build_clarification_questions(missing)

    raw_flows = llm_data.get("flows") or []
    if not raw_flows:
        if prev_result is not None:
            return "completed", prev_result, questions
        return "needs_clarification", None, questions

    net_info = llm_data.get("networks") or {}
    open_name = net_info.get("open_name") or "Открытая сеть"
    closed_name = net_info.get("closed_name") or "Закрытый сегмент"
    both_open = bool(net_info.get("both_open"))
    assumptions: list[str] = []
    unknowns: list[str] = []

    if both_open and not net_info.get("protected_side_confirmed"):
        unknowns.append("Не выбрана защищаемая сторона среди двух открытых сетей")
    elif both_open and net_info.get("protected_side_confirmed"):
        assumptions.append(f"Сеть «{closed_name}» принята за защищаемый сегмент по согласованию")

    if any_unknown_answer:
        unknowns.extend(missing)

    networks = [
        NetworkNode(id="open", name=open_name, trust="open"),
        NetworkNode(id="closed", name=closed_name, trust="closed"),
    ]

    # Детерминированный подсчёт и объединение правил
    rules: list[RuleItem] = []
    data_dedup: dict[tuple[str, str, str, Optional[int], str], RuleItem] = {}
    pull_rules_count = 0
    manual_users_exact: Optional[int] = 0
    manual_range: Optional[FileUsersRange] = None
    has_file_flows = False

    rule_id_seq = 1
    for f in raw_flows:
        ftype = f.get("type", "data")
        from_net = f.get("from", "open")
        to_net = f.get("to", "closed")
        desc = f.get("description") or "Поток обмена"

        if ftype == "data":
            proto_raw = str(f.get("protocol") or "TCP").strip()
            proto_upper = proto_raw.upper()
            port = f.get("port")
            receiver = str(f.get("receiver_id") or desc)

            if proto_upper == "NTP":
                mode = "one-way"
                from_net = "open"
                to_net = "closed"
                proto_clean = "UDP"
                port = port or 123
            elif proto_upper in INDUSTRIAL_PROTOCOLS:
                mode = "two-way"
                proto_clean = proto_raw
            else:
                mode_raw = f.get("mode", "one-way")
                mode = "two-way" if mode_raw == "two-way" else "one-way"
                proto_clean = proto_raw

            dedup_key = (from_net, to_net, proto_clean.upper(), port, receiver)
            if dedup_key not in data_dedup:
                item = RuleItem(
                    id=rule_id_seq,
                    **{"from": from_net, "to": to_net},
                    type="data",
                    mode=mode,
                    protocol=proto_clean,
                    port=port,
                    checks=[],
                    description=desc,
                    rationale=f"Поток к получателю «{receiver}» по {proto_clean}"
                    + (f" (порт {port})" if port is not None else " (порт не указан)"),
                )
                data_dedup[dedup_key] = item
                rules.append(item)
                rule_id_seq += 1

        else:
            has_file_flows = True
            open_m = str(f.get("file_open_method") or "не уточнён")
            closed_m = str(f.get("file_closed_method") or "не уточнён")
            checks_open = list(f.get("checks_open") or [])
            checks_closed = list(f.get("checks_closed") or [])
            all_checks = list(dict.fromkeys(checks_open + checks_closed))

            if "pull" in open_m.lower() or "pull" in closed_m.lower():
                pull_rules_count += 1

            if f.get("manual_users_count") is not None:
                if manual_users_exact is not None:
                    manual_users_exact += int(f["manual_users_count"])
            elif f.get("manual_users_range"):
                manual_users_exact = None
                r = f["manual_users_range"]
                manual_range = FileUsersRange(min=int(r.get("min", 1)), max=r.get("max"))
            elif "не уточн" in open_m and any_unknown_answer:
                manual_users_exact = None
                unknowns.append("Количество файловых пользователей")

            mode = "two-way" if f.get("mode") == "two-way" else "one-way"
            item = RuleItem(
                id=rule_id_seq,
                **{"from": from_net, "to": to_net},
                type="file",
                mode=mode,
                protocol=FileProtocolSide(open=open_m, closed=closed_m),
                port=None,
                checks=all_checks,
                checks_by_node={"node_a": checks_open, "node_b": checks_closed}
                if (checks_open or checks_closed)
                else None,
                description=desc,
                rationale="Файловое правило; способы на Узлах А и В настраиваются независимо.",
            )
            rules.append(item)
            rule_id_seq += 1

    # Предел ПАК: 256 правил
    if len(rules) > 256:
        return (
            "unsupported",
            ProjectResult(
                has_diagram=False,
                status_label="Превышен предел 256 правил",
                explanation=f"По расчёту требуется {len(rules)} правил, что превышает предел одного ПАК «Синоникс» (256 правил).",
                networks=networks,
                rules=[],
                rules_count=len(rules),
                unknowns=unknowns,
                assumptions=assumptions,
                requests_for_vendor=vendor_requests_history,
                sources=kb_sources,
            ),
            [],
        )

    # Расчёт file_users_count
    file_users_count: Optional[int]
    file_users_range: Optional[FileUsersRange] = None
    if not has_file_flows:
        file_users_count = 0
    elif manual_users_exact is not None:
        file_users_count = manual_users_exact + pull_rules_count
    else:
        file_users_count = None
        if manual_range:
            file_users_range = FileUsersRange(
                min=manual_range.min + pull_rules_count,
                max=(manual_range.max + pull_rules_count)
                if manual_range.max is not None
                else None,
            )

    if unknowns or (questions and not any_unknown_answer):
        status: SessionStatus = "preliminary"
        status_label = f"Предварительная оценка: минимум {len(rules)} правил"
    else:
        status = "completed"
        status_label = "Готово"

    fw_side = "both" if both_open else "open"
    result = ProjectResult(
        has_diagram=True,
        status_label=status_label,
        explanation=llm_data.get("assistant_text", ""),
        networks=networks,
        firewall={"side": fw_side},
        synonyx={"location": "closed", "node_a_faces": "open", "node_b_faces": "closed"},
        rules=rules,
        rules_count=len(rules),
        file_users_count=file_users_count,
        file_users_range=file_users_range,
        unknowns=list(dict.fromkeys(unknowns)),
        assumptions=assumptions,
        requests_for_vendor=vendor_requests_history,
        sources=kb_sources,
    )
    result.diagram_drawio_xml = generate_drawio_xml(result)
    return status, result, questions
