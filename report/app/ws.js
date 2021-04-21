export class Workspace {
  constructor({ kbase_session, url }) {
    this.kbaseSession = kbase_session; // eslint-disable-line camelcase
    this.url = url;
  }

  async request(params) {
    const resp = await fetch(this.url, {
      headers: {
        authorization: this.kbaseSession,
        'content-type': 'application/json; charset=UTF-8',
      },
      body: JSON.stringify(params),
      method: 'POST',
    });
    const out = await resp.json();
    return out;
  }

  // get workspace info
  getWorkspaceInfo(wsid) {
    const params = {
      params: [
        {
          id: wsid,
        },
      ],
      method: 'Workspace.get_workspace_info',
      version: '1.1',
      id: `id${new Date().toISOString()}`,
    };
    return this.request(params);
  }

  listObjects(wsid) {
    // list_objects
    const params = {
      params: [
        {
          ids: [wsid],
        },
      ],
      method: 'Workspace.list_objects',
      version: '1.1',
      id: `id${new Date().toISOString()}`,
    };
    return this.request(params);
  }

  getObjects2(refs) {
    // get_objects2
    const objects = refs.map((ref) => ({ ref }));
    const params = {
      params: [{ objects }],
      method: 'Workspace.get_objects2',
      version: '1.1',
      id: `id${new Date().toISOString()}`,
    };
    return this.request(params);
  }

  // save_objects
  saveObjects(wsid, objects) {
    const params = {
      params: [
        {
          id: wsid,
          objects,
        },
      ],
      method: 'Workspace.save_objects',
      version: '1.1',
      id: `id${new Date().toISOString()}`,
    };
    return this.request(params);
  }
}
