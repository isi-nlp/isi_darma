/*
 * Copyright (c) 2017-present, Facebook, Inc.
 * All rights reserved.
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree. An additional grant
 * of patent rights can be found in the PATENTS file in the same directory.
 */

import React from "react";
import { ErrorBoundary } from './error_boundary.jsx';
import { Checkboxes, Signbox } from './inputs.jsx';
const DEFAULT_MIN_CORRECT = 1;
const DEFAULT_MAX_INCORRECT = 0;
const DEFAULT_MAX_FAILURES_ALLOWED = 100;
var onboardingFailuresCount = 0;
var myCode = "abc123!"

var renderOnboardingFail = function () {
    // Update the UI
    document.getElementById("onboarding-submit-button").style.display = 'none';

    alert('Sorry, you\'ve exceeded the maximum tries to complete this form completely. Please return the HIT.')
}


function getCurrentDate(separator='-'){
    // reference: https://stackoverflow.com/questions/43744312/react-js-get-current-date
    let newDate = new Date()
    let date = newDate.getDate();
    let month = newDate.getMonth() + 1;
    let year = newDate.getFullYear();
    
    return `${year}${separator}${month<10?`0${month}`:`${month}`}${separator}${date}`
}

function arraysEqual(_arr1, _arr2) {
    if (!Array.isArray(_arr1) || ! Array.isArray(_arr2) || _arr1.length !== _arr2.length)
      return false;

    var arr1 = _arr1.concat().sort();
    var arr2 = _arr2.concat().sort();
    for (var i = 0; i < arr1.length; i++) {
        if (arr1[i] !== arr2[i])
            return false;
    }
    return true;
}

var handleOnboardingSubmit = function ({ onboardingData, currentTurnAnnotations, signed_name, onSubmit }) {
    console.log('handleOnboardingSubmit');
    var countCorrect = 0;
    var countIncorrect = 0;
    for (var turnIdx = 0; turnIdx < onboardingData.dialog.length; turnIdx++) {
        var modelUtteranceForTurn = onboardingData.dialog[turnIdx][1];
        var answersForTurn = modelUtteranceForTurn.answers;
        if (!answersForTurn) {
            continue
        } else {
            let givenAnswers = currentTurnAnnotations[turnIdx];
            let answerArray = [];
            for (let arrayKey in givenAnswers) {
                if (givenAnswers[arrayKey]) {
                    answerArray.push(arrayKey);
                }
            }
            if (arraysEqual(answerArray, answersForTurn)) {
                countCorrect += 1;
            } else {
                countIncorrect += 1;
            }
        }
    }
    console.log('correct: ' + countCorrect + ', incorrect: ' + countIncorrect);
    const min_correct = onboardingData.hasOwnProperty("min_correct") ? onboardingData.min_correct : DEFAULT_MIN_CORRECT;
    const max_incorrect = onboardingData.hasOwnProperty("max_incorrect") ? onboardingData.max_incorrect : DEFAULT_MAX_INCORRECT;
    const max_failures_allowed = onboardingData.hasOwnProperty("max_failures_allowed") ? onboardingData.max_failures_allowed : DEFAULT_MAX_FAILURES_ALLOWED;

    var userTextCode = document.getElementById("inputtextarea").value

    if (userTextCode != myCode){
        alert("The code you inputed was incorrect. Please try again.")
    }
    else if (signed_name == ""){
        alert("You must provide your full name as the signature.")
    }
    else if (countCorrect >= min_correct && countIncorrect <= max_incorrect) {
        onSubmit({ annotations: currentTurnAnnotations, success: true, signature: signed_name, date: getCurrentDate() });
    }     
    else {
        if (onboardingFailuresCount < max_failures_allowed) {
            onboardingFailuresCount += 1;
            alert('If you do not agree that you have been given informed consent please do not continue with this task.');
        } else {
            renderOnboardingFail();
            onSubmit({ annotations: currentTurnAnnotations, success: false })
        }
    }
}

function OnboardingDirections({ children }) {
    return (
        <section className="hero is-light">
        </section>
    );
}

function OnboardingQuestion({ 
    annotationBuckets, 
    turnIdx, 
    annotations = null, 
    onUpdateAnnotation = null,
    onUpdateName = null,
}) {
    
    return (
        <div className="alert alert-info" style={{ float: `${turnIdx % 2 == 0 ? "right" : "left"}`, display: 'table' }}>

            <h4>
                Prerequisite Task
            </h4>

            <p>
                Please use the link below to go to another Mechanical Turk task. This prerequisite task will include a statement of consent that you must read, more specific instructions and examples about what you will be working on, and a language and understanding task to ensure your fluency in both English and French and your understanding of the instructions. At the end of the prerequisite task, you will be given a code. Please copy and paste the code into the text area below. Then, affirm that you've read the statement of consent.        
            </p>

            <p>
                
            </p>
                
            <p>
                <ErrorBoundary>
                    <label for="inputtextarea">Input code here:</label>
                    <textarea id="inputtextarea">

                    </textarea>
                </ErrorBoundary>
            </p>

            <h4>
                STATEMENT OF CONSENT
            </h4>
            <p>
                <b>
                    I have read (or someone has read to me) the information provided above. I have been given a chance to ask questions. All my questions have been answered. By signing this form, I am agreeing to take part in this study.
                </b>
                
                <br/>

                <b>
                    Do you agree with this informed consent form? 
                </b>
                <ErrorBoundary>
                    <Checkboxes 
                        annotations={annotations} 
                        onUpdateAnnotations={onUpdateAnnotation} 
                        annotationBuckets={annotationBuckets} 
                        turnIdx={turnIdx} 
                        askReason={false} 
                    />

                    <Signbox 
                        onUpdateName={onUpdateName} 
                    />
                </ErrorBoundary>            
                <div>
                    Date signed: {getCurrentDate()}
                </div>
            </p>



        </div>
    )
}

function OnboardingComponent({ onboardingData, annotationBuckets, annotationQuestion, onSubmit }) {
    if (onboardingData === null) {
        return (
            <div id="onboarding-main-pane">
                Please wait while we set up the task...
            </div>
        );
    } else {
        const [currentTurnAnnotations, setCurrentAnnotations] = React.useState(
            Array.from(Array(onboardingData.dialog.length), () => Object.fromEntries(
                Object.keys(annotationBuckets.config).map(bucket => [bucket, false]))
            )
        );
            
        const [signed_name, setSignedName] = React.useState("")

        return (
            <div id="onboarding-main-pane">
                <OnboardingDirections/>
                <div style={{ width: '850px', margin: '0px auto', clear: 'both' }}>
                    <ErrorBoundary>
                        <div>
                            {
                                onboardingData.dialog.map((turn, idx) => (
                                    <div key={'turn_pair_' + idx}>
                                        {/* <OnboardingQuestion
                                            key={idx * 2}
                                            annotationBuckets={annotationBuckets}
                                            annotationQuestion={annotationQuestion}
                                            annotations={currentTurnAnnotations[idx]}
                                            turnIdx={idx * 2}
                                            text={turn[0].text} /> */}
                                        <OnboardingQuestion
                                            key={idx * 2 + 1}
                                            annotationBuckets={annotationBuckets}
                                            turnIdx={idx * 2 + 1} 
                                            annotations={currentTurnAnnotations[idx]}
                                            onUpdateAnnotation={
                                                (newAnnotations) => {
                                                    let updatedAnnotations = currentTurnAnnotations.slice()
                                                    updatedAnnotations[idx] = newAnnotations;
                                                    setCurrentAnnotations(updatedAnnotations);
                                                }
                                            }
                                            onUpdateName={
                                                (signature) =>{
                                                    let newname = signature 
                                                    setSignedName(newname)
                                                }
                                            }
                                            />
                                    </div>
                                ))
                            }
                        </div>
                    </ErrorBoundary>
                    <div style={{ clear: 'both' }}></div>
                </div>
                <hr />
                <div style={{ textAlign: 'center' }}>
                    <button id="onboarding-submit-button"
                        className="button is-link btn-lg"
                        onClick={() => handleOnboardingSubmit({ 
                            onboardingData, 
                            currentTurnAnnotations,
                            signed_name, 
                            onSubmit,
                        })}
                    >
                        Submit
                    </button>
                </div>
            </div>
        );
    }
}

export { OnboardingComponent, OnboardingQuestion };