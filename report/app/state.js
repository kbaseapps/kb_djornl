/* App state management */
/* This object deliberately imitates the data model of React. */
export class State {
  constructor(state, callback) {
    this.state = state;
    this.callback = callback;
  }
  setState(state) {
    this.state = { ...this.state, ...state };
    this.callback(this);
    return this.state;
  }
}
