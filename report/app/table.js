/* Scalar value sorts and factories */
const sortNatural = (a, b) => {
  const eq = Number(a == b);
  const gt = Number(a > b);
  return -1 + eq + 2 * gt; // eslint-disable-line no-mixed-operators
};
// This needs to know about sort reverse to know whether aces are high or low
const sortEmptyAlwaysLastFactory = ({ reverse }) => (a, b) => {
  const truthyOrZero = (x) => Boolean(x === 0 || x);
  // What counts as empty?
  const empty = Infinity;
  const aVal = truthyOrZero(a) ? a : empty;
  const bVal = truthyOrZero(b) ? b : empty;
  if (aVal === bVal) return 0;
  // Empties always sort last.
  if (aVal === empty) return 1;
  if (bVal === empty) return -1;
  // Otherwise, sort as usual.
  return reverse * sortNatural(aVal, bVal);
};
/* Node sorts and factories */
// Selected nodes
const sortNodeSelected = (node1, node2) => {
  const node1Selected = node1.selected();
  const node2Selected = node2.selected();
  if (node1Selected && !node2Selected) return -1;
  if (node1Selected && node2Selected) return 0;
  if (!node1Selected && !node2Selected) return 0;
  if (!node1Selected && node2Selected) return 1;
};
// Sorting attributes should always sort selected nodes high and empties low.
const sortNodeFactory = ({ serializer, reverse }) => (node1, node2) => {
  const node1Val = serializer(node1);
  const node2Val = serializer(node2);
  const nodeSort = sortEmptyAlwaysLastFactory({ reverse });
  const sorted = nodeSort(node1Val, node2Val);
  const selected = sortNodeSelected(node1, node2);
  if (selected === 0) {
    return sorted;
  }
  return selected;
};
/* Node attribute serializers. */
const nodeSerializers = (attr) => {
  const serializers = {
    _collected: (node) => -Number(node.data().collected),
    _selected: (node) => node.selected(),
    GOInfos: (node) => {
      const nodeGO = node.data().GOInfos;
      if (nodeGO.length > 0) {
        return nodeGO[0].desc;
      }
    },
    mapmanInfos: (node) => {
      const nodeMapman = node.data().mapmanInfos;
      if (nodeMapman.length > 0) {
        return nodeMapman[0].desc;
      }
    },
  };
  if (attr in serializers) {
    return serializers[attr];
  }
  // If the attribute is a list of strings, join them and compare that.
  return (node) => node.data()[attr].join('');
};
const sortOverrides = new Set([
  '_collected',
  '_selected',
  'geneSymbols',
  'GOInfos',
  'KOEffects',
  'mapmanInfos',
  'names',
]);
// Compute the sort function to be used on the data.
export const sortFnFactory = ({ sortOn, sortReverse }) => {
  if (sortOverrides.has(sortOn)) {
    const serializer = nodeSerializers(sortOn);
    return sortNodeFactory({
      serializer,
      reverse: sortReverse,
    });
  }
  // Default serializer.
  const serializer = (node) => node.data()[sortOn];
  // This defines a default scalar sort.
  return sortNodeFactory({ serializer, reverse: sortReverse });
};
// What is the desired sort order?
export const sortStateParse = ({ sortState }) => {
  let sortReverse = 1;
  let sortOn = sortState;
  if (sortState.startsWith('-')) {
    sortOn = sortState.slice(1);
    sortReverse = -sortReverse;
  }
  return { sortOn, sortReverse };
};
/* Compute table data from given parameters.*/
export const computeTable = ({
  columnsDisplayed,
  columnsExtra,
  columnsNode,
  nodes,
  sortState,
}) => {
  const { sortOn, sortReverse } = sortStateParse({ sortState });
  const columnsRawTitles = columnsDisplayed.map((col) => {
    let title = col;
    const colSort = col;
    if (col in columnsNode) {
      title = columnsNode[col];
    }
    if (col in columnsExtra) {
      title = columnsExtra[col];
      //colSort = col.slice(1);
    }
    return {
      title,
      column: col,
      sort: colSort === sortOn ? sortReverse : null,
      sortable: col !== '_selected',
    };
  });
  const tableRawDataFormat = {
    geneSymbols: (items) => ({
      geneSymbols: { items, classes: ['symbols'] },
      type: 'List Items',
    }),
    GOInfos: (infos, prefix) => ({ GOInfos: { infos, prefix }, type: 'GO Infos' }),
    KOEffects: (items) => ({ KOEffects: { items }, type: 'List Items' }),
    mapmanInfos: (infos, prefix) => ({
      mapmanInfos: { infos, prefix },
      type: 'Mapman Infos',
    }),
    names: (items) => ({ names: { items }, type: 'List Items' }),
    name: (name) => ({ name: { name }, type: 'Gene Name' }),
    rank: (rank) => ({ rank: { rank }, type: 'Gene Rank' }),
    seed: (seed) => ({ seed: { seed }, type: 'Seed' }),
  };
  // Compute sort comparison function.
  const sortFn = sortFnFactory({ sortOn, sortReverse });
  const sortedNodes = nodes.sort(sortFn);
  const rows = sortedNodes.map((node) => {
    return columnsDisplayed
      .filter((col) => col in columnsNode)
      .map((col) => {
        const data = node.data();
        const datum = data[col];
        const prefix = data.id;
        if (col in tableRawDataFormat) {
          return { ...tableRawDataFormat[col](datum, prefix) };
        }
        return {
          [col]: {
            prefix,
            value: datum,
            type: 'default',
          },
        };
      })
      .concat({ node });
  });
  return { headers: columnsRawTitles, rows };
};
