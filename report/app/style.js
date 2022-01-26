import './style.css';
/* KBase colors and cytoscape style */
const CYANOBACTERIA_TEAL = '#009688';
const FROST_BLUE = '#c7dbee';
const GOLDEN_YELLOW = '#ffd200';
const LUPINE_PURPLE = '#66489d';
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
  LUPINE_PURPLE,
  SPRING_GREEN,
  '#9d9389', // graphite grey
  FROST_BLUE,
  GOLDEN_YELLOW,
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
const colorFunc = `mapData(rank, 1, 100, ${CYANOBACTERIA_TEAL}, ${FROST_BLUE})`;
export const cytoscapeStyle = [
  {
    selector: 'node',
    style: {
      'background-color': colorFunc,
      content: 'data(name)',
      color: '#fff',
      'font-family': 'Oxygen, Arial, sans-serif',
      'font-size': '1.375em',
      shape: 'round-rectangle',
      'text-halign': 'center',
      'text-outline-color': '#000',
      'text-outline-width': '2px',
      'text-valign': 'center',
      width: '110px',
    },
  },
  {
    selector: 'node[rank > 0]',
    style: {
      'background-color': colorFunc,
      'text-outline-color': colorFunc,
    },
  },
  {
    selector: 'node.collected',
    style: {
      'border-width': '4px',
      'border-style': 'solid',
      'border-color': RAINIER_CHERRY_RED,
    },
  },
  {
    selector: 'node.highlight',
    style: {
      'border-color': GOLDEN_YELLOW,
      'border-width': '8px',
    },
  },
  {
    selector: 'node.seed',
    style: {
      'background-color': LUPINE_PURPLE,
      'text-outline-color': LUPINE_PURPLE,
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
export const edgeScoreScale = {
  'AT-UU-GA-01-AA-01': (score) => {
    const scoreMin = 6.7;
    const scoreMax = 29.7;
    const scaled = (score - scoreMin) / (scoreMax - scoreMin);
    return 6 * scaled + 4; // eslint-disable-line no-mixed-operators
  },
};
