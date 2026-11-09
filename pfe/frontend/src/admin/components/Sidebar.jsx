import { NavLink } from 'react-router-dom';
import { List, ListItemButton, ListItemIcon, ListItemText } from '@mui/material';

const listItemSx = {
  py: 1.25,
  borderRadius: 0,
  textDecoration: 'none',
  color: 'inherit',
  '&.Mui-selected': {
    bgcolor: 'rgba(37, 99, 235, 0.08)',
    borderLeft: '4px solid',
    borderLeftColor: 'primary.main',
    pl: '12px',
    '&:hover': {
      bgcolor: 'rgba(37, 99, 235, 0.1)',
    },
  },
  '&:not(.Mui-selected):hover': {
    bgcolor: 'rgba(0,0,0,0.04)',
  },
};

export default function Sidebar({ items, isPathActive }) {
  return (
    <List sx={{ py: 0 }}>
      {items.map(({ path, label, Icon }) => {
        const selected = isPathActive(path);
        return (
          <ListItemButton
            key={path}
            component={NavLink}
            to={path}
            selected={selected}
            sx={listItemSx}
          >
            <ListItemIcon
              sx={{
                minWidth: 40,
                color: selected ? 'primary.main' : 'text.secondary',
              }}
            >
              <Icon fontSize="small" />
            </ListItemIcon>
            <ListItemText
              primary={label}
              primaryTypographyProps={{
                variant: 'body2',
                fontWeight: selected ? 600 : 400,
              }}
            />
          </ListItemButton>
        );
      })}
    </List>
  );
}
