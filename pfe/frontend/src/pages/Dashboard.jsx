import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  ResponsiveContainer,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
} from 'recharts';
import { useTranslation } from 'react-i18next';

const priceEvolutionData = [
  { day: 'J-30', our: 92, a: 95, b: 97 },
  { day: 'J-24', our: 91, a: 94, b: 98 },
  { day: 'J-18', our: 90, a: 93, b: 96 },
  { day: 'J-12', our: 89, a: 92, b: 95 },
  { day: 'J-6', our: 88, a: 91, b: 94 },
  { day: 'Aujourd’hui', our: 89, a: 93, b: 95 },
];

const competitorComparisonData = [
  { name: 'Nous', value: 89 },
  { name: 'Concurrent A', value: 92 },
  { name: 'Concurrent B', value: 95 },
  { name: 'Concurrent C', value: 90 },
];

const categoryPerformanceData = [
  { name: 'Électronique', value: 35 },
  { name: 'Mode', value: 25 },
  { name: 'Maison', value: 20 },
  { name: 'Sport', value: 12 },
  { name: 'Autres', value: 8 },
];

const CATEGORY_COLORS = ['#3B82F6', '#93C5FD', '#22C55E', '#F97316', '#6B7280'];

export default function Dashboard() {
  const { t } = useTranslation();
  const kpiCards = [
    {
      title: t('dashboardLegacy.kpis.marketAverage'),
      value: '€89.99',
      trend: '+2.3%',
    },
    {
      title: t('dashboardLegacy.kpis.trackedProducts'),
      value: '248',
      trend: '+12',
    },
    {
      title: t('dashboardLegacy.kpis.activeAlerts'),
      value: '23',
      trend: '+8',
    },
    {
      title: t('dashboardLegacy.kpis.competitivePosition'),
      value: '87%',
      trend: '+3.1%',
    },
  ];

  const competitorComparisonData = [
    { name: t('dashboardLegacy.series.us'), value: 89 },
    { name: t('dashboardLegacy.series.competitorA'), value: 92 },
    { name: t('dashboardLegacy.series.competitorB'), value: 95 },
    { name: t('dashboardLegacy.series.competitorC'), value: 90 },
  ];

  const categoryPerformanceData = [
    { name: t('dashboardLegacy.categories.electronics'), value: 35 },
    { name: t('dashboardLegacy.categories.fashion'), value: 25 },
    { name: t('dashboardLegacy.categories.home'), value: 20 },
    { name: t('dashboardLegacy.categories.sport'), value: 12 },
    { name: t('dashboardLegacy.categories.others'), value: 8 },
  ];

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-1">
        <h1 className="text-2xl font-semibold text-text-primary">
          {t('dashboardLegacy.title')}
        </h1>
        <p className="text-sm text-text-secondary">
          {t('dashboardLegacy.subtitle')}
        </p>
      </div>

      {/* KPI cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {kpiCards.map((card) => (
          <div
            key={card.title}
            className="flex items-start justify-between rounded-card border border-border bg-white p-4 shadow-card"
          >
            <div>
              <div className="text-xs font-medium uppercase tracking-wide text-text-secondary">
                {card.title}
              </div>
              <div className="mt-2 text-2xl font-semibold text-text-primary">
                {card.value}
              </div>
              <div className="mt-1 inline-flex items-center text-xs font-medium text-success">
                <span className="mr-1 inline-flex h-4 w-4 items-center justify-center rounded-full bg-success/10">
                  ↑
                </span>
                {card.trend}
              </div>
            </div>
            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-primary-soft/40 text-primary">
              €
            </div>
          </div>
        ))}
      </div>

      {/* Charts grid */}
      <div className="grid gap-6 lg:grid-cols-3">
        {/* Price evolution line chart */}
        <div className="lg:col-span-2 rounded-card border border-border bg-white p-4 shadow-card">
          <div className="mb-2 flex items-baseline justify-between">
            <div>
              <h2 className="text-sm font-semibold text-text-primary">
                {t('dashboardLegacy.charts.priceEvolutionTitle')}
              </h2>
              <p className="text-xs text-text-secondary">
                {t('dashboardLegacy.charts.priceEvolutionSubtitle')}
              </p>
            </div>
          </div>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={priceEvolutionData}>
                <XAxis dataKey="day" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="our"
                  name={t('dashboardLegacy.series.ourPrice')}
                  stroke="#3B82F6"
                  strokeWidth={2}
                  dot={false}
                />
                <Line
                  type="monotone"
                  dataKey="a"
                  name={t('dashboardLegacy.series.competitorA')}
                  stroke="#22C55E"
                  strokeWidth={2}
                  dot={false}
                />
                <Line
                  type="monotone"
                  dataKey="b"
                  name={t('dashboardLegacy.series.competitorB')}
                  stroke="#F97316"
                  strokeWidth={2}
                  dot={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Competitor comparison bar chart */}
        <div className="rounded-card border border-border bg-white p-4 shadow-card">
          <div className="mb-2">
            <h2 className="text-sm font-semibold text-text-primary">
              {t('dashboardLegacy.charts.competitorComparisonTitle')}
            </h2>
            <p className="text-xs text-text-secondary">
              {t('dashboardLegacy.charts.competitorComparisonSubtitle')}
            </p>
          </div>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={competitorComparisonData}>
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="value" name={t('dashboardLegacy.charts.averagePrice')} fill="#3B82F6" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Category performance pie chart */}
      <div className="rounded-card border border-border bg-white p-4 shadow-card">
        <div className="mb-2 flex items-baseline justify-between">
          <div>
            <h2 className="text-sm font-semibold text-text-primary">
              {t('dashboardLegacy.charts.categoryPerformanceTitle')}
            </h2>
            <p className="text-xs text-text-secondary">
              {t('dashboardLegacy.charts.categoryPerformanceSubtitle')}
            </p>
          </div>
        </div>
        <div className="flex flex-col gap-4 md:flex-row md:items-center">
          <div className="h-64 flex-1">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={categoryPerformanceData}
                  dataKey="value"
                  nameKey="name"
                  innerRadius={60}
                  outerRadius={90}
                  paddingAngle={3}
                >
                  {categoryPerformanceData.map((entry, index) => (
                    <Cell
                      key={entry.name}
                      fill={CATEGORY_COLORS[index % CATEGORY_COLORS.length]}
                    />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className="flex-1 space-y-2 text-sm">
            {categoryPerformanceData.map((cat, index) => (
              <div
                key={cat.name}
                className="flex items-center justify-between rounded-md bg-bg-soft px-3 py-2"
              >
                <div className="flex items-center gap-2">
                  <span
                    className="h-2.5 w-2.5 rounded-full"
                    style={{
                      backgroundColor:
                        CATEGORY_COLORS[index % CATEGORY_COLORS.length],
                    }}
                  />
                  <span className="text-text-primary">{cat.name}</span>
                </div>
                <span className="text-text-secondary">{cat.value}%</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}


