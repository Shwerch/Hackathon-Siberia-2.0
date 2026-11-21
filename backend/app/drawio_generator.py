from __future__ import annotations

import html
from typing import Optional

from .schemas import ProjectResult

RULE_COLORS = ["#E06733", "#35C4AF", "#FFAB4D", "#B9C5CD", "#6FA8DC"]

# Встроенная векторная иконка МЭ (кирпичная стена с огоньком) из 06_template.drawio
FIREWALL_SVG_DATA_URI = (
    "data:image/svg+xml,"
    "%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%2044%2084%22%3E"
    "%3Crect%20x%3D%222%22%20y%3D%2218%22%20width%3D%2240%22%20height%3D%2264%22%20rx%3D%224%22%20fill%3D%22%23354552%22%20stroke%3D%22%23FFAB4D%22%20stroke-width%3D%222%22%2F%3E"
    "%3Cline%20x1%3D%222%22%20y1%3D%2234%22%20x2%3D%2242%22%20y2%3D%2234%22%20stroke%3D%22%23FFAB4D%22%20stroke-width%3D%221.5%22%2F%3E"
    "%3Cline%20x1%3D%222%22%20y1%3D%2250%22%20x2%3D%2242%22%20y2%3D%2250%22%20stroke%3D%22%23FFAB4D%22%20stroke-width%3D%221.5%22%2F%3E"
    "%3Cline%20x1%3D%222%22%20y1%3D%2266%22%20x2%3D%2242%22%20y2%3D%2266%22%20stroke%3D%22%23FFAB4D%22%20stroke-width%3D%221.5%22%2F%3E"
    "%3Cline%20x1%3D%2222%22%20y1%3D%2218%22%20x2%3D%2222%22%20y2%3D%2234%22%20stroke%3D%22%23FFAB4D%22%20stroke-width%3D%221.5%22%2F%3E"
    "%3Cline%20x1%3D%2212%22%20y1%3D%2234%22%20x2%3D%2212%22%20y2%3D%2250%22%20stroke%3D%22%23FFAB4D%22%20stroke-width%3D%221.5%22%2F%3E"
    "%3Cline%20x1%3D%2232%22%20y1%3D%2234%22%20x2%3D%2232%22%20y2%3D%2250%22%20stroke%3D%22%23FFAB4D%22%20stroke-width%3D%221.5%22%2F%3E"
    "%3Cline%20x1%3D%2222%22%20y1%3D%2250%22%20x2%3D%2222%22%20y2%3D%2266%22%20stroke%3D%22%23FFAB4D%22%20stroke-width%3D%221.5%22%2F%3E"
    "%3Cpath%20d%3D%22M22%202%20C28%208%2029%2014%2022%2016%20C15%2014%2016%208%2022%202%20Z%22%20fill%3D%22%23E06733%22%2F%3E"
    "%3C%2Fsvg%3E"
)


def _esc(text: str) -> str:
    return html.escape(text, quote=True)


def generate_drawio_xml(result: ProjectResult, title: str = "СХЕМА ОБМЕНА «СИНОНИКС»") -> str:
    open_net = next((n for n in result.networks if n.trust == "open"), None)
    closed_net = next((n for n in result.networks if n.trust == "closed"), None)
    open_name = open_net.name if open_net else "Открытая сеть"
    closed_name = closed_net.name if closed_net else "Закрытый сегмент"

    has_usb = any(
        r.type == "file"
        and not isinstance(r.protocol, str)
        and "usb" in r.protocol.open.lower()
        for r in result.rules
    )

    rules_count = result.rules_count
    row_height = 82
    num_rows = max(1, len(result.rules))
    net_body_height = max(250, num_rows * row_height + (80 if has_usb else 40))

    open_box_x, open_box_y, open_box_w = 40, 90, 320
    closed_box_x, closed_box_y, closed_box_w = 430, 90, 620

    fw_x = closed_box_x - 22
    fw_y = closed_box_y + 70
    syn_x = closed_box_x + 56
    syn_y = closed_box_y + 55
    syn_w, syn_h = 190, 110

    cells: list[str] = [
        '<mxCell id="0"/>',
        '<mxCell id="1" parent="0"/>',
    ]
    cid = 2

    def next_id() -> str:
        nonlocal cid
        val = str(cid)
        cid += 1
        return val

    # Заголовок и подзаголовок
    cells.append(
        f'<mxCell id="{next_id()}" value="{_esc(title.upper())}" '
        f'style="text;html=1;align=left;verticalAlign=middle;fontColor=#FFFFFF;fontSize=20;fontStyle=1;fontFamily=Open Sans;" '
        f'vertex="1" parent="1"><mxGeometry x="40" y="20" width="900" height="30" as="geometry"/></mxCell>'
    )
    sub = f"Правил Синоникса: {rules_count}"
    if result.file_users_count is not None and result.file_users_count > 0:
        sub += f" · пользователей передачи файлов: {result.file_users_count}"
    cells.append(
        f'<mxCell id="{next_id()}" value="{_esc(sub)}" '
        f'style="text;html=1;align=left;verticalAlign=middle;fontColor=#B9C5CD;fontSize=12;fontFamily=Open Sans;" '
        f'vertex="1" parent="1"><mxGeometry x="40" y="50" width="700" height="22" as="geometry"/></mxCell>'
    )

    # Рамка Открытой сети
    open_label = f'<b>ОТКРЫТАЯ СЕТЬ</b><br><span style="font-weight:normal;font-size:11px">{_esc(open_name)}</span>'
    cells.append(
        f'<mxCell id="{next_id()}" value="{_esc(open_label)}" '
        f'style="rounded=1;arcSize=5;dashed=1;dashPattern=8 6;fillColor=none;strokeColor=#E06733;strokeWidth=2;html=1;align=left;verticalAlign=top;spacingLeft=14;spacingTop=10;fontColor=#FFFFFF;fontSize=12;fontFamily=Open Sans;" '
        f'vertex="1" parent="1"><mxGeometry x="{open_box_x}" y="{open_box_y}" width="{open_box_w}" height="{net_body_height}" as="geometry"/></mxCell>'
    )

    # Рамка Закрытого сегмента
    closed_label = f'<b>ЗАКРЫТЫЙ СЕГМЕНТ</b><br><span style="font-weight:normal;font-size:11px">{_esc(closed_name)}</span>'
    cells.append(
        f'<mxCell id="{next_id()}" value="{_esc(closed_label)}" '
        f'style="rounded=1;arcSize=5;dashed=1;dashPattern=8 6;fillColor=none;strokeColor=#35C4AF;strokeWidth=2;html=1;align=left;verticalAlign=top;spacingLeft=30;spacingTop=10;fontColor=#FFFFFF;fontSize=12;fontFamily=Open Sans;" '
        f'vertex="1" parent="1"><mxGeometry x="{closed_box_x}" y="{closed_box_y}" width="{closed_box_w}" height="{net_body_height}" as="geometry"/></mxCell>'
    )

    # МЭ на границе закрытого сегмента
    cells.append(
        f'<mxCell id="{next_id()}" value="МЭ" '
        f'style="shape=image;imageAspect=0;aspect=fixed;html=1;image={FIREWALL_SVG_DATA_URI};fontColor=#FFAB4D;fontSize=11;fontStyle=1;fontFamily=Open Sans;verticalLabelPosition=top;verticalAlign=bottom;" '
        f'vertex="1" parent="1"><mxGeometry x="{fw_x}" y="{fw_y}" width="44" height="84" as="geometry"/></mxCell>'
    )

    # Второй МЭ, если обе сети открытые
    if result.firewall.get("side") == "both":
        cells.append(
            f'<mxCell id="{next_id()}" value="МЭ" '
            f'style="shape=image;imageAspect=0;aspect=fixed;html=1;image={FIREWALL_SVG_DATA_URI};fontColor=#FFAB4D;fontSize=11;fontStyle=1;fontFamily=Open Sans;verticalLabelPosition=top;verticalAlign=bottom;" '
            f'vertex="1" parent="1"><mxGeometry x="{open_box_x + open_box_w - 22}" y="{fw_y}" width="44" height="84" as="geometry"/></mxCell>'
        )

    # Блок Синоникс (Узел А, Ядро, Узел В)
    cells.append(
        f'<mxCell id="{next_id()}" value="" '
        f'style="rounded=1;arcSize=10;fillColor=#FFFFFF;strokeColor=#E06733;strokeWidth=2;html=1;" '
        f'vertex="1" parent="1"><mxGeometry x="{syn_x}" y="{syn_y}" width="{syn_w}" height="{syn_h}" as="geometry"/></mxCell>'
    )
    cells.append(
        f'<mxCell id="{next_id()}" value="СИНОНИКС" '
        f'style="text;html=1;align=center;verticalAlign=middle;fontColor=#E06733;fontSize=13;fontStyle=1;fontFamily=Open Sans;" '
        f'vertex="1" parent="1"><mxGeometry x="{syn_x}" y="{syn_y + 6}" width="{syn_w}" height="22" as="geometry"/></mxCell>'
    )
    node_a_id = next_id()
    cells.append(
        f'<mxCell id="{node_a_id}" value="УЗЕЛ А" '
        f'style="rounded=1;arcSize=12;fillColor=#F2F4F6;strokeColor=#B9C5CD;html=1;fontColor=#3A4D59;fontSize=10;fontStyle=1;fontFamily=Open Sans;" '
        f'vertex="1" parent="1"><mxGeometry x="{syn_x + 10}" y="{syn_y + 38}" width="52" height="54" as="geometry"/></mxCell>'
    )
    cells.append(
        f'<mxCell id="{next_id()}" value="ЯДРО" '
        f'style="shape=hexagon;perimeter=hexagonPerimeter2;fixedSize=1;size=12;fillColor=#F2F4F6;strokeColor=#B9C5CD;html=1;fontColor=#3A4D59;fontSize=10;fontStyle=1;fontFamily=Open Sans;" '
        f'vertex="1" parent="1"><mxGeometry x="{syn_x + 69}" y="{syn_y + 38}" width="52" height="54" as="geometry"/></mxCell>'
    )
    node_b_id = next_id()
    cells.append(
        f'<mxCell id="{node_b_id}" value="УЗЕЛ В" '
        f'style="rounded=1;arcSize=12;fillColor=#F2F4F6;strokeColor=#B9C5CD;html=1;fontColor=#3A4D59;fontSize=10;fontStyle=1;fontFamily=Open Sans;" '
        f'vertex="1" parent="1"><mxGeometry x="{syn_x + 128}" y="{syn_y + 38}" width="52" height="54" as="geometry"/></mxCell>'
    )

    # USB-носитель (если есть) — строго под Узлом А внутри закрытого сегмента
    usb_cell_id: Optional[str] = None
    if has_usb:
        usb_cell_id = next_id()
        usb_x = syn_x + 2
        usb_y = syn_y + syn_h + 45
        cells.append(
            f'<mxCell id="{usb_cell_id}" value="USB-носитель" '
            f'style="rounded=1;arcSize=30;fillColor=#354552;strokeColor=#B9C5CD;html=1;fontColor=#FFFFFF;fontSize=11;fontStyle=1;fontFamily=Open Sans;" '
            f'vertex="1" parent="1"><mxGeometry x="{usb_x}" y="{usb_y}" width="110" height="36" as="geometry"/></mxCell>'
        )

    # Карточки систем и стрелки для каждого правила
    for idx, rule in enumerate(result.rules):
        color = RULE_COLORS[idx % len(RULE_COLORS)]
        ry = closed_box_y + 52 + idx * row_height

        # Левая карточка (в открытой сети) или USB
        is_usb_rule = (
            rule.type == "file"
            and not isinstance(rule.protocol, str)
            and "usb" in rule.protocol.open.lower()
        )

        right_card_x = closed_box_x + 310
        right_card_w = 270
        right_card_id = next_id()
        right_title = "Система закрытого сегмента"
        right_sub = rule.description[:38]
        if rule.to_net == "closed" and rule.type == "data":
            right_title = f"Получатель ({rule.protocol})"
        elif rule.from_net == "closed" and rule.type == "data":
            right_title = "Источник в закрытом сегменте"
        elif rule.type == "file":
            right_title = "Файловый сервер / Узел цеха"

        cells.append(
            f'<mxCell id="{right_card_id}" value="{_esc(f"<b>{right_title}</b><br><font color=#35C4AF style=font-size:11px>{right_sub}</font>")}" '
            f'style="rounded=1;arcSize=14;fillColor=#4A5D6A;strokeColor=none;html=1;whiteSpace=wrap;align=left;verticalAlign=middle;spacingLeft=12;fontColor=#FFFFFF;fontSize=12;fontFamily=Open Sans;" '
            f'vertex="1" parent="1"><mxGeometry x="{right_card_x}" y="{ry}" width="{right_card_w}" height="56" as="geometry"/></mxCell>'
        )

        # Подпись потока
        if isinstance(rule.protocol, str):
            port_txt = f" {rule.port}" if rule.port is not None else ""
            badge_left = f"{rule.id} · {rule.protocol}{port_txt}"
            badge_right = badge_left
        else:
            badge_left = f"{rule.id} · {rule.protocol.open[:22]}"
            badge_right = f"{rule.id} · {rule.protocol.closed[:22]}"

        # Стрелки на стороне Узла А (слева)
        if is_usb_rule and usb_cell_id:
            cells.append(
                f'<mxCell id="{next_id()}" value="{_esc(badge_left)}" '
                f'style="edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;strokeColor={color};strokeWidth=2;endArrow=block;endFill=1;fontColor=#FFFFFF;fontSize=10;fontStyle=1;fontFamily=Open Sans;" '
                f'edge="1" parent="1" source="{usb_cell_id}" target="{node_a_id}">'
                f'<mxGeometry relative="1" as="geometry"/></mxCell>'
            )
        else:
            left_card_x = open_box_x + 24
            left_card_w = 270
            left_card_id = next_id()
            left_title = "Система открытой сети"
            if rule.from_net == "open":
                left_title = "Источник в открытой сети"
            elif rule.to_net == "open":
                left_title = "Получатель в открытой сети"

            cells.append(
                f'<mxCell id="{left_card_id}" value="{_esc(f"<b>{left_title}</b><br><font color=#35C4AF style=font-size:11px>{rule.description[:36]}</font>")}" '
                f'style="rounded=1;arcSize=14;fillColor=#4A5D6A;strokeColor=none;html=1;whiteSpace=wrap;align=left;verticalAlign=middle;spacingLeft=12;fontColor=#FFFFFF;fontSize=12;fontFamily=Open Sans;" '
                f'vertex="1" parent="1"><mxGeometry x="{left_card_x}" y="{ry}" width="{left_card_w}" height="56" as="geometry"/></mxCell>'
            )

            # Направление стрелок слева (Открытая <-> Узел А)
            if rule.mode == "two-way":
                start_arr = "block"
                end_arr = "block"
            elif rule.from_net == "open":
                start_arr = "none"
                end_arr = "block"
            else:
                start_arr = "block"
                end_arr = "none"

            cells.append(
                f'<mxCell id="{next_id()}" value="{_esc(badge_left)}" '
                f'style="edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;strokeColor={color};strokeWidth=2;startArrow={start_arr};startFill=1;endArrow={end_arr};endFill=1;fontColor=#FFFFFF;fontSize=10;fontStyle=1;fontFamily=Open Sans;" '
                f'edge="1" parent="1" source="{left_card_id}" target="{node_a_id}">'
                f'<mxGeometry relative="1" as="geometry">'
                f'<Array as="points">'
                f'<mxPoint x="{open_box_x + open_box_w + 20}" y="{ry + 28}"/>'
                f'<mxPoint x="{open_box_x + open_box_w + 20}" y="{syn_y + 55 + idx * 6}"/>'
                f'</Array></mxGeometry></mxCell>'
            )

        # Стрелка справа (Узел В <-> Закрытый сегмент)
        if rule.mode == "two-way":
            r_start = "block"
            r_end = "block"
        elif rule.to_net == "closed":
            r_start = "none"
            r_end = "block"
        else:
            r_start = "block"
            r_end = "none"

        cells.append(
            f'<mxCell id="{next_id()}" value="{_esc(badge_right)}" '
            f'style="edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;strokeColor={color};strokeWidth=2;startArrow={r_start};startFill=1;endArrow={r_end};endFill=1;fontColor=#FFFFFF;fontSize=10;fontStyle=1;fontFamily=Open Sans;" '
            f'edge="1" parent="1" source="{node_b_id}" target="{right_card_id}">'
            f'<mxGeometry relative="1" as="geometry">'
            f'<Array as="points">'
            f'<mxPoint x="{syn_x + syn_w + 28 + idx * 8}" y="{syn_y + 55 + idx * 6}"/>'
            f'<mxPoint x="{syn_x + syn_w + 28 + idx * 8}" y="{ry + 28}"/>'
            f'</Array></mxGeometry></mxCell>'
        )

    # Легенда под схемой
    legend_y = closed_box_y + net_body_height + 24
    cells.append(
        f'<mxCell id="{next_id()}" value="{_esc(f"Правил Синоникса: {rules_count}")}" '
        f'style="text;html=1;align=left;verticalAlign=middle;whiteSpace=wrap;fontColor=#FFFFFF;fontSize=13;fontStyle=1;fontFamily=Open Sans;" '
        f'vertex="1" parent="1"><mxGeometry x="40" y="{legend_y}" width="300" height="24" as="geometry"/></mxCell>'
    )
    for idx, rule in enumerate(result.rules):
        color = RULE_COLORS[idx % len(RULE_COLORS)]
        ly = legend_y + 28 + idx * 24
        mode_ru = "однонаправленное правило" if rule.mode == "one-way" else "двунаправленное правило"
        line_text = f"{rule.id}. {rule.description} ({mode_ru})"
        cells.append(
            f'<mxCell id="{next_id()}" value="" '
            f'style="rounded=1;fillColor={color};strokeColor=none;" '
            f'vertex="1" parent="1"><mxGeometry x="40" y="{ly + 5}" width="12" height="12" as="geometry"/></mxCell>'
        )
        cells.append(
            f'<mxCell id="{next_id()}" value="{_esc(line_text)}" '
            f'style="text;html=1;align=left;verticalAlign=middle;whiteSpace=wrap;fontColor=#FFFFFF;fontSize=11;fontFamily=Open Sans;" '
            f'vertex="1" parent="1"><mxGeometry x="60" y="{ly}" width="980" height="22" as="geometry"/></mxCell>'
        )

    note_y = legend_y + 34 + len(result.rules) * 24
    note_text = "МЭ стоит на границе закрытого сегмента. Синоникс размещён в закрытом сегменте сразу за МЭ: Узел А обращён к открытой сети, Узел В к закрытой."
    cells.append(
        f'<mxCell id="{next_id()}" value="{_esc(note_text)}" '
        f'style="text;html=1;align=left;verticalAlign=middle;whiteSpace=wrap;fontColor=#B9C5CD;fontSize=11;fontFamily=Open Sans;" '
        f'vertex="1" parent="1"><mxGeometry x="40" y="{note_y}" width="980" height="24" as="geometry"/></mxCell>'
    )

    cells_xml = "\n        ".join(cells)
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<mxfile host="app.diagrams.net" modified="2026-11-21T00:00:00.000Z" agent="SynonyxAssistant" version="24.0.0">\n'
        '  <diagram id="synonyx-scheme" name="Схема Синоникс">\n'
        '    <mxGraphModel dx="1200" dy="800" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="1169" pageHeight="827" math="0" shadow="0">\n'
        '      <root>\n'
        f'        {cells_xml}\n'
        '      </root>\n'
        '    </mxGraphModel>\n'
        '  </diagram>\n'
        '</mxfile>'
    )
