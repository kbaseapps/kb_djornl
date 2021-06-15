import { swapElement } from './dom.js';
import { State } from './state.js';
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

/* KBase state saving mechanism chrome */
export const registerStateSaveChrome = (nav) => {
  const componentChrome = ({ previousStates }) => {
    const navNew = document.createElement('nav');
    navNew.id = 'state-save';
    navNew.classList.add('flow-h');
    console.log('previousStates', previousStates); // eslint-disable-line no-console
    return navNew;
  };
  const render = (chromeState) => {
    console.log('render chromeState', chromeState); // eslint-disable-line no-console
    return componentChrome(chromeState.state);
  };
  const chromeStateInitial = {
    previousStates: [
      ['prev', 'Previous state'],
      ['orig', 'Original state'],
      ['snowman', '☃'],
      ['long', 'a really obnoxiously named state whose name is really too long'],
    ],
  };
  const chromeState = new State(chromeStateInitial, (state) =>
    swapElement(nav, render(state))
  );
  const formSave = nav.querySelector('form');
  const buttonGoTop = nav.querySelector('#go-top');
  const buttonSave = nav.querySelector('#state-save-button');
  const inputName = nav.querySelector('#state-name');
  const selectState = nav.querySelector('#state-select');
  const saveListener = () => {
    console.log('save', inputName.value); // eslint-disable-line no-console
    console.log('chromeState', chromeState); // eslint-disable-line no-console
    const nameNew = inputName.value;
    chromeState.setState({
      previousStates: [...chromeState.state.previousStates, [nameNew, nameNew]],
    });
    inputName.value = '';
    buttonSave.disabled = 'disabled';
  };
  const nameListener = (evt) => {
    buttonSave.disabled = '';
    if (evt.target.value) return;
    buttonSave.disabled = 'disabled';
  };
  buttonGoTop.addEventListener('click', () => window.scrollTo(0, 0));
  buttonSave.addEventListener('click', saveListener);
  formSave.addEventListener('submit', (evt) => evt.preventDefault());
  inputName.addEventListener('input', nameListener);
  selectState.addEventListener('change', (evt) => {
    console.log(evt.target.value); // eslint-disable-line no-console
  });
};
