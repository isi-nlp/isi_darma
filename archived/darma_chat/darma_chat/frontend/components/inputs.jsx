/*
 * Copyright (c) 2017-present, Facebook, Inc.
 * All rights reserved.
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree. An additional grant
 * of patent rights can be found in the PATENTS file in the same directory.
 */

import React from "react";


function Signbox({
  onUpdateName,
  placeholder_text="Full Name of Research Participant"
}){

  return (
    <div>
      {/* <textarea name="signature" id="signature_box" cols="30" rows="1" placeholder={placeholder_text}></textarea> */}
      <input 
        name="signature" 
        id="signature_box" 
        placeholder={placeholder_text} 
        type="text"
        onChange={(evt) => {
          let newVal = evt.target.value;
          onUpdateName(newVal);
        }}
        style={{
          border: 'none',
          borderBottom: '2px solid black',
          width: "100%",
          padding: "12px 20px",
          margin: "8px 0",
          boxSizing: "border-box"
        }}
      />

    </div>
  )
}

function Checkboxes({
  annotationBuckets,
  turnIdx,
  askReason,
  annotations,
  onUpdateAnnotations,
  enabled=true,
}) {
  var reasonComponent = (
    <div>
      <br></br>
      <div>
        <div>Why did you select the checkboxes you did?</div>
        <input 
          type="text" id={'input_reason_' + turnIdx} style={{ minWidth: '50%' }} />
      </div>
    </div>
  )
  if (!askReason) {
    reasonComponent = '';
  }
  // TODO: add support for radio input type
  // let input_type = "checkbox";
  let input_type = "radio";
  const showLineBreaks = annotationBuckets.hasOwnProperty("show_line_breaks") ? annotationBuckets.show_line_breaks : false;
  const numBuckets = Object.keys(annotationBuckets.config).length;
  return (
    <div key={'checkboxes_' + turnIdx}>
      {
        Object.keys(annotationBuckets.config).map((c, checkboxIdx) => (
          <>
            <span key={'span_' + c + '_' + turnIdx}>
              <input
                type={input_type}
                id={c + '_' + turnIdx}
                name={'checkbox_group_' + turnIdx}
                onChange={(evt) => {
                  let newVal = evt.target.checked;
                  console.log(newVal)
                  let oldAnnotations = Object.assign({}, annotations);
                  oldAnnotations[c] = newVal;
                  // hack: set all others as false for radio input type 
                  if (input_type == "radio"){
                    for (var i = 0; i < numBuckets; i++) {
                      let k = Object.keys(annotationBuckets.config)[i]
                      if (k==c){
                        continue 
                      }
                      oldAnnotations[k] = false 
                    } 
                  }
                  console.log(oldAnnotations)
                  onUpdateAnnotations(oldAnnotations);
                }}
                disabled={!enabled}
              />
              <span style={{ marginRight: '15px' }}>
                {annotationBuckets.config[c].name}
              </span>
            </span>
            {(showLineBreaks && checkboxIdx < numBuckets - 1) ? <br></br> : ''}
          </>
        ))
      }
      <div id={'checkbox_description_' + turnIdx} style={{ height: '24px' }}></div>
      {reasonComponent}
    </div>
  )
}
// showLineBreaks: show a line break after every checkbox other than the final one

export { Checkboxes, Signbox };

