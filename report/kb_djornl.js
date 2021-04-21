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
  componentULLegend,
  makeTippy,
  renderTable,
  swapElement,
} from './app/dom.js';
import {
  cytoscapeStyle,
  edgeColorClass,
  edgeColors,
  edgeMetadata,
} from './app/style.js';
import { WOF } from './app/wof.js';
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
  if (node.data.position) {
    node.position = node.data.position;
  }
  return node;
};
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
  const updateAfter = 250; // how long to wait before updating position state
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
  // render the table to update selections
  const table = document.getElementById('node-data');
  // TODO: fix sort
  const tableNew = renderTable({
    table,
    cytoscapeInstance: evt.cy,
    highlight,
    appState,
  });
  swapElement(table, tableNew);
};
const nodeClickHandler = (evt) => {
  console.log(evt.target.data().name); // eslint-disable-line no-console
};
/* metadata checks */
const loadMetadata = async () => {
  const metadataResponse = await fetch('graph-metadata.json');
  const metadata = await metadataResponse.json();
  console.log('metadata', metadata); // eslint-disable-line no-console
  return {
    nodesMeta: metadata.nodes,
    edgesMeta: metadata.edges,
    stateWSRef: metadata.state,
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
    initialized,
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
    return;
  }
  /* Convert graph data to cytoscape format.  */
  const nodesCytoscape = nodes.map((node) => annotateNode(node));
  const edgesCytoscape = edges.map((edge) => annotateEdge(edge));
  let useLayout = cytoscapeLayout;
  if (!layout) {
    useLayout = { name: 'preset' };
  }
  if (!initialized) {
    // Load popper plugin on first render only.
    cytoscape.use(popper);
  }
  /* Initialize cytoscape instance.  */
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
  // Instantiate and register event handlers.
  const layoutChangeHandler = layoutChangeHandlerFactory(appState);
  const nodeSelectChangeHandler = nodeSelectChangeHandlerFactory(appState);
  cy.nodes().on('click', nodeClickHandler);
  cy.nodes().on('position', layoutChangeHandler);
  cy.nodes().on('select', nodeSelectChangeHandler);
  cy.nodes().on('unselect', nodeSelectChangeHandler);
  /* debug */
  if (!initialized) {
    console.log('cytoscape', cy); // eslint-disable-line no-console
  }
  window.cy = cy;
  /* add extra DOM */
  // ul#legend
  const legend = document.getElementById('legend');
  const legendNew = componentULLegend({
    edgeMetadata,
    manifest,
    colorClasses: ColorClassAssigned,
    cytoscapeInstance: cy,
  });
  swapElement(legend, legendNew);
  // table#node-data
  const table = document.getElementById('node-data');
  const tableNew = renderTable({ table, cytoscapeInstance: cy, appState });
  swapElement(table, tableNew);
};
// Load manifest, graph and state information from the workspace.
const loadManifestAndGraph = async (wof) => {
  const manifestResponse = await fetch('manifest.json');
  const manifest = await manifestResponse.json();
  const elementsResponse = await fetch('graph.json');
  let { nodes, edges } = await elementsResponse.json(); // eslint-disable-line prefer-const
  /* Currently, the workspace object stores only nodes and their positions. */
  const storedNodes = await wof.getStoredNodes();
  let layout = true;
  if (storedNodes.length === nodes.length) {
    nodes = storedNodes;
    layout = false;
  }
  return [edges, layout, manifest, nodes];
};
// Load graph and workspace data and initialize state.
const loadAndRenderGraph = async (appState, stateWSRef) => {
  const { wof } = appState.state;
  const [edges, layout, manifest, nodes] = await loadManifestAndGraph(wof);
  appState.setState({
    edges,
    layout,
    manifest,
    nodes,
    stateWSRef,
    initialized: true,
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
  /* Initialize appState. */
  const appState = new State(
    {
      wof,
      edges: [],
      initialized: false,
      layout: true,
      loading: false,
      manifest: {
        file_list: [], // eslint-disable-line camelcase
      },
      message: '',
      messageCallback: () => {},
      nodes: [],
      sort: 'selected',
      stateWSRef: '',
    },
    /* Render the graph when appState.state is updated. */
    (appState) => {
      main({ appState });
    }
  );
  /* loading metadata */
  appState.setState({ loading: true });
  const { nodesMeta, edgesMeta, stateWSRef, wsurl } = await loadMetadata();
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
        loading: true,
        message: '',
        messageCallback: () => {},
      });
      await loadAndRenderGraph(appState, stateWSRef);
    };
    /* Stop loading and prompt user to load large graph. */
    appState.setState({
      initialized: true,
      message: graphIsLargeMessage,
      messageCallback: graphIsLargeCallback,
      loading: false,
    });
    return;
  }
  await loadAndRenderGraph(appState, stateWSRef);
})();
