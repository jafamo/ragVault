import { Bar, BarChart, Cell, CartesianGrid, LabelList, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

interface Props {
  byTag: Record<string, number>;
}

export default function TagChart({ byTag }: Props) {
  const data = Object.entries(byTag)
    .map(([tag, count]) => ({ tag: tag === "sin_tag" ? "Sin tag" : tag, count, untagged: tag === "sin_tag" }))
    .sort((a, b) => b.count - a.count);

  return (
    <section className="stats-card" aria-label="Documentos por tag">
      <h2 className="stats-card-title">Por tag</h2>
      {data.every((d) => d.count === 0) ? (
        <p className="stats-empty">Todavía no hay documentos tagueados.</p>
      ) : (
        <ResponsiveContainer width="100%" height={Math.max(160, data.length * 32)}>
          <BarChart data={data} layout="vertical" margin={{ top: 4, right: 24, left: 8, bottom: 0 }}>
            <CartesianGrid stroke="var(--chart-grid)" horizontal={false} />
            <XAxis
              type="number"
              allowDecimals={false}
              tick={{ fill: "var(--chart-text)", fontSize: 11 }}
              axisLine={false}
              tickLine={false}
            />
            <YAxis
              dataKey="tag"
              type="category"
              tick={{ fill: "var(--chart-text)", fontSize: 11 }}
              axisLine={{ stroke: "var(--chart-grid)" }}
              tickLine={false}
              width={90}
            />
            <Tooltip
              cursor={{ fill: "var(--chart-grid)", opacity: 0.4 }}
              formatter={(value) => [value, "Documentos"]}
              contentStyle={{
                background: "var(--sf)",
                border: "1px solid var(--ln)",
                borderRadius: 4,
                color: "var(--tx)",
                fontSize: 12,
              }}
            />
            <Bar dataKey="count" name="Documentos" radius={[0, 4, 4, 0]}>
              {data.map((entry) => (
                <Cell
                  key={entry.tag}
                  fill={entry.untagged ? "var(--chart-neutral)" : "var(--chart-accent)"}
                />
              ))}
              <LabelList dataKey="count" position="right" fill="var(--chart-text)" fontSize={11} />
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      )}
    </section>
  );
}
