import { Box, Typography } from '@mui/material';
import Sidebar from './Sidebar';

const drawerWidth = 240;

export default function AdminLayout({ title, menuItems, isPathActive, children }) {
  return (
    <Box sx={{ display: 'flex', minHeight: 'calc(100vh - 56px)', bgcolor: '#f5f7fa' }}>
      <Box
        component="aside"
        sx={{
          width: drawerWidth,
          flexShrink: 0,
          borderRight: '1px solid #e5e7eb',
          bgcolor: '#fff',
          pt: 1,
          boxShadow: '1px 0 0 rgba(0,0,0,.03)',
        }}
      >
        <Sidebar items={menuItems} isPathActive={isPathActive} />
      </Box>

      <Box component="main" sx={{ flexGrow: 1, p: 0 }}>
        <Box
          sx={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            px: 2.5,
            py: 1.25,
            borderBottom: '1px solid #e5e7eb',
            bgcolor: '#fff',
          }}
        >
          <Typography variant="body2" sx={{ fontWeight: 600, color: '#374151' }}>
            {title}
          </Typography>
        </Box>
        <Box sx={{ p: 3 }}>{children}</Box>
      </Box>
    </Box>
  );
}
