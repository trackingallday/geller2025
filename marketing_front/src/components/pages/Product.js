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
      <div className="row" style={{marginTop: heading ? '25px' : '5px'}}>
        { heading &&
             <div style={{fontSize: '12px'}}>
              <span className="">{heading}</span>
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
        <div className="container p-0">
          <div className='row px-0 py-4'>
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
                <div className="col-md-6" style={{height: '350px' }}>
                  <div className="row">
                    <div className="col-md-12" align="center">
                      <div className="contain p-4" style={{margin: 'auto'}}>
                        {p.primaryImageLink ? (
                          <img className="brighten main-product-detail" src={URI + p.primaryImageLink} alt={p.name + '-image'} />
                        ) : (
                          <span>No Image</span>
                        )}
                      </div>
                    </div>
                  </div>
                  
                </div>
                <div className="col-md-6 p-0">

                  <div className="row py-2" style={{borderBottom: '1px solid #e0e0e0'}}>
                    <span className="heading products-heading">{ p.name }</span>
                  </div>
                  {p.subheading  && <div className="row pt-2">
                    <span className="product-detail product-subheading">
                      { p.subheading }
                    </span>
                  </div>
                  }
                  {
                    // Optionally render the old SKU if the new field is not being used.
                    this.renderConditionally(
                      !p.productCodes,
                      this.renderProductDetail("SKU: " + p.productCode, "product-detail tiny-text")
                    )
                  }
                  { this.renderProductDetail(p.description, "description-text", "Description", undefined, true)}
                  { this.renderProductDetail(p.directions, "description-text", "Directions", undefined, true)}
                  { this.renderProductDetail(p.market) }
                  <div className="row pt-2" style={{borderTop: '1px solid #e0e0e0'}}>
                    <span className="product-detail product-size-subheading" >Available Sizes</span>
                  </div>
                  <div className="row pt-2" style={{minHeight: '100px'}}>
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
      </div>
    );
  }

}

export default withRouter(Product);
