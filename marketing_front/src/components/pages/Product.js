import React, { Component } from 'react';
import ProductsList from '../ProductsList';
import CategoryList from '../CategoryList';
import { withRouter } from 'react-router'
import { NavLink } from 'react-router-dom';
import URI from '../../constants/serverUrl';
import ReactMarkdown from 'react-markdown';
import HeaderSmall from '../HeaderSmall/HeaderSmall';


class Product extends Component {

  onCategoryClick(c) {
    this.props.router.push('/our_products/' + c.id)
  }

  /* Only render the output if the condition is met */
  renderConditionally(condition, renderOutput) {
    if (condition) {
      return renderOutput;
    } else {
      return false;
    }
  }

  renderProductDetail(text, className="product-detail", heading=null, size=null, markdown /*:Boolean|ReactMarkdown.NodeType[]*/ =false) {
    let detailBody;
    if (markdown) {
      let defaultMarkdownTypes = ['text', 'list', 'listItem', 'paragraph'];
      let markdownPermittedTypes = (markdown === true) ? defaultMarkdownTypes : markdown;
      detailBody = <ReactMarkdown
                    source={text}
                    escapeHtml={false}
                    allowedTypes={
                      markdownPermittedTypes
                    }
                    />
    } else {
      detailBody = text;
    }

    return (
      <div className="col-md-12" style={{marginTop: heading ? '25px' : '5px'}}>
        { heading &&
             <div style={{fontSize: '12px', fontWeight: 'bold'}}>
              <span className="product-name">{heading}</span>
            </div>
        }
        <span className={className}>
          { detailBody }
        </span>
      </div>
    )
  }

  render() {
    const p = this.props.product;

    const aSizes = this.props.sizes.filter(a => !!a.isBag);
    const bSizes = this.props.sizes.filter(a => !a.isBag);

    const sizes = [];

    if(bSizes.filter(siz => !!p.sizes.find(ps => ps === siz.id)).length){
      bSizes.forEach(aS => {
        if(p.sizes.find(ps => ps === aS.id)) {
          sizes.push(<img key={"a"+aS.id} src={URI + aS.image} style={{height: '52px',  width:'33px', padding: '3px'}}></img>);
        }
      });
    }

    if(aSizes.filter(siz => !!p.sizes.find(ps => ps === siz.id)).length){
      aSizes.forEach(aS => {
        if(p.sizes.find(ps => ps === aS.id)) {
          sizes.push(<img key={"b"+aS.id}  src={URI + aS.image} style={{height: '52px',  width:'33px', padding: '3px'}}></img>);
        }
      });
    }

    return (
      <div>
        <HeaderSmall title={p.name} />
        <div className="row" style={{ height: '80px'}}>
            <div className="col-md-6">
              <div className="med-right">
                <div className="hexagon white"></div>
              </div>
              <div style={{height: '80px', width: '100%'}}></div>
          </div>
        </div>
        <div className="row" style={{backgroundColor: '#FFF', paddingLeft: '45px', paddingTop: '15px', paddingBottom: '270px'}}>
          <div className="col-md-2" style={{ minWidth: '191px'}}>
            <CategoryList
              categories={this.props.categories}
              onCategoryClick={this.onCategoryClick}
              category={p.productCategory}
              history={this.props.history}
            />
          </div>
          <div className="col-md-8 col-lg-9" style={{padding: '10px 5px 10px 5px'}}>
            <div className="row">
              <div className="col-md-6">
                { this.renderProductDetail(p.name, "product-name-detail", null, "20px")}
                {
                  // Optionally render the subheading if its not empty
                  this.renderConditionally(
                    p.subheading,
                    this.renderProductDetail(p.subheading, "product-detail product-subtitle-detail")
                  )
                }
                {
                  // Optionally render the old SKU if the new field is not being used.
                  this.renderConditionally(
                    !p.productCodes,
                    this.renderProductDetail("SKU: " + p.productCode, "product-detail tiny-text")
                  )
                }
                { this.renderProductDetail(p.description, "product-detail", "Description", undefined, true)}
                { this.renderProductDetail(p.directions, "product-detail", "Directions", undefined, true)}
                { this.renderProductDetail(p.market) }
              </div>
              <div className="col-md-6" style={{height: '350px' }}>
                <div className="row">
                  <div className="col-md-12" align="center">
                    <div className="contain" style={{margin: 'auto'}}>
                      {p.primaryImageLink ? (
                        <img className="brighten" src={URI + p.primaryImageLink} alt={p.name + '-image'} />
                      ) : (
                        <span>No Image</span>
                      )}
                    </div>
                  </div>
                </div>
                <div className="row" style={{height: '50px'}}>
                  <div className="col-md-12" style={{paddingTop: '12px'}}>
                    <span className="nav-link bold" style={{fontSize: '15px'}}>Available Sizes</span>
                  </div>
                </div>
                <div className="row" style={{minHeight: '100px'}}>
                  <div className="col-md-8 col-xs-12 col-sm-12">
                    { sizes }
                  </div>
                  <div className="col-md-4 col-xs-12 col-sm-12 pdf-links">
                  <div className="row justify-content-center">
                      <div className="col-lg-6  col-md-auto" style={{padding: '0'}}>
                        <a href={URI + '/product_download/' + p.id + '/info/'} target="_blank">
                          <div className="roman grey-text">
                            <div style={{margin: '0 auto', maxWidth: '50px'}}>
                              <img src={require('../../assets/pdf-icoin.png')} style={{ width: '50px', marginLeft: '-3px'}} />
                            </div>
                            <div style={{fontSize: '12px', textAlign: 'center'}}>
                              Info<br />(download)
                            </div>
                          </div>
                        </a>
                      </div>
                      <div className="col-lg-6 col-md-auto" style={{padding: '0'}}>
                        <a href={'/getsds/' + p.id }>
                          <div className="roman grey-text">
                            <div style={{margin: '0 auto', maxWidth: '50px'}}>
                              <img src={require('../../assets/pdf-icoin.png')} style={{ width: '50px', marginLeft: '-3px'}} />
                            </div>
                            <div style={{fontSize: '12px', textAlign: 'center'}}>
                              SDS<br />(download)
                            </div>
                          </div>
                        </a>
                      </div>
                    </div>
                  </div>
                </div>
                <div className="row">
                  {
                    // Optionally render the new SKUs if they are present.
                    this.renderConditionally(
                      p.productCodes,
                      this.renderProductDetail('| | |\n|-|-|\n' + p.productCodes, "product-sku-list", undefined, undefined, [
                        'text', 'table', 'tableBody', 'tableRow', 'tableCell'
                      ])
                    )
                  }
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

}

export default withRouter(Product);
