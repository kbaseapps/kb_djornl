// kb_djornl cytoscape display
// Third-party dependencies
import 'regenerator-runtime/runtime';
import cytoscape from 'cytoscape';
import popper from 'cytoscape-popper';
// Local dependencies
import {
  componentMessageAcknowledge,
  componentMessageLoading,
  componentTippy,
  CWSALegend,
  CWSATable,
  makeTippy,
  swapElement,
} from './app/dom.js';
import {
  cytoscapeStyle,
  edgeColorClass,
  edgeColors,
  edgeScoreScale,
} from './app/style.js';
import { WOF } from './app/wof.js';
/* element data */
const ColorClassAssigned = {};
const scaleScore = (score, edgeType) => {
  if (edgeType in edgeScoreScale) {
    return edgeScoreScale[edgeType](score);
  }
  const scaled = Math.floor(Math.max(Math.round(-10 * Math.log10(1.1 - score)), 2));
  return scaled;
};
const annotateEdgeFactory = (edgeMetadata) => (edge) => {
  const colorClass = edgeColorClass(edge.data.edgeType, ColorClassAssigned);
  const [colorBg, colorFg] = edgeColors(edge.data.edgeType);
  const edgeTypeMeta = edgeMetadata[edge.data.edgeType];
  const label = edgeTypeMeta && edgeTypeMeta.name;
  edge.data = {
    ...edge.data,
    bg: colorBg,
    className: ['hidden', colorClass].join(' '),
    fg: colorFg,
    label: label,
    scoreRounded: edge.data.score.toFixed(6),
    scoreScaled: scaleScore(edge.data.score, edge.data.edgeType),
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
  if (node.data.position) {
    node.position = node.data.position;
  }
  return node;
};
/* App render management */
class Renderer {
  constructor(render) {
    this.frameRequest = null;
    this.render = render;
  }
  requestRender(...args) {
    // ideally only render on animation frames
    // but render management needs more sophistication
    cancelAnimationFrame(this.frameRequest);
    this.frameRequest = requestAnimationFrame(() => this.render(...args));
  }
}
/* App state management */
/* This object deliberately imitates the data model of React. */
class State {
  constructor(state, callback) {
    this.state = state;
    this.callback = callback;
  }
  setState(state) {
    this.state = { ...this.state, ...state };
    this.callback(this);
    return this.state;
  }
}
/* event handlers */
const layoutChangeHandlerFactory = (appState) => {
  let timer;
  const { wof } = appState.state;
  const updateAfter = 1000; // how long to wait before updating position state
  return (evt) => {
    const update = async () => {
      appState.setState({ loading: true });
      const nodesCyRaw = evt.cy
        .nodes()
        .map((node) => ({ ...node.data(), position: node.position() }));
      const nodes = nodesCyRaw.map((nodecy) => annotateNode({ data: nodecy }));
      await wof.putStoredNodes(nodes);
      appState.setState({ nodes, layout: false, loading: false });
    };
    clearTimeout(timer);
    timer = setTimeout(update, updateAfter);
  };
};
const nodeSelectChangeHandlerFactory = (appState) => (evt) => {
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
  appState.setState({ highlight });
};
const nodeClickHandler = (evt) => {
  console.log(evt.target.data().name); // eslint-disable-line no-console
};
const nodeMouseoutHandlerFactory = (appState) => (evt) => {
  const { highlight } = appState.state;
  const nodeId = evt.target.data().id;
  if (nodeId === highlight) return;
  const rowNode = document.getElementById(nodeId);
  rowNode.classList.remove('highlight');
};
const nodeMouseoverHandler = (evt) => {
  const rowNode = document.getElementById(evt.target.data().id);
  rowNode.classList.add('highlight');
};
/* Determine workspace id. */
const getWorkspaceId = () => {
  const loc = new URL(window.location.href);
  // In development use localStorage to store worskapce id.
  if (loc.hostname === 'localhost') {
    const wsidStored = localStorage.getItem('wsid');
    if (wsidStored) {
      return wsidStored;
    }
    const wsidPrompted = prompt('Use which workspace for state?');
    localStorage.setItem('wsid', wsidPrompted);
    return wsidPrompted;
  }
  /* This is coupled to the KBase HTMLFileSetServ api v1 URL specification.
   * See the [HTMLFileSetServ][repo] for details:
   * [repo]: https://github.com/kbaseapps/HTMLFileSetServ
   */
  return loc.pathname.split('/')[5];
};
/* metadata checks */
const loadMetadata = async () => {
  const metadataResponse = await fetch('graph-metadata.json');
  const metadata = await metadataResponse.json();
  console.log('metadata', metadata); // eslint-disable-line no-console
  const wsid = getWorkspaceId();
  /* The version below is a placeholder that is eventually replaced with the
   * latest version.
   */
  const ref = `${wsid}/${metadata.objid}/1`;
  return {
    edgesMeta: metadata.edges,
    layers: metadata.layers,
    nodesMeta: metadata.nodes,
    stateWSRef: ref,
    wsurl: metadata.wsurl,
  };
};
const graphIsLarge = ({ nodes }) => {
  return nodes > 50;
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
const main = ({ appState }) => {
  const {
    nodes,
    edges,
    edgeMetadata,
    highlight,
    layers,
    layersVisible,
    layout,
    loading,
    manifest,
    message,
    messageCallback,
  } = appState.state;
  const messages = document.getElementById('messages');
  const container = document.querySelectorAll('.kb-html-report')[0];
  /* Indicate whether loading is in process. */
  if (loading) {
    swapElement(messages, componentMessageLoading());
    container.classList.add('blur');
  } else {
    messages.classList.add('hidden');
    container.classList.remove('blur');
  }
  /* If a message is present then show it to the user */
  if (message) {
    const messageContainer = componentMessageAcknowledge({
      message,
      callback: messageCallback,
    });
    swapElement(messages, messageContainer);
    messageContainer.querySelectorAll('button')[0].focus();
    return;
  }
  let useLayout = cytoscapeLayout;
  if (!layout) {
    useLayout = { name: 'preset' };
  }
  window.cytoscape = cytoscape;
  window.popper = popper;
  /* Initialize cytoscape instance.  */
  const cyDOM = document.getElementById('cy');
  let cy = window.cy;
  if (!cy.nodes || cy.nodes().length === 0) {
    /* Convert graph data to cytoscape format.  */
    const annotateEdge = annotateEdgeFactory(edgeMetadata);
    const edgesCytoscape = edges.map((edge) => annotateEdge(edge));
    const nodesCytoscape = nodes.map((node) => annotateNode(node));
    cy = cytoscape({
      container: cyDOM,
      elements: { nodes: nodesCytoscape, edges: edgesCytoscape },
      layout: useLayout,
      maxZoom: 10,
      minZoom: 1 / 10,
      style: cytoscapeStyle,
      zoom: 4,
    });
    // Load popper plugin only once. It may be loaded after cy is initialized.
    if (!cy.popper) {
      cytoscape.use(popper);
    }
    // Instantiate and register event handlers.
    const layoutChangeHandler = layoutChangeHandlerFactory(appState);
    const nodeSelectChangeHandler = nodeSelectChangeHandlerFactory(appState);
    cy.nodes().on('click', nodeClickHandler);
    cy.nodes().on('mouseout', nodeMouseoutHandlerFactory(appState));
    cy.nodes().on('mouseover', nodeMouseoverHandler);
    cy.nodes().on('position', layoutChangeHandler);
    cy.nodes().on('select', nodeSelectChangeHandler);
    cy.nodes().on('unselect', nodeSelectChangeHandler);
    window.cy = cy;
    if (cy.nodes().length === 0) {
      console.log('cytoscape instance', cy); // eslint-disable-line no-console
    }
  }
  /* cy.nodes exists and there is at least one node */
  /* update graph based on state */
  cy.edges().forEach((edge) => {
    edge.removeClass('hidden');
    if (layersVisible.indexOf(edge.data().edgeType) === -1) {
      edge.addClass('hidden');
    }
  });
  /* add extra DOM */
  // ul#legend
  const legend = document.getElementById('legend');
  const legendNew = CWSALegend({
    appState,
    edgeMetadata,
    layers,
    layersVisible,
    manifest,
    colorClasses: ColorClassAssigned,
  });
  swapElement(legend, legendNew);
  // table#node-data
  const table = document.getElementById('node-data');
  const tableNew = CWSATable({ appState, table, highlight, cytoscapeInstance: cy });
  swapElement(table, tableNew);
};
// Load manifest, graph and state information from the workspace.
const loadGraphAssets = async (wof) => {
  const manifestResponse = await fetch('manifest.json');
  const manifest = await manifestResponse.json();
  const edgeMetadataResponse = await fetch('edge-metadata.json');
  const edgeMetadata = await edgeMetadataResponse.json();
  const elementsResponse = await fetch('graph.json');
  let { nodes, edges } = await elementsResponse.json(); // eslint-disable-line prefer-const
  /* Currently, the workspace object stores only nodes and their positions. */
  let storedNodes = [];
  try {
    storedNodes = await wof.getStoredNodes();
  } catch (err) {
    console.error('There was an error retrieving stored state.'); // eslint-disable-line no-console
  }
  const debugMetadata = localStorage.getItem('debug') === 'true';
  let layout = true;
  if (debugMetadata) {
    console.log('debugMetadata', debugMetadata); //eslint-disable-line no-console
    return [edges, layout, manifest, nodes];
  }
  if (storedNodes.length === nodes.length) {
    nodes = storedNodes;
    layout = false;
  }
  return [edges, edgeMetadata, layout, manifest, nodes];
};
// Load graph and workspace data and initialize state.
const loadAndRenderGraph = async (appState, stateWSRef) => {
  const { wof } = appState.state;
  const [edges, edgeMetadata, layout, manifest, nodes] = await loadGraphAssets(wof);
  appState.setState({
    edges,
    edgeMetadata,
    layout,
    manifest,
    nodes,
    stateWSRef,
    loading: false,
    message: '',
    messageCallback: () => {},
  });
};
// initalize environment
(async () => {
  /* Read Cookies */
  const cookies = Object.fromEntries(
    document.cookie.split('; ').map((cookie) => cookie.split('=', 2))
  );
  /* Instantiate workspace object facade for state persistence. */
  const wof = new WOF({
    kbase_session: cookies.kbase_session, // eslint-disable-line camelcase
  });
  /* Initialize renderer. */
  const appRenderer = new Renderer((appState) => main({ appState }));
  /* Initialize appState. */
  const appState = new State(
    {
      wof,
      edges: [],
      edgeMetadata: {},
      highlight: null,
      layout: true,
      layers: [],
      layersVisible: [],
      loading: false,
      manifest: {
        file_list: [], // eslint-disable-line camelcase
      },
      message: '',
      messageCallback: () => {},
      nodes: [],
      sort: '_selected',
      stateWSRef: '',
    },
    /* Render the graph when appState.state is updated. */
    (appState) => appRenderer.requestRender(appState)
  );
  /* loading metadata */
  appState.setState({ loading: true });
  const { edgesMeta, layers, nodesMeta, stateWSRef, wsurl } = await loadMetadata();
  wof.setURL(wsurl);
  wof.setRef(stateWSRef);
  /* metadata checks */
  if (graphIsLarge({ nodes: nodesMeta })) {
    const graphIsLargeMessage = [
      'Refusing to load large dataset automatically.',
      `This graph contains ${nodesMeta} nodes and ${edgesMeta} edges.`,
      'Click the button to load anyway.',
    ].join(' ');
    const graphIsLargeCallback = async () => {
      appState.setState({
        layers,
        layersVisible: layers,
        loading: true,
        message: '',
        messageCallback: () => {},
      });
      await loadAndRenderGraph(appState, stateWSRef);
    };
    /* Stop loading and prompt user to load large graph. */
    appState.setState({
      layers,
      layersVisible: layers,
      loading: false,
      message: graphIsLargeMessage,
      messageCallback: graphIsLargeCallback,
    });
    return;
  }
  await loadAndRenderGraph(appState, stateWSRef);
})();
