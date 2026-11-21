from html import escape
from app.models.state import SessionState

RULE_COLORS = ["#E06733", "#35C4AF", "#FFAB4D", "#B9C5CD", "#6FA8DC"]

FIREWALL_SVG_B64 = (
    "data:image/svg+xml,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSI0OCIgaGVpZ2h0PSIyODAiIHZpZXdCb3g9IjAgMCA0OCAyODAiPg=="
)


def _firewall_svg_data_uri(height: int) -> str:
    # Компактный SVG стены с огоньком в стиле 06_template.drawio
    svg = (
        f'<svg xmlns="[http://www.w3.org/2000/svg](http://www.w3.org/2000/svg)" width="48" height="{height}" viewBox="0 0 48 {height}">'
        f'<rect x="1" y="1" width="46" height="{height-2}" rx="6" fill="#354552" stroke="#FFAB4D" stroke-width="2"/>'
        f'<line x1="2" y1="58" x2="46" y2="58" stroke="#FFAB4D" stroke-width="1.5"/>'
        f'<line x1="2" y1="90" x2="46" y2="90" stroke="#FFAB4D" stroke-width="1.5"/>'
        f'<line x1="2" y1="122" x2="46" y2="122" stroke="#FFAB4D" stroke-width="1.5"/>'
        f'<path transform="translate(24,30)" d="M0,-20 C7,-10 13,-4 13,5 C13,13 7,19 0,19 C-7,19 -13,13 -13,5 C-13,0 -10,-4 -7,-8 C-6,-4 -4,-2 -2,-2 C-4,-8 -3,-14 0,-20 Z" fill="#E06733"/>'
        f'<path transform="translate(24,35)" d="M0,-9 C4,-4 6,-1 6,3 C6,8 3,11 0,11 C-3,11 -6,8 -6,3 C-6,0 -3,-4 0,-9 Z" fill="#FFAB4D"/>'
        '</svg>'
    )
    import base64
    return "data:image/svg+xml;base64," + base64.b64encode(svg.encode("utf-8")).decode("ascii")


def build_drawio_xml(state: SessionState) -> str:
    open_net = next((n for n in state.networks if n.id == "open"), None)
    closed_net = next((n for n in state.networks if n.id == "closed"), None)
    open_name = escape(open_net.name if open_net else "Открытая сеть")
    closed_name = escape(closed_net.name if closed_net else "Закрытый сегмент")

    open_devs = [d for d in state.devices if d.network_id == "open"]
    closed_devs = [d for d in state.devices if d.network_id == "closed"]
    max_rows = max(len(open_devs), len(closed_devs), 1)
    seg_height = max(340, 140 + max_rows * 86)
    legend_y = 110 + seg_height
    total_height = legend_y + 70 + max(1, len(state.rules)) * 30

    cells: list[str] = [
        '<mxCell id="0"/>',
        '<mxCell id="1" parent="0"/>',
        f'<mxCell id="t1" value="СХЕМА РАЗМЕЩЕНИЯ «СИНОНИКС»" style="text;html=1;align=left;verticalAlign=middle;fontColor=#FFFFFF;fontSize=20;fontStyle=1;fontFamily=Open Sans;" vertex="1" parent="1"><mxGeometry x="40" y="16" width="760" height="30" as="geometry"/></mxCell>',
        f'<mxCell id="t2" value="Правил Синоникса: {state.rules_count}" style="text;html=1;align=left;verticalAlign=middle;fontColor=#B9C5CD;fontSize=12;fontFamily=Open Sans;" vertex="1" parent="1"><mxGeometry x="40" y="46" width="900" height="20" as="geometry"/></mxCell>',
        f'<mxCell id="seg_open" value="&lt;b&gt;ОТКРЫТАЯ СЕТЬ&lt;/b&gt;&lt;br&gt;&lt;span style=&quot;font-weight:normal;font-size:11px&quot;&gt;{open_name}&lt;/span&gt;" style="rounded=1;arcSize=5;dashed=1;dashPattern=8 6;fillColor=none;strokeColor=#E06733;strokeWidth=2;html=1;align=left;verticalAlign=top;spacingLeft=14;spacingTop=6;fontColor=#E06733;fontSize=12;fontFamily=Open Sans;" vertex="1" parent="1"><mxGeometry x="30" y="90" width="320" height="{seg_height}" as="geometry"/></mxCell>',
        f'<mxCell id="seg_closed" value="&lt;b&gt;ЗАКРЫТЫЙ СЕГМЕНТ&lt;/b&gt;&lt;br&gt;&lt;span style=&quot;font-weight:normal;font-size:11px&quot;&gt;{closed_name}&lt;/span&gt;" style="rounded=1;arcSize=5;dashed=1;dashPattern=8 6;fillColor=none;strokeColor=#35C4AF;strokeWidth=2;html=1;align=left;verticalAlign=top;spacingLeft=14;spacingTop=6;fontColor=#35C4AF;fontSize=12;fontFamily=Open Sans;" vertex="1" parent="1"><mxGeometry x="584" y="90" width="836" height="{seg_height}" as="geometry"/></mxCell>',
    ]

    dev_cell_id: dict[str, str] = {}
    for idx, dev in enumerate(open_devs):
        cid = f"o_{idx+1}"
        dev_cell_id[f"open:{dev.name}"] = cid
        y = 175 + idx * 84
        cells.append(
            f'<mxCell id="{cid}" value="&lt;b&gt;{escape(dev.name)}&lt;/b&gt;" style="rounded=1;arcSize=14;fillColor=#4A5D6A;strokeColor=none;html=1;whiteSpace=wrap;align=left;verticalAlign=middle;spacingLeft=14;spacingRight=8;fontColor=#FFFFFF;fontSize=13;fontFamily=Open Sans;" vertex="1" parent="1"><mxGeometry x="70" y="{y}" width="240" height="56" as="geometry"/></mxCell>'
        )

    for idx, dev in enumerate(closed_devs):
        cid = f"c_{idx+1}"
        dev_cell_id[f"closed:{dev.name}"] = cid
        y = 175 + idx * 84
        cells.append(
            f'<mxCell id="{cid}" value="&lt;b&gt;{escape(dev.name)}&lt;/b&gt;" style="rounded=1;arcSize=14;fillColor=#4A5D6A;strokeColor=none;html=1;whiteSpace=wrap;align=left;verticalAlign=middle;spacingLeft=14;spacingRight=8;fontColor=#FFFFFF;fontSize=13;fontFamily=Open Sans;" vertex="1" parent="1"><mxGeometry x="1150" y="{y}" width="240" height="56" as="geometry"/></mxCell>'
        )

    fw_h = min(280, seg_height - 90)
    fw_uri = _firewall_svg_data_uri(fw_h)
    cells.append(
        f'<mxCell id="fw" value="МЭ" style="shape=image;imageAspect=0;aspect=fixed;html=1;image={fw_uri};verticalLabelPosition=top;verticalAlign=bottom;labelPosition=center;align=center;fontColor=#FFAB4D;fontSize=13;fontStyle=1;fontFamily=Open Sans;" vertex="1" parent="1"><mxGeometry x="560" y="155" width="48" height="{fw_h}" as="geometry"/></mxCell>'
    )

    sx_y = 90 + (seg_height - 120) // 2
    cells.extend([
        f'<mxCell id="sx_label" value="СИНОНИКС" style="text;html=1;align=center;verticalAlign=middle;fontColor=#E06733;fontSize=13;fontStyle=1;fontFamily=Open Sans;" vertex="1" parent="1"><mxGeometry x="644" y="{sx_y-30}" width="240" height="24" as="geometry"/></mxCell>',
        f'<mxCell id="sx_box" value="" style="rounded=1;arcSize=10;fillColor=#FFFFFF;strokeColor=#E06733;strokeWidth=2;html=1;" vertex="1" parent="1"><mxGeometry x="644" y="{sx_y}" width="240" height="120" as="geometry"/></mxCell>',
        f'<mxCell id="node_left" value="УЗЕЛ А" style="rounded=1;arcSize=12;fillColor=#F2F4F6;strokeColor=#B9C5CD;html=1;fontColor=#3A4D59;fontSize=10;fontStyle=1;fontFamily=Open Sans;" vertex="1" parent="1"><mxGeometry x="656" y="{sx_y+20}" width="64" height="80" as="geometry"/></mxCell>',
        f'<mxCell id="core" value="ЯДРО" style="shape=hexagon;perimeter=hexagonPerimeter2;fixedSize=1;size=14;fillColor=#F2F4F6;strokeColor=#B9C5CD;html=1;fontColor=#3A4D59;fontSize=10;fontStyle=1;fontFamily=Open Sans;" vertex="1" parent="1"><mxGeometry x="732" y="{sx_y+20}" width="64" height="80" as="geometry"/></mxCell>',
        f'<mxCell id="node_right" value="УЗЕЛ В" style="rounded=1;arcSize=12;fillColor=#F2F4F6;strokeColor=#B9C5CD;html=1;fontColor=#3A4D59;fontSize=10;fontStyle=1;fontFamily=Open Sans;" vertex="1" parent="1"><mxGeometry x="808" y="{sx_y+20}" width="64" height="80" as="geometry"/></mxCell>',
    ])

    has_usb = any(r.uses_usb for r in state.rules)
    if has_usb:
        cells.append(
            f'<mxCell id="usb_drive" value="USB-носитель" style="rounded=1;arcSize=30;fillColor=#354552;strokeColor=#B9C5CD;html=1;fontColor=#FFFFFF;fontSize=11;fontStyle=1;fontFamily=Open Sans;" vertex="1" parent="1"><mxGeometry x="633" y="{sx_y+145}" width="110" height="34" as="geometry"/></mxCell>'
        )

    # Рёбра по правилам
    for idx, rule in enumerate(state.rules):
        color = RULE_COLORS[idx % len(RULE_COLORS)]
        start_arrow = "block" if rule.mode == "two-way" else "none"
        proto_text = (
            f"{rule.protocol} {rule.port}".strip()
            if isinstance(rule.protocol, str) and rule.port
            else (rule.protocol if isinstance(rule.protocol, str) else "Файлы")
        )
        label = escape(f"{rule.id} · {proto_text}")

        open_dev = (rule.source_devices[0] if rule.from_net == "open" else rule.target_device) or ""
        closed_dev = (rule.target_device if rule.from_net == "open" else rule.source_devices[0]) or ""
        o_cid = dev_cell_id.get(f"open:{open_dev}", "o_1")
        c_cid = dev_cell_id.get(f"closed:{closed_dev}", "c_1")

        if rule.uses_usb:
            cells.append(
                f'<mxCell id="e_usb_{rule.id}" value="{label}" style="edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;strokeColor={color};strokeWidth=2;endArrow=block;endFill=1;startArrow={start_arrow};startFill=1;labelBackgroundColor=#354552;fontColor=#FFFFFF;fontSize=10;fontStyle=1;fontFamily=Open Sans;" edge="1" parent="1" source="usb_drive" target="node_left"><mxGeometry relative="1" as="geometry"/></mxCell>'
            )
        else:
            src_left, tgt_left = (o_cid, "node_left") if rule.from_net == "open" else ("node_left", o_cid)
            cells.append(
                f'<mxCell id="e_l_{rule.id}" value="{label}" style="edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;strokeColor={color};strokeWidth=2;endArrow=block;endFill=1;startArrow={start_arrow};startFill=1;labelBackgroundColor=#354552;fontColor=#FFFFFF;fontSize=10;fontStyle=1;fontFamily=Open Sans;" edge="1" parent="1" source="{src_left}" target="{tgt_left}"><mxGeometry relative="1" as="geometry"/></mxCell>'
            )

        src_right, tgt_right = ("node_right", c_cid) if rule.from_net == "open" else (c_cid, "node_right")
        cells.append(
            f'<mxCell id="e_r_{rule.id}" value="{label}" style="edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;strokeColor={color};strokeWidth=2;endArrow=block;endFill=1;startArrow={start_arrow};startFill=1;labelBackgroundColor=#354552;fontColor=#FFFFFF;fontSize=10;fontStyle=1;fontFamily=Open Sans;" edge="1" parent="1" source="{src_right}" target="{tgt_right}"><mxGeometry relative="1" as="geometry"/></mxCell>'
        )

    # Описание под схемой
    cells.append(
        f'<mxCell id="leg_title" value="Правил Синоникса: {state.rules_count}" style="text;html=1;align=center;verticalAlign=middle;whiteSpace=wrap;fontColor=#FFFFFF;fontSize=13;fontStyle=1;fontFamily=Open Sans;" vertex="1" parent="1"><mxGeometry x="40" y="{legend_y}" width="1370" height="28" as="geometry"/></mxCell>'
    )
    for idx, rule in enumerate(state.rules):
        color = RULE_COLORS[idx % len(RULE_COLORS)]
        ry = legend_y + 32 + idx * 28
        mode_ru = "двунаправленное правило" if rule.mode == "two-way" else "однонаправленное правило"
        cells.append(
            f'<mxCell id="m_{rule.id}" value="" style="rounded=1;arcSize=30;fillColor={color};strokeColor=none;" vertex="1" parent="1"><mxGeometry x="40" y="{ry+9}" width="12" height="12" as="geometry"/></mxCell>'
        )
        cells.append(
            f'<mxCell id="l_{rule.id}" value="{rule.id}. {escape(rule.description)} ({mode_ru})" style="text;html=1;align=left;verticalAlign=middle;whiteSpace=wrap;fontColor=#FFFFFF;fontSize=11;fontFamily=Open Sans;" vertex="1" parent="1"><mxGeometry x="62" y="{ry}" width="1350" height="28" as="geometry"/></mxCell>'
        )

    footer_y = legend_y + 36 + len(state.rules) * 28
    cells.append(
        f'<mxCell id="leg_footer" value="МЭ стоит на границе закрытого сегмента. Синоникс размещён в закрытом сегменте сразу за МЭ: Узел А обращён к открытой сети, Узел В к системам закрытого сегмента." style="text;html=1;align=left;verticalAlign=middle;whiteSpace=wrap;fontColor=#B9C5CD;fontSize=11;fontFamily=Open Sans;" vertex="1" parent="1"><mxGeometry x="62" y="{footer_y}" width="1350" height="28" as="geometry"/></mxCell>'
    )

    return (
        '<mxfile host="app.diagrams.net">'
        '<diagram id="synonyx-scheme" name="Схема Синоникса">'
        f'<mxGraphModel dx="1450" dy="{total_height}" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="1450" pageHeight="{total_height}" math="0" shadow="0" background="#303E48">'
        f'<root>{"".join(cells)}</root>'
        '</mxGraphModel></diagram></mxfile>'
    )
