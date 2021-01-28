const cytoscape = window.cytoscape;
const tippy = window.tippy;
const cytoscapeSpread = window.cytoscapeSpread;
const RAINIER_CHERRY_RED = '#d2232a';
const color_palette = [
  '#009688', // cyanobacteria_teal
  RAINIER_CHERRY_RED,
  '#037ac0', // freshwater_blue
  '#f78e1e', // microbe orange
  '#66489d', // lupine purple
  '#c1cd23', // spring green
  '#9d9389', // graphite grey
  '#c7dbee', // frost_blue
  '#ffd200', // golden yellow
  '#72ccd2', // ocean_blue
  '#5e9732', // grass green
];
const label_palette = [
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
const colors_assigned = {};
const edge_colors = (edge_type) => {
  if (edge_type in colors_assigned) {
    return colors_assigned[edge_type];
  }
  const n_colors = Object.keys(colors_assigned).length;
  const colorIndex = n_colors % color_palette.length;
  const colorBg = color_palette[colorIndex];
  const colorFg = label_palette[colorIndex];
  colors_assigned[edge_type] = [colorBg, colorFg];
  return [colorBg, colorFg];
};
const annotateEdge = (edge) => {
  const [colorBg, colorFg] = edge_colors(edge.data.label);
  edge.data = {
    ...edge.data,
    fg: colorFg,
    bg: colorBg,
  };
  return edge;
};
const annotateNode = (node) => {
  node.data = {
    ...node.data,
    collected: false,
    name: node.data.id.split('/')[1],
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
// style for nodes and elements
const cytoscapeStyle = [
  {
    selector: 'node',
    style: {
      'background-color': 'mapData(id.length, 0, 15, #000, #4682b4)',
      content: 'data(name)',
      shape: 'round-rectangle',
      'text-halign': 'center',
      'text-outline-color': '#4682b4',
      'text-outline-width': '2px',
      'text-valign': 'center',
      width: '100px',
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
    selector: 'node:selected',
    style: {
      'border-color': '#e77943',
      'border-width': '4px',
      label: 'data(name)',
    },
  },
  {
    selector: 'node.phenotype',
    style: {
      width: 50,
      height: 50,
      shape: 'round-diamond',
    },
  },
  {
    selector: 'edge',
    style: {
      color: 'data(fg)',
      'curve-style': 'bezier',
      'font-weight': 'bold',
      'line-color': 'data(bg)',
      'text-outline-color': 'data(bg)',
      'text-outline-width': '2px',
      width: 3,
      'z-index': 1,
    },
  },
  {
    selector: 'edge:selected',
    style: {
      label: 'data(label)',
    },
  },
];
const makeTippy = function (ele, text) {
  const ref = ele.popperRef();
  const dummyDomEle = document.createElement('div');
  const tip = tippy(dummyDomEle, {
    // your own preferences:
    appendTo: document.body, // or append dummyDomEle to document.body
    arrow: true,
    content: () => {
      const div = document.createElement('div');
      div.appendChild(document.createTextNode(text));
      return div;
    },
    hideOnClick: false,
    getReferenceClientRect: ref.getBoundingClientRect,
    interactive: true,
    placement: 'bottom',
    sticky: 'reference',
    trigger: 'manual',
  });

  return tip;
};
const nodeData = (data) => {
  return Object.values(data);
};
const nodeClickListener = (evt) => {
  console.log(evt.target.data().name); // eslint-disable-line no-console
};
const tableRow = (cells, tag = 'td') => {
  const tr = document.createElement('tr');
  cells.forEach((cell) => {
    const td = document.createElement(tag);
    td.appendChild(cell);
    tr.appendChild(td);
  });
  return tr;
};
const hold = (node) => {
  const id = node.data().id;
  const holdBox = document.createElement('input');
  holdBox.type = 'checkbox';
  holdBox.id = `hold-${id}`;
  holdBox.name = holdBox.id;
  holdBox.checked = node.data().collected || false;
  holdBox.onchange = (evt) => {
    node.data().collected = evt.target.checked;
    if (!evt.target.checked) {
      node.select();
      node.deselect();
    }
  };
  return holdBox;
};
const nodeSelectChangeListener = (evt) => {
  // selected node
  console.log('evt.target', evt.target); // eslint-disable-line no-console
  const id = evt.target.data().id;
  let nodeTippy = evt.target.data().tippy;
  if (!nodeTippy) {
    nodeTippy = makeTippy(
      evt.cy.getElementById(id),
      nodeData(evt.target.data().go_terms)
    );
  }
  evt.target.data().tippy = nodeTippy;
  evt.cy.nodes().forEach((node) => {
    const thisNodeTippy = node.data().tippy;
    if (thisNodeTippy && thisNodeTippy.hide) {
      node.data().tippy.hide();
    }
  });
  nodeTippy.show();
  // selection/collection table
  const table = document.getElementById('selection');
  [...table.children].forEach((child) => child.remove());
  const selectedNodes = evt.cy.nodes().filter((node) => node.selected());
  const collectedNodes = evt.cy.nodes().filter((node) => node.data().collected);
  const displayedNodes = [...collectedNodes.add(selectedNodes)];
  displayedNodes.forEach((node) => node.removeClass('collected'));
  collectedNodes.forEach((node) => node.addClass('collected'));
  const firstNode = displayedNodes[0];
  if (!firstNode) return;
  const keys = Object.keys(firstNode.data()).map((node) =>
    document.createTextNode(node)
  );
  const headers = tableRow(keys, 'th');
  table.appendChild(headers);
  displayedNodes.forEach((node) => {
    const nodeData = Object.values(node.data()).map((datum) =>
      document.createTextNode(datum)
    );
    const nodeHold = hold(node);
    const row = tableRow(nodeData.concat(nodeHold));
    table.appendChild(row);
  });
};

// initalize environment
(async () => {
  const elements_response = await fetch('djornl.json');
  const elements_json = await elements_response.json();
  cytoscape.use(cytoscapeSpread); // eslint-disable-line no-undef
  const cy = cytoscape({
    container: document.getElementById('cy'), // container to render in
    elements: annotateElements(elements_json),
    style: cytoscapeStyle,
    layout: {
      animate: false,
      minDist: 100,
      name: 'spread',
      prelayout: {
        animate: false,
        name: 'cose',
        gravity: 100,
      },
    },
  });
  // add listeners
  cy.nodes().on('click', nodeClickListener);
  cy.nodes().on('select', nodeSelectChangeListener);
  cy.nodes().on('unselect', nodeSelectChangeListener);
  console.log('cytoscape', cy); // eslint-disable-line no-console
  // table
  const table = document.createElement('table');
  table.id = 'selection';
  document.body.appendChild(table);
})();
