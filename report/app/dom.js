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
  collectBox.classList.add('control');
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
  selectBox.classList.add('control');
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
const componentCellGO = ({ term, description, prefix }) => {
  const checkbox = document.createElement('input');
  checkbox.type = 'checkbox';
  const checkboxId = `${prefix}-${term}`;
  checkbox.id = checkboxId;
  const label = document.createElement('label');
  label.setAttribute('for', checkboxId);
  const termNode = document.createTextNode(term);
  const span = document.createElement('span');
  const spanTerm = span.cloneNode();
  spanTerm.classList.add('term');
  spanTerm.classList.add('alt');
  spanTerm.appendChild(termNode);
  const spanDescription = span.cloneNode();
  spanDescription.classList.add('main');
  spanDescription.classList.add('description');
  const descriptionNode = document.createTextNode(description);
  spanDescription.appendChild(descriptionNode);
  const elements = [spanTerm, spanDescription];
  elements.forEach((elt) => label.appendChild(elt));
  const div = document.createElement('div');
  div.classList.add('data');
  div.appendChild(checkbox);
  div.appendChild(label);
  return div;
};
const componentCellGOInfos = ({ infos, prefix }) => {
  const goterms = {};
  infos.forEach((info) => {
    if (info.term in goterms) return;
    goterms[info.term] = info.desc;
  });

  const ul = document.createElement('ul');
  Object.entries(goterms).forEach(([term, description]) => {
    const ili = document.createElement('li');
    const gotermDiv = componentCellGO({ description, term, prefix });
    ili.append(gotermDiv);
    ul.append(ili);
  });
  const div = document.createElement('div');
  div.appendChild(ul);
  return div;
};
const componentCellListItems = ({ items }) => {
  const ul = document.createElement('ul');
  items.forEach((term) => {
    const ili = document.createElement('li');
    ili.append(document.createTextNode(term));
    ul.append(ili);
  });
  return ul;
};
const componentCellMapman = ({ code, desc, name, prefix }) => {
  const checkbox = document.createElement('input');
  checkbox.type = 'checkbox';
  const checkboxId = `${prefix}-${code}-${desc}`;
  checkbox.id = checkboxId;
  const label = document.createElement('label');
  label.setAttribute('for', checkboxId);
  // wbr indicates a possible word break, allowing Mapman names to wrap.
  const wbr = () => document.createElement('wbr');
  let displayName = [];
  if (name) {
    displayName = name
      .split('.')
      .flatMap((part) => [document.createTextNode(`${part}.`), wbr()]);
  }
  const span = document.createElement('span');
  const spanDesc = span.cloneNode();
  spanDesc.classList.add('desc');
  spanDesc.classList.add('main');
  spanDesc.appendChild(document.createTextNode(desc));
  const spanName = span.cloneNode();
  spanName.classList.add('code');
  spanName.classList.add('name');
  spanName.classList.add('alt');
  const displayCode = document.createTextNode(code ? `(${code}) ` : '');
  spanName.appendChild(displayCode);
  displayName.forEach((part) => spanName.appendChild(part));
  const elements = [spanDesc, spanName];
  elements.forEach((elt) => label.appendChild(elt));
  const div = document.createElement('div');
  div.classList.add('data');
  div.appendChild(checkbox);
  div.appendChild(label);
  return div;
};
const componentCellMapmanInfos = ({ infos, prefix }) => {
  const mapmans = {};
  infos.forEach((info) => {
    if (info.code in mapmans) return;
    mapmans[info.code] = {
      desc: info.desc,
      name: info.name,
    };
  });

  const ul = document.createElement('ul');
  Object.entries(mapmans).forEach(([code, data]) => {
    const ili = document.createElement('li');
    const mapmanDiv = componentCellMapman({
      code,
      prefix,
      desc: data.desc,
      name: data.name,
    });
    ili.append(mapmanDiv);
    ul.append(ili);
  });
  const div = document.createElement('div');
  div.appendChild(ul);
  return div;
};
const componentCellName = ({ name }) => {
  const link = document.createElement('a');
  const workspace = 'Phytozome_Genomes/Athaliana_TAIR10';
  link.href = `/#dataview/${workspace}?sub=Feature&subid=${name}`;
  link.target = '_blank';
  link.appendChild(document.createTextNode(name));
  return link;
};
const componentMessage = ({ content }) => {
  const contentNode = document.createTextNode(content);
  const loadingIcon = document.createElement('i');
  loadingIcon.classList.add('fa');
  loadingIcon.classList.add('fa-refresh');
  loadingIcon.classList.add('fa-spin');
  const span = document.createElement('span');
  span.appendChild(contentNode);
  span.appendChild(loadingIcon);
  span.classList.add('loading');
  span.classList.add('message');
  return span;
};
export const componentMessageAcknowledge = ({ message, callback }) => {
  const div = document.createElement('div');
  div.id = 'messages';
  const messageNode = document.createTextNode(message);
  const ackButton = document.createElement('button');
  ackButton.appendChild(document.createTextNode('OK'));
  ackButton.addEventListener('click', callback);
  const span = document.createElement('span');
  span.classList.add('message');
  span.appendChild(messageNode);
  span.appendChild(ackButton);
  div.appendChild(span);
  return div;
};
export const componentMessageLoading = () => {
  const div = document.createElement('div');
  div.id = 'messages';
  const messageComponent = componentMessage({ content: 'Loading...' });
  div.appendChild(messageComponent);
  return div;
};
const componentNetworkTippy = ({ edgeTypeMeta, edgemani }) => {
  const contentTippy = document.createElement('span');
  const edgemaniObj = edgemani[edgeTypeMeta.title];
  const description = (edgemaniObj && edgemaniObj.description) || '';
  const citation = document.createTextNode(`${edgeTypeMeta.title}: ${description} [`);
  const link = document.createElement('a');
  link.href = edgeTypeMeta.cite;
  link.appendChild(document.createTextNode('citation'));
  contentTippy.appendChild(citation);
  contentTippy.appendChild(link);
  contentTippy.appendChild(document.createTextNode(']'));
  return contentTippy;
};
const componentNetworkVisibilityToggle = ({
  edgeType,
  edgeTypeName,
  toggleVisibility,
}) => {
  const checkboxVisibility = document.createElement('input');
  checkboxVisibility.type = 'checkbox';
  checkboxVisibility.addEventListener('change', toggleVisibility(edgeType));
  const slug = edgeTypeName.split(' ')[0];
  const checkboxVisibilityName = `${slug}-visibility`;
  checkboxVisibility.id = checkboxVisibilityName;
  checkboxVisibility.name = checkboxVisibilityName;
  checkboxVisibility.classList.add('visibility');
  return checkboxVisibility;
};
const componentNetworkZone = ({
  colorClass,
  edgeMetadata,
  edgeType,
  edgeTypeToggleVisibility,
  manifest,
}) => {
  const edgemani = Object.fromEntries(
    manifest.file_list
      .filter((file) => file.data_type === 'edge')
      .map((file) => {
        return [file.title, file];
      })
  );
  const edgeTypeMetaDefault = (edgeType) => {
    const unknown = `Unknown edge type: ${edgeType}`;
    edgemani[unknown] = { description: 'unknown' };
    return {
      cite: '#',
      name: unknown,
      title: unknown,
    };
  };
  const edgeTypeMeta = edgeMetadata[edgeType] || edgeTypeMetaDefault(edgeType);
  const edgeTypeName = edgeTypeMeta.name;
  const label = document.createElement('label');
  const li = document.createElement('li');
  const span = document.createElement('span');
  // friendly edge name
  const labelCite = label.cloneNode();
  labelCite.append(document.createTextNode(edgeTypeName));
  li.append(labelCite);
  // colors
  li.classList.add(colorClass.slice(1));
  // toggle network visibility
  const checkboxVisibility = componentNetworkVisibilityToggle({
    edgeType,
    edgeTypeName,
    toggleVisibility: edgeTypeToggleVisibility,
  });
  li.append(checkboxVisibility);
  const labelVisibility = label.cloneNode();
  labelVisibility.setAttribute('for', checkboxVisibility.name);
  li.append(labelVisibility);
  // citation tippy
  const contentTippy = componentNetworkTippy({ edgeTypeMeta, edgemani });
  tippy(li, {
    content: contentTippy,
    interactive: true,
    placement: 'left',
  });
  span.appendChild(li);
  return span;
};
const componentTableRow = ({ cells, tag }) => {
  let tagName = 'td';
  if (tag) tagName = tag;
  const tr = document.createElement('tr');
  cells.forEach((cell) => {
    const td = document.createElement(tagName);
    td.appendChild(cell);
    if (cell.classList) {
      [...cell.classList].forEach((cls) => td.classList.add(cls));
    }
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
const componentTippyGOInfos = ({ infos, prefix }) => {
  if (!infos.length) return;
  const li = componentTextItem({ text: 'GO Terms: ' });
  li.appendChild(componentCellGOInfos({ infos, prefix }));
  return li;
};
const componentTippyMapmanInfos = ({ infos, prefix }) => {
  const li = componentTextItem({ text: 'Mapman: ' });
  const mapmanDiv = componentCellMapmanInfos({ infos, prefix });
  li.appendChild(mapmanDiv);
  return li;
};
export const componentTippy = ({ data }) => {
  const ul = document.createElement('ul');
  ul.classList.add('_tippy');
  const prefix = `tippy-${data.id}`;
  const tippyItems = [
    componentTippyGeneSymbol({ geneSymbol: data.geneSymbol }),
    componentTippyGOInfos({ infos: data.GOInfos, prefix }),
    componentTippyMapmanInfos({ infos: data.mapmanInfos, prefix }),
  ].filter((item) => item);
  tippyItems.forEach((item) => ul.appendChild(item));
  return ul;
};
export const componentULLegend = ({
  cytoscapeInstance,
  colorClasses,
  edgeMetadata,
  manifest,
}) => {
  const legend = document.createElement('ul');
  legend.id = 'legend';
  const edgeTypeToggleVisibility = (edgeType) => () => {
    cytoscapeInstance
      .edges()
      .filter((edge) => edge.data().edgeType === edgeType)
      .forEach((edge) => edge.toggleClass('hidden'));
  };
  // legend
  Object.entries(colorClasses)
    .map(([edgeType, colorClass]) =>
      componentNetworkZone({
        colorClass,
        edgeMetadata,
        edgeType,
        edgeTypeToggleVisibility,
        manifest,
      })
    )
    .forEach((item) => legend.appendChild(item));
  return legend;
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
export const swapElement = (original, replacement) => {
  if (!replacement) return;
  if (original === replacement) return;
  const parentDOM = original.parentElement;
  const index = Array.from(parentDOM.children).indexOf(original);
  const children = Array.from(parentDOM.children);
  const childrenNew = [
    ...children.slice(0, index),
    replacement,
    ...children.slice(index + 1),
  ];
  parentDOM.replaceChildren(...childrenNew);
};
export const renderTable = ({ table, cytoscapeInstance, highlight, appState }) => {
  if (!table) return table;
  const { sort } = appState.state;
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
    'defline',
    'geneSymbols',
    'names',
    'KOEffects',
    'GOInfos',
    'mapmanInfos',
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
    defline: 'Defline',
    geneSymbols: 'Symbols',
    GOInfos: 'GO terms',
    KOEffects: 'KO Effects',
    mapmanInfos: 'MapMan',
    names: 'Names',
    name: 'Gene',
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
      appState.setState({ sort: sortNew });
    };
    return span;
  });
  const headers = componentTableRow({ cells: columnsTitles, tag: 'th' });
  table.appendChild(headers);
  // node data rows
  const tableDataFormat = {
    geneSymbols: (items) => componentCellListItems({ items }),
    GOInfos: (infos, prefix) => componentCellGOInfos({ infos, prefix }),
    KOEffects: (items) => componentCellListItems({ items }),
    mapmanInfos: (infos, prefix) => componentCellMapmanInfos({ infos, prefix }),
    names: (items) => componentCellListItems({ items }),
    name: (name) => componentCellName({ name }),
  };
  const sortedNodes = cy.nodes().sort(sortFn);
  sortedNodes.forEach((node) => {
    const nodeData = columnsDisplayed
      .filter((col) => col in columnsNode)
      .map((col) => {
        const data = node.data();
        const datum = data[col];
        const prefix = data.id;
        if (col in tableDataFormat) {
          return tableDataFormat[col](datum, prefix);
        }
        return document.createTextNode(datum);
      });
    const row = componentTableRow({ cells: nodeData });
    const nodesInterface = [
      componentCheckboxSelect({ node }),
      componentCheckboxCollect({ node }),
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
