import { Workspace } from './ws.js';
/* workspace object facade */
export class WOF {
  constructor({ kbase_session, ref, url }) {
    this.kbaseSession = kbase_session; // eslint-disable-line camelcase
    this.object = null;
    this.ref = ref;
    this.url = url;
    if (url) {
      this.ws = new Workspace({
        kbase_session, // eslint-disable-line camelcase
        url,
      });
    }
  }

  // get latest object ref
  async getLatestVersionRef() {
    if (!this.ref) {
      //eslint-disable-next-line no-console
      console.error('The ref for this object is unset. Use setRef to do so.');
    }
    const [wsid, objid] = this.ref.split('/').slice(0, 2);
    const listObjectsResponse = await this.ws.listObjects(wsid);
    const objects = listObjectsResponse.result[0];
    this.object = objects.filter((object) => object[0] === parseInt(objid))[0];
    const latestVer = this.object[4];
    return `${wsid}/${objid}/${latestVer}`;
  }
  // get stored nodes
  async getStoredNodes() {
    /* get latest object ref */
    const latestRef = await this.getLatestVersionRef();
    let storedNodes = [];
    try {
      const storedNodesResponse = await this.ws.getObjects2([latestRef]);
      storedNodes = JSON.parse(storedNodesResponse.result[0].data[0].data.description);
    } catch (err) {
      console.error('The workspace is inaccessible.'); // eslint-disable-line no-console
    }
    return storedNodes;
  }
  // update stored nodes
  async putStoredNodes(nodes) {
    if (!this.object) {
      this.getLatestVersionRef();
    }
    const [wsid] = this.ref.split('/').slice(0, 1);
    const objects = [
      {
        type: 'KBaseNarrative.Metadata-3.0',
        name: this.object[1],
        data: {
          data_dependencies: [], // eslint-disable-line camelcase
          description: JSON.stringify(nodes),
          format: 'JSON',
        },
      },
    ];
    await this.ws.saveObjects(wsid, objects);
  }

  setRef(ref) {
    this.ref = ref;
  }

  setURL(url) {
    this.url = url;
    this.ws = new Workspace({
      kbase_session: this.kbaseSession, // eslint-disable-line camelcase
      url,
    });
  }
}
