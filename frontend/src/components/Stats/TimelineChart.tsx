import { Bar, BarChart, CartesianGrid, LabelList, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

interface Props {
  timeline: Record<string, number>;
}

export default function TimelineChart({ timeline }: Props) {
  const data = Object.entries(timeline)
    .map(([days, count]) => ({ days: Number(days), count, label: `${days}d` }))
    .sort((a, b) => a.days - b.days);

  return (
    <section className="stats-card" aria-label="Documentos ingeridos por franja temporal">
      <h2 className="stats-card-title">Ingeridos por franja temporal</h2>
      <ResponsiveContainer width="100%" height={220}>
        <BarChart data={data} margin={{ top: 8, right: 12, left: 0, bottom: 0 }}>
          <CartesianGrid stroke="var(--chart-grid)" vertical={false} />
          <XAxis
            dataKey="label"
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
            formatter={(value) => [value, "Documentos"]}
            labelFormatter={(label) => `Últimos ${label}`}
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
    </section>
  );
}
