"use client";
import { useState } from "react";
const samples = [
  { label: "English", lang: "en", text: "A little less typing. More room for the thought.", command: "open notepad" },
  { label: "தமிழ்", lang: "ta", text: "என் எண்ணங்களை என் மொழியில் எழுதுகிறேன்.", command: "நோட்பேடு திற" },
  { label: "Tanglish", lang: "ta", text: "நாளைக்கு meeting இருக்கு. Notes தயார் பண்ணலாம்.", command: "notepad open பண்ணு" },
];
export function Demo() {
  const [selected, setSelected] = useState(0);
  const [shown, setShown] = useState(false);
  const sample = samples[selected];
  return <div className="demo app-frame" aria-label="Illustrative dictation demo">
    <div className="demo-top"><span><span className="status-dot" /> Dictation preview</span><span>Illustrative demo</span></div>
    <div className="language-picker" aria-label="Demo language">{samples.map((item, i) => <button key={item.label} aria-pressed={selected === i} onClick={() => { setSelected(i); setShown(false); }}>{item.label}</button>)}</div>
    <div className="paper"><span className="paper-label">A note to yourself</span><p lang={sample.lang} aria-live="polite">{shown ? sample.text : "Your next thought starts here."}</p><span className="paper-line" /><span className="paper-line short" /></div>
    <div className="demo-bottom"><div className="wave" aria-hidden="true">{[12, 24, 36, 19, 30, 42, 25, 14, 29, 37, 21, 12].map((height, i) => <i key={i} style={{ height }} />)}</div><button className="demo-play" onClick={() => setShown(!shown)}>{shown ? "Reset demo" : "Try the demo"}<span aria-hidden="true"> ↗</span></button></div>
    <p className="demo-disclaimer">Preset text only. No microphone access or live transcription.</p>
  </div>;
}
