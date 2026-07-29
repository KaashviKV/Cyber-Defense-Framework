import { ACTION_LABELS, RISK_COLORS, ACTION_COLORS } from "./constants";

export function getRiskColor(level) {
  return RISK_COLORS[level] || "#94A3B8";
}

export function getActionColor(action) {
  return ACTION_COLORS[action] || "#94A3B8";
}

export function getActionLabel(action) {
  return ACTION_LABELS[action] || action || "Unknown";
}

export function formatDateTime(value) {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return String(value);
  return date.toLocaleString(undefined, {
    year: "numeric",
    month: "short",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}

export function formatPercent(value, digits = 1) {
  const num = Number(value);
  if (Number.isNaN(num)) return "—";
  return `${num.toFixed(digits)}%`;
}

export function formatNumber(value, digits = 0) {
  const num = Number(value);
  if (Number.isNaN(num)) return "—";
  return num.toLocaleString(undefined, {
    maximumFractionDigits: digits,
    minimumFractionDigits: digits,
  });
}

export function safeGet(obj, path, fallback = "—") {
  try {
    const parts = path.split(".");
    let cur = obj;
    for (const part of parts) {
      if (cur == null) return fallback;
      cur = cur[part];
    }
    return cur == null || cur === "" ? fallback : cur;
  } catch {
    return fallback;
  }
}

export function hasCtiError(cti) {
  return !cti || typeof cti !== "object" || "error" in cti;
}

export function getCtiErrorMessage(cti, source = "cti") {
  if (!cti) {
    return source === "virustotal"
      ? "VirusTotal unavailable. Analysis completed using ML + Risk Engine."
      : source === "abuseipdb"
        ? "AbuseIPDB unavailable. Analysis completed using ML + Risk Engine."
        : "Threat intelligence unavailable.";
  }

  const code = cti.error ?? cti.status;
  const provider = source === "virustotal" ? "VirusTotal" : source === "abuseipdb" ? "AbuseIPDB" : "Threat intelligence";

  if (code === "missing_api_key" || code === "MISSING_API_KEY") {
    return `${provider} API key not configured. Analysis continued with ML + Risk Engine.`;
  }
  if (code === 401 || code === "401" || code === "unauthorized") {
    return `${provider} unavailable. Analysis completed using ML + Risk Engine.`;
  }
  if (code === 429 || code === "429") {
    return `${provider} rate limit reached. Analysis continued with cached or partial CTI data.`;
  }
  if (cti.message) return String(cti.message);
  if (code != null) return `${provider} unavailable (${code}). Analysis continued with ML + Risk Engine.`;
  return `${provider} unavailable. Analysis completed using ML + Risk Engine.`;
}

export async function copyToClipboard(text) {
  const value = String(text ?? "");
  if (!value) return false;
  try {
    await navigator.clipboard.writeText(value);
    return true;
  } catch {
    const area = document.createElement("textarea");
    area.value = value;
    document.body.appendChild(area);
    area.select();
    const ok = document.execCommand("copy");
    document.body.removeChild(area);
    return ok;
  }
}

export function parseFeatureInput(raw) {
  const text = String(raw || "").trim();
  if (!text) {
    return { ok: false, error: "Feature values are required.", values: [] };
  }

  let values;
  try {
    if (text.startsWith("[")) {
      const parsed = JSON.parse(text);
      if (!Array.isArray(parsed)) {
        return { ok: false, error: "JSON must be an array of numbers.", values: [] };
      }
      values = parsed;
    } else {
      values = text
        .split(/[\s,]+/)
        .map((part) => part.trim())
        .filter(Boolean);
    }
  } catch {
    return {
      ok: false,
      error: "Could not parse features. Use a JSON array or comma-separated numbers.",
      values: [],
    };
  }

  const numbers = values.map((v) => Number(v));
  if (numbers.some((n) => Number.isNaN(n))) {
    return { ok: false, error: "All feature values must be valid numbers.", values: [] };
  }

  if (numbers.length !== 78) {
    return {
      ok: false,
      error: `Exactly 78 feature values are required (received ${numbers.length}).`,
      values: numbers,
    };
  }

  return { ok: true, error: null, values: numbers };
}

export function generateDemoFeatures() {
  return Array.from({ length: 78 }, () =>
    Number((Math.random() * 100).toFixed(4))
  );
}

export function exportHistoryToCsv(rows) {
  const headers = [
    "timestamp",
    "ip_address",
    "attack",
    "confidence",
    "severity",
    "risk_level",
    "risk_score",
    "action",
    "country",
    "analysis_id",
  ];

  const escape = (value) => {
    const str = value == null ? "" : String(value);
    if (/[",\n]/.test(str)) return `"${str.replace(/"/g, '""')}"`;
    return str;
  };

  const lines = [headers.join(",")];
  rows.forEach((row) => {
    lines.push(
      [
        row.timestamp || "",
        row.ip_address || "",
        row.prediction?.attack || "",
        row.prediction?.confidence ?? "",
        row.prediction?.severity ?? "",
        row.risk?.risk_level || "",
        row.risk?.risk_score ?? "",
        row.decision?.action || "",
        row.abuseipdb?.country || "",
        row.analysis_id || row._id || "",
      ]
        .map(escape)
        .join(",")
    );
  });

  const blob = new Blob([lines.join("\n")], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `threat-history-${Date.now()}.csv`;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

export function getRecordId(record) {
  return record?.analysis_id || record?._id || null;
}
