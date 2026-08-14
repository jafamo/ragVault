import { useEffect, useState } from "react";
import {
  getStatsByFormat,
  getStatsByStatus,
  getStatsByTag,
  getStatsErrors,
  getStatsTimeline,
  type ErrorDocumentResponse,
} from "../../services/api";
import FormatChart from "./FormatChart";
import StatusTiles from "./StatusTiles";
import TimelineChart from "./TimelineChart";
import TagChart from "./TagChart";
import ErrorsTable from "./ErrorsTable";

interface StatsData {
  byFormat: Record<string, number>;
  byStatus: Record<string, number>;
  byTag: Record<string, number>;
  timeline: Record<string, number>;
  errors: ErrorDocumentResponse[];
}

export default function StatsDashboard() {
  const [data, setData] = useState<StatsData | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([
      getStatsByFormat(),
      getStatsByStatus(),
      getStatsByTag(),
      getStatsTimeline(),
      getStatsErrors(),
    ])
      .then(([byFormat, byStatus, byTag, timeline, errors]) =>
        setData({ byFormat, byStatus, byTag, timeline, errors }),
      )
      .catch(() => setError("No se han podido cargar las estadísticas."));
  }, []);

  if (error) {
    return (
      <main className="app-main stats-view">
        <p className="stats-empty">{error}</p>
      </main>
    );
  }

  if (!data) {
    return (
      <main className="app-main stats-view">
        <p className="stats-empty">Cargando estadísticas…</p>
      </main>
    );
  }

  return (
    <main className="app-main stats-view">
      <h1 className="stats-title">Estadísticas</h1>

      <StatusTiles byStatus={data.byStatus} />

      <div className="stats-grid">
        <FormatChart byFormat={data.byFormat} />
        <TimelineChart timeline={data.timeline} />
        <TagChart byTag={data.byTag} />
      </div>

      <ErrorsTable errors={data.errors} />
    </main>
  );
}
