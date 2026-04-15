function t(t,e,i,s){var r,n=arguments.length,o=n<3?e:null===s?s=Object.getOwnPropertyDescriptor(e,i):s;if("object"==typeof Reflect&&"function"==typeof Reflect.decorate)o=Reflect.decorate(t,e,i,s);else for(var a=t.length-1;a>=0;a--)(r=t[a])&&(o=(n<3?r(o):n>3?r(e,i,o):r(e,i))||o);return n>3&&o&&Object.defineProperty(e,i,o),o}"function"==typeof SuppressedError&&SuppressedError;const e=globalThis,i=e.ShadowRoot&&(void 0===e.ShadyCSS||e.ShadyCSS.nativeShadow)&&"adoptedStyleSheets"in Document.prototype&&"replace"in CSSStyleSheet.prototype,s=Symbol(),r=new WeakMap;let n=class{constructor(t,e,i){if(this._$cssResult$=!0,i!==s)throw Error("CSSResult is not constructable. Use `unsafeCSS` or `css` instead.");this.cssText=t,this.t=e}get styleSheet(){let t=this.o;const e=this.t;if(i&&void 0===t){const i=void 0!==e&&1===e.length;i&&(t=r.get(e)),void 0===t&&((this.o=t=new CSSStyleSheet).replaceSync(this.cssText),i&&r.set(e,t))}return t}toString(){return this.cssText}};const o=i?t=>t:t=>t instanceof CSSStyleSheet?(t=>{let e="";for(const i of t.cssRules)e+=i.cssText;return(t=>new n("string"==typeof t?t:t+"",void 0,s))(e)})(t):t,{is:a,defineProperty:h,getOwnPropertyDescriptor:c,getOwnPropertyNames:l,getOwnPropertySymbols:d,getPrototypeOf:p}=Object,u=globalThis,_=u.trustedTypes,m=_?_.emptyScript:"",$=u.reactiveElementPolyfillSupport,f=(t,e)=>t,y={toAttribute(t,e){switch(e){case Boolean:t=t?m:null;break;case Object:case Array:t=null==t?t:JSON.stringify(t)}return t},fromAttribute(t,e){let i=t;switch(e){case Boolean:i=null!==t;break;case Number:i=null===t?null:Number(t);break;case Object:case Array:try{i=JSON.parse(t)}catch(t){i=null}}return i}},g=(t,e)=>!a(t,e),v={attribute:!0,type:String,converter:y,reflect:!1,useDefault:!1,hasChanged:g};Symbol.metadata??=Symbol("metadata"),u.litPropertyMetadata??=new WeakMap;let b=class extends HTMLElement{static addInitializer(t){this._$Ei(),(this.l??=[]).push(t)}static get observedAttributes(){return this.finalize(),this._$Eh&&[...this._$Eh.keys()]}static createProperty(t,e=v){if(e.state&&(e.attribute=!1),this._$Ei(),this.prototype.hasOwnProperty(t)&&((e=Object.create(e)).wrapped=!0),this.elementProperties.set(t,e),!e.noAccessor){const i=Symbol(),s=this.getPropertyDescriptor(t,i,e);void 0!==s&&h(this.prototype,t,s)}}static getPropertyDescriptor(t,e,i){const{get:s,set:r}=c(this.prototype,t)??{get(){return this[e]},set(t){this[e]=t}};return{get:s,set(e){const n=s?.call(this);r?.call(this,e),this.requestUpdate(t,n,i)},configurable:!0,enumerable:!0}}static getPropertyOptions(t){return this.elementProperties.get(t)??v}static _$Ei(){if(this.hasOwnProperty(f("elementProperties")))return;const t=p(this);t.finalize(),void 0!==t.l&&(this.l=[...t.l]),this.elementProperties=new Map(t.elementProperties)}static finalize(){if(this.hasOwnProperty(f("finalized")))return;if(this.finalized=!0,this._$Ei(),this.hasOwnProperty(f("properties"))){const t=this.properties,e=[...l(t),...d(t)];for(const i of e)this.createProperty(i,t[i])}const t=this[Symbol.metadata];if(null!==t){const e=litPropertyMetadata.get(t);if(void 0!==e)for(const[t,i]of e)this.elementProperties.set(t,i)}this._$Eh=new Map;for(const[t,e]of this.elementProperties){const i=this._$Eu(t,e);void 0!==i&&this._$Eh.set(i,t)}this.elementStyles=this.finalizeStyles(this.styles)}static finalizeStyles(t){const e=[];if(Array.isArray(t)){const i=new Set(t.flat(1/0).reverse());for(const t of i)e.unshift(o(t))}else void 0!==t&&e.push(o(t));return e}static _$Eu(t,e){const i=e.attribute;return!1===i?void 0:"string"==typeof i?i:"string"==typeof t?t.toLowerCase():void 0}constructor(){super(),this._$Ep=void 0,this.isUpdatePending=!1,this.hasUpdated=!1,this._$Em=null,this._$Ev()}_$Ev(){this._$ES=new Promise(t=>this.enableUpdating=t),this._$AL=new Map,this._$E_(),this.requestUpdate(),this.constructor.l?.forEach(t=>t(this))}addController(t){(this._$EO??=new Set).add(t),void 0!==this.renderRoot&&this.isConnected&&t.hostConnected?.()}removeController(t){this._$EO?.delete(t)}_$E_(){const t=new Map,e=this.constructor.elementProperties;for(const i of e.keys())this.hasOwnProperty(i)&&(t.set(i,this[i]),delete this[i]);t.size>0&&(this._$Ep=t)}createRenderRoot(){const t=this.shadowRoot??this.attachShadow(this.constructor.shadowRootOptions);return((t,s)=>{if(i)t.adoptedStyleSheets=s.map(t=>t instanceof CSSStyleSheet?t:t.styleSheet);else for(const i of s){const s=document.createElement("style"),r=e.litNonce;void 0!==r&&s.setAttribute("nonce",r),s.textContent=i.cssText,t.appendChild(s)}})(t,this.constructor.elementStyles),t}connectedCallback(){this.renderRoot??=this.createRenderRoot(),this.enableUpdating(!0),this._$EO?.forEach(t=>t.hostConnected?.())}enableUpdating(t){}disconnectedCallback(){this._$EO?.forEach(t=>t.hostDisconnected?.())}attributeChangedCallback(t,e,i){this._$AK(t,i)}_$ET(t,e){const i=this.constructor.elementProperties.get(t),s=this.constructor._$Eu(t,i);if(void 0!==s&&!0===i.reflect){const r=(void 0!==i.converter?.toAttribute?i.converter:y).toAttribute(e,i.type);this._$Em=t,null==r?this.removeAttribute(s):this.setAttribute(s,r),this._$Em=null}}_$AK(t,e){const i=this.constructor,s=i._$Eh.get(t);if(void 0!==s&&this._$Em!==s){const t=i.getPropertyOptions(s),r="function"==typeof t.converter?{fromAttribute:t.converter}:void 0!==t.converter?.fromAttribute?t.converter:y;this._$Em=s;const n=r.fromAttribute(e,t.type);this[s]=n??this._$Ej?.get(s)??n,this._$Em=null}}requestUpdate(t,e,i,s=!1,r){if(void 0!==t){const n=this.constructor;if(!1===s&&(r=this[t]),i??=n.getPropertyOptions(t),!((i.hasChanged??g)(r,e)||i.useDefault&&i.reflect&&r===this._$Ej?.get(t)&&!this.hasAttribute(n._$Eu(t,i))))return;this.C(t,e,i)}!1===this.isUpdatePending&&(this._$ES=this._$EP())}C(t,e,{useDefault:i,reflect:s,wrapped:r},n){i&&!(this._$Ej??=new Map).has(t)&&(this._$Ej.set(t,n??e??this[t]),!0!==r||void 0!==n)||(this._$AL.has(t)||(this.hasUpdated||i||(e=void 0),this._$AL.set(t,e)),!0===s&&this._$Em!==t&&(this._$Eq??=new Set).add(t))}async _$EP(){this.isUpdatePending=!0;try{await this._$ES}catch(t){Promise.reject(t)}const t=this.scheduleUpdate();return null!=t&&await t,!this.isUpdatePending}scheduleUpdate(){return this.performUpdate()}performUpdate(){if(!this.isUpdatePending)return;if(!this.hasUpdated){if(this.renderRoot??=this.createRenderRoot(),this._$Ep){for(const[t,e]of this._$Ep)this[t]=e;this._$Ep=void 0}const t=this.constructor.elementProperties;if(t.size>0)for(const[e,i]of t){const{wrapped:t}=i,s=this[e];!0!==t||this._$AL.has(e)||void 0===s||this.C(e,void 0,i,s)}}let t=!1;const e=this._$AL;try{t=this.shouldUpdate(e),t?(this.willUpdate(e),this._$EO?.forEach(t=>t.hostUpdate?.()),this.update(e)):this._$EM()}catch(e){throw t=!1,this._$EM(),e}t&&this._$AE(e)}willUpdate(t){}_$AE(t){this._$EO?.forEach(t=>t.hostUpdated?.()),this.hasUpdated||(this.hasUpdated=!0,this.firstUpdated(t)),this.updated(t)}_$EM(){this._$AL=new Map,this.isUpdatePending=!1}get updateComplete(){return this.getUpdateComplete()}getUpdateComplete(){return this._$ES}shouldUpdate(t){return!0}update(t){this._$Eq&&=this._$Eq.forEach(t=>this._$ET(t,this[t])),this._$EM()}updated(t){}firstUpdated(t){}};b.elementStyles=[],b.shadowRootOptions={mode:"open"},b[f("elementProperties")]=new Map,b[f("finalized")]=new Map,$?.({ReactiveElement:b}),(u.reactiveElementVersions??=[]).push("2.1.2");const A=globalThis,E=t=>t,w=A.trustedTypes,x=w?w.createPolicy("lit-html",{createHTML:t=>t}):void 0,S="$lit$",k=`lit$${Math.random().toFixed(9).slice(2)}$`,P="?"+k,C=`<${P}>`,T=document,O=()=>T.createComment(""),U=t=>null===t||"object"!=typeof t&&"function"!=typeof t,R=Array.isArray,M="[ \t\n\f\r]",H=/<(?:(!--|\/[^a-zA-Z])|(\/?[a-zA-Z][^>\s]*)|(\/?$))/g,N=/-->/g,I=/>/g,V=RegExp(`>|${M}(?:([^\\s"'>=/]+)(${M}*=${M}*(?:[^ \t\n\f\r"'\`<>=]|("|')|))|$)`,"g"),K=/'/g,L=/"/g,j=/^(?:script|style|textarea|title)$/i,D=(t=>(e,...i)=>({_$litType$:t,strings:e,values:i}))(1),z=Symbol.for("lit-noChange"),Y=Symbol.for("lit-nothing"),B=new WeakMap,W=T.createTreeWalker(T,129);function q(t,e){if(!R(t)||!t.hasOwnProperty("raw"))throw Error("invalid template strings array");return void 0!==x?x.createHTML(e):e}const F=(t,e)=>{const i=t.length-1,s=[];let r,n=2===e?"<svg>":3===e?"<math>":"",o=H;for(let e=0;e<i;e++){const i=t[e];let a,h,c=-1,l=0;for(;l<i.length&&(o.lastIndex=l,h=o.exec(i),null!==h);)l=o.lastIndex,o===H?"!--"===h[1]?o=N:void 0!==h[1]?o=I:void 0!==h[2]?(j.test(h[2])&&(r=RegExp("</"+h[2],"g")),o=V):void 0!==h[3]&&(o=V):o===V?">"===h[0]?(o=r??H,c=-1):void 0===h[1]?c=-2:(c=o.lastIndex-h[2].length,a=h[1],o=void 0===h[3]?V:'"'===h[3]?L:K):o===L||o===K?o=V:o===N||o===I?o=H:(o=V,r=void 0);const d=o===V&&t[e+1].startsWith("/>")?" ":"";n+=o===H?i+C:c>=0?(s.push(a),i.slice(0,c)+S+i.slice(c)+k+d):i+k+(-2===c?e:d)}return[q(t,n+(t[i]||"<?>")+(2===e?"</svg>":3===e?"</math>":"")),s]};class G{constructor({strings:t,_$litType$:e},i){let s;this.parts=[];let r=0,n=0;const o=t.length-1,a=this.parts,[h,c]=F(t,e);if(this.el=G.createElement(h,i),W.currentNode=this.el.content,2===e||3===e){const t=this.el.content.firstChild;t.replaceWith(...t.childNodes)}for(;null!==(s=W.nextNode())&&a.length<o;){if(1===s.nodeType){if(s.hasAttributes())for(const t of s.getAttributeNames())if(t.endsWith(S)){const e=c[n++],i=s.getAttribute(t).split(k),o=/([.?@])?(.*)/.exec(e);a.push({type:1,index:r,name:o[2],strings:i,ctor:"."===o[1]?tt:"?"===o[1]?et:"@"===o[1]?it:Q}),s.removeAttribute(t)}else t.startsWith(k)&&(a.push({type:6,index:r}),s.removeAttribute(t));if(j.test(s.tagName)){const t=s.textContent.split(k),e=t.length-1;if(e>0){s.textContent=w?w.emptyScript:"";for(let i=0;i<e;i++)s.append(t[i],O()),W.nextNode(),a.push({type:2,index:++r});s.append(t[e],O())}}}else if(8===s.nodeType)if(s.data===P)a.push({type:2,index:r});else{let t=-1;for(;-1!==(t=s.data.indexOf(k,t+1));)a.push({type:7,index:r}),t+=k.length-1}r++}}static createElement(t,e){const i=T.createElement("template");return i.innerHTML=t,i}}function J(t,e,i=t,s){if(e===z)return e;let r=void 0!==s?i._$Co?.[s]:i._$Cl;const n=U(e)?void 0:e._$litDirective$;return r?.constructor!==n&&(r?._$AO?.(!1),void 0===n?r=void 0:(r=new n(t),r._$AT(t,i,s)),void 0!==s?(i._$Co??=[])[s]=r:i._$Cl=r),void 0!==r&&(e=J(t,r._$AS(t,e.values),r,s)),e}class Z{constructor(t,e){this._$AV=[],this._$AN=void 0,this._$AD=t,this._$AM=e}get parentNode(){return this._$AM.parentNode}get _$AU(){return this._$AM._$AU}u(t){const{el:{content:e},parts:i}=this._$AD,s=(t?.creationScope??T).importNode(e,!0);W.currentNode=s;let r=W.nextNode(),n=0,o=0,a=i[0];for(;void 0!==a;){if(n===a.index){let e;2===a.type?e=new X(r,r.nextSibling,this,t):1===a.type?e=new a.ctor(r,a.name,a.strings,this,t):6===a.type&&(e=new st(r,this,t)),this._$AV.push(e),a=i[++o]}n!==a?.index&&(r=W.nextNode(),n++)}return W.currentNode=T,s}p(t){let e=0;for(const i of this._$AV)void 0!==i&&(void 0!==i.strings?(i._$AI(t,i,e),e+=i.strings.length-2):i._$AI(t[e])),e++}}class X{get _$AU(){return this._$AM?._$AU??this._$Cv}constructor(t,e,i,s){this.type=2,this._$AH=Y,this._$AN=void 0,this._$AA=t,this._$AB=e,this._$AM=i,this.options=s,this._$Cv=s?.isConnected??!0}get parentNode(){let t=this._$AA.parentNode;const e=this._$AM;return void 0!==e&&11===t?.nodeType&&(t=e.parentNode),t}get startNode(){return this._$AA}get endNode(){return this._$AB}_$AI(t,e=this){t=J(this,t,e),U(t)?t===Y||null==t||""===t?(this._$AH!==Y&&this._$AR(),this._$AH=Y):t!==this._$AH&&t!==z&&this._(t):void 0!==t._$litType$?this.$(t):void 0!==t.nodeType?this.T(t):(t=>R(t)||"function"==typeof t?.[Symbol.iterator])(t)?this.k(t):this._(t)}O(t){return this._$AA.parentNode.insertBefore(t,this._$AB)}T(t){this._$AH!==t&&(this._$AR(),this._$AH=this.O(t))}_(t){this._$AH!==Y&&U(this._$AH)?this._$AA.nextSibling.data=t:this.T(T.createTextNode(t)),this._$AH=t}$(t){const{values:e,_$litType$:i}=t,s="number"==typeof i?this._$AC(t):(void 0===i.el&&(i.el=G.createElement(q(i.h,i.h[0]),this.options)),i);if(this._$AH?._$AD===s)this._$AH.p(e);else{const t=new Z(s,this),i=t.u(this.options);t.p(e),this.T(i),this._$AH=t}}_$AC(t){let e=B.get(t.strings);return void 0===e&&B.set(t.strings,e=new G(t)),e}k(t){R(this._$AH)||(this._$AH=[],this._$AR());const e=this._$AH;let i,s=0;for(const r of t)s===e.length?e.push(i=new X(this.O(O()),this.O(O()),this,this.options)):i=e[s],i._$AI(r),s++;s<e.length&&(this._$AR(i&&i._$AB.nextSibling,s),e.length=s)}_$AR(t=this._$AA.nextSibling,e){for(this._$AP?.(!1,!0,e);t!==this._$AB;){const e=E(t).nextSibling;E(t).remove(),t=e}}setConnected(t){void 0===this._$AM&&(this._$Cv=t,this._$AP?.(t))}}class Q{get tagName(){return this.element.tagName}get _$AU(){return this._$AM._$AU}constructor(t,e,i,s,r){this.type=1,this._$AH=Y,this._$AN=void 0,this.element=t,this.name=e,this._$AM=s,this.options=r,i.length>2||""!==i[0]||""!==i[1]?(this._$AH=Array(i.length-1).fill(new String),this.strings=i):this._$AH=Y}_$AI(t,e=this,i,s){const r=this.strings;let n=!1;if(void 0===r)t=J(this,t,e,0),n=!U(t)||t!==this._$AH&&t!==z,n&&(this._$AH=t);else{const s=t;let o,a;for(t=r[0],o=0;o<r.length-1;o++)a=J(this,s[i+o],e,o),a===z&&(a=this._$AH[o]),n||=!U(a)||a!==this._$AH[o],a===Y?t=Y:t!==Y&&(t+=(a??"")+r[o+1]),this._$AH[o]=a}n&&!s&&this.j(t)}j(t){t===Y?this.element.removeAttribute(this.name):this.element.setAttribute(this.name,t??"")}}class tt extends Q{constructor(){super(...arguments),this.type=3}j(t){this.element[this.name]=t===Y?void 0:t}}class et extends Q{constructor(){super(...arguments),this.type=4}j(t){this.element.toggleAttribute(this.name,!!t&&t!==Y)}}class it extends Q{constructor(t,e,i,s,r){super(t,e,i,s,r),this.type=5}_$AI(t,e=this){if((t=J(this,t,e,0)??Y)===z)return;const i=this._$AH,s=t===Y&&i!==Y||t.capture!==i.capture||t.once!==i.once||t.passive!==i.passive,r=t!==Y&&(i===Y||s);s&&this.element.removeEventListener(this.name,this,i),r&&this.element.addEventListener(this.name,this,t),this._$AH=t}handleEvent(t){"function"==typeof this._$AH?this._$AH.call(this.options?.host??this.element,t):this._$AH.handleEvent(t)}}class st{constructor(t,e,i){this.element=t,this.type=6,this._$AN=void 0,this._$AM=e,this.options=i}get _$AU(){return this._$AM._$AU}_$AI(t){J(this,t)}}const rt=A.litHtmlPolyfillSupport;rt?.(G,X),(A.litHtmlVersions??=[]).push("3.3.2");const nt=globalThis;class ot extends b{constructor(){super(...arguments),this.renderOptions={host:this},this._$Do=void 0}createRenderRoot(){const t=super.createRenderRoot();return this.renderOptions.renderBefore??=t.firstChild,t}update(t){const e=this.render();this.hasUpdated||(this.renderOptions.isConnected=this.isConnected),super.update(t),this._$Do=((t,e,i)=>{const s=i?.renderBefore??e;let r=s._$litPart$;if(void 0===r){const t=i?.renderBefore??null;s._$litPart$=r=new X(e.insertBefore(O(),t),t,void 0,i??{})}return r._$AI(t),r})(e,this.renderRoot,this.renderOptions)}connectedCallback(){super.connectedCallback(),this._$Do?.setConnected(!0)}disconnectedCallback(){super.disconnectedCallback(),this._$Do?.setConnected(!1)}render(){return z}}ot._$litElement$=!0,ot.finalized=!0,nt.litElementHydrateSupport?.({LitElement:ot});const at=nt.litElementPolyfillSupport;at?.({LitElement:ot}),(nt.litElementVersions??=[]).push("4.2.2");const ht={attribute:!0,type:String,converter:y,reflect:!1,hasChanged:g},ct=(t=ht,e,i)=>{const{kind:s,metadata:r}=i;let n=globalThis.litPropertyMetadata.get(r);if(void 0===n&&globalThis.litPropertyMetadata.set(r,n=new Map),"setter"===s&&((t=Object.create(t)).wrapped=!0),n.set(i.name,t),"accessor"===s){const{name:s}=i;return{set(i){const r=e.get.call(this);e.set.call(this,i),this.requestUpdate(s,r,t,!0,i)},init(e){return void 0!==e&&this.C(s,void 0,t,e),e}}}if("setter"===s){const{name:s}=i;return function(i){const r=this[s];e.call(this,i),this.requestUpdate(s,r,t,!0,i)}}throw Error("Unsupported decorator location: "+s)};function lt(t){return(e,i)=>"object"==typeof i?ct(t,e,i):((t,e,i)=>{const s=e.hasOwnProperty(i);return e.constructor.createProperty(i,t),s?Object.getOwnPropertyDescriptor(e,i):void 0})(t,e,i)}function dt(t){return lt({...t,state:!0,attribute:!1})}const pt=((t,...e)=>{const i=1===t.length?t[0]:e.reduce((e,i,s)=>e+(t=>{if(!0===t._$cssResult$)return t.cssText;if("number"==typeof t)return t;throw Error("Value passed to 'css' function must be a 'css' function result: "+t+". Use 'unsafeCSS' to pass non-literal values, but take care to ensure page security.")})(i)+t[s+1],t[0]);return new n(i,t,s)})`
  :host {
    --btn-bg: var(--card-background-color, #1c1c1c);
    --btn-fg: var(--primary-text-color, #e0e0e0);
    --btn-active: var(--primary-color, #03a9f4);
    --btn-radius: 12px;
    --gap: 6px;
  }

  ha-card {
    padding: 12px;
    overflow: hidden;
  }

  /* ── Common button ──────────────────────────────────────── */

  button {
    display: flex;
    align-items: center;
    justify-content: center;
    background: var(--btn-bg);
    color: var(--btn-fg);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: var(--btn-radius);
    cursor: pointer;
    font-size: 13px;
    padding: 10px 0;
    min-height: 42px;
    touch-action: manipulation;
    user-select: none;
    -webkit-tap-highlight-color: transparent;
    transition: opacity 0.1s;
  }

  button:active {
    opacity: 0.6;
  }

  button ha-icon {
    --mdc-icon-size: 22px;
  }

  /* Power button special */
  button.power-on {
    color: var(--btn-active);
    border-color: var(--btn-active);
  }

  /* ── Grid rows ──────────────────────────────────────────── */

  .row-2 {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: var(--gap);
    margin-bottom: var(--gap);
  }

  .row-3 {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: var(--gap);
    margin-bottom: var(--gap);
  }

  .row-4 {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: var(--gap);
    margin-bottom: var(--gap);
  }

  .row-5 {
    display: grid;
    grid-template-columns: repeat(5, 1fr);
    gap: var(--gap);
    margin-bottom: var(--gap);
  }

  /* ── Text input row ─────────────────────────────────────── */

  .text-row {
    display: flex;
    gap: var(--gap);
    margin-bottom: var(--gap);
    animation: slideIn 0.2s ease-out;
  }

  @keyframes slideIn {
    from {
      opacity: 0;
      max-height: 0;
    }
    to {
      opacity: 1;
      max-height: 60px;
    }
  }

  .text-row input {
    flex: 1;
    min-width: 0;
    background: var(--btn-bg);
    color: var(--btn-fg);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: var(--btn-radius);
    padding: 8px 12px;
    font-size: 14px;
    outline: none;
  }

  .text-row input:focus {
    border-color: var(--btn-active);
  }

  .text-row button {
    flex-shrink: 0;
    padding: 8px 14px;
    min-height: 0;
  }

  /* ── Status line ────────────────────────────────────────── */

  .status {
    text-align: center;
    font-size: 11px;
    color: var(--secondary-text-color, #888);
    padding: 2px 0 6px;
  }
`;window.customCards=window.customCards||[],window.customCards.push({type:"samsung-tv-remote-card",name:"Samsung TV Remote",description:"Full remote control for Samsung Tizen TVs (Samsung TV Max)"});const ut=[{key:"_POWER",icon:"mdi:power",label:"ON"},{key:"KEY_MENU",icon:"mdi:menu",label:"Menu"}],_t=[{key:"KEY_VOLUP",icon:"mdi:volume-plus",label:"Vol +",hold:!0},{key:"KEY_MUTE",icon:"mdi:volume-off",label:"Mute"},{key:"KEY_CHUP",icon:"mdi:arrow-up-bold",label:"CH up",hold:!0}],mt=[{key:"KEY_VOLDOWN",icon:"mdi:volume-minus",label:"Vol −",hold:!0},{key:"KEY_SOURCE",icon:"mdi:video-input-hdmi",label:"Source"},{key:"KEY_CHDOWN",icon:"mdi:arrow-down-bold",label:"CH dn",hold:!0}],$t=[{key:"KEY_HOME",icon:"mdi:home",label:"Home"},{key:"KEY_UP",icon:"mdi:arrow-up",hold:!0},{key:"KEY_INFO",icon:"mdi:information",label:"Info"}],ft=[{key:"KEY_LEFT",icon:"mdi:arrow-left",hold:!0},{key:"KEY_ENTER",icon:"mdi:keyboard-return",label:"OK"},{key:"KEY_RIGHT",icon:"mdi:arrow-right",hold:!0}],yt=[{key:"KEY_RETURN",icon:"mdi:keyboard-backspace",label:"Back"},{key:"KEY_DOWN",icon:"mdi:arrow-down",hold:!0},{key:"KEY_EXIT",icon:"mdi:close",label:"Exit"}],gt=[{service:"media_play",icon:"mdi:play",label:"Play"},{service:"media_pause",icon:"mdi:pause",label:"Pause"},{service:"media_stop",icon:"mdi:stop",label:"Stop"},{service:"media_previous_track",icon:"mdi:skip-previous",label:"Prev"},{service:"media_next_track",icon:"mdi:skip-next",label:"Next"}],vt=[{name:"YouTube",icon:"mdi:youtube",label:"YT"},{name:"Netflix",icon:"mdi:netflix",label:"Netflix"},{name:"Spotify",icon:"mdi:spotify",label:"Spotify"},{name:"Browser",icon:"mdi:earth",label:"Web"}];let bt=class extends ot{constructor(){super(...arguments),this._textValue=""}setConfig(t){if(!t.entity)throw new Error("entity is required");this._config=t}getCardSize(){return 8}updated(t){if(super.updated(t),t.has("hass")&&this.hass&&this._config){const t=this.hass.states[this._config.entity];if(t){t.attributes.keyboard_active&&this._textValue}}}firstUpdated(){this._bindHoldButtons()}render(){if(!this._config||!this.hass)return D``;const t=this.hass.states[this._config.entity];if(!t)return D`<ha-card><div class="status">Entity not found: ${this._config.entity}</div></ha-card>`;const e=t.attributes,i="on"===t.state;return D`
      <ha-card>
        ${this._renderRow(ut,"row-2",i)}
        ${e.keyboard_active?this._renderTextInput():Y}
        ${this._renderRow(_t,"row-3")}
        ${this._renderRow(mt,"row-3")}
        ${this._renderRow($t,"row-3")}
        ${this._renderRow(ft,"row-3")}
        ${this._renderRow(yt,"row-3")}
        ${this._renderTransport(e)}
        ${this._renderApps(e)}
        <div class="status">
          ${e.tv_model||"Samsung TV"} &middot; ${e.power_state}
        </div>
      </ha-card>
    `}_renderRow(t,e,i){return D`
      <div class="${e}">
        ${t.map(t=>D`
            <button
              class="${"_POWER"===t.key&&i?"power-on":""}"
              data-key="${t.key}"
              @click=${()=>this._handleKeyTap(t.key)}
            >
              <ha-icon icon="${t.icon}"></ha-icon>
              ${t.label?D`&nbsp;${t.label}`:Y}
            </button>
          `)}
      </div>
    `}_renderTextInput(){return D`
      <div class="text-row">
        <input
          type="text"
          placeholder="Type URL / text…"
          .value=${this._textValue}
          @input=${t=>{this._textValue=t.target.value}}
          @keydown=${t=>{"Enter"===t.key&&this._sendText()}}
        />
        <button @click=${this._sendText}>
          <ha-icon icon="mdi:send"></ha-icon>
        </button>
        <button @click=${()=>{this._textValue=""}}>
          <ha-icon icon="mdi:close-circle-outline"></ha-icon>
        </button>
      </div>
    `}_renderTransport(t){const e=this._findMediaPlayer(t);return e?D`
      <div class="row-5">
        ${gt.map(t=>D`
            <button @click=${()=>this._callMediaPlayer(t.service,e)}>
              <ha-icon icon="${t.icon}"></ha-icon>
            </button>
          `)}
      </div>
    `:D``}_renderApps(t){return D`
      <div class="row-4">
        ${vt.map(e=>D`
            <button @click=${()=>this._launchApp(e.name,t)}>
              <ha-icon icon="${e.icon}"></ha-icon>
              &nbsp;${e.label}
            </button>
          `)}
      </div>
    `}_bindHoldButtons(){const t=this.shadowRoot;t&&t.querySelectorAll("button[data-key]").forEach(t=>{const e=t.dataset.key,i=[..._t,...mt,...$t,...ft,...yt].find(t=>t.key===e);i?.hold&&function(t,e){let i;const s=()=>{void 0!==i&&(clearInterval(i),i=void 0)};t.addEventListener("pointerdown",t=>{0===t.button&&(t.preventDefault(),s(),e(),i=setInterval(e,150))}),t.addEventListener("pointerup",s),t.addEventListener("pointerleave",s),t.addEventListener("pointercancel",s)}(t,()=>this._sendKey(e))})}_handleKeyTap(t){"_POWER"!==t?this.hass.callService("remote","send_command",{command:t},{entity_id:this._config.entity}):this.hass.callService("remote","toggle",void 0,{entity_id:this._config.entity})}_sendKey(t){const e=this._getEntryId();this.hass.callService("samsungtv_max","send_key",{key:t,entry_id:e})}_sendText(){if(!this._textValue)return;const t=this._getEntryId();this.hass.callService("samsungtv_max","send_text",{text:this._textValue,entry_id:t}),this._textValue=""}_launchApp(t,e){this.hass.callService("samsungtv_max","launch_app",{app_name:t,entry_id:e.config_entry_id})}_callMediaPlayer(t,e){this.hass.callService("media_player",t,void 0,{entity_id:e})}_getEntryId(){const t=this.hass.states[this._config.entity];return t?.attributes?.config_entry_id??""}_findMediaPlayer(t){const e=t.config_entry_id;for(const t of Object.keys(this.hass.states)){if(!t.startsWith("media_player."))continue;const i=this.hass.states[t];if(i.attributes?.config_entry_id===e)return t}const i=this._config.entity.replace("remote.","media_player.").replace(/_remote$/,"");if(this.hass.states[i])return i}};bt.styles=pt,t([lt({attribute:!1})],bt.prototype,"hass",void 0),t([dt()],bt.prototype,"_config",void 0),t([dt()],bt.prototype,"_textValue",void 0),bt=t([(t=>(e,i)=>{void 0!==i?i.addInitializer(()=>{customElements.define(t,e)}):customElements.define(t,e)})("samsung-tv-remote-card")],bt);export{bt as SamsungTvRemoteCard};
