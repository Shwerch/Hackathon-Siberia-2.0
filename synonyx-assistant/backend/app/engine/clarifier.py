from app.models.state import ClarifyOption, ClarifyQuestion, SessionState


def build_clarifications(state: SessionState) -> list[ClarifyQuestion]:
    questions: list[ClarifyQuestion] = []

    if len(state.networks) < 2 or state.both_initially_open:
        questions.append(
            ClarifyQuestion(
                question_id="q_closed_net",
                field="closed_network",
                text="Какая из двух сетей является более защищаемой (закрытым сегментом)?",
                options=[
                    ClarifyOption(id="first", label="Первая сеть"),
                    ClarifyOption(id="second", label="Вторая сеть"),
                    ClarifyOption(id="both_open", label="Обе сети открытые"),
                ],
            )
        )

    for flow in state.flows:
        if flow.type == "data" and not flow.protocol:
            questions.append(
                ClarifyQuestion(
                    question_id=f"q_proto_{flow.flow_key}",
                    flow_key=flow.flow_key,
                    field="protocol",
                    text=f"По какому протоколу передаются данные ({flow.description or flow.flow_key})?",
                    options=[
                        ClarifyOption(id="TCP", label="TCP"),
                        ClarifyOption(id="UDP", label="UDP"),
                        ClarifyOption(id="MQTT", label="MQTT"),
                        ClarifyOption(id="Modbus TCP", label="Modbus TCP"),
                        ClarifyOption(id="МЭК 104", label="МЭК 104"),
                    ],
                )
            )
        if flow.type == "data" and not flow.mode:
            questions.append(
                ClarifyQuestion(
                    question_id=f"q_mode_{flow.flow_key}",
                    flow_key=flow.flow_key,
                    field="mode",
                    text=f"Нужна ли передача в обратную сторону ({flow.description or flow.flow_key})?",
                    options=[
                        ClarifyOption(id="one-way", label="Нет, только в одну сторону"),
                        ClarifyOption(id="two-way", label="Да, нужна (запрос-ответ или в обе стороны)"),
                    ],
                )
            )
        if flow.type == "file":
            if not flow.send_method:
                questions.append(
                    ClarifyQuestion(
                        question_id=f"q_send_{flow.flow_key}",
                        flow_key=flow.flow_key,
                        field="send_method",
                        text=f"Как файлы будут отправляться ({flow.description or flow.flow_key})?",
                        options=[
                            ClarifyOption(id="manual", label="Вручную (SFTP)"),
                            ClarifyOption(id="pull", label="Автоматически по расписанию из хранилища (PULL)"),
                            ClarifyOption(id="usb", label="С USB-носителя (флешки)"),
                        ],
                    )
                )
            if not flow.receive_method:
                questions.append(
                    ClarifyQuestion(
                        question_id=f"q_recv_{flow.flow_key}",
                        flow_key=flow.flow_key,
                        field="receive_method",
                        text=f"Куда и как файлы должны попадать на принимающей стороне ({flow.description or flow.flow_key})?",
                        options=[
                            ClarifyOption(id="manual", label="Заберёт человек вручную (SFTP)"),
                            ClarifyOption(id="push", label="Автоматически в хранилище при поступлении (PUSH)"),
                            ClarifyOption(id="usb", label="Выгрузка на USB-носитель"),
                        ],
                    )
                )
            if flow.isolate_groups is None:
                questions.append(
                    ClarifyQuestion(
                        question_id=f"q_iso_{flow.flow_key}",
                        flow_key=flow.flow_key,
                        field="isolate_groups",
                        text="Могут ли пользователи видеть принятые файлы друг друга или нужны разные профили проверок?",
                        options=[
                            ClarifyOption(id="shared", label="Общая видимость и одинаковые проверки"),
                            ClarifyOption(id="isolated", label="Нужно разделять доступ или проверки"),
                        ],
                    )
                )

    return questions
