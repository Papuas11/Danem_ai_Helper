"use client";

import { useEffect, useState } from "react";
import { api } from "../lib/api";

type Deal = any;
type Instrument = any;

export default function Home() {
  const [tab, setTab] = useState<"manager" | "instruments" | "history">("manager");
  const [inputText, setInputText] = useState("We need calibration of 3 manometers, urgent, no onsite visit");
  const [deal, setDeal] = useState<Deal | null>(null);
  const [deals, setDeals] = useState<Deal[]>([]);
  const [instruments, setInstruments] = useState<Instrument[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadAll = async () => {
    try {
      const [dealList, instrumentList] = await Promise.all([api<Deal[]>("/api/deals"), api<Instrument[]>("/api/instruments")]);
      setDeals(dealList);
      setInstruments(instrumentList);
    } catch (e) {
      setError(String(e));
    }
  };

  useEffect(() => {
    loadAll();
  }, []);

  const analyze = async () => {
    setLoading(true);
    setError(null);
    try {
      const d = await api<Deal>("/api/deals/analyze", { method: "POST", body: JSON.stringify({ input_text: inputText, title: "New analysis" }) });
      setDeal(d);
      await loadAll();
    } catch (e) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
  };

  const recalc = async () => {
    if (!deal) return;
    const d = await api<Deal>(`/api/deals/${deal.id}/recalculate`, {
      method: "POST",
      body: JSON.stringify({
        parsed_quantity: deal.parsed_quantity,
        parsed_onsite: deal.parsed_onsite,
        manager_notes: deal.manager_notes,
        final_price: deal.final_price,
        final_cost: deal.final_cost,
        deviation_reason_tag: deal.deviation_reason_tag,
        deviation_reason_text: deal.deviation_reason_text,
      }),
    });
    setDeal(d);
    loadAll();
  };

  const managerView = (
    <div>
      <div className="card">
        <h3>A. Input block</h3>
        <textarea rows={4} value={inputText} onChange={(e) => setInputText(e.target.value)} />
        <button onClick={analyze} disabled={loading}>Analyze</button>
        <button onClick={() => setInputText("")}>Clear</button>
      </div>
      {deal && (
        <>
          <div className="grid">
            <div className="card"><h3>B. Parsed request</h3><pre>{JSON.stringify({ instrument: deal.parsed_instrument_name, service: deal.parsed_service_type, quantity: deal.parsed_quantity, onsite: deal.parsed_onsite, urgency: deal.parsed_urgency, confidence: deal.ai_confidence }, null, 2)}</pre></div>
            <div className="card"><h3>C. Completeness</h3><p>Score: {deal.completeness_score}</p><pre>{deal.missing_fields}</pre></div>
            <div className="card"><h3>D. Deal probability</h3><p>{deal.deal_probability}%</p></div>
            <div className="card"><h3>E. Missing client data</h3><pre>{deal.missing_fields}</pre></div>
            <div className="card"><h3>F. Next 3 steps</h3><pre>{deal.next_steps}</pre></div>
            <div className="card"><h3>G. Economics</h3><pre>{JSON.stringify({ price: deal.calculated_price, cost: deal.calculated_cost, profit: deal.calculated_profit, margin: deal.calculated_margin }, null, 2)}</pre></div>
            <div className="card"><h3>H. Draft reply</h3><p>{deal.draft_reply}</p></div>
            <div className="card"><h3>I. Warnings</h3><pre>{deal.warnings}</pre></div>
          </div>
          <div className="card">
            <h3>J. Manual edits / notes</h3>
            <label>Quantity<input type="number" value={deal.parsed_quantity ?? ""} onChange={(e) => setDeal({ ...deal, parsed_quantity: Number(e.target.value) || null })} /></label>
            <label>Onsite<select value={deal.parsed_onsite ?? "unknown"} onChange={(e) => setDeal({ ...deal, parsed_onsite: e.target.value })}><option value="yes">yes</option><option value="no">no</option><option value="unknown">unknown</option></select></label>
            <label>Manager notes<textarea rows={2} value={deal.manager_notes ?? ""} onChange={(e) => setDeal({ ...deal, manager_notes: e.target.value })} /></label>
            <label>Factual final price<input type="number" value={deal.final_price ?? ""} onChange={(e) => setDeal({ ...deal, final_price: Number(e.target.value) || null })} /></label>
            <label>Factual final cost<input type="number" value={deal.final_cost ?? ""} onChange={(e) => setDeal({ ...deal, final_cost: Number(e.target.value) || null })} /></label>
            <label>Deviation tag<input value={deal.deviation_reason_tag ?? ""} onChange={(e) => setDeal({ ...deal, deviation_reason_tag: e.target.value })} /></label>
            <label>Deviation reason<textarea rows={2} value={deal.deviation_reason_text ?? ""} onChange={(e) => setDeal({ ...deal, deviation_reason_text: e.target.value })} /></label>
            <button onClick={recalc}>Recalculate</button>
          </div>
          <div className="card">
            <h3>K. Similar deals</h3>
            {deals
              .filter((d) => d.id !== deal.id && d.parsed_instrument_name === deal.parsed_instrument_name)
              .slice(0, 5)
              .map((d) => (
                <div key={d.id}>#{d.id} {d.parsed_instrument_name}/{d.parsed_service_type} est:{d.calculated_price} final:{d.final_price ?? "-"} deviation:{(d.final_price ?? d.calculated_price) - d.calculated_price}</div>
              ))}
          </div>
        </>
      )}
    </div>
  );

  const instrumentsView = (
    <div className="card">
      <h3>Instruments database</h3>
      <p>Total: {instruments.length}</p>
      {instruments.map((i) => (
        <div key={i.id} className="card">
          <b>{i.name}</b> ({i.status}) | Category: {i.category}
          <div>Aliases: {i.aliases?.map((a: any) => a.alias).join(", ") || "-"}</div>
          <div>Services: {i.services?.map((s: any) => `${s.service_type} (${s.base_price})`).join(", ") || "-"}</div>
        </div>
      ))}
    </div>
  );

  const historyView = (
    <div className="card">
      <h3>Deal history</h3>
      {deals.map((d) => (
        <div key={d.id} className="card">
          <div>#{d.id} {d.title}</div>
          <div>{d.input_text}</div>
          <div>Prob: {d.deal_probability}% | Completeness: {d.completeness_score}</div>
          <div>Calc P/C/Pr/M: {d.calculated_price}/{d.calculated_cost}/{d.calculated_profit}/{d.calculated_margin}%</div>
          <div>Final P/C/Pr: {d.final_price ?? "-"}/{d.final_cost ?? "-"}/{d.final_profit ?? "-"}</div>
        </div>
      ))}
    </div>
  );

  return (
    <div className="container">
      <h1>DANEM Sales Copilot MVP</h1>
      <div className="tabs">
        <button onClick={() => setTab("manager")}>Manager AI</button>
        <button onClick={() => setTab("instruments")}>Instruments Database</button>
        <button onClick={() => setTab("history")}>Deal History</button>
      </div>
      {error && <div className="card">Error: {error}</div>}
      {loading && <div className="card">Loading...</div>}
      {tab === "manager" && managerView}
      {tab === "instruments" && instrumentsView}
      {tab === "history" && historyView}
    </div>
  );
}
