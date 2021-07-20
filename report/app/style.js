import './style.css';
/* KBase colors and cytoscape style */
const CYANOBACTERIA_TEAL = '#009688';
const FROST_BLUE = '#c7dbee';
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
  CYANOBACTERIA_TEAL,
  RAINIER_CHERRY_RED,
  '#037ac0', // freshwater_blue
  '#f78e1e', // microbe orange
  '#66489d', // lupine purple
  SPRING_GREEN,
  '#9d9389', // graphite grey
  FROST_BLUE,
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
      'background-color': FROST_BLUE,
      content: 'data(name)',
      'font-family': 'Oxygen, Arial, sans-serif',
      'font-size': '1.375em',
      shape: 'round-rectangle',
      'text-halign': 'center',
      'text-outline-color': FROST_BLUE,
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
      'border-color': SPRING_GREEN,
      'border-opacity': 1,
    },
  },
  {
    selector: 'node.highlight',
    style: {
      'border-color': CYANOBACTERIA_TEAL,
      'border-width': '8px',
    },
  },
  {
    selector: 'node.seed',
    style: {
      'border-color': RAINIER_CHERRY_RED,
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
  GO: {
    cite: '#GO',
    name: 'GO',
    title:
      'GeneA connects to GeneB if the two genes have semantically similar GO terms (with a similarity score > 0). This network is used to evaluate other networks for biological functional content. DOI: [TODO]',
  },
  Knockout: {
    cite: '#Knockout',
    name: 'Knockout',
    title:
      'GeneA connects to GeneB if the phenotypic effect of knocking out GeneA is similar to the phenotypic effect of knocking out GeneB. Similarity is based on Phenotype Ontology semantic similarity. DOI: https://doi.org/10.1186/s13007-015-0053-y',
  },
  'Metabolic-AraCyc': {
    cite: '#Metabolic-AraCyc',
    name: 'Metabolic-AraCyc',
    title:
      'GeneA connects to GeneB if they are both enzymes and are linked by a common substrate or product. E.g. RXNA (GeneA) → Compound1 → RXNB (GeneB). Here GeneA connects to GeneB due to Compound1. DOI: [TODO]',
  },
  'PPI-6merged': {
    cite: '#PPI-6merged',
    name: 'PPI-6merged',
    title:
      'GeneA connects to GeneB if their protein products have been shown to bind to interact with each other, typically through experimental evidence. The PPI-6merged network is the union of 6 different A.thaliana PPI networks: AraNet2 LC, AraNet2 HT, AraPPInet2 0.60, BIOGRID 4.3.194 physical, AtPIN, Mentha. These 6 were all relatively high scoring with GOintersect. DOI: [TODO]',
  },
  'Regulation-ATRM': {
    cite: '#Regulation-ATRM',
    name: 'Regulation-ATRM',
    title:
      'GeneA connects to GeneB if GeneA is a Transcription Factor (TF) that is shown to interact with GeneB (which may or may not be a TF). This dataset contains literature mined and manually curated TF regulatory interactions for A.thaliana. Started from 1701 TFs from PlantTFDB 2.0 and retrieved 4663 TF-associated interactions. These were manually filtered (e.g. FPs, PPI interactions removed). They then added some from other sources. Final result is 1431 confirmed TF regulatory interactions, of which 637 are TF-TF. Data origin: http://atrm.cbi.pku.edu.cn/download.php DOI: [TODO]',
  },
};
