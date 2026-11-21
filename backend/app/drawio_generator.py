from __future__ import annotations

import html
from typing import Optional

from .schemas import ProjectResult

RULE_COLORS = ["#E06733", "#35C4AF", "#FFAB4D", "#B9C5CD", "#6FA8DC"]

# Точный SVG стены с огоньком из 06_template.drawio (48x166)
FIREWALL_SVG_DATA_URI = (
    "data:image/svg+xml,"
    "PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSI0OCIgaGVpZ2h0PSIxNjYiIHZpZXdCb3g9IjAgMCA0OCAxNjYiPjxyZWN0IHg9IjEiIHk9IjEiIHdpZHRoPSI0NiIgaGVpZ2h0PSIxNjQiIHJ4PSI2IiBmaWxsPSIjMzU0NTUyIiBzdHJva2U9IiNGRkFCNEQiIHN0cm9rZS13aWR0aD0iMiIvPjxsaW5lIHgxPSIyIiB5MT0iNTgiIHgyPSI0NiIgeTI9IjU4IiBzdHJva2U9IiNGRkFCNEQiIHN0cm9rZS13aWR0aD0iMS41Ii8+PGxpbmUgeDE9IjI0LjAiIHkxPSI1OCIgeDI9IjI0LjAiIHkyPSI3NiIgc3Ryb2tlPSIjRkZBQjREIiBzdHJva2Utd2lkdGg9IjEuNSIvPjxsaW5lIHgxPSIyIiB5MT0iNzYiIHgyPSI0NiIgeTI9Ijc2IiBzdHJva2U9IiNGRkFCNEQiIHN0cm9rZS13aWR0aD0iMS41Ii8+PGxpbmUgeDE9IjEyLjAiIHkxPSI3NiIgeDI9IjEyLjAiIHkyPSI5NCIgc3Ryb2tlPSIjRkZBQjREIiBzdHJva2Utd2lkdGg9IjEuNSIvPjxsaW5lIHgxPSIzNi4wIiB5MT0iNzYiIHgyPSIzNi4wIiB5Mj0iOTQiIHN0cm9rZT0iI0ZGQUI0RCIgc3Ryb2tlLXdpZHRoPSIxLjUiLz48bGluZSB4MT0iMiIgeTE9Ijk0IiB4Mj0iNDYiIHkyPSI5NCIgc3Ryb2tlPSIjRkZBQjREIiBzdHJva2Utd2lkdGg9IjEuNSIvPjxsaW5lIHgxPSIyNC4wIiB5MT0iOTQiIHgyPSIyNC4wIiB5Mj0iMTEyIiBzdHJva2U9IiNGRkFCNEQiIHN0cm9rZS13aWR0aD0iMS41Ii8+PGxpbmUgeDE9IjIiIHkxPSIxMTIiIHgyPSI0NiIgeTI9IjExMiIgc3Ryb2tlPSIjRkZBQjREIiBzdHJva2Utd2lkdGg9IjEuNSIvPjxsaW5lIHgxPSIxMi4wIiB5MT0iMTEyIiB4Mj0iMTIuMCIgeTI9IjEzMCIgc3Ryb2tlPSIjRkZBQjREIiBzdHJva2Utd2lkdGg9IjEuNSIvPjxsaW5lIHgxPSIzNi4wIiB5MT0iMTEyIiB4Mj0iMzYuMCIgeTI9IjEzMCIgc3Ryb2tlPSIjRkZBQjREIiBzdHJva2Utd2lkdGg9IjEuNSIvPjxsaW5lIHgxPSIyIiB5MT0iMTMwIiB4Mj0iNDYiIHkyPSIxMzAiIHN0cm9rZT0iI0ZGQUI0RCIgc3Ryb2tlLXdpZHRoPSIxLjUiLz48bGluZSB4MT0iMjQuMCIgeTE9IjEzMCIgeDI9IjI0LjAiIHkyPSIxNDgiIHN0cm9rZT0iI0ZGQUI0RCIgc3Ryb2tlLXdpZHRoPSIxLjUiLz48bGluZSB4MT0iMiIgeTE9IjE0OCIgeDI9IjQ2IiB5Mj0iMTQ4IiBzdHJva2U9IiNGRkFCNEQiIHN0cm9rZS13aWR0aD0iMS41Ii8+PGxpbmUgeDE9IjEyLjAiIHkxPSIxNDgiIHgyPSIxMi4wIiB5Mj0iMTY0IiBzdHJva2U9IiNGRkFCNEQiIHN0cm9rZS13aWR0aD0iMS41Ii8+PGxpbmUgeDE9IjM2LjAiIHkxPSIxNDgiIHgyPSIzNi4wIiB5Mj0iMTY0IiBzdHJva2U9IiNGRkFCNEQiIHN0cm9rZS13aWR0aD0iMS41Ii8+PHBhdGggdHJhbnNmb3JtPSJ0cmFuc2xhdGUoMjQuMCwzMCkiIGQ9Ik0wLC0yMCBDNywtMTAgMTMsLTQgMTMsNSBDMTMsMTMgNywxOSAwLDE5IEMtNywxOSAtMTMsMTMgLTEzLDUgQy0xMywwIC0xMCwtNCAtNywtOCBDLTYsLTQgLTQsLTIgLTIsLTIgQy00LC04IC0zLC0xNCAwLC0yMCBaIiBmaWxsPSIjRTA2NzMzIi8+PHBhdGggdHJhbnNmb3JtPSJ0cmFuc2xhdGUoMjQuMCwzNSkiIGQ9Ik0wLC05IEM0LC00IDYsLTEgNiwzIEM2LDggMywxMSAwLDExIEMtMywxMSAtNiw4IC02LDMgQy02LDAgLTMsLTQgMCwtOSBaIiBmaWxsPSIjRkZBQjREIi8+PC9zdmc+"
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
    num_rows = max(1, len(result.rules))
    row_height = 96

    open_box_x, open_box_y, open_box_w = 40, 96, 270
    closed_box_x, closed_box_y, closed_box_w = 520, 96, 850

    fw_w, fw_h = 48, 166
    fw_x = closed_box_x - fw_w // 2

    node_w = 64
    node_h = max(84, num_rows * 28 + 26)
    pad_x = 24
    pad_y = 40
    gap_nodes = 16

    syn_x = closed_box_x + 68
    syn_w = pad_x * 2 + node_w * 3 + gap_nodes * 2
    syn_h = node_h + pad_y * 2
    syn_y = closed_box_y + 72
    fw_y = syn_y + (syn_h - fw_h) // 2

    cards_total_h = num_rows * row_height + 60
    syn_total_h = (syn_y - closed_box_y) + syn_h + (160 if has_usb else 40)
    net_body_height = max(340, cards_total_h, syn_total_h)

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

    cells.append(
        f'<mxCell id="{next_id()}" value="{_esc(title.upper())}" '
        f'style="text;html=1;align=left;verticalAlign=middle;fontColor=#FFFFFF;fontSize=20;fontStyle=1;fontFamily=Open Sans;" '
        f'vertex="1" parent="1"><mxGeometry x="40" y="16" width="900" height="30" as="geometry"/></mxCell>'
    )
    sub = f"Правил Синоникса: {rules_count}"
    if result.file_users_count is not None and result.file_users_count > 0:
        sub += f" · пользователей передачи файлов: {result.file_users_count}"
    cells.append(
        f'<mxCell id="{next_id()}" value="{_esc(sub)}" '
        f'style="text;html=1;align=left;verticalAlign=middle;fontColor=#B9C5CD;fontSize=12;fontFamily=Open Sans;" '
        f'vertex="1" parent="1"><mxGeometry x="40" y="48" width="700" height="22" as="geometry"/></mxCell>'
    )

    open_label = f'<b>ОТКРЫТАЯ СЕТЬ</b><br><span style="font-weight:normal;font-size:11px">{_esc(open_name)}</span>'
    cells.append(
        f'<mxCell id="{next_id()}" value="{_esc(open_label)}" '
        f'style="rounded=1;arcSize=5;dashed=1;dashPattern=8 6;fillColor=none;strokeColor=#E06733;strokeWidth=2;html=1;align=left;verticalAlign=top;spacingLeft=14;spacingTop=6;fontColor=#E06733;fontSize=12;fontFamily=Open Sans;" '
        f'vertex="1" parent="1"><mxGeometry x="{open_box_x}" y="{open_box_y}" width="{open_box_w}" height="{net_body_height}" as="geometry"/></mxCell>'
    )

    closed_label = f'<b>ЗАКРЫТЫЙ СЕГМЕНТ</b><br><span style="font-weight:normal;font-size:11px">{_esc(closed_name)}</span>'
    cells.append(
        f'<mxCell id="{next_id()}" value="{_esc(closed_label)}" '
        f'style="rounded=1;arcSize=5;dashed=1;dashPattern=8 6;fillColor=none;strokeColor=#35C4AF;strokeWidth=2;html=1;align=left;verticalAlign=top;spacingLeft=32;spacingTop=6;fontColor=#35C4AF;fontSize=12;fontFamily=Open Sans;" '
        f'vertex="1" parent="1"><mxGeometry x="{closed_box_x}" y="{closed_box_y}" width="{closed_box_w}" height="{net_body_height}" as="geometry"/></mxCell>'
    )

    cells.append(
        f'<mxCell id="{next_id()}" value="МЭ" '
        f'style="shape=image;imageAspect=0;aspect=fixed;html=1;image={FIREWALL_SVG_DATA_URI};verticalLabelPosition=top;verticalAlign=bottom;labelPosition=center;align=center;fontColor=#FFAB4D;fontSize=13;fontStyle=1;fontFamily=Open Sans;" '
        f'vertex="1" parent="1"><mxGeometry x="{fw_x}" y="{fw_y}" width="{fw_w}" height="{fw_h}" as="geometry"/></mxCell>'
    )

    if result.firewall.get("side") == "both":
        cells.append(
            f'<mxCell id="{next_id()}" value="МЭ" '
            f'style="shape=image;imageAspect=0;aspect=fixed;html=1;image={FIREWALL_SVG_DATA_URI};verticalLabelPosition=top;verticalAlign=bottom;labelPosition=center;align=center;fontColor=#FFAB4D;fontSize=13;fontStyle=1;fontFamily=Open Sans;" '
            f'vertex="1" parent="1"><mxGeometry x="{open_box_x + open_box_w - fw_w // 2}" y="{fw_y}" width="{fw_w}" height="{fw_h}" as="geometry"/></mxCell>'
        )

    cells.append(
        f'<mxCell id="{next_id()}" value="СИНОНИКС" '
        f'style="text;html=1;align=center;verticalAlign=middle;fontColor=#E06733;fontSize=13;fontStyle=1;fontFamily=Open Sans;" '
        f'vertex="1" parent="1"><mxGeometry x="{syn_x}" y="{syn_y - 28}" width="{syn_w}" height="24" as="geometry"/></mxCell>'
    )

    cells.append(
        f'<mxCell id="{next_id()}" value="" '
        f'style="rounded=1;arcSize=10;fillColor=#FFFFFF;strokeColor=#E06733;strokeWidth=2;html=1;" '
        f'vertex="1" parent="1"><mxGeometry x="{syn_x}" y="{syn_y}" width="{syn_w}" height="{syn_h}" as="geometry"/></mxCell>'
    )

    node_y = syn_y + pad_y
    node_a_x = syn_x + pad_x
    core_x = node_a_x + node_w + gap_nodes
    node_b_x = core_x + node_w + gap_nodes

    node_a_id = next_id()
    cells.append(
        f'<mxCell id="{node_a_id}" value="УЗЕЛ А" '
        f'style="rounded=1;arcSize=12;fillColor=#F2F4F6;strokeColor=#B9C5CD;html=1;fontColor=#3A4D59;fontSize=10;fontStyle=1;fontFamily=Open Sans;" '
        f'vertex="1" parent="1"><mxGeometry x="{node_a_x}" y="{node_y}" width="{node_w}" height="{node_h}" as="geometry"/></mxCell>'
    )
    cells.append(
        f'<mxCell id="{next_id()}" value="ЯДРО" '
        f'style="shape=hexagon;perimeter=hexagonPerimeter2;fixedSize=1;size=14;fillColor=#F2F4F6;strokeColor=#B9C5CD;html=1;fontColor=#3A4D59;fontSize=10;fontStyle=1;fontFamily=Open Sans;" '
        f'vertex="1" parent="1"><mxGeometry x="{core_x}" y="{node_y}" width="{node_w}" height="{node_h}" as="geometry"/></mxCell>'
    )
    node_b_id = next_id()
    cells.append(
        f'<mxCell id="{node_b_id}" value="УЗЕЛ В" '
        f'style="rounded=1;arcSize=12;fillColor=#F2F4F6;strokeColor=#B9C5CD;html=1;fontColor=#3A4D59;fontSize=10;fontStyle=1;fontFamily=Open Sans;" '
        f'vertex="1" parent="1"><mxGeometry x="{node_b_x}" y="{node_y}" width="{node_w}" height="{node_h}" as="geometry"/></mxCell>'
    )

    usb_cell_id: Optional[str] = None
    usb_x = node_a_x - 23
    usb_y = syn_y + syn_h + 96
    if has_usb:
        usb_cell_id = next_id()
        cells.append(
            f'<mxCell id="{usb_cell_id}" value="USB-носитель" '
            f'style="rounded=1;arcSize=30;fillColor=#354552;strokeColor=#B9C5CD;html=1;fontColor=#FFFFFF;fontSize=11;fontStyle=1;fontFamily=Open Sans;" '
            f'vertex="1" parent="1"><mxGeometry x="{usb_x}" y="{usb_y}" width="110" height="34" as="geometry"/></mxCell>'
        )

    for idx, rule in enumerate(result.rules):
        color = RULE_COLORS[idx % len(RULE_COLORS)]
        ry = closed_box_y + 62 + idx * row_height
        card_mid_y = ry + 32

        frac = (idx + 1) / (num_rows + 1)
        slot_rel_y = round(0.15 + frac * 0.70, 3)
        slot_abs_y = round(node_y + node_h * slot_rel_y, 1)

        is_usb_rule = (
            rule.type == "file"
            and not isinstance(rule.protocol, str)
            and "usb" in rule.protocol.open.lower()
        )

        right_card_x = closed_box_x + 570
        right_card_w = 250
        right_card_id = next_id()
        right_title = "Система закрытого сегмента"
        right_sub = rule.description[:34]
        if rule.to_net == "closed" and rule.type == "data":
            right_title = f"Получатель ({rule.protocol})"
        elif rule.from_net == "closed" and rule.type == "data":
            right_title = "Источник в закрытом сегменте"
        elif rule.type == "file":
            right_title = "Файловый сервер цеха"

        cells.append(
            f'<mxCell id="{right_card_id}" value="{_esc(f"<b>{right_title}</b><br><font color=#35C4AF style=font-size:11px>{right_sub}</font>")}" '
            f'style="rounded=1;arcSize=14;fillColor=#4A5D6A;strokeColor=none;html=1;whiteSpace=wrap;align=left;verticalAlign=middle;spacingLeft=14;spacingRight=8;fontColor=#FFFFFF;fontSize=13;fontFamily=Open Sans;" '
            f'vertex="1" parent="1"><mxGeometry x="{right_card_x}" y="{ry}" width="{right_card_w}" height="64" as="geometry"/></mxCell>'
        )

        if isinstance(rule.protocol, str):
            port_txt = f" {rule.port}" if rule.port is not None else ""
            badge_left = f"{rule.id} · {rule.protocol}{port_txt}"
            badge_right = badge_left
        else:
            badge_left = f"{rule.id} · {rule.protocol.open[:20]}"
            badge_right = f"{rule.id} · {rule.protocol.closed[:20]}"

        if is_usb_rule and usb_cell_id:
            cells.append(
                f'<mxCell id="{next_id()}" value="{_esc(badge_left)}" '
                f'style="edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;strokeColor={color};strokeWidth=2;exitX=0.5;exitY=0;entryX=0.5;entryY=1;endArrow=block;endFill=1;startArrow=none;labelBackgroundColor=#354552;labelBorderColor=none;fontColor=#FFFFFF;fontSize=10;fontStyle=1;spacing=4;fontFamily=Open Sans;" '
                f'edge="1" parent="1" source="{usb_cell_id}" target="{node_a_id}">'
                f'<mxGeometry relative="1" as="geometry"/></mxCell>'
            )
        else:
            left_card_x = open_box_x + 25
            left_card_w = 220
            left_card_id = next_id()
            left_title = "Система открытой сети"
            if rule.from_net == "open":
                left_title = "Источник в открытой сети"
            elif rule.to_net == "open":
                left_title = "Получатель в открытой сети"

            cells.append(
                f'<mxCell id="{left_card_id}" value="{_esc(f"<b>{left_title}</b><br><font color=#35C4AF style=font-size:11px>{rule.description[:32]}</font>")}" '
                f'style="rounded=1;arcSize=14;fillColor=#4A5D6A;strokeColor=none;html=1;whiteSpace=wrap;align=left;verticalAlign=middle;spacingLeft=14;spacingRight=8;fontColor=#FFFFFF;fontSize=13;fontFamily=Open Sans;" '
                f'vertex="1" parent="1"><mxGeometry x="{left_card_x}" y="{ry}" width="{left_card_w}" height="64" as="geometry"/></mxCell>'
            )

            if rule.mode == "two-way":
                start_arr = "block"
                end_arr = "block"
            elif rule.from_net == "open":
                start_arr = "none"
                end_arr = "block"
            else:
                start_arr = "block"
                end_arr = "none"

            if card_mid_y < slot_abs_y:
                left_channel_x = 456 + idx * 10
            else:
                left_channel_x = 486 - idx * 10

            cells.append(
                f'<mxCell id="{next_id()}" value="{_esc(badge_left)}" '
                f'style="edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;strokeColor={color};strokeWidth=2;exitX=1;exitY=0.5;entryX=0;entryY={slot_rel_y};startArrow={start_arr};startFill=1;endArrow={end_arr};endFill=1;labelBackgroundColor=#354552;labelBorderColor=none;fontColor=#FFFFFF;fontSize=10;fontStyle=1;spacing=4;fontFamily=Open Sans;" '
                f'edge="1" parent="1" source="{left_card_id}" target="{node_a_id}">'
                f'<mxGeometry relative="1" as="geometry">'
                f'<Array as="points">'
                f'<mxPoint x="{left_channel_x}" y="{card_mid_y}"/>'
                f'<mxPoint x="{left_channel_x}" y="{slot_abs_y}"/>'
                f'</Array></mxGeometry></mxCell>'
            )

        if rule.mode == "two-way":
            r_start = "block"
            r_end = "block"
        elif rule.to_net == "closed":
            r_start = "none"
            r_end = "block"
        else:
            r_start = "block"
            r_end = "none"

        if card_mid_y < slot_abs_y:
            right_channel_x = (syn_x + syn_w + 20) + idx * 12
        else:
            right_channel_x = (syn_x + syn_w + 20) + (num_rows - 1 - idx) * 12

        cells.append(
            f'<mxCell id="{next_id()}" value="{_esc(badge_right)}" '
            f'style="edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;strokeColor={color};strokeWidth=2;exitX=1;exitY={slot_rel_y};entryX=0;entryY=0.5;startArrow={r_start};startFill=1;endArrow={r_end};endFill=1;labelBackgroundColor=#354552;labelBorderColor=none;fontColor=#FFFFFF;fontSize=10;fontStyle=1;spacing=4;fontFamily=Open Sans;" '
            f'edge="1" parent="1" source="{node_b_id}" target="{right_card_id}">'
            f'<mxGeometry relative="1" as="geometry">'
            f'<Array as="points">'
            f'<mxPoint x="{right_channel_x}" y="{slot_abs_y}"/>'
            f'<mxPoint x="{right_channel_x}" y="{card_mid_y}"/>'
            f'</Array></mxGeometry></mxCell>'
        )

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
            f'vertex="1" parent="1"><mxGeometry x="60" y="{ly}" width="1300" height="22" as="geometry"/></mxCell>'
        )

    note_y = legend_y + 34 + len(result.rules) * 24
    note_text = "МЭ стоит на границе закрытого сегмента. Синоникс размещён в закрытом сегменте сразу за МЭ: Узел А обращён к открытой сети, Узел В к закрытой."
    cells.append(
        f'<mxCell id="{next_id()}" value="{_esc(note_text)}" '
        f'style="text;html=1;align=left;verticalAlign=middle;whiteSpace=wrap;fontColor=#B9C5CD;fontSize=11;fontFamily=Open Sans;" '
        f'vertex="1" parent="1"><mxGeometry x="40" y="{note_y}" width="1300" height="24" as="geometry"/></mxCell>'
    )

    cells_xml = "\n        ".join(cells)
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<mxfile host="app.diagrams.net" modified="2026-11-21T00:00:00.000Z" agent="SynonyxAssistant" version="24.0.0">\n'
        '  <diagram id="synonyx-scheme" name="Схема Синоникс">\n'
        '    <mxGraphModel dx="1460" dy="960" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="1420" pageHeight="980" math="0" shadow="0">\n'
        '      <root>\n'
        f'        {cells_xml}\n'
        '      </root>\n'
        '    </mxGraphModel>\n'
        '  </diagram>\n'
        '</mxfile>'
    )
