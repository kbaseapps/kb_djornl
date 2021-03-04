import tippy, { sticky } from 'tippy.js';
import 'tippy.js/dist/tippy.css';

/* components */
/* In this module, the signature of a component is
    component({...}) => dom node
   which deliberately mimics React functional components.
*/
const componentCheckboxCollect = ({ node }) => {
  const id = node.data().id;
  const collectBox = document.createElement('input');
  collectBox.type = 'checkbox';
  collectBox.id = `collect-${id}`;
  collectBox.name = collectBox.id;
  collectBox.checked = node.data().collected || false;
  collectBox.onchange = (evt) => {
    const checked = evt.target.checked;
    node.data().collected = checked;
    if (checked) {
      node.addClass('collected');
      return;
    }
    node.removeClass('collected');
  };
  const collectLabel = document.createElement('label');
  collectLabel.setAttribute('for', collectBox.name);
  const collectDiv = document.createElement('div');
  collectDiv.appendChild(collectBox);
  collectDiv.appendChild(collectLabel);
  return collectDiv;
};
const componentCheckboxSelect = ({ node }) => {
  const id = node.data().id;
  const selectBox = document.createElement('input');
  selectBox.type = 'checkbox';
  selectBox.id = `select-${id}`;
  selectBox.name = selectBox.id;
  selectBox.checked = node.selected();
  selectBox.onchange = (evt) => {
    const checked = evt.target.checked;
    node.data().selected = checked;
    if (!checked) {
      node.deselect();
    }
    if (checked) {
      node.select();
    }
  };
  const selectLabel = document.createElement('label');
  selectLabel.setAttribute('for', selectBox.name);
  const selectDiv = document.createElement('div');
  selectDiv.appendChild(selectBox);
  selectDiv.appendChild(selectLabel);
  return selectDiv;
};
const componentCellMapman = ({ bin, desc, name }) => {
  // wbr indicates a possible word break, allowing Mapman names to wrap.
  const wbr = () => document.createElement('wbr');
  const div = document.createElement('div');
  let displayName = [];
  if (name) {
    displayName = name
      .split('.')
      .flatMap((part) => [document.createTextNode(`${part}.`), wbr()]);
  }
  const displayBin = document.createTextNode(bin ? `(${bin}) ` : '');
  const displayDesc = document.createTextNode(desc ? `: ${desc}` : '');
  const elements = [displayBin, ...displayName, displayDesc];
  elements.forEach((elt) => div.appendChild(elt));
  return div;
};
const componentCellGOTerms = ({ terms }) => {
  const ul = document.createElement('ul');
  terms.forEach((term) => {
    const ili = document.createElement('li');
    ili.append(document.createTextNode(term));
    ul.append(ili);
  });
  return ul;
};
const componentMessage = ({ content }) => {
  const contentNode = document.createTextNode(content);
  const loadingIcon = document.createElement('i');
  loadingIcon.classList.add('fa');
  loadingIcon.classList.add('fa-refresh');
  loadingIcon.classList.add('fa-spin');
  const messageContainer = document.createElement('span');
  messageContainer.appendChild(contentNode);
  messageContainer.appendChild(loadingIcon);
  messageContainer.classList.add('loading');
  messageContainer.classList.add('message');
  return messageContainer;
};
const componentTableRow = ({ cells, tag }) => {
  let tagName = 'td';
  if (tag) tagName = tag;
  const tr = document.createElement('tr');
  cells.forEach((cell) => {
    const td = document.createElement(tagName);
    td.appendChild(cell);
    tr.appendChild(td);
  });
  return tr;
};
const componentTextItem = ({ text }) => {
  const li = document.createElement('li');
  li.appendChild(document.createTextNode(text));
  return li;
};
const componentTippyGeneSymbol = ({ geneSymbol }) => {
  if (!geneSymbol) return;
  return componentTextItem({ text: `Gene Symbol: ${geneSymbol}` });
};
const componentTippyGOTerms = ({ terms }) => {
  if (!terms.length) return;
  const li = componentTextItem({ text: 'GO Terms: ' });
  li.appendChild(componentCellGOTerms({ terms }));
  return li;
};
const componentTippyMapman = ({ bin, desc, name }) => {
  if (!bin) return;
  const li = componentTextItem({ text: 'Mapman: ' });
  const abbr = document.createElement('abbr');
  abbr.appendChild(document.createTextNode(bin));
  abbr.title = name + (desc ? `: ${desc}` : '');
  li.appendChild(abbr);
  return li;
};
export const componentTippy = ({ data }) => {
  const ul = document.createElement('ul');
  ul.classList.add('_tippy');
  const tippyItems = [
    componentTippyGeneSymbol({ geneSymbol: data.geneSymbol }),
    componentTippyGOTerms({ terms: data.GOTerms }),
    componentTippyMapman(data.mapman),
  ].filter((item) => item);
  tippyItems.forEach((item) => ul.appendChild(item));
  return ul;
};
/* ui cells */
export const makeTippy = (ele, fragment) => {
  const ref = ele.popperRef();
  const dummyDomEle = document.createElement('div');
  const tip = tippy(dummyDomEle, {
    // your own preferences:
    appendTo: document.body, // or append dummyDomEle to document.body
    arrow: true,
    content: () => {
      const div = document.createElement('div');
      div.appendChild(fragment);
      return div;
    },
    hideOnClick: false,
    getReferenceClientRect: ref.getBoundingClientRect,
    interactive: true,
    placement: 'bottom',
    plugins: [sticky],
    sticky: 'reference',
    trigger: 'manual',
  });
  return tip;
};
// prompt user for confirmation
export const promptUserForConfirmation = (doms, message, callback) => {
  const { container, messages } = doms;
  const updateMessage = (content, options) => {
    [...messages.childNodes].forEach((childNode) => childNode.remove());
    messages.appendChild(content);
    if (options) {
      const { handler, selector } = options;
      const handle = messages.querySelector(selector);
      handle.addEventListener('click', handler);
    }
  };
  messages.classList.toggle('hidden');
  container.classList.toggle('blur');
  const ackHandler = async () => {
    const messageContainer = componentMessage({ content: 'Loading...' });
    updateMessage(messageContainer);
    await callback();
    container.classList.toggle('blur');
    messages.classList.toggle('hidden');
  };
  updateMessage(message, { selector: 'button', handler: ackHandler });
};
export const renderLegend = ({
  legend,
  cytoscapeInstance,
  colorClasses,
  edgeNames,
}) => {
  const edgeTypeToggleVisibility = (edgeType) => () => {
    cytoscapeInstance
      .edges()
      .filter((edge) => edge.data().edgeType === edgeType)
      .forEach((edge) => edge.toggleClass('hidden'));
  };
  // legend
  Object.entries(colorClasses)
    .map(([edgeType, colorClass]) => {
      const li = document.createElement('li');
      const edgeTypeName = edgeNames[edgeType];
      const checkbox = document.createElement('input');
      checkbox.addEventListener('change', edgeTypeToggleVisibility(edgeType));
      checkbox.type = 'checkbox';
      const checkboxName = `${edgeTypeName.split(' ')[0]}-visibility`;
      checkbox.id = checkboxName;
      checkbox.name = checkboxName;
      li.append(checkbox);
      const label = document.createElement('label');
      label.append(document.createTextNode(edgeTypeName));
      label.setAttribute('for', checkbox.name);
      li.append(label);
      li.classList.add(colorClass.slice(1));
      return li;
    })
    .forEach((item) => legend.appendChild(item));
  return legend;
};
export const renderTable = ({ table, cytoscapeInstance, highlight, sort }) => {
  // node-data selection/collection table
  const cy = cytoscapeInstance;
  [...table.childNodes].forEach((childNode) => childNode.remove());
  const selectedNodes = cy.nodes().filter((node) => node.selected());
  const collectedNodes = cy.nodes().filter((node) => node.data().collected);
  const displayedNodes = [...collectedNodes.add(selectedNodes)];
  displayedNodes.forEach((node) => node.removeClass('collected'));
  collectedNodes.forEach((node) => node.addClass('collected'));
  const firstNode = cy.nodes()[0];
  if (!firstNode) return;
  const columnsExtra = {
    _selected: 'Selected',
    _collected: 'Collected',
  };
  const columnsDisplayed = [
    'name',
    'geneSymbol',
    'GOTerms',
    'mapman',
    '_selected',
    '_collected',
  ];
  // sort
  let sortState = sort;
  if (!sortState) {
    sortState = table.dataset.sort || 'selected';
  }
  table.dataset.sort = sortState;
  let sortReverse = 1;
  let sortOn = sortState;
  if (sortState.startsWith('-')) {
    sortOn = sortState.slice(1);
    sortReverse = -sortReverse;
  }
  const sortFn = (node1, node2) => {
    const node1Val = node1.data()[sortOn];
    const node2Val = node2.data()[sortOn];
    const gt = Number(node1Val > node2Val);
    const eq = Number(node1Val == node2Val);
    // flip the sort for extra columns
    const flip = sortOn in columnsExtra ? 1 : -1;
    return flip * sortReverse * (-1 + eq + 2 * gt); // eslint-disable-line no-mixed-operators
  };
  // header row
  const columnsNode = {
    geneSymbol: 'Gene symbol',
    GOTerms: 'GO terms',
    mapman: 'Mapman data',
    mapmanBin: 'Mapman bin',
    mapmanDesc: 'Mapman description',
    mapmanName: 'Mapman name',
    name: 'Name',
  };
  const sortIconAsc = 'fa-sort-up';
  const sortIconDesc = 'fa-sort-down';
  const columnsTitles = columnsDisplayed.map((col) => {
    let title = col;
    let icon = 'fa-sort';
    let colSort = col;
    if (col in columnsNode) {
      title = columnsNode[col];
    }
    if (col in columnsExtra) {
      title = columnsExtra[col];
      colSort = col.slice(1);
    }
    if (colSort === sortOn) {
      icon = sortReverse > 0 ? sortIconAsc : sortIconDesc;
    }
    const span = document.createElement('span');
    span.appendChild(document.createTextNode(title));
    const sortControl = document.createElement('i');
    sortControl.classList.add('fa');
    sortControl.classList.add(icon);
    span.appendChild(sortControl);
    span.onclick = () => {
      let sortNew = colSort;
      if (sortOn === colSort) {
        sortReverse = -sortReverse;
        sortNew = sortReverse === 1 ? sortOn : `-${sortOn}`;
      }
      renderTable({ table, cytoscapeInstance: cy, sort: sortNew });
    };
    return span;
  });
  const headers = componentTableRow({ cells: columnsTitles, tag: 'th' });
  table.appendChild(headers);
  // node data rows
  const tableDataFormat = {
    GOTerms: (terms) => componentCellGOTerms({ terms }),
    mapman: ({ bin, desc, name }) => componentCellMapman({ bin, desc, name }),
  };
  const sortedNodes = cy.nodes().sort(sortFn);
  sortedNodes.forEach((node) => {
    const nodeData = columnsDisplayed
      .filter((col) => col in columnsNode)
      .map((col) => {
        const datum = node.data()[col];
        if (col in tableDataFormat) {
          return tableDataFormat[col](datum);
        }
        return document.createTextNode(datum);
      });
    const row = componentTableRow({ cells: nodeData });
    const nodesInterface = [
      componentCheckboxCollect({ node }),
      componentCheckboxSelect({ node }),
    ];
    nodesInterface.forEach((elt) => {
      const td = document.createElement('td');
      td.classList.add('ui');
      td.appendChild(elt);
      row.appendChild(td);
    });
    if (node.data().id === highlight) {
      row.classList.add('highlight');
    }
    row.onmouseover = () => {
      node.addClass('highlight');
    };
    row.onmouseleave = () => {
      node.removeClass('highlight');
    };
    table.appendChild(row);
  });
  return table;
};
