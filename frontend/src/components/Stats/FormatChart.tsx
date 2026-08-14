import { Bar, BarChart, CartesianGrid, LabelList, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

interface Props {
  byFormat: Record<string, number>;
}

export default function FormatChart({ byFormat }: Props) {
  const data = Object.entries(byFormat)
    .map(([format, count]) => ({ format, count }))
    .sort((a, b) => b.count - a.count);

  return (
    <section className="stats-card" aria-label="Documentos por formato">
      <h2 className="stats-card-title">Por formato</h2>
      {data.length === 0 ? (
        <p className="stats-empty">Todavía no hay documentos cargados.</p>
      ) : (
        <ResponsiveContainer width="100%" height={220}>
          <BarChart data={data} margin={{ top: 8, right: 12, left: 0, bottom: 0 }}>
            <CartesianGrid stroke="var(--chart-grid)" vertical={false} />
            <XAxis
              dataKey="format"
              tick={{ fill: "var(--chart-text)", fontSize: 11 }}
              axisLine={{ stroke: "var(--chart-grid)" }}
              tickLine={false}
            />
            <YAxis
              allowDecimals={false}
              tick={{ fill: "var(--chart-text)", fontSize: 11 }}
              axisLine={false}
              tickLine={false}
              width={28}
            />
            <Tooltip
              cursor={{ fill: "var(--chart-grid)", opacity: 0.4 }}
              contentStyle={{
                background: "var(--sf)",
                border: "1px solid var(--ln)",
                borderRadius: 4,
                color: "var(--tx)",
                fontSize: 12,
              }}
            />
            <Bar dataKey="count" name="Documentos" fill="var(--chart-accent)" radius={[4, 4, 0, 0]}>
              <LabelList dataKey="count" position="top" fill="var(--chart-text)" fontSize={11} />
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      )}
    </section>
  );
}
