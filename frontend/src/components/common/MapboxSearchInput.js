import React, { Component } from 'react';
import searchMapbox from '../../util/SearchMapbox';
import { AutoComplete } from 'antd';
const Option = AutoComplete.Option;


export default class MapboxSearchInput extends Component {

  state = {
    dataSource: [],
    searchTime: new Date(),
  }

  getPlaceNameResults = (features) => {
    const options = features.map(f => (
      <Option key={f.place_name} value={JSON.stringify(f)} feature={f}>
        {f.place_name}
      </Option>
    ));
    if(this.props.initialValue) {
      options.push(this.getInitialOption());
    }
    return options;
  }

  getInitialOption = () => {
    return (
      <Option key={'initialAddress'} value={"initialValue"} feature={{initialValue: true}}>
        { this.props.initialValue }
      </Option>
    );
  }

  getPlaceTextResults = (features) => {
    const options = features.map(f => (
      <Option key={f.text} value={JSON.stringify(f)} feature={f}>
        {f.text}
      </Option>
    ));
    if(this.props.initialValue) {
      options.push(this.getInitialOption());
    }
    return options;
  }

  onSearchComplete = (err, res, body, searchTime) => {
    // searchTime is compared with the last search to set the state
    // to ensure that a slow xhr response does not scramble the
    // sequence of autocomplete display.
    const renderData = this.props.displayText ? this.getPlaceTextResults : this.getPlaceNameResults;
    if (!err && body && body.features && this.state.searchTime <= searchTime) {
      this.setState({
        searchTime: searchTime,
        loading: false,
        dataSource: renderData(body.features),
      });
    }
  }

  handleSearch = (value) => {
    console.log('search', value)
    searchMapbox(value, this.onSearchComplete);
  }

  render() {
    const { dataSource } = this.state;
    return (
      <AutoComplete
        dataSource={dataSource}
        style={{ width: '%100' }}
        onSelect={this.props.onSelect}
        onSearch={this.handleSearch}
        placeholder="address"
        defaultValue={this.props.initialValue}
      />
    );
  }


}
