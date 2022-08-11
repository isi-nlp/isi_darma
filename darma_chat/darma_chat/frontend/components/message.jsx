/*
 * Copyright (c) 2017-present, Facebook, Inc.
 * All rights reserved.
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree. An additional grant
 * of patent rights can be found in the PATENTS file in the same directory.
 */

import React from "react";

import { Checkboxes } from './inputs.jsx';

function MaybeCheckboxChatMessage({ isSelf, duration, agentName, message = "", checkbox = null }) {
  // color scheme for alert classes can be referenced here: https://getbootstrap.com/docs/4.0/components/alerts/ 
  const floatToSide = isSelf ? "right" : "left"; // the target speaker's messages are shown to the right while all others are are shown on the left 
  let alertStyle = isSelf ? "alert-info" : "alert-warning"; // the target speaker's messages are in blue while all others are in yellow 
  let message_class = "non-bot-message" // differentiate between bot responses and all other responses to keep track of number of interactions

  // set box color to green if the response is coming from the bot
  if (agentName == "Moderator"){
    alertStyle = "alert-success"
    message_class = "bot-message" // differentiate between bot responses and all other responses to keep track of number of interactions
  }

  return (
    <div className="row" style={{ marginLeft: "0", marginRight: "0" }}>
      <div
        className={"alert message " + alertStyle + " " + message_class}
        role="alert"
        style={{ float: floatToSide }}
      >
        <span style={{ fontSize: "16px", whiteSpace: "pre-wrap" }}>
          {/* <span dangerouslySetInnerHTML={{ __html: message }}></span> */}
          <b>{agentName}</b>: <span dangerouslySetInnerHTML={{ __html: message }}></span>
        </span>
        {checkbox}
      </div>
    </div>
  );
}

function RenderChatMessage({ message, mephistoContext, appContext, idx }) {
  const { agentId, taskConfig } = mephistoContext;
  const { currentAgentNames } = appContext.taskContext;
  const { appSettings, setAppSettings } = appContext;
  const { checkboxValues } = appSettings;
  const isHuman = (message.id === agentId || message.id == currentAgentNames[agentId]);
  const annotationBuckets = taskConfig.annotation_buckets;
  const annotationIntro = taskConfig.annotation_question;

  var checkboxes = null;
  if (!isHuman && annotationBuckets !== null) {
    let thisBoxAnnotations = checkboxValues[idx];
    if (!thisBoxAnnotations) {
      thisBoxAnnotations = Object.fromEntries(
        Object.keys(annotationBuckets.config).map(bucket => [bucket, false])
      )
    }
    checkboxes = <div style={{"fontStyle": "italic"}}>
      <br />
      {annotationIntro}
      <br />
      <Checkboxes 
        annotations={thisBoxAnnotations} 
        onUpdateAnnotations={
          (newAnnotations) => {
            checkboxValues[idx] = newAnnotations;
            setAppSettings({checkboxValues});
          }
        } 
        annotationBuckets={annotationBuckets} 
        turnIdx={idx} 
        askReason={false} 
        enabled={idx == appSettings.numMessages - 1}
      />
    </div>;
  }
  return (
    <MaybeCheckboxChatMessage
      isSelf={isHuman}
      agentName={
        message.id in currentAgentNames
          ? currentAgentNames[message.id]
          : message.id
      }
      message={message.text}
      taskData={message.task_data}
      messageId={message.message_id}
      // checkbox={checkboxes}
    />
  );
}

export { RenderChatMessage, MaybeCheckboxChatMessage };