// kb_djornl cytoscape display
// Third-party dependencies
import 'regenerator-runtime/runtime';
import cytoscape from 'cytoscape';
import popper from 'cytoscape-popper';

// Local dependencies
import {
  componentTippy,
  makeTippy,
  promptUserForConfirmation,
  renderLegend,
  renderTable,
} from './app/dom.js';
import {
  cytoscapeStyle,
  edgeColorClass,
  edgeColors,
  edgeMetadata,
} from './app/style.js';

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
    label: edgeMetadata[edge.data.edgeType].name,
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
  node.classes = [node.data.seed ? 'seed' : ''];
  return node;
};

/* event handlers */
const nodeSelectChangeHandler = (evt) => {
  // selected node
  const id = evt.target.data().id;
  // get or make the tippy element for this node
  let nodeTippy = evt.target.data().tippy;
  if (!nodeTippy) {
    nodeTippy = makeTippy(
      evt.cy.getElementById(id),
      componentTippy({ data: evt.target.data() })
    );
  }
  evt.target.data().tippy = nodeTippy;
  // hide the tippy for each node
  evt.cy.nodes().forEach((node) => {
    const thisNodeTippy = node.data().tippy;
    if (thisNodeTippy && thisNodeTippy.hide) {
      node.data().tippy.hide();
    }
  });
  // if this node is being selected, display the tippy
  const selected = evt.type === 'select';
  evt.target.data().selected = selected;
  let highlight;
  if (selected) {
    nodeTippy.show();
    highlight = id;
  }
  // render the table to update selections
  const table = document.getElementById('node-data');
  renderTable({ table, cytoscapeInstance: evt.cy, highlight });
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
const main = ({ nodes, edges, loaded, manifest }) => {
  //cytoscape.use(cytoscapeSpread);
  const nodesCytoscape = nodes.map((node) => annotateNode(node));
  const edgesCytoscape = edges.map((edge) => annotateEdge(edge));
  let useLayout = cytoscapeLayout;
  if (loaded) {
    // set these values on subsequent loads
    useLayout = { name: 'preset' };
  } else {
    // load popper on first load
    cytoscape.use(popper);
  }
  const cyDOM = document.getElementById('cy');
  const cy = cytoscape({
    container: cyDOM,
    elements: { nodes: nodesCytoscape, edges: edgesCytoscape },
    layout: useLayout,
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
  console.log('cytoscape', cy); // eslint-disable-line no-console
  /* add extra DOM */
  // ul#legend
  const legend = document.getElementById('legend');
  renderLegend({
    edgeMetadata,
    legend,
    manifest,
    colorClasses: ColorClassAssigned,
    cytoscapeInstance: cy,
  });
  // table#node-data
  const table = document.getElementById('node-data');
  renderTable({ table, cytoscapeInstance: cy });
};
// initalize environment
(async () => {
  const messages = document.getElementById('messages');
  const container = document.querySelectorAll('.kb-html-report')[0];
  const elementsMetadataResponse = await fetch('graph-metadata.json');
  const elementsMetadata = await elementsMetadataResponse.json();
  const loadMain = async () => {
    const elementsResponse = await fetch('graph.json');
    const { nodes, edges } = await elementsResponse.json();
    const manifestResponse = await fetch('manifest.json');
    const manifest = await manifestResponse.json();
    main({ nodes, edges, manifest });
  };
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
  await loadMain();
})();
