import React from 'react';
import {
  Box,
  Card,
  CardContent,
  Grid,
  Typography,
  Paper,
  List,
  ListItem,
  ListItemText,
} from '@mui/material';
import {
  Description as DocumentsIcon,
  Search as SearchIcon,
  Psychology as RAGIcon,
  Assessment as ReportsIcon,
} from '@mui/icons-material';

const Dashboard: React.FC = () => {
  const stats = [
    { title: 'Total Documents', value: '0', icon: <DocumentsIcon /> },
    { title: 'Search Queries', value: '0', icon: <SearchIcon /> },
    { title: 'RAG Responses', value: '0', icon: <RAGIcon /> },
    { title: 'Generated Reports', value: '0', icon: <ReportsIcon /> },
  ];

  const recentActivity = [
    'System initialized',
    'Ready for document upload',
    'Schema definitions loaded',
  ];

  return (
    <Box>
      <Typography variant="h4" component="h1" gutterBottom>
        Dashboard
      </Typography>
      
      <Grid container spacing={3} sx={{ mb: 3 }}>
        {stats.map((stat, index) => (
          <Grid item xs={12} sm={6} md={3} key={index}>
            <Card>
              <CardContent>
                <Box display="flex" alignItems="center" justifyContent="space-between">
                  <Box>
                    <Typography color="textSecondary" gutterBottom>
                      {stat.title}
                    </Typography>
                    <Typography variant="h4">
                      {stat.value}
                    </Typography>
                  </Box>
                  <Box color="primary.main">
                    {stat.icon}
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Recent Activity
            </Typography>
            <List>
              {recentActivity.map((activity, index) => (
                <ListItem key={index}>
                  <ListItemText primary={activity} />
                </ListItem>
              ))}
            </List>
          </Paper>
        </Grid>
        
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Quick Actions
            </Typography>
            <Typography variant="body2" color="textSecondary">
              • Upload your first document to get started
            </Typography>
            <Typography variant="body2" color="textSecondary">
              • Configure remote directory access
            </Typography>
            <Typography variant="body2" color="textSecondary">
              • Explore available reporting schemas
            </Typography>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

export default Dashboard;