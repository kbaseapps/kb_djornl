import cytoscape from 'https://cdnjs.cloudflare.com/ajax/libs/cytoscape/3.17.1/cytoscape.esm.min.js';
(async () => {
  const elements_response = await fetch('djornl.json');
  const elements_json = await elements_response.json();
  cytoscape.use(cytoscapeSpread);
  const cy = cytoscape({
    container: document.getElementById('cy'), // container to render in
    elements: elements_json,
    style: [ // the stylesheet for the graph
      {
        selector: 'node',
        style: {
          'background-color': '#666',
          'label': 'data(id)'
        }
      },
      {
        selector: 'edge',
        style: {
          'width': 3,
          'line-color': '#ccc',
          'target-arrow-color': '#ccc',
          'target-arrow-shape': 'triangle',
          'curve-style': 'bezier'
        }
      }
    ],
    layout: {
      name: 'cose',
      gravity: 80,
    }
  });
  await cy.makeLayout({ name: 'cose' });
  await cy.makeLayout({ name: 'spread', prelayout: false });
  console.log('cytoscape', cy)
})()
