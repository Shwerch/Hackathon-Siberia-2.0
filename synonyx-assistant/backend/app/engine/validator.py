from app.models.state import FlowDraft, SessionState


INDUSTRIAL_PROTOCOLS = {"MQTT", "Modbus TCP", "МЭК 104"}
MAX_SYNONYX_RULES = 256


def validate_and_normalize_state(state: SessionState) -> list[str]:
    """Проверяет инженерные ограничения методики и возвращает список предупреждений."""
    warnings: list[str] = []

    if len(state.networks) > 2:
        warnings.append("Кейс ограничен двумя сетями и одной границей. Выберите пару сетей.")
        state.status = "unsupported"
        return warnings

    for flow in state.flows:
        if flow.protocol in INDUSTRIAL_PROTOCOLS and flow.mode == "one-way":
            flow.mode = "two-way"
            warnings.append(
                f"Для промышленного протокола {flow.protocol} однонаправленный режим не поддерживается; "
                "применено двунаправленное правило с фильтрацией по структуре протокола."
            )
        if flow.is_ntp:
            flow.type = "data"
            flow.protocol = "UDP"
            flow.port = flow.port or 123
            flow.mode = "one-way"

        if flow.send_method == "usb" or flow.receive_method == "usb":
            # USB-порт есть только на Узле А (со стороны открытой сети)
            if flow.send_method == "usb":
                flow.send_protocol = "USB"
            if flow.receive_method == "usb":
                flow.receive_protocol = "USB"

    return warnings
