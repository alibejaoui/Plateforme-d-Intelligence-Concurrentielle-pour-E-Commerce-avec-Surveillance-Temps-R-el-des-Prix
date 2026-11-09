import { useEffect, useMemo, useState } from "react";
import api from "../api/api";
import PriceHistoryChart from "../components/PriceHistoryChart";
import HistoricalMarketCharts from "../components/HistoricalMarketCharts";
import { useTranslation } from "react-i18next";

export default function DashboardDynamic() {
  const { t } = useTranslation();
  const [products, setProducts] = useState([]);
  const [competitors, setCompetitors] = useState([]);
  const [alerts, setAlerts] = useState([]);

  const [selectedProductId, setSelectedProductId] = useState(null);
  const [selectedCompetitorId, setSelectedCompetitorId] = useState(null);

  const [historyPoints, setHistoryPoints] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [scrapeLoading, setScrapeLoading] = useState(false);
  const [scrapeMessage, setScrapeMessage] = useState(null);
  const [scrapeJob, setScrapeJob] = useState(null);

  const formatDateTime = (iso) => {
    if (!iso) return "";
    const d = new Date(iso);
    if (Number.isNaN(d.getTime())) return "";
    return d.toLocaleString();
  };

  const unreadCount = useMemo(() => {
    return (alerts || []).filter((a) => a.status === "pending").length;
  }, [alerts]);

  const loadProducts = async () => {
    const { data } = await api.get("/products");
    const items = data?.items || [];
    setProducts(items);
    if (!selectedProductId && items.length > 0) {
      setSelectedProductId(items[0].id);
    }
  };

  const loadCompetitors = async () => {
    const { data } = await api.get("/competitors");
    const items = data?.items || [];
    setCompetitors(items);
    if (!selectedCompetitorId && items.length > 0) {
      setSelectedCompetitorId(items[0].id);
    }
  };

  const loadAlerts = async () => {
    const { data } = await api.get("/alerts");
    setAlerts(data?.items || []);
  };

  const loadPriceHistory = async () => {
    if (!selectedProductId) return;
    const { data } = await api.get(
      `/prices/history/${selectedProductId}?days=30`
    );
    const prices = data?.prices || [];
    // backend renvoie souvent du plus récent au plus ancien -> on inverse pour une courbe
    const chronological = [...prices].reverse();

    const points = chronological
      .map((p) => {
        const t = p.scraped_at || p.created_at;
        return {
          label: t ? new Date(t).toLocaleDateString() : "",
          value: p.price,
        };
      })
      .filter((pt) => pt.label);

    setHistoryPoints(points);
  };

  useEffect(() => {
    const boot = async () => {
      try {
        setError(null);
        setLoading(true);

        const phase1 = await Promise.allSettled([loadProducts(), loadCompetitors()]);
        const phase2 = await Promise.allSettled([loadAlerts(), loadPriceHistory()]);
        const rejected = [...phase1, ...phase2].filter((r) => r.status === "rejected");
        if (rejected.length) {
          const first = rejected[0];
          const reason =
            first.status === "rejected" && first.reason?.response?.data?.detail
              ? first.reason.response.data.detail
              : t("dashboard.failedLoad");
          setError(reason);
        }
      } catch (e) {
        setError(e?.response?.data?.detail || t("dashboard.failedLoad"));
      } finally {
        setLoading(false);
      }
    };

    boot();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Reload chart when selected product changes (not only on initial mount).
  useEffect(() => {
    if (!selectedProductId) return;
    loadPriceHistory().catch(() => {});
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedProductId]);

  // Auto-refresh: history + alerts
  useEffect(() => {
    if (!selectedProductId) return;
    const id = setInterval(() => {
      loadPriceHistory().catch(() => {});
      loadAlerts().catch(() => {});
    }, 30000);
    return () => clearInterval(id);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedProductId]);

  const handleTriggerScrape = async () => {
    if (!selectedCompetitorId || !selectedProductId) return;
    setScrapeLoading(true);
    setScrapeMessage(null);
    setScrapeJob(null);
    try {
      const res = await api.post(
        `/scraping/trigger/${selectedCompetitorId}?product_id=${selectedProductId}`
      );
      const jobId = res?.data?.job_id;
      setScrapeMessage(res?.data?.message || t("dashboard.scrapingTriggered"));
      if (jobId) {
        setScrapeJob({ id: jobId, status: res?.data?.status || "pending" });
      }

      // Poll job until completion; refresh data on success.
      if (jobId) {
        let lastStatus = "pending";
        for (let i = 0; i < 20; i++) {
          const jobRes = await api.get(`/scraping/jobs/${jobId}`);
          const jobData = jobRes?.data;
          if (jobData) {
            setScrapeJob(jobData);
            lastStatus = jobData.status || lastStatus;
          }
          if (
            jobData?.status === "completed" ||
            jobData?.status === "failed" ||
            jobData?.status === "cancelled"
          ) {
            if (jobData?.status === "completed") {
              await Promise.all([loadPriceHistory(), loadAlerts()]);
              const rd = jobData?.result_data;
              const price = rd && typeof rd === "object" ? rd.price : null;
              setScrapeMessage(
                price != null
                  ? `${t("dashboard.refreshed") || "Refreshed."} (${t("dashboard.lastPrice") || "price"}: ${price})`
                  : t("dashboard.refreshed") || "Refreshed."
              );
            } else if (jobData?.status === "failed") {
              setScrapeMessage(jobData?.error_message || t("dashboard.failedTrigger"));
            } else {
              setScrapeMessage(t("dashboard.failedTrigger"));
            }
            break;
          }
          // Wait 2 seconds before next poll (avoid hammering the API).
          // eslint-disable-next-line no-await-in-loop
          await new Promise((r) => setTimeout(r, 2000));
        }
        if (lastStatus === "pending" || lastStatus === "running") {
          setScrapeMessage(
            t("dashboard.scrapeTimeout") ||
              "Job still pending — start the Celery worker (docker compose), wait, then click Refresh."
          );
        }
      }
    } catch (e) {
      setScrapeMessage(
        e?.response?.data?.detail || t("dashboard.failedTrigger")
      );
    } finally {
      setScrapeLoading(false);
    }
  };

  const handleRefreshManual = async () => {
    try {
      await Promise.all([loadPriceHistory(), loadAlerts()]);
      setScrapeMessage(t("dashboard.refreshed"));
    } catch (e) {
      setError(e?.response?.data?.detail || t("dashboard.failedRefresh"));
    }
  };

  if (loading) {
    return <div className="text-sm text-text-secondary">{t("dashboard.loading")}</div>;
  }

  if (error) {
    return (
      <div className="rounded-md border border-warning/40 bg-warning/10 px-3 py-2 text-sm text-warning">
        {error}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-1">
        <h1 className="text-2xl font-semibold text-text-primary">{t("dashboard.title")}</h1>
        <p className="text-sm text-text-secondary">
          {t("dashboard.subtitle")}
        </p>
      </div>

      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="text-sm text-text-secondary">
            {t("dashboard.unreadAlerts")}: <span className="font-semibold">{unreadCount}</span>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={handleRefreshManual}
            className="rounded-md border border-border bg-white px-3 py-1 text-xs text-text-primary hover:bg-bg-soft"
          >
            {t("common.refresh")}
          </button>
          <button
            onClick={handleTriggerScrape}
            disabled={scrapeLoading}
            className="rounded-md bg-primary px-3 py-1 text-xs font-semibold text-black hover:bg-blue-500 disabled:opacity-60"
          >
            {scrapeLoading ? t("dashboard.scraping") : t("dashboard.scrapeNow")}
          </button>
        </div>
      </div>

      {scrapeMessage && (
        <div className="rounded-md border border-border bg-white px-3 py-2 text-sm text-text-secondary">
          {scrapeMessage}
        </div>
      )}

      {scrapeJob?.id && (
        <div className="rounded-md border border-border bg-white px-3 py-2 text-xs text-text-secondary">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div className="font-medium text-text-primary">
              {t("dashboard.scraping")}: #{scrapeJob.id}
            </div>
            <div className="rounded-full bg-bg-soft px-2 py-0.5 text-[11px] uppercase tracking-wide">
              {scrapeJob.status}
            </div>
          </div>
          <div className="mt-1 flex flex-wrap gap-x-4 gap-y-1">
            {scrapeJob.started_at && (
              <div>
                <span className="font-medium">{t("common.startedAt") || "Started"}:</span>{" "}
                {formatDateTime(scrapeJob.started_at)}
              </div>
            )}
            {scrapeJob.completed_at && (
              <div>
                <span className="font-medium">{t("common.completedAt") || "Completed"}:</span>{" "}
                {formatDateTime(scrapeJob.completed_at)}
              </div>
            )}
            {scrapeJob.error_message && (
              <div className="text-warning">
                <span className="font-medium">{t("common.error") || "Error"}:</span>{" "}
                {scrapeJob.error_message}
              </div>
            )}
          </div>
        </div>
      )}

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2 rounded-card border border-border bg-white p-4 shadow-card">
          <div className="flex flex-wrap items-center justify-between gap-2 mb-3">
            <div>
              <h2 className="text-sm font-semibold text-text-primary">{t("dashboard.price30Days")}</h2>
              <p className="text-xs text-text-secondary">{t("dashboard.evolution")}</p>
            </div>
            <div className="flex items-center gap-2">
              <select
                className="rounded-md border border-border bg-white px-2 py-1 text-sm"
                value={selectedProductId || ""}
                onChange={(e) => setSelectedProductId(Number(e.target.value))}
              >
                {products.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.name}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="h-72">
            <PriceHistoryChart points={historyPoints} label={t("dashboard.priceDataset")} />
          </div>
        </div>

        <div className="rounded-card border border-border bg-white p-4 shadow-card">
          <div className="mb-3">
            <h2 className="text-sm font-semibold text-text-primary">{t("dashboard.alerts")}</h2>
            <p className="text-xs text-text-secondary">
              {t("dashboard.alertsSubtitle")}
            </p>
          </div>

          {alerts.length === 0 ? (
            <div className="text-sm text-text-secondary">{t("dashboard.noAlerts")}</div>
          ) : (
            <div className="space-y-2">
              {alerts.slice(0, 20).map((a) => (
                <div
                  key={a.id}
                  className="rounded-md border border-border bg-bg-soft p-3 text-sm"
                >
                  <div className="flex items-center justify-between gap-2">
                    <div className="font-medium text-text-primary">
                      {a.alert_type}
                    </div>
                    <div className="text-xs text-text-secondary">{a.status}</div>
                  </div>
                  <div className="mt-1 text-text-secondary">{a.message}</div>
                  <div className="mt-2 text-xs text-text-secondary">
                    {a.created_at ? new Date(a.created_at).toLocaleString() : ""}
                  </div>
                </div>
              ))}
            </div>
          )}

          <div className="mt-4 pt-3 border-t border-border">
            <div className="text-xs font-medium uppercase tracking-wide text-text-secondary mb-2">
              {t("dashboard.scrapingSource")}
            </div>
            <select
              className="w-full rounded-md border border-border bg-white px-2 py-1 text-sm"
              value={selectedCompetitorId || ""}
              onChange={(e) => setSelectedCompetitorId(Number(e.target.value))}
            >
              {competitors.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      <HistoricalMarketCharts productId={selectedProductId} />
    </div>
  );
}
