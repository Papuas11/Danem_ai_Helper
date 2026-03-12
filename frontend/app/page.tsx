'use client';

import { useEffect, useState } from 'react';
import { apiGet, apiPost, apiPut } from '../lib/api';

type Deal = any;
type Instrument = any;

export default function HomePage() {
  const [tab, setTab] = useState<'assistant' | 'instruments' | 'history'>('assistant');
  const [text, setText] = useState('Нам нужна калибровка 3 манометров, срочно, без выезда');
  const [deal, setDeal] = useState<Deal | null>(null);
  const [deals, setDeals] = useState<Deal[]>([]);
  const [instruments, setInstruments] = useState<Instrument[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadData = async () => {
    try {
      const [d, i] = await Promise.all([apiGet<Deal[]>('/api/deals'), apiGet<Instrument[]>('/api/instruments')]);
      setDeals(d);
      setInstruments(i);
    } catch (e) {
      setError(String(e));
    }
  };

  useEffect(() => { loadData(); }, []);

  const analyze = async () => {
    setLoading(true); setError(null);
    try {
      const result = await apiPost<Deal>('/api/deals/analyze', { input_text: text, title: 'Запрос с UI' });
      setDeal(result);
      await loadData();
    } catch (e) { setError(String(e)); }
    setLoading(false);
  };

  const recalc = async () => {
    if (!deal) return;
    setLoading(true);
    try {
      const result = await apiPost<Deal>(`/api/deals/${deal.id}/recalculate`, {
        parsed_quantity: deal.parsed_quantity,
        parsed_onsite: deal.parsed_onsite,
        manager_notes: deal.manager_notes,
        final_price: deal.final_price,
        final_cost: deal.final_cost,
        deviation_reason_tag: deal.deviation_reason_tag,
        deviation_reason_text: deal.deviation_reason_text,
      });
      setDeal(result);
      await loadData();
    } catch (e) { setError(String(e)); }
    setLoading(false);
  };

  return (
    <main>
      <h1>DANEM Sales Copilot MVP</h1>
      <div className="tabs card">
        <button className={tab === 'assistant' ? 'active' : ''} onClick={() => setTab('assistant')}>AI помощник</button>
        <button className={tab === 'instruments' ? 'active' : ''} onClick={() => setTab('instruments')}>База приборов</button>
        <button className={tab === 'history' ? 'active' : ''} onClick={() => setTab('history')}>История сделок</button>
      </div>
      {error && <p className="error">{error}</p>}

      {tab === 'assistant' && (
        <div>
          <div className="card">
            <h3>A. Ввод</h3>
            <textarea rows={4} value={text} onChange={(e) => setText(e.target.value)} />
            <button onClick={analyze} disabled={loading}>Анализировать</button>
            <button onClick={() => setText('')}>Очистить</button>
          </div>

          {deal && (
            <div className="grid">
              <div className="card"><h3>B. Разбор</h3><p>Прибор: {deal.parsed_instrument_name || '-'}</p><p>Услуга: {deal.parsed_service_type || '-'}</p><p>Количество: {deal.parsed_quantity || '-'}</p><p>Выезд: {deal.parsed_onsite}</p><p>Срочность: {deal.parsed_urgency}</p><p>Confidence: {Math.round(deal.ai_confidence * 100)}%</p></div>
              <div className="card"><h3>C. Полнота</h3><p>{deal.completeness_score}%</p><p>Известно: {JSON.stringify({ instrument: deal.parsed_instrument_name, service: deal.parsed_service_type, quantity: deal.parsed_quantity })}</p><p>Не хватает: {deal.missing_fields?.join(', ') || '—'}</p></div>
              <div className="card"><h3>D. Вероятность</h3><p>{deal.deal_probability}%</p></div>
              <div className="card"><h3>E. Недостающие данные</h3><ul>{(deal.missing_fields || []).map((x: string) => <li key={x}>{x}</li>)}</ul></div>
              <div className="card"><h3>F. Следующие 3 шага</h3><ol>{(deal.next_steps || []).slice(0,3).map((x: string) => <li key={x}>{x}</li>)}</ol></div>
              <div className="card"><h3>G. Экономика</h3><p>Цена: {deal.calculated_price ?? '-'}</p><p>Себестоимость: {deal.calculated_cost ?? '-'}</p><p>Прибыль: {deal.calculated_profit ?? '-'}</p><p>Маржа: {deal.calculated_margin ?? '-'}%</p></div>
              <div className="card"><h3>H. Черновик ответа</h3><p>{deal.draft_reply}</p></div>
              <div className="card"><h3>I. Предупреждения</h3><ul>{(deal.warnings || []).map((x: string) => <li key={x}>{x}</li>)}</ul></div>
              <div className="card">
                <h3>J. Ручные правки</h3>
                <label>Количество<input type="number" value={deal.parsed_quantity || ''} onChange={(e) => setDeal({ ...deal, parsed_quantity: Number(e.target.value) || null })} /></label>
                <label>Выезд<select value={deal.parsed_onsite || 'unknown'} onChange={(e) => setDeal({ ...deal, parsed_onsite: e.target.value })}><option value="yes">yes</option><option value="no">no</option><option value="unknown">unknown</option></select></label>
                <label>Заметки<textarea rows={2} value={deal.manager_notes || ''} onChange={(e) => setDeal({ ...deal, manager_notes: e.target.value })} /></label>
                <label>Финальная цена<input type="number" value={deal.final_price || ''} onChange={(e) => setDeal({ ...deal, final_price: Number(e.target.value) || null })} /></label>
                <label>Финальная себестоимость<input type="number" value={deal.final_cost || ''} onChange={(e) => setDeal({ ...deal, final_cost: Number(e.target.value) || null })} /></label>
                <label>Тег отклонения<input value={deal.deviation_reason_tag || ''} onChange={(e) => setDeal({ ...deal, deviation_reason_tag: e.target.value })} /></label>
                <label>Причина<textarea rows={2} value={deal.deviation_reason_text || ''} onChange={(e) => setDeal({ ...deal, deviation_reason_text: e.target.value })} /></label>
                <button onClick={recalc}>Пересчитать</button>
              </div>
              <div className="card"><h3>K. Похожие сделки</h3><ul>{(deal.similar_deals || []).map((d: any) => <li key={d.id}>{d.instrument} / {d.service} / calc {d.calculated_price} / final {d.final_price}</li>)}</ul></div>
            </div>
          )}
        </div>
      )}

      {tab === 'instruments' && <InstrumentsTab instruments={instruments} onReload={loadData} />}
      {tab === 'history' && <HistoryTab deals={deals} setDeal={setDeal} setTab={setTab} />}
    </main>
  );
}

function InstrumentsTab({ instruments, onReload }: { instruments: Instrument[]; onReload: () => Promise<void> }) {
  const [name, setName] = useState('');
  const [category, setCategory] = useState('');
  const [search, setSearch] = useState('');
  const filtered = instruments.filter((i) => i.name.toLowerCase().includes(search.toLowerCase()));

  const create = async () => {
    if (!name || !category) return;
    await apiPost('/api/instruments', { name, category, status: 'active' });
    setName(''); setCategory('');
    await onReload();
  };

  return <div className="card"><h3>Управление приборами</h3><label>Поиск<input value={search} onChange={(e) => setSearch(e.target.value)} /></label>
    <div className="grid">{filtered.map((i) => <div className="card" key={i.id}><b>{i.name}</b><p>{i.category} | {i.status}</p><p className="small">aliases: {(i.aliases || []).map((a: any)=>a.alias).join(', ')}</p><p className="small">services: {(i.services || []).length}</p></div>)}</div>
    <h4>Создать прибор</h4><input placeholder="name" value={name} onChange={(e)=>setName(e.target.value)} /><input placeholder="category" value={category} onChange={(e)=>setCategory(e.target.value)} /><button onClick={create}>Создать</button>
  </div>;
}

function HistoryTab({ deals, setDeal, setTab }: { deals: Deal[]; setDeal: (d: Deal) => void; setTab: (t: 'assistant' | 'instruments' | 'history') => void }) {
  return <div className="card"><h3>Сделки</h3>{deals.length === 0 && <p>Нет сделок</p>}<ul>{deals.map((d) => <li key={d.id}><b>{d.title}</b> | {d.parsed_instrument_name} | {d.deal_probability}% <button onClick={() => { setDeal(d); setTab('assistant'); }}>Открыть</button></li>)}</ul></div>;
}
