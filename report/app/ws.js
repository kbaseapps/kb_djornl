export class Workspace {
  constructor({ kbase_session, url }) {
    this.kbaseSession = kbase_session; // eslint-disable-line camelcase
    this.status = true;
    this.url = url;
  }

  async request(params) {
    if (!this.kbaseSession) {
      this.status = false;
      return;
    }
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
  async getWorkspaceInfo(wsid) {
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
    return await this.request(params);
  }

  async listObjects(wsid) {
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
    const response = await this.request(params);
    // An error indicates the workspace is unreachable for some reason.
    if (response.error) {
      const message = response.error.message;
      // eslint-disable-next-line no-console
      console.error('The Workspace responded with an error:', message);
      // Disable subsequent workspace calls.
      this.status = false;
    }
    return response;
  }

  async getObjects2(refs) {
    // get_objects2
    const objects = refs.map((ref) => ({ ref }));
    const params = {
      params: [{ objects }],
      method: 'Workspace.get_objects2',
      version: '1.1',
      id: `id${new Date().toISOString()}`,
    };
    return await this.request(params);
  }

  // save_objects
  async saveObjects(wsid, objects) {
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
    return await this.request(params);
  }
}
