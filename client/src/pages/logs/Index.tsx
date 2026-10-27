import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { Log } from "@/lib/api";
import {
  Database,
  Filter,
  Info,
  PlusCircle,
  RefreshCw,
  Search,
  Trash2,
  X,
} from "lucide-react";

export default function LogsExplorer() {
  const [logs, setLogs] = useState<Log[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedLog, setSelectedLog] = useState<Log | null>(null);

  // Trace logs (logs with same trace_id)
  const [traceLogs, setTraceLogs] = useState<Log[]>([]);

  // Filtering states
  const [serviceFilter, setServiceFilter] = useState("");
  const [levelFilter, setLevelFilter] = useState("");
  const [searchQuery, setSearchQuery] = useState("");

  // Ingest form states
  const [ingestService, setIngestService] = useState("auth-service");
  const [ingestEnvironment, setIngestEnvironment] = useState("production");
  const [ingestLevel, setIngestLevel] = useState("INFO");
  const [ingestMessage, setIngestMessage] = useState(
    "User authenticated successfully.",
  );
  const [ingestTraceId, setIngestTraceId] = useState("trc_92a18d");
  const [ingestMetadata, setIngestMetadata] = useState(
    JSON.stringify({ user_id: "usr_291", ip: "192.168.1.105" }, null, 2),
  );
  const [ingestError, setIngestError] = useState("");
  const [ingesting, setIngesting] = useState(false);

  // Extract unique services from logs for filters
  const [availableServices, setAvailableServices] = useState<string[]>([]);

  const loadLogs = async () => {
    setLoading(true);
    try {
      const response = await api.getLogs(
        serviceFilter || undefined,
        levelFilter || undefined,
      );
      const data = response.data;
      setLogs(data);

      // Collect unique services for filter list
      const svcs = new Set<string>();
      data.forEach((l) => {
        if (l.service) svcs.add(l.service);
      });
      setAvailableServices(Array.from(svcs));
    } catch (error) {
      console.error("Failed to fetch logs:", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadLogs();
  }, [serviceFilter, levelFilter]);

  // Load trace logs when selected log changes
  useEffect(() => {
    if (selectedLog && selectedLog.trace_id) {
      const traces = logs.filter(
        (l) => l.trace_id === selectedLog.trace_id && l.id !== selectedLog.id,
      );
      setTraceLogs(traces);
    } else {
      setTraceLogs([]);
    }
  }, [selectedLog, logs]);

  const handleIngest = async (e: React.FormEvent) => {
    e.preventDefault();
    setIngestError("");
    setIngesting(true);

    let parsedMeta = null;
    if (ingestMetadata.trim()) {
      try {
        parsedMeta = JSON.parse(ingestMetadata);
      } catch (err) {
        setIngestError("Invalid JSON in metadata field.");
        setIngesting(false);
        return;
      }
    }

    try {
      await api.createLog({
        service: ingestService,
        environment: ingestEnvironment,
        level: ingestLevel,
        log_message: ingestMessage,
        trace_id: ingestTraceId || undefined,
        metadata: parsedMeta || undefined,
      });

      // Clear ingestion inputs or reset defaults
      setIngestMessage("");
      // Reset default trace ID to something unique
      setIngestTraceId("trc_" + Math.random().toString(36).substring(2, 10));

      // Reload logs
      await loadLogs();
    } catch (error: any) {
      setIngestError(error.message || "Failed to ingest log");
    } finally {
      setIngesting(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (
      !confirm(
        "Are you sure you want to delete this log? This action is irreversible.",
      )
    ) {
      return;
    }
    try {
      await api.deleteLog(id);
      setSelectedLog(null);
      await loadLogs();
    } catch (err) {
      alert("Failed to delete log: " + err);
    }
  };

  // Filter logs locally based on search query
  const filteredLogs = logs.filter((log) => {
    if (!searchQuery) return true;
    const q = searchQuery.toLowerCase();
    const msg = log.log_message?.toLowerCase() || "";
    const trace = log.trace_id?.toLowerCase() || "";
    const service = log.service?.toLowerCase() || "";
    return msg.includes(q) || trace.includes(q) || service.includes(q);
  });

  return (
    <div className="split-layout">
      {/* Side Filters & Ingestion Form */}
      <aside className="split-layout-aside gap-4">
        {/* Filters Card */}
        <div className="card">
          <div className="card-header pb-2">
            <h3 className="card-title text-sm flex items-center gap-2">
              <Filter className="h-4 w-4" />
              <span>Filters</span>
            </h3>
          </div>
          <div className="card-content flex flex-col gap-3">
            <div className="form-group">
              <label className="form-label">Search Query</label>
              <div className="relative">
                <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
                <input
                  type="text"
                  placeholder="Message or Trace ID..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="form-input pl-8"
                />
              </div>
            </div>

            <div className="form-group">
              <label className="form-label">Service</label>
              <select
                value={serviceFilter}
                onChange={(e) => setServiceFilter(e.target.value)}
                className="form-select"
              >
                <option value="">All Services</option>
                {availableServices.map((s) => (
                  <option key={s} value={s}>
                    {s}
                  </option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label className="form-label">Severity Level</label>
              <select
                value={levelFilter}
                onChange={(e) => setLevelFilter(e.target.value)}
                className="form-select"
              >
                <option value="">All Levels</option>
                <option value="INFO">INFO</option>
                <option value="WARNING">WARNING</option>
                <option value="ERROR">ERROR</option>
                <option value="CRITICAL">CRITICAL</option>
              </select>
            </div>
          </div>
        </div>

        {/* Mock Log Ingestor Card */}
        <div className="card">
          <div className="card-header pb-2">
            <h3 className="card-title text-sm flex items-center gap-2">
              <PlusCircle className="h-4 w-4" />
              <span>Ingest Mock Event</span>
            </h3>
          </div>
          <div className="card-content">
            <form onSubmit={handleIngest} className="flex flex-col gap-3">
              <div className="grid grid-cols-2 gap-2">
                <div className="form-group">
                  <label className="form-label">Service</label>
                  <input
                    type="text"
                    required
                    value={ingestService}
                    onChange={(e) => setIngestService(e.target.value)}
                    className="form-input font-mono text-xs"
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Env</label>
                  <input
                    type="text"
                    required
                    value={ingestEnvironment}
                    onChange={(e) => setIngestEnvironment(e.target.value)}
                    className="form-input font-mono text-xs"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-2">
                <div className="form-group">
                  <label className="form-label">Level</label>
                  <select
                    value={ingestLevel}
                    onChange={(e) => setIngestLevel(e.target.value)}
                    className="form-select font-mono text-xs"
                  >
                    <option value="INFO">INFO</option>
                    <option value="WARNING">WARNING</option>
                    <option value="ERROR">ERROR</option>
                    <option value="CRITICAL">CRITICAL</option>
                  </select>
                </div>
                <div className="form-group">
                  <label className="form-label">Trace ID</label>
                  <input
                    type="text"
                    placeholder="None"
                    value={ingestTraceId}
                    onChange={(e) => setIngestTraceId(e.target.value)}
                    className="form-input font-mono text-xs"
                  />
                </div>
              </div>

              <div className="form-group">
                <label className="form-label">Message</label>
                <input
                  type="text"
                  required
                  placeholder="Log message details..."
                  value={ingestMessage}
                  onChange={(e) => setIngestMessage(e.target.value)}
                  className="form-input text-xs"
                />
              </div>

              <div className="form-group">
                <label className="form-label">Metadata (JSON)</label>
                <textarea
                  placeholder="{}"
                  value={ingestMetadata}
                  onChange={(e) => setIngestMetadata(e.target.value)}
                  className="form-textarea font-mono text-xs h-24"
                />
              </div>

              {ingestError && <div className="form-error">{ingestError}</div>}

              <button
                type="submit"
                className="button w-full cursor-pointer flex items-center justify-center gap-1 py-1.5"
                disabled={ingesting}
              >
                <span>Ingest Event</span>
              </button>
            </form>
          </div>
        </div>
      </aside>

      {/* Main Logs Explorer Table */}
      <main className="split-layout-main">
        <div className="card flex-grow overflow-hidden">
          <div className="card-header flex-row justify-between items-center pb-3">
            <div>
              <h3 className="card-title text-base flex items-center gap-2">
                <Database className="h-5 w-5" />
                <span>Logs Explorer</span>
              </h3>
              <p className="card-description">
                Showing {filteredLogs.length} matching events. Click a row to
                inspect.
              </p>
            </div>
            <button
              onClick={loadLogs}
              className="button button-outline cursor-pointer p-2 flex items-center justify-center"
              title="Refresh Logs"
              type="button"
            >
              <RefreshCw className="h-4 w-4" />
            </button>
          </div>

          <div className="card-content p-0 overflow-y-auto max-h-[70vh]">
            {loading ? (
              <div className="flex justify-center items-center py-20">
                <RefreshCw className="h-8 w-8 animate-spin" />
              </div>
            ) : filteredLogs.length > 0 ? (
              <div className="table-container border-0 rounded-none">
                <table className="table table-hover table-striped">
                  <thead>
                    <tr>
                      <th className="w-[10%]">Level</th>
                      <th className="w-[20%]">Timestamp</th>
                      <th className="w-[15%]">Service</th>
                      <th className="w-[45%]">Message</th>
                      <th className="w-[10%]">Trace ID</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredLogs.map((log) => (
                      <tr key={log.id} onClick={() => setSelectedLog(log)}>
                        <td>
                          <span
                            className={`badge ${
                              log.level === "ERROR" || log.level === "CRITICAL"
                                ? "badge-danger"
                                : log.level === "WARNING"
                                  ? "badge-warning"
                                  : log.level === "INFO"
                                    ? "badge-info"
                                    : ""
                            }`}
                          >
                            {log.level}
                          </span>
                        </td>
                        <td className="text-xs font-mono text-muted-foreground whitespace-nowrap">
                          {new Date(log.created_at).toLocaleString()}
                        </td>
                        <td className="font-semibold text-sm">{log.service}</td>
                        <td className="font-mono text-xs truncate max-w-[300px]">
                          {log.log_message}
                        </td>
                        <td className="font-mono text-xs text-muted-foreground whitespace-nowrap">
                          {log.trace_id || "—"}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="text-center py-20 text-muted-foreground text-sm flex flex-col items-center gap-2">
                <Info className="h-10 w-10 text-muted-foreground/50" />
                <span>No logs match the current filters.</span>
              </div>
            )}
          </div>
        </div>
      </main>

      {/* Log Inspector Detail Modal */}
      {selectedLog && (
        <div className="dialog-overlay" onClick={() => setSelectedLog(null)}>
          <div
            className="dialog max-w-lg md:max-w-2xl overflow-y-auto max-h-[85vh] cursor-default"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="dialog-header flex-row justify-between items-start">
              <div>
                <h3 className="dialog-title text-base flex items-center gap-2">
                  <span>Event Details</span>
                  <span
                    className={`badge ${
                      selectedLog.level === "ERROR" ||
                      selectedLog.level === "CRITICAL"
                        ? "badge-danger"
                        : selectedLog.level === "WARNING"
                          ? "badge-warning"
                          : "badge-info"
                    }`}
                  >
                    {selectedLog.level}
                  </span>
                </h3>
                <p className="dialog-description mt-1">ID: {selectedLog.id}</p>
              </div>
              <button
                onClick={() => setSelectedLog(null)}
                className="button button-outline p-1 rounded-full border-none hover:bg-muted"
                type="button"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            <div className="flex flex-col gap-4 mt-2">
              {/* Event Info */}
              <div className="grid grid-cols-2 gap-4 p-3 bg-muted/30 border rounded-lg">
                <div>
                  <span className="text-xs text-muted-foreground block">
                    Service
                  </span>
                  <span className="font-semibold text-sm">
                    {selectedLog.service}
                  </span>
                </div>
                <div>
                  <span className="text-xs text-muted-foreground block">
                    Environment
                  </span>
                  <span className="font-semibold text-sm">
                    {selectedLog.environment}
                  </span>
                </div>
                <div>
                  <span className="text-xs text-muted-foreground block">
                    Timestamp
                  </span>
                  <span className="font-mono text-xs">
                    {new Date(selectedLog.created_at).toLocaleString()}
                  </span>
                </div>
                <div>
                  <span className="text-xs text-muted-foreground block">
                    Trace ID
                  </span>
                  <span className="font-mono text-xs">
                    {selectedLog.trace_id || "—"}
                  </span>
                </div>
              </div>

              {/* Message */}
              <div>
                <span className="text-xs font-semibold text-muted-foreground uppercase block mb-1">
                  Message
                </span>
                <div className="p-3 bg-muted rounded border font-mono text-xs whitespace-pre-wrap break-all">
                  {selectedLog.log_message}
                </div>
              </div>

              {/* Metadata */}
              {selectedLog.metadata && (
                <div>
                  <span className="text-xs font-semibold text-muted-foreground uppercase block mb-1">
                    Structured Metadata
                  </span>
                  <pre className="p-3 bg-card rounded border font-mono text-xs overflow-x-auto">
                    {JSON.stringify(selectedLog.metadata, null, 2)}
                  </pre>
                </div>
              )}

              {/* Trace Timeline */}
              {selectedLog.trace_id && (
                <div>
                  <span className="text-xs font-semibold text-muted-foreground uppercase block mb-2">
                    Trace Timeline
                  </span>
                  <div className="flex flex-col gap-2 pl-2 border-l-2 ml-1">
                    {traceLogs.length > 0 ? (
                      [selectedLog, ...traceLogs]
                        .sort(
                          (a, b) =>
                            new Date(a.created_at).getTime() -
                            new Date(b.created_at).getTime(),
                        )
                        .map((tLog) => (
                          <div key={tLog.id} className="relative py-1">
                            <div className="absolute -left-[14px] top-2.5 h-2 w-2 rounded-full" />
                            <div className="pl-4">
                              <div className="flex items-center gap-2">
                                <span
                                  className={`text-[10px] font-semibold badge px-1.5 py-0.25 ${
                                    tLog.level === "ERROR"
                                      ? "badge-danger"
                                      : tLog.level === "WARNING"
                                        ? "badge-warning"
                                        : "badge-info"
                                  }`}
                                >
                                  {tLog.level}
                                </span>
                                <span className="text-xs font-bold">
                                  {tLog.service}
                                </span>
                                <span className="text-[10px] text-muted-foreground font-mono">
                                  {new Date(
                                    tLog.created_at,
                                  ).toLocaleTimeString()}
                                </span>
                              </div>
                              <p className="text-xs text-muted-foreground font-mono mt-0.5 truncate">
                                {tLog.log_message}
                              </p>
                            </div>
                          </div>
                        ))
                    ) : (
                      <p className="text-xs text-muted-foreground italic pl-3">
                        No other logs found sharing trace ID "
                        {selectedLog.trace_id}".
                      </p>
                    )}
                  </div>
                </div>
              )}
            </div>

            <div className="dialog-footer">
              <button
                onClick={() => setSelectedLog(null)}
                className="button button-outline cursor-pointer"
                type="button"
              >
                Close
              </button>
              <button
                onClick={() => handleDelete(selectedLog.id)}
                className="button bg-rose-500 hover:bg-rose-600 border-none text-white cursor-pointer flex items-center gap-1"
                type="button"
              >
                <Trash2 className="h-4 w-4" />
                <span>Delete Log</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
