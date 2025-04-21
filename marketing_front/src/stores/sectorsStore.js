/* create a store for sectors using redux not persistant */
import { createStore } from 'redux';
import { combineReducers } from 'redux';

const initialState = {
  sectors: [],
};

const sectorsReducer = (state = initialState, action) => {
  switch (action.type) {
    case 'SET_SECTORS':
      return {
        ...state,
        sectors: action.payload,
      };
    default:
      return state;
  }
}
const rootReducer = combineReducers({
  sectors: sectorsReducer,
});
const store = createStore(rootReducer);
export default store;
export const setSectors = (sectors) => {
  return {
    type: 'SET_SECTORS',
    payload: sectors,
  };
};



