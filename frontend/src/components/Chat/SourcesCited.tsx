import { useThemeStore } from "../../stores/themeStore";
import type { Source } from "../../stores/chatStore";

export default function SourcesCited({ sources }: { sources: Source[] }) {
  const skin = useThemeStore((s) => s.skin);

  if (skin === "terminal") {
    return (
      <div className="receipt">
        {sources.map((s, i) => (
          <div key={`${s.doc}-${s.page}-${i}`}>
            [src] <b>{s.doc}</b>:{s.page.replace(/\D/g, "")} &nbsp;
            score=<span className="score">{s.score.toFixed(2)}</span>
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className="receipt">
      <div className="receipt-title">Fuentes citadas</div>
      {sources.map((s, i) => (
        <div className="src-row" key={`${s.doc}-${s.page}-${i}`}>
          <span className="src-doc">{s.doc}</span>
          <span className="src-page">{s.page}</span>
          <span className="gauge">
            <span style={{ width: `${Math.round(s.score * 100)}%` }} />
          </span>
        </div>
      ))}
    </div>
  );
}
