import type { ErrorDocumentResponse } from "../../services/api";

interface Props {
  errors: ErrorDocumentResponse[];
}

export default function ErrorsTable({ errors }: Props) {
  return (
    <section className="stats-card" aria-label="Documentos con error">
      <h2 className="stats-card-title">Documentos con error</h2>
      {errors.length === 0 ? (
        <p className="stats-empty">No hay documentos con error.</p>
      ) : (
        <div className="stats-table-wrap">
          <table className="stats-table">
            <thead>
              <tr>
                <th>Fichero</th>
                <th>Formato</th>
                <th>Error</th>
              </tr>
            </thead>
            <tbody>
              {errors.map((doc) => (
                <tr key={doc.id}>
                  <td>{doc.filename}</td>
                  <td>{doc.format}</td>
                  <td>{doc.error_message ?? "Sin detalle"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
