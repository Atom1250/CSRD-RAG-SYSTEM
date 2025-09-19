import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  Tabs,
  Tab,
  List,
  ListItem,
  ListItemText,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Chip,
} from '@mui/material';
import { ExpandMore as ExpandMoreIcon } from '@mui/icons-material';

interface SchemaElement {
  code: string;
  name: string;
  description: string;
  requirements: string[];
  subElements?: SchemaElement[];
}

const Schemas: React.FC = () => {
  const [selectedTab, setSelectedTab] = useState(0);

  const esrsSchema: SchemaElement[] = [
    {
      code: 'ESRS 1',
      name: 'General Requirements',
      description: 'General principles and requirements for sustainability reporting',
      requirements: [
        'Double materiality assessment',
        'Stakeholder engagement',
        'Value chain considerations',
      ],
    },
    {
      code: 'ESRS E1',
      name: 'Climate Change',
      description: 'Climate-related disclosures including transition and physical risks',
      requirements: [
        'Climate-related risks and opportunities',
        'GHG emissions (Scope 1, 2, 3)',
        'Climate adaptation and mitigation',
        'Energy consumption and mix',
      ],
      subElements: [
        {
          code: 'E1-1',
          name: 'Transition Plan',
          description: 'Climate transition plan disclosure requirements',
          requirements: ['Transition plan details', 'Targets and milestones'],
        },
        {
          code: 'E1-2',
          name: 'Physical Risks',
          description: 'Physical climate risk assessment and management',
          requirements: ['Risk identification', 'Adaptation measures'],
        },
      ],
    },
    {
      code: 'ESRS E2',
      name: 'Pollution',
      description: 'Pollution prevention and control disclosures',
      requirements: [
        'Air pollutants',
        'Water pollutants',
        'Soil pollutants',
        'Waste management',
      ],
    },
    {
      code: 'ESRS S1',
      name: 'Own Workforce',
      description: 'Disclosures related to the undertaking\'s own workforce',
      requirements: [
        'Working conditions',
        'Equal treatment and opportunities',
        'Health and safety',
        'Social dialogue',
      ],
    },
    {
      code: 'ESRS G1',
      name: 'Business Conduct',
      description: 'Business conduct and governance disclosures',
      requirements: [
        'Corporate culture',
        'Anti-corruption and bribery',
        'Political engagement',
        'Payment practices',
      ],
    },
  ];

  const ukSrdSchema: SchemaElement[] = [
    {
      code: 'UK-1',
      name: 'Mandatory Climate Disclosures',
      description: 'Required climate-related financial disclosures',
      requirements: [
        'Governance arrangements',
        'Strategy and risk management',
        'Metrics and targets',
        'Scenario analysis',
      ],
    },
    {
      code: 'UK-2',
      name: 'Environmental Reporting',
      description: 'Environmental impact and sustainability reporting',
      requirements: [
        'Energy and carbon reporting',
        'Water usage',
        'Waste and circular economy',
        'Biodiversity impact',
      ],
    },
    {
      code: 'UK-3',
      name: 'Social and Governance',
      description: 'Social responsibility and governance disclosures',
      requirements: [
        'Employee wellbeing',
        'Diversity and inclusion',
        'Supply chain responsibility',
        'Board oversight',
      ],
    },
  ];

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setSelectedTab(newValue);
  };

  const renderSchemaElements = (elements: SchemaElement[]) => (
    <Box>
      {elements.map((element) => (
        <Accordion key={element.code} sx={{ mb: 1 }}>
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <Box display="flex" alignItems="center" gap={2} width="100%">
              <Chip label={element.code} color="primary" size="small" />
              <Typography variant="h6">{element.name}</Typography>
            </Box>
          </AccordionSummary>
          <AccordionDetails>
            <Typography variant="body2" color="textSecondary" paragraph>
              {element.description}
            </Typography>
            
            <Typography variant="subtitle2" gutterBottom>
              Key Requirements:
            </Typography>
            <List dense>
              {element.requirements.map((requirement, index) => (
                <ListItem key={index} sx={{ py: 0.5 }}>
                  <ListItemText 
                    primary={`• ${requirement}`}
                    primaryTypographyProps={{ variant: 'body2' }}
                  />
                </ListItem>
              ))}
            </List>

            {element.subElements && (
              <Box mt={2}>
                <Typography variant="subtitle2" gutterBottom>
                  Sub-elements:
                </Typography>
                {element.subElements.map((subElement) => (
                  <Card key={subElement.code} variant="outlined" sx={{ mt: 1, ml: 2 }}>
                    <CardContent sx={{ py: 1 }}>
                      <Box display="flex" alignItems="center" gap={1} mb={1}>
                        <Chip label={subElement.code} size="small" variant="outlined" />
                        <Typography variant="subtitle2">{subElement.name}</Typography>
                      </Box>
                      <Typography variant="body2" color="textSecondary" sx={{ mb: 1 }}>
                        {subElement.description}
                      </Typography>
                      <List dense>
                        {subElement.requirements.map((req, idx) => (
                          <ListItem key={idx} sx={{ py: 0 }}>
                            <ListItemText 
                              primary={`• ${req}`}
                              primaryTypographyProps={{ variant: 'body2' }}
                            />
                          </ListItem>
                        ))}
                      </List>
                    </CardContent>
                  </Card>
                ))}
              </Box>
            )}
          </AccordionDetails>
        </Accordion>
      ))}
    </Box>
  );

  return (
    <Box>
      <Typography variant="h4" component="h1" gutterBottom>
        Reporting Schemas
      </Typography>
      
      <Card>
        <CardContent>
          <Tabs value={selectedTab} onChange={handleTabChange} sx={{ mb: 3 }}>
            <Tab label="EU ESRS/CSRD" />
            <Tab label="UK SRD" />
          </Tabs>

          {selectedTab === 0 && (
            <Box>
              <Typography variant="h6" gutterBottom>
                European Sustainability Reporting Standards (ESRS)
              </Typography>
              <Typography variant="body2" color="textSecondary" paragraph>
                The ESRS are the technical standards that specify the information that companies 
                must report under the Corporate Sustainability Reporting Directive (CSRD).
              </Typography>
              {renderSchemaElements(esrsSchema)}
            </Box>
          )}

          {selectedTab === 1 && (
            <Box>
              <Typography variant="h6" gutterBottom>
                UK Sustainability Reporting Directive (UK SRD)
              </Typography>
              <Typography variant="body2" color="textSecondary" paragraph>
                UK-specific sustainability reporting requirements for large companies and 
                financial institutions operating in the United Kingdom.
              </Typography>
              {renderSchemaElements(ukSrdSchema)}
            </Box>
          )}
        </CardContent>
      </Card>
    </Box>
  );
};

export default Schemas;