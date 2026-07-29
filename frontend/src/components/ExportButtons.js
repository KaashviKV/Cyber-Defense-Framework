import { FiDownload, FiFileText } from "react-icons/fi";
import { exportAnalysisCsv, exportAnalysisJson, exportAnalysisPdf } from "../utils/exports";

export default function ExportButtons({ analysis, disabled = false }) {
  if (!analysis) return null;

  return (
    <div className="export-buttons">
      <button
        type="button"
        className="btn btn-outline"
        disabled={disabled}
        onClick={() => exportAnalysisJson(analysis)}
      >
        <FiDownload /> JSON
      </button>
      <button
        type="button"
        className="btn btn-outline"
        disabled={disabled}
        onClick={() => exportAnalysisCsv(analysis)}
      >
        <FiDownload /> CSV
      </button>
      <button
        type="button"
        className="btn btn-outline"
        disabled={disabled}
        onClick={() => exportAnalysisPdf(analysis)}
      >
        <FiFileText /> PDF
      </button>
    </div>
  );
}
