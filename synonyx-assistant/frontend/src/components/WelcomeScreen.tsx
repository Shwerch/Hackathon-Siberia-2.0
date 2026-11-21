import React from "react";

interface Props {
  onUseExample: (text: string) => void;
}

const EXAMPLE_TEXT =
  "Есть закрытая сеть цеха и офисная сеть. Два сервера цеха отправляют журналы на сервер в офисе по UDP 514. Сервер в офисе опрашивает контроллер по Modbus TCP. Инженер из офиса передаёт в цех файлы программ для станков, их нужно проверять антивирусом.";

export const WelcomeScreen: React.FC<Props> = ({ onUseExample }) => {
  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/70 p-5 space-y-3">
      <h2 className="text-base font-semibold text-teal-400">
        Проектирование размещения СКИО «Синоникс» (v1.9)
      </h2>
      <p className="text-sm text-slate-300 leading-relaxed">
        Я помогу понять, где в вашей инфраструктуре поставить «Синоникс» и межсетевой экран,
        рассчитаю минимальное число правил передачи и подготовлю схему в формате{" "}
        <code className="text-amber-400">.drawio</code>. Опишите две сети и потоки между ними.
      </p>
      <div className="rounded-lg bg-slate-950/80 border border-slate-800 p-3 text-xs text-slate-300">
        <div className="font-medium text-slate-400 mb-1">Пример запроса:</div>
        <p className="italic">«{EXAMPLE_TEXT}»</p>
        <button
          type="button"
          onClick={() => onUseExample(EXAMPLE_TEXT)}
          className="mt-2.5 inline-flex items-center rounded-md bg-teal-600/20 px-3 py-1.5 text-xs font-medium text-teal-300 hover:bg-teal-600/30 transition"
        >
          Подставить пример в поле ввода
        </button>
      </div>
    </div>
  );
};
