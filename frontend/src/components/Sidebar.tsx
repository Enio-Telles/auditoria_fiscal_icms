import React from 'react';
import {
  Drawer,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Divider,
  Box,
  Typography,
  Chip,
} from '@mui/material';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  Dashboard as DashboardIcon,
  Business as BusinessIcon,
  Inventory as InventoryIcon,
  Assessment as AssessmentIcon,
  Star as StarIcon,
  Description as ReportsIcon,
  Analytics as AnalyticsIcon,
} from '@mui/icons-material';

const drawerWidth = 240;

interface SidebarItem {
  text: string;
  icon: React.ReactElement;
  path: string;
  badge?: string;
}

const menuItems: SidebarItem[] = [
  {
    text: 'Dashboard',
    icon: <DashboardIcon />,
    path: '/dashboard',
  },
  {
    text: 'Empresas',
    icon: <BusinessIcon />,
    path: '/empresas',
    badge: '3',
  },
  {
    text: 'Classificações',
    icon: <AssessmentIcon />,
    path: '/classificacoes',
  },
  {
    text: 'Golden Set',
    icon: <StarIcon />,
    path: '/golden-set',
  },
  {
    text: 'Relatórios',
    icon: <ReportsIcon />,
    path: '/relatorios',
  },
];

const Sidebar: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();

  const handleNavigation = (path: string) => {
    navigate(path);
  };

  return (
    <Drawer
      variant="permanent"
      sx={{
        width: drawerWidth,
        flexShrink: 0,
        '& .MuiDrawer-paper': {
          width: drawerWidth,
          boxSizing: 'border-box',
          mt: 8, // Account for AppBar height
          backgroundColor: '#fafafa',
          borderRight: '1px solid #e0e0e0',
        },
      }}
    >
      <Box sx={{ p: 2 }}>
        <Typography variant="overline" color="text.secondary" sx={{ fontWeight: 600 }}>
          MENU PRINCIPAL
        </Typography>
      </Box>

      <List>
        {menuItems.map((item) => (
          <ListItem key={item.text} disablePadding>
            <ListItemButton
              onClick={() => handleNavigation(item.path)}
              selected={location.pathname === item.path}
              sx={{
                mx: 1,
                borderRadius: 1,
                '&.Mui-selected': {
                  backgroundColor: 'primary.light',
                  color: 'white',
                  '& .MuiListItemIcon-root': {
                    color: 'white',
                  },
                  '&:hover': {
                    backgroundColor: 'primary.main',
                  },
                },
                '&:hover': {
                  backgroundColor: 'action.hover',
                },
              }}
            >
              <ListItemIcon
                sx={{
                  color: location.pathname === item.path ? 'white' : 'text.secondary',
                }}
              >
                {item.icon}
              </ListItemIcon>
              <ListItemText 
                primary={item.text}
                primaryTypographyProps={{
                  fontSize: '0.875rem',
                  fontWeight: location.pathname === item.path ? 600 : 400,
                }}
              />
              {item.badge && (
                <Chip 
                  label={item.badge} 
                  size="small" 
                  color="primary"
                  sx={{ 
                    height: 20, 
                    fontSize: '0.75rem',
                    backgroundColor: location.pathname === item.path ? 'white' : 'primary.main',
                    color: location.pathname === item.path ? 'primary.main' : 'white',
                  }}
                />
              )}
            </ListItemButton>
          </ListItem>
        ))}
      </List>

      <Divider sx={{ my: 2 }} />

      {/* Status da API */}
      <Box sx={{ p: 2 }}>
        <Typography variant="overline" color="text.secondary" sx={{ fontWeight: 600 }}>
          STATUS DO SISTEMA
        </Typography>
        <Box sx={{ mt: 1, display: 'flex', alignItems: 'center', gap: 1 }}>
          <Box
            sx={{
              width: 8,
              height: 8,
              borderRadius: '50%',
              backgroundColor: 'success.main',
            }}
          />
          <Typography variant="caption" color="text.secondary">
            API Conectada
          </Typography>
        </Box>
        <Box sx={{ mt: 0.5, display: 'flex', alignItems: 'center', gap: 1 }}>
          <Box
            sx={{
              width: 8,
              height: 8,
              borderRadius: '50%',
              backgroundColor: 'success.main',
            }}
          />
          <Typography variant="caption" color="text.secondary">
            6 Bancos Ativos
          </Typography>
        </Box>
        <Box sx={{ mt: 0.5, display: 'flex', alignItems: 'center', gap: 1 }}>
          <Box
            sx={{
              width: 8,
              height: 8,
              borderRadius: '50%',
              backgroundColor: 'warning.main',
            }}
          />
          <Typography variant="caption" color="text.secondary">
            IA Simulada
          </Typography>
        </Box>
      </Box>

      {/* Informações da versão */}
      <Box sx={{ p: 2, mt: 'auto' }}>
        <Divider sx={{ mb: 2 }} />
        <Typography variant="caption" color="text.secondary" align="center" display="block">
          Sistema Multi-Tenant v2.0
        </Typography>
        <Typography variant="caption" color="text.secondary" align="center" display="block">
          16 Endpoints Ativos
        </Typography>
      </Box>
    </Drawer>
  );
};

export default Sidebar;
