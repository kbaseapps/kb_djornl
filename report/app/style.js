import './style.css';
/* KBase colors and cytoscape style */
const RAINIER_CHERRY_RED = '#d2232a';
const SPRING_GREEN = '#c1cd23';
const ColorClassOrder = [
  '.cyanobacteria_teal',
  '.rainier_cherry_red',
  '.freshwater_blue',
  '.microbe_orange',
  '.lupine_purple',
  '.spring_green',
  '.graphite_grey',
  '.frost_blue',
  '.golden_yellow',
  '.ocean_blue',
  '.grass_green',
];
const colorPalette = [
  '#009688', // cyanobacteria_teal
  RAINIER_CHERRY_RED,
  '#037ac0', // freshwater_blue
  '#f78e1e', // microbe orange
  '#66489d', // lupine purple
  SPRING_GREEN,
  '#9d9389', // graphite grey
  '#c7dbee', // frost_blue
  '#ffd200', // golden yellow
  '#72ccd2', // ocean_blue
  '#5e9732', // grass green
];
const labelPalette = [
  '#ffffff',
  '#ffffff',
  '#ffffff',
  '#000000',
  '#ffffff',
  '#000000',
  '#000000',
  '#000000',
  '#000000',
  '#000000',
  '#ffffff',
];
const colorsAssigned = {};
export const edgeColors = (edgeType) => {
  if (edgeType in colorsAssigned) {
    return colorsAssigned[edgeType];
  }
  const colorsLen = Object.keys(colorsAssigned).length;
  const colorIndex = colorsLen % colorPalette.length;
  const colorBg = colorPalette[colorIndex];
  const colorFg = labelPalette[colorIndex];
  colorsAssigned[edgeType] = [colorBg, colorFg];
  return [colorBg, colorFg];
};
export const edgeColorClass = (edgeType, assigned = {}) => {
  if (edgeType in assigned) {
    return assigned[edgeType];
  }
  const colorsLen = Object.keys(assigned).length;
  const colorIndex = colorsLen % ColorClassOrder.length;
  const colorClass = ColorClassOrder[colorIndex];
  assigned[edgeType] = colorClass;
  return colorClass;
};
export const cytoscapeStyle = [
  {
    selector: 'node',
    style: {
      'background-color': 'mapData(id.length, 0, 15, #000, #4682b4)',
      content: 'data(name)',
      'font-family': 'Oxygen, Arial, sans-serif',
      'font-size': '1.375em',
      shape: 'round-rectangle',
      'text-halign': 'center',
      'text-outline-color': '#4682b4',
      'text-outline-width': '2px',
      'text-valign': 'center',
      width: '110px',
    },
  },
  {
    selector: 'node.collected',
    style: {
      'border-width': 4,
      'border-style': 'solid',
      'border-color': RAINIER_CHERRY_RED,
      'border-opacity': 1,
    },
  },
  {
    selector: 'node.highlight',
    style: {
      'border-color': SPRING_GREEN,
      'border-width': '8px',
    },
  },
  {
    selector: 'node:selected',
    style: {
      'border-color': '#e77943',
      'border-width': '4px',
      label: 'data(name)',
    },
  },
  {
    selector: 'edge',
    style: {
      color: 'data(fg)',
      'curve-style': 'bezier',
      'font-weight': 'bold',
      'line-color': 'data(bg)',
      'source-endpoint': 'inside-to-node',
      'target-endpoint': 'inside-to-node',
      'text-outline-color': 'data(bg)',
      'text-outline-width': '2px',
      width: 'data(scoreScaled)',
      'z-index': 1,
    },
  },
  {
    selector: 'edge:selected',
    style: {
      label: 'data(scoreRounded)',
    },
  },
  {
    selector: 'edge.hidden',
    style: {
      display: 'none',
    },
  },
];
export const edgeMetadata = {
  'phenotype-association_AraGWAS_subnet_permsig_geni': {
    cite: '#aragwas',
    name: 'AraGWAS subnet',
    title: 'AraGWAS phenotype association',
  },
  'phenotype-association_GWAS_gene_to_metabolite_10.1371/journal.pgen.1006363': {
    cite: '#gwasgene',
    name: 'GWAS gene to metabolite',
    title: 'AraGWAS subnet permsig geni GeneToPhenotype',
  },
  'protein-protein-interaction_AtPIN': {
    cite: '#atpin',
    name: 'AtPIN',
    title: 'AtPIN PPI',
  },
  'protein-protein-interaction_Mentha_A_thaliana_3702_040319': {
    cite: '#mentha',
    name: 'Mentha A thaliana',
    title: 'Mentha AT 3702 040319 PPI',
  },
  'protein-protein-interaction_biogrid_date/release3.5.188': {
    cite: '#biogrid',
    name: 'BIOGrid',
    title: 'BIOGRID ORGANISM Arabidopsis thaliana Columbia 3.5.188 tab3 PPI',
  },
  'protein-protein-interaction_literature_curated_AraNet_v2_subnet': {
    cite: '#aranet',
    name: 'AraNet subnet',
    title: 'AraNetv2 subnet AT-LC PPI',
  },
  'transcription-factor-regulatory-interaction_literature_curated_ATRM_01082020': {
    cite: '#atrm',
    name: 'ATRM',
    title: 'ATRM TF to Target LitCurated 01082020 TranscriptionFactorToGene',
  },
};
