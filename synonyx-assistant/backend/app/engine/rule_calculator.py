import re
from app.models.state import DeviceItem, FlowDraft, RuleItem, SessionState
from app.engine.validator import MAX_SYNONYX_RULES


def _slug(text: str) -> str:
    s = re.sub(r"[^a-zA-Zа-яА-Я0-9]+", "-", text.lower()).strip("-")
    return s or "dev"


def recalculate_rules(state: SessionState) -> None:
    """Детерминированно пересчитывает devices, rules, rules_count и file_users_count."""
    devices_map: dict[tuple[str, str], DeviceItem] = {}
    rules: list[RuleItem] = []
    rule_id = 1

    def ensure_device(net_id: str, name: str, hint: str = "") -> DeviceItem:
        key = (net_id, name.strip())
        if key not in devices_map:
            devices_map[key] = DeviceItem(
                id=f"{net_id}-{_slug(name)}-{len(devices_map)+1}",
                network_id=net_id,  # type: ignore[arg-type]
                name=name.strip(),
                role_hint=hint,
            )
        return devices_map[key]

    # 1. Группировка потоков данных по (from, to, target_device, protocol, port, mode)
    data_groups: dict[tuple, list[FlowDraft]] = {}
    file_flows: list[FlowDraft] = []

    for flow in state.flows:
        if not flow.from_network or not flow.to_network:
            continue
        if flow.type == "data":
            targets = flow.target_devices or ["Получатель"]
            for tgt in targets:
                ensure_device(flow.to_network, tgt)
                for src in (flow.source_devices or ["Отправитель"]):
                    ensure_device(flow.from_network, src)
                gkey = (
                    flow.from_network,
                    flow.to_network,
                    tgt.strip(),
                    flow.protocol or "неизвестно",
                    flow.port,
                    flow.mode or "one-way",
                )
                data_groups.setdefault(gkey, []).append(flow)
        elif flow.type == "file":
            file_flows.append(flow)

    for (from_n, to_n, tgt, proto, port, mode), group in data_groups.items():
        all_srcs: list[str] = []
        for f in group:
            for s in f.source_devices:
                if s not in all_srcs:
                    all_srcs.append(s)
        desc = group[0].description or f"Передача данных на {tgt}"
        rules.append(
            RuleItem(
                id=rule_id,
                **{"from": from_n, "to": to_n},
                type="data",
                mode=mode,
                protocol=proto,
                port=port,
                description=desc,
                source_devices=all_srcs or ["Отправитель"],
                target_device=tgt,
            )
        )
        rule_id += 1

    # 2. Правила передачи файлов и подсчёт лицензируемых пользователей
    total_manual_users: int = 0
    manual_unknown = False
    pull_rules_count = 0

    for flow in file_flows:
        from_n = flow.from_network or "open"
        to_n = flow.to_network or "closed"
        for src in (flow.source_devices or ["Отправитель файлов"]):
            ensure_device(from_n, src)
        for tgt in (flow.target_devices or ["Файловый сервер"]):
            ensure_device(to_n, tgt)

        # Количество правил для файлового потока: разделение по группам изоляции / профилям
        split_count = max(1, flow.access_groups_count)
        # Если в одном потоке на одной стороне требуются и PULL, и PUSH — 2 правила
        if flow.send_method == "pull" and flow.receive_method == "push" and flow.mode == "two-way":
            split_count = max(split_count, 2)

        uses_usb = flow.send_method == "usb" or flow.receive_method == "usb"
        proto_obj = {
            from_n: f"{flow.send_protocol or 'неизвестно'}"
            + (f", {flow.send_method}" if flow.send_method else ""),
            to_n: f"{flow.receive_protocol or 'неизвестно'}"
            + (f", {flow.receive_method}" if flow.receive_method else ""),
        }
        combined_checks = list(dict.fromkeys(flow.checks_send + flow.checks_receive))
        checks_by_node = None
        if flow.checks_send and flow.checks_receive and set(flow.checks_send) != set(flow.checks_receive):
            checks_by_node = {"send": flow.checks_send, "receive": flow.checks_receive}

        for idx in range(split_count):
            suffix = f" (группа {idx+1})" if split_count > 1 else ""
            rules.append(
                RuleItem(
                    id=rule_id,
                    **{"from": from_n, "to": to_n},
                    type="file",
                    mode=flow.mode or "one-way",
                    protocol=proto_obj,
                    port=None,
                    description=(flow.description or "Передача файлов") + suffix,
                    checks=combined_checks,
                    checks_by_node=checks_by_node,
                    source_devices=flow.source_devices or ["Отправитель файлов"],
                    target_device=(flow.target_devices[0] if flow.target_devices else "Файловый сервер"),
                    uses_usb=uses_usb,
                )
            )
            rule_id += 1
            if flow.send_method == "pull":
                pull_rules_count += 1

        if flow.send_method == "manual" or flow.receive_method == "manual" or uses_usb:
            if flow.manual_users_count is not None:
                total_manual_users += flow.manual_users_count
            else:
                manual_unknown = True

    state.devices = list(devices_map.values())
    state.rules = rules
    state.rules_count = len(rules)

    if not file_flows:
        state.file_users_count = 0
        state.file_users_range = None
    elif manual_unknown:
        state.file_users_count = None
        state.file_users_range = {"min": max(1, pull_rules_count), "max": None}
    else:
        state.file_users_count = total_manual_users + pull_rules_count
        state.file_users_range = None

    if state.rules_count > MAX_SYNONYX_RULES:
        state.status = "unsupported"
