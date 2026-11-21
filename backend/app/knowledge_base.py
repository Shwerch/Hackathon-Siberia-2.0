from __future__ import annotations

import os
import re
from dataclasses import dataclass

from .schemas import SourceRef


@dataclass
class KBChunk:
    file: str
    section: str
    text: str
    tokens: set[str]


BUILTIN_CHUNKS: list[tuple[str, str, str]] = [
    (
        "01_scope_functions_synonyx_1.9.md",
        "Раздел 3. Общие принципы правил",
        "На одном ПАК «Синоникс» версии 1.9 можно настроить до 256 правил. Это ограничение аппаратной платформы ПАК. Передача возможна только по разрешающим правилам; правило задаётся на каждом из двух Узлов независимо.",
    ),
    (
        "01_scope_functions_synonyx_1.9.md",
        "Раздел 2. Как устроено устройство",
        "Устройство состоит из трёх изолированных плат: Узел А, Ядро, Узел В. Прямой маршрутизации между сетями нет, доступ на диапазон адресов не открывается. Передача идёт только в режиме «точка-точка». USB-порт для носителей есть только на Узле А.",
    ),
    (
        "01_scope_functions_synonyx_1.9.md",
        "Раздел 4. Передача данных",
        "Протоколы данных: TCP, UDP (однонаправленный и двунаправленный режимы) и промышленные протоколы MQTT, Modbus TCP, МЭК 60870-5-104 (всегда двунаправленные). Скорость передачи до 1 Гбит/с. На стороне отправителей используется collect, на стороне получателя — exchange.",
    ),
    (
        "01_scope_functions_synonyx_1.9.md",
        "Раздел 5. Передача файлов",
        "Способы: вручную (SFTP), PULL по расписанию (SFTP, FTP, SMB), PUSH при поступлении (SFTP, FTP, SMB), USB-носитель на Узле А. Проверки: маска имени, тип и расширение, размер, целостность (цифровая подпись), внешние системы по ICAP (антивирус, песочница, DLP). Встроенного антивируса нет. Число пользователей ограничивается лицензией: каждый ручной пользователь + 1 пользователь на каждое правило с PULL.",
    ),
    (
        "01_scope_functions_synonyx_1.9.md",
        "Раздел 9. Ограничения и Раздел 10. Отличия от NGFW и диода данных",
        "Встроенного антивируса нет. Нет функций PAM-системы (записи действий конкретного человека — это задача СКДПУ НТ). При передаче данных «Синоникс» пересобирает только нижние 4 уровня модели OSI и не анализирует содержимое обычного TCP/UDP-трафика, поэтому работает в связке с межсетевым экраном (МЭ/NGFW).",
    ),
    (
        "02_methodology.md",
        "Раздел 2. Размещение",
        "Логическая цепочка: открытая сеть — МЭ — «Синоникс» (Узел А обращён к открытой сети, Узел В к закрытой) — системы закрытого сегмента. МЭ стоит на границе закрытого сегмента со стороны открытой сети. «Синоникс» ставится внутри закрытого сегмента сразу за МЭ. Поток с USB-носителя идёт сразу на Узел А, минуя МЭ.",
    ),
    (
        "02_methodology.md",
        "Раздел 3. Подсчёт правил",
        "1 поток = 1 правило. Для данных: несколько отправителей одному получателю на один порт и протокол = 1 правило; разные получатели/порты/протоколы = отдельные правила. NTP = 1 однонаправленное правило. Для файлов: направление не создаёт второе правило; разделение требуется при разных проверках на одной стороне, изоляции видимости файлов или конфликте PULL/PUSH на узле.",
    ),
]


def _tokenize(text: str) -> set[str]:
    return set(re.findall(r"[a-zа-яё0-9_.-]{2,}", text.lower()))


class KnowledgeBase:
    def __init__(self, kb_dir: str) -> None:
        self.chunks: list[KBChunk] = []
        self._load(kb_dir)

    def _load(self, kb_dir: str) -> None:
        loaded_files = 0
        if os.path.isdir(kb_dir):
            for fname in sorted(os.listdir(kb_dir)):
                if not (fname.endswith(".md") or fname.endswith(".txt")):
                    continue
                fpath = os.path.join(kb_dir, fname)
                if not os.path.isfile(fpath):
                    continue
                loaded_files += 1
                with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                self._parse_markdown(fname, content)

        if loaded_files == 0:
            for fname, section, text in BUILTIN_CHUNKS:
                self.chunks.append(
                    KBChunk(
                        file=fname,
                        section=section,
                        text=text,
                        tokens=_tokenize(f"{section} {text}"),
                    )
                )

    def _parse_markdown(self, fname: str, content: str) -> None:
        current_section = "Общие сведения"
        buf: list[str] = []
        for line in content.splitlines():
            if line.startswith("#"):
                if buf:
                    body = "\n".join(buf).strip()
                    if body:
                        self.chunks.append(
                            KBChunk(
                                file=fname,
                                section=current_section,
                                text=body[:1800],
                                tokens=_tokenize(f"{current_section} {body}"),
                            )
                        )
                    buf = []
                current_section = line.lstrip("#").strip()
            else:
                buf.append(line)
        if buf:
            body = "\n".join(buf).strip()
            if body:
                self.chunks.append(
                    KBChunk(
                        file=fname,
                        section=current_section,
                        text=body[:1800],
                        tokens=_tokenize(f"{current_section} {body}"),
                    )
                )

    def search(self, query: str, top_k: int = 4) -> tuple[str, list[SourceRef]]:
        q_tokens = _tokenize(query)
        scored: list[tuple[int, KBChunk]] = []
        for ch in self.chunks:
            overlap = len(q_tokens & ch.tokens)
            if overlap > 0:
                # Приоритет документам 01 и 02
                priority = 2 if ch.file.startswith("01_") or ch.file.startswith("02_") else 0
                scored.append((overlap + priority, ch))

        scored.sort(key=lambda x: x[0], reverse=True)
        selected = [ch for _, ch in scored[:top_k]]
        if not selected:
            selected = self.chunks[:2]

        context_lines = []
        sources: list[SourceRef] = []
        seen_src: set[tuple[str, str]] = set()
        for ch in selected:
            context_lines.append(f"[{ch.file} | {ch.section}]\n{ch.text}")
            key = (ch.file, ch.section)
            if key not in seen_src:
                seen_src.add(key)
                sources.append(SourceRef(file=ch.file, section=ch.section))

        return "\n\n".join(context_lines), sources
