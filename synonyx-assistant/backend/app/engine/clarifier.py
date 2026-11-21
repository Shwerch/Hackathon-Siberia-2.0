from app.models.state import ClarifyOption, ClarifyQuestion, SessionState


def build_clarifications(state: SessionState) -> tuple[list[ClarifyQuestion], list[str]]:
    """Возвращает (новые вопросы, полный список неизвестных параметров для unknowns)."""
    questions: list[ClarifyQuestion] = []
    unknowns: list[str] = []
    dismissed = set(state.dismissed_questions)

    def add_q(q: ClarifyQuestion, unknown_label: str) -> None:
        unknowns.append(unknown_label)
        if q.question_id not in dismissed:
            questions.append(q)

    if len(state.networks) < 2 or state.both_initially_open:
        add_q(
            ClarifyQuestion(
                question_id="q_closed_net",
                field="closed_network",
                text="Какая из двух сетей является более защищаемой (закрытым сегментом)?",
                options=[
                    ClarifyOption(id="first", label="Первая сеть"),
                    ClarifyOption(id="second", label="Вторая сеть"),
                    ClarifyOption(id="both_open", label="Обе сети открытые"),
                ],
            ),
            "Защищаемая (закрытая) сторона не определена",
        )

    for flow in state.flows:
        label = flow.description or flow.flow_key
        if flow.type == "data" and not flow.protocol:
            add_q(
                ClarifyQuestion(
                    question_id=f"q_proto_{flow.flow_key}",
                    flow_key=flow.flow_key,
                    field="protocol",
                    text=f"По какому протоколу передаются данные ({label})?",
                    options=[
                        ClarifyOption(id="TCP", label="TCP"),
                        ClarifyOption(id="UDP", label="UDP"),
                        ClarifyOption(id="MQTT", label="MQTT"),
                        ClarifyOption(id="Modbus TCP", label="Modbus TCP"),
                        ClarifyOption(id="МЭК 104", label="МЭК 104"),
                    ],
                ),
                f"Протокол потока «{label}» неизвестен",
            )
        if flow.type == "data" and not flow.mode:
            add_q(
                ClarifyQuestion(
                    question_id=f"q_mode_{flow.flow_key}",
                    flow_key=flow.flow_key,
                    field="mode",
                    text=f"Нужна ли передача в обратную сторону ({label})?",
                    options=[
                        ClarifyOption(id="one-way", label="Нет, только в одну сторону"),
                        ClarifyOption(id="two-way", label="Да, нужна (запрос-ответ или в обе стороны)"),
                    ],
                ),
                f"Необходимость обратного обмена для «{label}» неизвестна",
            )
        if flow.type == "file":
            if not flow.send_method:
                add_q(
                    ClarifyQuestion(
                        question_id=f"q_send_{flow.flow_key}",
                        flow_key=flow.flow_key,
                        field="send_method",
                        text=f"Как файлы будут отправляться ({label})?",
                        options=[
                            ClarifyOption(id="manual", label="Вручную (SFTP)"),
                            ClarifyOption(id="pull", label="Автоматически по расписанию из хранилища (PULL)"),
                            ClarifyOption(id="usb", label="С USB-носителя (флешки)"),
                        ],
                    ),
                    f"Способ отправки файлов («{label}») неизвестен",
                )
            if not flow.receive_method:
                add_q(
                    ClarifyQuestion(
                        question_id=f"q_recv_{flow.flow_key}",
                        flow_key=flow.flow_key,
                        field="receive_method",
                        text=f"Куда и как файлы должны попадать на принимающей стороне ({label})?",
                        options=[
                            ClarifyOption(id="manual", label="Заберёт человек вручную (SFTP)"),
                            ClarifyOption(id="push", label="Автоматически в хранилище при поступлении (PUSH)"),
                            ClarifyOption(id="usb", label="Выгрузка на USB-носитель"),
                        ],
                    ),
                    f"Способ получения файлов («{label}») неизвестен",
                )
            # Если пользователь один (manual_users_count == 1), разделение видимости между пользователями не требуется
            if flow.isolate_groups is None and flow.manual_users_count != 1:
                add_q(
                    ClarifyQuestion(
                        question_id=f"q_iso_{flow.flow_key}",
                        flow_key=flow.flow_key,
                        field="isolate_groups",
                        text="Могут ли пользователи видеть принятые файлы друг друга или нужны разные профили проверок?",
                        options=[
                            ClarifyOption(id="shared", label="Общая видимость и одинаковые проверки"),
                            ClarifyOption(id="isolated", label="Нужно разделять доступ или проверки"),
                        ],
                    ),
                    f"Требования к разделению доступа/проверок («{label}») неизвестны",
                )

    return questions, unknowns
