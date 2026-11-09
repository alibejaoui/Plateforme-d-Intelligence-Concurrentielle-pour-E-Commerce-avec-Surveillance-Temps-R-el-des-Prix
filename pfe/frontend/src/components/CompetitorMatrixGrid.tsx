import React, { useMemo } from 'react';
import { DataGrid, GridColDef, GridRenderCellParams, GridToolbarQuickFilter } from '@mui/x-data-grid';
import { Box } from '@mui/material';
import HeatBadge from './HeatBadge';

type Competitor = { id: number; name: string };

type Row = {
  id: number; // internal_product_id
  internal_name: string;
  brand?: string;
  category?: string;
  our_price?: number | null;
  matched_competitors: number;
  cells?: Record<number, { price?: number; availability?: string; confidence_score?: number }>; // key = competitor id
  cheapest_competitor_price?: number;
  most_expensive_competitor_price?: number;
};

interface CompetitorMatrixGridProps {
  rows: Row[];
  competitors: Competitor[];
  loading: boolean;
}

const CompetitorMatrixGrid: React.FC<CompetitorMatrixGridProps> = ({ rows, competitors, loading }) => {
  const columns: GridColDef[] = useMemo(() => {
    const base: GridColDef[] = [
      { field: 'internal_name', headerName: 'Product', flex: 1, sortable: true },
      { field: 'brand', headerName: 'Brand', flex: 0.5, sortable: true },
      { field: 'category', headerName: 'Category', flex: 0.5, sortable: true },
      { field: 'our_price', headerName: 'Our price', flex: 0.5, type: 'number', sortable: true },
      {
        field: 'matched_competitors',
        headerName: 'Coverage',
        flex: 0.5,
        valueGetter: (params) => `${params.row.matched_competitors}/${competitors.length}`,
        sortable: true,
      },
    ];
    // Dynamically add a column per competitor
    const competitorCols = competitors.map((c) => ({
      field: `competitor_${c.id}`,
      headerName: c.name,
      flex: 0.7,
      renderCell: (params: GridRenderCellParams<any, Row>) => {
        const cell = params.row.cells?.[c.id];
        if (!cell) {
          return <span style={{ color: '#d32f2f' }}>Missing</span>;
        }
        const isCheapest = params.row.cheapest_competitor_price !== undefined && cell.price === params.row.cheapest_competitor_price;
        const isExpensive = params.row.most_expensive_competitor_price !== undefined && cell.price === params.row.most_expensive_competitor_price;
        // Determine badge type
        let badge: 'cheapest' | 'expensive' | 'opportunity' | 'risk' | undefined;
        if (isCheapest) badge = 'cheapest';
        else if (isExpensive) badge = 'expensive';
        // Additional logic could set opportunity/risk based on price gap – omitted for brevity
        return (
          <Box>
            <div>{cell.price ?? '-'} </div>
            <div style={{ fontSize: '0.75rem', color: '#666' }}>{cell.availability ?? '-'}</div>
            <div style={{ fontSize: '0.75rem', color: '#666' }}>conf {Number(cell.confidence_score ?? 0).toFixed(2)}</div>
            {badge && <HeatBadge type={badge} />}
          </Box>
        );
      },
      sortable: false,
      filterable: false,
    }));
    return [...base, ...competitorCols];
  }, [competitors]);

  return (
    <div style={{ height: 600, width: '100%' }}>
      <DataGrid
        rows={rows}
        columns={columns}
        loading={loading}
        pageSizeOptions={[20, 50, 100]}
        pagination
        sortingMode="client"
        filterMode="client"
        components={{ Toolbar: GridToolbarQuickFilter }}
        slotProps={{
          toolbar: {
            quickFilterProps: { debounceMs: 300 },
          },
        }}
      />
    </div>
  );
};

export default CompetitorMatrixGrid;
