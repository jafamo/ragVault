interface Props {
  byStatus: Record<string, number>;
}

export default function StatusTiles({ byStatus }: Props) {
  const pendientes = (byStatus.queued ?? 0) + (byStatus.processing ?? 0);
  const procesados = byStatus.done ?? 0;
  const conError = byStatus.error ?? 0;

  const tiles = [
    { label: "Pendientes de procesar", value: pendientes, tone: "warn" as const },
    { label: "Procesados", value: procesados, tone: "good" as const },
    { label: "Con error", value: conError, tone: "critical" as const },
  ];

  return (
    <div className="stats-tiles" role="group" aria-label="Documentos por estado">
      {tiles.map((tile) => (
        <div key={tile.label} className={`stats-tile stats-tile-${tile.tone}`}>
          <span className="stats-tile-value">{tile.value}</span>
          <span className="stats-tile-label">{tile.label}</span>
        </div>
      ))}
    </div>
  );
}
