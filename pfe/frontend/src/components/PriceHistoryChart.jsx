import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Tooltip,
  Legend,
} from "chart.js";
import { Line } from "react-chartjs-2";
import { useMemo } from "react";

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Tooltip,
  Legend
);

export default function PriceHistoryChart({ points = [], label = "Price" }) {
  const { labels, values } = useMemo(() => {
    const chronological = [...points];
    const labels = chronological.map((p) => p.label);
    const values = chronological.map((p) => p.value);
    return { labels, values };
  }, [points]);

  const data = useMemo(() => {
    return {
      labels,
      datasets: [
        {
          label,
          data: values,
          borderColor: "#3B82F6",
          backgroundColor: "rgba(59,130,246,0.15)",
          tension: 0.25,
          pointRadius: 2,
        },
      ],
    };
  }, [labels, values]);

  const options = useMemo(
    () => ({
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: true } },
      scales: {
        y: {
          beginAtZero: false,
        },
      },
    }),
    []
  );

  return (
    <div style={{ height: "100%", width: "100%" }}>
      <Line data={data} options={options} />
    </div>
  );
}

