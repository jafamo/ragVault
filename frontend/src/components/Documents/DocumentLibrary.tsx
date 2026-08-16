import { useEffect, useMemo, useState } from "react";
import {
  deleteDocument,
  getDocumentFileUrl,
  listDocuments,
  type DocumentListItem,
} from "../../services/api";

const STATUS_LABELS: Record<string, string> = {
  queued: "En cola",
  processing: "Procesando",
  done: "Completado",
  error: "Error",
  cancelled: "Cancelado",
};

function formatSize(bytes: number | null): string {
  if (bytes === null) return "—";
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

interface Filters {
  status: string;
  filename: string;
  format: string;
  size: string;
  tags: string;
  path: string;
}

const EMPTY_FILTERS: Filters = { status: "", filename: "", format: "", size: "", tags: "", path: "" };

export default function DocumentLibrary() {
  const [documents, setDocuments] = useState<DocumentListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [filters, setFilters] = useState<Filters>(EMPTY_FILTERS);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  useEffect(() => {
    void loadDocuments();
  }, []);

  async function loadDocuments() {
    setLoading(true);
    setErrorMessage(null);
    try {
      const items = await listDocuments();
      setDocuments(items);
    } catch (err) {
      setErrorMessage(err instanceof Error ? err.message : "Error al cargar los documentos");
    } finally {
      setLoading(false);
    }
  }

  async function handleDelete(doc: DocumentListItem) {
    const confirmed = window.confirm(`¿Eliminar "${doc.filename}"? Esta acción no se puede deshacer.`);
    if (!confirmed) return;

    setDeletingId(doc.id);
    try {
      await deleteDocument(doc.id);
      setDocuments((prev) => prev.filter((d) => d.id !== doc.id));
    } catch (err) {
      setErrorMessage(err instanceof Error ? err.message : "Error al eliminar el documento");
    } finally {
      setDeletingId(null);
    }
  }

  const filteredDocuments = useMemo(() => {
    return documents.filter((doc) => {
      if (filters.status && doc.status !== filters.status) return false;
      if (filters.filename && !doc.filename.toLowerCase().includes(filters.filename.toLowerCase())) {
        return false;
      }
      if (filters.format && !doc.format.toLowerCase().includes(filters.format.toLowerCase())) {
        return false;
      }
      if (filters.size && !formatSize(doc.size_bytes).toLowerCase().includes(filters.size.toLowerCase())) {
        return false;
      }
      if (
        filters.tags &&
        !doc.tags.some((tag) => tag.toLowerCase().includes(filters.tags.toLowerCase()))
      ) {
        return false;
      }
      if (
        filters.path &&
        !(doc.absolute_path ?? "").toLowerCase().includes(filters.path.toLowerCase())
      ) {
        return false;
      }
      return true;
    });
  }, [documents, filters]);

  const statusOptions = useMemo(
    () => Array.from(new Set(documents.map((d) => d.status))).sort(),
    [documents],
  );

  return (
    <section className="library-view" aria-label="Biblioteca de documentos">
      <h1 className="library-title">Biblioteca de documentos</h1>

      {errorMessage && <p className="library-error">{errorMessage}</p>}

      {loading ? (
        <div className="stats-loading">Cargando documentos…</div>
      ) : documents.length === 0 ? (
        <p className="stats-empty">No hay documentos ingeridos todavía.</p>
      ) : (
        <div className="stats-table-wrap">
          <table className="stats-table library-table">
            <thead>
              <tr>
                <th>Estado</th>
                <th>Título</th>
                <th>Tipo</th>
                <th>Tamaño</th>
                <th>Tags</th>
                <th>Ruta absoluta</th>
                <th aria-label="Acciones" />
              </tr>
              <tr className="library-filter-row">
                <th>
                  <select
                    aria-label="Filtrar por estado"
                    value={filters.status}
                    onChange={(e) => setFilters((f) => ({ ...f, status: e.target.value }))}
                  >
                    <option value="">Todos</option>
                    {statusOptions.map((status) => (
                      <option key={status} value={status}>
                        {STATUS_LABELS[status] ?? status}
                      </option>
                    ))}
                  </select>
                </th>
                <th>
                  <input
                    type="text"
                    aria-label="Filtrar por título"
                    placeholder="Buscar título…"
                    value={filters.filename}
                    onChange={(e) => setFilters((f) => ({ ...f, filename: e.target.value }))}
                  />
                </th>
                <th>
                  <input
                    type="text"
                    aria-label="Filtrar por tipo"
                    placeholder="Buscar tipo…"
                    value={filters.format}
                    onChange={(e) => setFilters((f) => ({ ...f, format: e.target.value }))}
                  />
                </th>
                <th>
                  <input
                    type="text"
                    aria-label="Filtrar por tamaño"
                    placeholder="Buscar tamaño…"
                    value={filters.size}
                    onChange={(e) => setFilters((f) => ({ ...f, size: e.target.value }))}
                  />
                </th>
                <th>
                  <input
                    type="text"
                    aria-label="Filtrar por tag"
                    placeholder="Buscar tag…"
                    value={filters.tags}
                    onChange={(e) => setFilters((f) => ({ ...f, tags: e.target.value }))}
                  />
                </th>
                <th>
                  <input
                    type="text"
                    aria-label="Filtrar por ruta absoluta"
                    placeholder="Buscar ruta…"
                    value={filters.path}
                    onChange={(e) => setFilters((f) => ({ ...f, path: e.target.value }))}
                  />
                </th>
                <th />
              </tr>
            </thead>
            <tbody>
              {filteredDocuments.length === 0 ? (
                <tr>
                  <td colSpan={7} className="stats-empty">
                    Ningún documento coincide con los filtros.
                  </td>
                </tr>
              ) : (
                filteredDocuments.map((doc) => (
                  <tr key={doc.id}>
                    <td>
                      <span className={`library-status library-status-${doc.status}`}>
                        {STATUS_LABELS[doc.status] ?? doc.status}
                      </span>
                    </td>
                    <td>{doc.filename}</td>
                    <td>{doc.format}</td>
                    <td>{formatSize(doc.size_bytes)}</td>
                    <td>{doc.tags.length > 0 ? doc.tags.join(", ") : "—"}</td>
                    <td className="library-path" title={doc.absolute_path ?? undefined}>
                      {doc.absolute_path ?? "—"}
                    </td>
                    <td className="library-actions">
                      <a
                        className={`library-open-btn${doc.absolute_path ? "" : " library-open-btn-disabled"}`}
                        href={doc.absolute_path ? getDocumentFileUrl(doc.id) : undefined}
                        target="_blank"
                        rel="noreferrer"
                        aria-disabled={!doc.absolute_path}
                        onClick={(e) => {
                          if (!doc.absolute_path) e.preventDefault();
                        }}
                      >
                        Abrir
                      </a>
                      <button
                        type="button"
                        className="library-delete-btn"
                        disabled={deletingId === doc.id}
                        onClick={() => void handleDelete(doc)}
                      >
                        {deletingId === doc.id ? "Eliminando…" : "Eliminar"}
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
