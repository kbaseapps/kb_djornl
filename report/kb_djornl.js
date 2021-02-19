// kb_djornl cytoscape display
// Third-party dependencies
import 'regenerator-runtime/runtime';
import cytoscape from 'cytoscape';
import popper from 'cytoscape-popper';

// Local dependencies
import {
  formatLegend,
  makeTippy,
  promptUserForConfirmation,
  renderTable,
  tippyContent,
} from './app/dom.js';
import { cytoscapeStyle, edgeColorClass, edgeColors, edgeNames } from './app/style.js';
/* element data */
const ColorClassAssigned = {};
const scaleScore = (score) => {
  const scaled = Math.max(Math.round(-10 * Math.log10(1.1 - score)), 2);
  return scaled;
};
const annotateEdge = (edge) => {
  const colorClass = edgeColorClass(edge.data.edgeType, ColorClassAssigned);
  const [colorBg, colorFg] = edgeColors(edge.data.edgeType);
  edge.data = {
    ...edge.data,
    bg: colorBg,
    className: colorClass,
    fg: colorFg,
    label: edgeNames[edge.data.edgeType],
    scoreRounded: edge.data.score.toFixed(6),
    scoreScaled: scaleScore(edge.data.score),
  };
  return edge;
};
const annotateNode = (node) => {
  node.data = {
    ...node.data,
    collected: false,
    name: node.data.id.split('/')[1],
    selected: false,
    tippy: false,
  };
  return node;
};
const annotations = {
  node: annotateNode,
  edge: annotateEdge,
};
const annotateElements = (elements) =>
  elements.map((element) => annotations[element.data.type](element));

/* event handlers */
const nodeSelectChangeHandler = (evt) => {
  // selected node
  const id = evt.target.data().id;
  // get or make the tippy element for this node
  let nodeTippy = evt.target.data().tippy;
  if (!nodeTippy) {
    nodeTippy = makeTippy(evt.cy.getElementById(id), tippyContent(evt.target.data()));
  }
  evt.target.data().tippy = nodeTippy;
  // hide the tippy for each node
  evt.cy.nodes().forEach((node) => {
    const thisNodeTippy = node.data().tippy;
    if (thisNodeTippy && thisNodeTippy.hide) {
      node.data().tippy.hide();
    }
  });
  const options = {};
  // if this node is being selected, display the tippy
  const selected = evt.type === 'select';
  evt.target.data().selected = selected;
  if (selected) {
    nodeTippy.show();
    options.highlight = id;
  }
  // render the table to update selections
  const table = document.getElementById('node-data');
  renderTable(table, evt.cy, options);
};
const nodeClickHandler = (evt) => {
  console.log(evt.target.data().name); // eslint-disable-line no-console
};
/* metadata checks */
const checkData = (metadata) => {
  console.log('metadata', metadata); // eslint-disable-line no-console
  if (metadata.nodes > 50) {
    console.log('More than 50 nodes.'); // eslint-disable-line no-console
    return false;
  }
  return true;
};
/* initial layout */
const cytoscapeLayout = {
  animate: false,
  fit: true,
  gravity: 1,
  name: 'cose',
  nodeDimensionsIncludeLabels: true,
  nodeOverlap: 10000,
  nodeRepulsion: (node) => {
    return (node.degree() * 2048) ** 2;
  },
  padding: 100,
};
/* main screen turn on */
const main = async (data = 'default.json') => {
  const elementsResponse = await fetch(data);
  const elementsJSON = await elementsResponse.json();
  //cytoscape.use(cytoscapeSpread);
  cytoscape.use(popper);
  const cyDOM = document.getElementById('cy');
  const cy = cytoscape({
    container: cyDOM,
    elements: annotateElements(elementsJSON),
    layout: cytoscapeLayout,
    maxZoom: 10,
    minZoom: 1 / 10,
    style: cytoscapeStyle,
    zoom: 4,
  });
  // add event handlers
  cy.nodes().on('click', nodeClickHandler);
  cy.nodes().on('select', nodeSelectChangeHandler);
  cy.nodes().on('unselect', nodeSelectChangeHandler);
  /* debug */
  window.cy = cy;
  console.log('cytoscape', cy); // eslint-disable-line no-console
  /* add extra DOM */
  // ul#legend
  const legend = document.getElementById('legend');
  formatLegend(legend, ColorClassAssigned, edgeNames);
  // table#node-data
  const table = document.getElementById('node-data');
  renderTable(table, cy);
};
// initalize environment
(async () => {
  const messages = document.getElementById('messages');
  const container = document.querySelectorAll('.kb-html-report')[0];
  const elementsMetadataResponse = await fetch('djornl-metadata.json');
  const elementsMetadata = await elementsMetadataResponse.json();
  const loadMain = () => main('djornl.json');
  if (!checkData(elementsMetadata)) {
    const { nodes, edges } = elementsMetadata;
    const message = document.createTextNode(
      [
        'Refusing to load large dataset automatically.',
        `This graph contains ${nodes} nodes and ${edges} edges.`,
        'Click the button to load anyway.',
      ].join(' ')
    );
    const ackButton = document.createElement('button');
    ackButton.appendChild(document.createTextNode('OK'));
    const messageContainer = document.createElement('span');
    messageContainer.classList.add('message');
    messageContainer.appendChild(message);
    messageContainer.appendChild(ackButton);
    promptUserForConfirmation({ container, messages }, messageContainer, loadMain);
    return;
  }
  loadMain();
})();
