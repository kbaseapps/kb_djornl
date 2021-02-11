import tippy, { sticky } from 'tippy.js';
import 'tippy.js/dist/tippy.css';

/* markup formatting including tippy */
const formatMapman = ({ bin, desc, name }) => {
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
const formatGOTerms = (terms) => {
  const ul = document.createElement('ul');
  terms.forEach((term) => {
    const ili = document.createElement('li');
    ili.append(document.createTextNode(term));
    ul.append(ili);
  });
  return ul;
};
export const formatLegend = (colorClasses, edgeTypeNames) => {
  // legend
  const legend = document.getElementById('legend');
  Object.entries(colorClasses)
    .map(([edgeType, colorClass]) => {
      const li = document.createElement('li');
      const edgeTypeName = edgeTypeNames[edgeType];
      const color = document.createTextNode(edgeTypeName);
      li.append(color);
      li.classList.add(colorClass.slice(1));
      return li;
    })
    .forEach((item) => legend.appendChild(item));
  return legend;
};
export const makeTippy = function (ele, fragment) {
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
const textToLI = (text) => {
  const li = document.createElement('li');
  li.appendChild(document.createTextNode(text));
  return li;
};
const tippyFormatGeneSymbol = (geneSymbol) => {
  if (!geneSymbol) return;
  return textToLI(`Gene Symbol: ${geneSymbol}`);
};
const tippyFormatGOTerms = (terms) => {
  if (!terms.length) return;
  const li = document.createElement('li');
  li.appendChild(document.createTextNode('GO Terms: '));
  const ul = formatGOTerms(terms);
  li.appendChild(ul);
  return li;
};
const tippyFormatMapman = ({ bin, desc, name }) => {
  if (!bin) return;
  const li = textToLI('Mapman: ');
  const abbr = document.createElement('abbr');
  abbr.appendChild(document.createTextNode(bin));
  abbr.title = name + (desc ? `: ${desc}` : '');
  li.appendChild(abbr);
  return li;
};
export const tippyContent = (data) => {
  const ul = document.createElement('ul');
  ul.classList.add('_tippy');
  const tippyItems = [
    tippyFormatGeneSymbol(data.geneSymbol),
    tippyFormatGOTerms(data.GOTerms),
    tippyFormatMapman(data.mapman),
  ].filter((item) => item);
  tippyItems.forEach((item) => ul.appendChild(item));
  return ul;
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
/* ui cells */
const nodesSelectCollect = (node) => {
  const id = node.data().id;
  const checkbox = document.createElement('input');
  const label = document.createElement('label');
  const div = document.createElement('div');
  checkbox.type = 'checkbox';
  const collectBox = checkbox.cloneNode();
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
  const collectLabel = label.cloneNode();
  collectLabel.setAttribute('for', collectBox.name);
  const collectDiv = div.cloneNode();
  collectDiv.appendChild(collectBox);
  collectDiv.appendChild(collectLabel);
  const selectBox = checkbox.cloneNode();
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
  const selectLabel = label.cloneNode();
  selectLabel.setAttribute('for', selectBox.name);
  const selectDiv = div.cloneNode();
  selectDiv.appendChild(selectBox);
  selectDiv.appendChild(selectLabel);
  return [selectDiv, collectDiv];
};
const tableDataFormat = {
  GOTerms: (terms) => formatGOTerms(terms),
  mapman: ({ bin, desc, name }) => formatMapman({ bin, desc, name }),
};
export const renderTable = (cy, options) => {
  // node-data selection/collection table
  const { highlight, sort } = options || {};
  const table = document.getElementById('node-data');
  [...table.children].forEach((child) => child.remove());
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
      renderTable(cy, { sort: sortNew });
    };
    return span;
  });
  const headers = tableRow(columnsTitles, 'th');
  table.appendChild(headers);
  // node data rows
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
    const nodesInterface = nodesSelectCollect(node);
    const row = tableRow(nodeData);
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
};
