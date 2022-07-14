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

    if (signed_name == ""){
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
            <div className="hero-head" style={{ width: '850px', padding: '20px', margin: '0px auto' }}>
                <h1 style={{textAlign: 'center'}}> Informed Consent For Research </h1>

                <h3>Introduction</h3>
                <div>
                    We invite you to take part in a research study. Please take as much time as you need to read the consent form. You may want to discuss it with your family, friends, or your personal doctor. If you find any of the language difficult to understand, please ask questions. If you decide to participate, you will be asked to sign this form. A copy of the signed form will be provided to you for your records.

                    <br />

                    The U.S. Department of Defense is funding the study.
                </div>

                <h3>Key Information</h3>
                <div>
                    <p>
                        The following is a short summary of this study to help you decide whether you should participate. More detailed information is listed later in this form.
                    </p>

                    <ol>
                        <li>
                            Being in this research study is voluntary - it is your choice.
                        </li>
                        <li>
                            You are being asked to take part in this study because you are bilingual, speaking both  French and English fluently, and you are at least 18 years old. The purpose of this study is to assess the ability of artificial intelligence-based moderators ("bots") to affect online toxic behavior. Your participation in this study will last approximately 10 minutes per conversation you wish to participate in, but you will have multiple opportunities to participate. Procedures will include reading an existing partial online conversation, assuming the persona, attitude, opinion, and behavior of one of the participants in that conversation, and reacting naturally to another participant who tries to alter "your" behavior.  
                        </li>
                        <li>
                            There are risks from participating in this study. The most common risks are that you will feel uncomfortable imitating the personality of someone whose views or style are dissimilar from your own, or that you will feel reluctant to discuss the topics of the given conversation. More detailed information about the risks of this study can be found under the “Risk and Discomfort” section. 
                        </li>
                        <li>
                            You may not receive any direct benefit from taking part in this study. However, your participation in this study may help us learn how to create better bots and this can lead to less toxic behavior online.
                        </li>
                        <li>
                            If you decide not to participate in this research, your other choices may include finding other tasks on Mechanical Turk that you find of greater interest. 
                        </li>
                    </ol>
                </div>

                <h3>Detailed Information </h3>  
                <div>
                    <h4>
                        <u>Purpose</u>
                    </h4>

                    <p>
                        The purpose of this study is to know if we can use AI to help reduce discord in heated online conversations. You may be familiar with online discussions in places such as Twitter, Facebook, and Reddit, where acrimony, ad hominem attacks, misunderstandings, and all manner of bad behavior turn civil discourse into a cesspool of toxic rhetoric. When well-meaning moderators step in and try and reason with people who are willing to listen, the rhetoric can be cooled, but this is a time-consuming task, usually using a lot of volunteer effort. We're trying to see if we can make "bots" that can help out humans. We hope to learn where bots can actually get people to listen and change their minds. We recognize that this is going to be hard -- it's even hard for humans to do this! But we think we can create software that is a little better at reasoning with upset people than the software we have today. You are invited as a possible participant because you are an adult who is fluent in English and in French, the language of the discussion forum we are studying today, you are located in a country where you can be a Mechanical Turk worker ("turker") and because you have signaled an interest in this kind of task by clicking on the Mechanical Turk link that took you to this document. About 10,000 participants may take part in the study, though the numbers could be much smaller, depending on how eager people are to participate. This research is being funded by DARPA, the Defense Advanced Research Projects Agency.
                    </p>

                </div>

                <div>
                    <h4>
                        <u>Procedures</u>
                    </h4>

                    If you decide to take part, this is what will happen: 
                    <ol>
                        <li>
                            We will show you a conversational thread from a discussion forum, in French. We will identify one of the participants in this thread as the participant you are supposed to act as. You should read the thread and try to understand the motivations and attitudes of the participant. We expect the participant will not be particularly kind. They may use profanity, and they may hold viewpoints you disagree with. In your own life, and in your personal online communications, you may not communicate like this! However, we want you to pretend to be this person for the duration of the task.
                        </li>
                        <li>
                            The conversation will leave off with a moderator who is asking you to stop or change your behavior. The moderator will either be an artificial intelligence or it will be a human. This will be chosen by a random selection, like rolling a die, and you won't be told whether you have a human or an AI. You should respond to the moderator as you would expect the participant to expect. The moderator will likely respond to your response.
                        </li>
                        <li>
                            Continue to chat back-and forth with the moderator until either you think the conversation has ended or the moderator has ended the conversation. Throughout, continue to act as if you are the participant.
                        </li>
                        <li>
                            After the conversation you will be asked several questions about the conversation you had. Think about whether the moderator seemed to understand "your" attitude and whether "your" mind was changed as a result of the conversation. 
                        </li>
                    </ol>
                </div>

                <div>
                    <h4>
                        <u>Risks and Discomforts</u>
                    </h4>

                    <p>
                        Possible risks and discomforts you could experience during this study include feeling offended or nervous at pretending to hold opinions that you do not have. The moderator may also respond to you in ways that you deem offensive or in other ways that lead you to experience unwanted emotions. You can choose to skip the scenario we have selected for you and be given another scenario if you find the subject matter or the participant you are supposed to pretend to be distasteful or offensive.
                    </p>

                    <p>
                        <b>Surveys/Questionnaires/Interviews:</b> Some of the questions may make you feel uneasy or embarrassed. You can choose to skip or stop answering any questions you don't want to.
                    </p>

                    <p>
                        <b>Breach of Confidentiality:</b> There is a small risk that people who are not connected with this study will learn your identity or your personal information. However, we will not store any personally identifying characteristics with the data we collect or release.

                    </p>

                    <p>
                        <b>Unforeseen Risks:</b> There may be other risks that are not known at this time. 
                    </p>
                </div>

                <div>
                    <h4><u>Benefits</u></h4>

                    <p>
                        There are no direct benefits to you from taking part in this study. However, your participation in this study may help us learn how to create artificially intelligent moderators that will directly engage with people in high-emotion, high-antagonism situations on a level that encourages beneficial civil discourse.
                    </p>
                </div>

                <div>
                    <h4><u>Privacy / Confidentiality</u></h4>

                    <p>
                        We will keep your records for this study confidential as far as permitted by law and in general will not collect personally identifying information such as your name, location, age, or any medical information. However, if we are required to do so by law, we will disclose confidential information about you. If any personal information is collected, efforts will be made to limit its use and disclosure to people who are required to review this information. We may publish the information from this study in journals or present it at meetings. If we do, we will not use your name.
                    </p>

                    <p>
                        The University of Southern California's Institutional Review Board (IRB) and Human Subject's Protections Program (HSPP) may review the records we have collected, including your records. Authorized rRepresentatives from of the U.S. Department of Defensethe Navy Human Research Protection Program will have access to research records as part of their responsibilities for human subjects protection oversight of the study.
                    </p>

                    <p>
                        Your responses, which are also called "data", will be stored indefinitely on github and will be made public to the research community without your additional informed consent. Any information that identifies you (such as your name) will be removed from the data or specimens before being shared with others or used in future research studies. 
                    </p>

                    <p>
                        This study is conducted on Amazon Mechanical Turk (MTurk) and it adheres to Amazon’s MTurk Privacy Policy. To understand the privacy and confidentiality limitations associated with using MTurk, we strongly advise you to familiarize yourself with Amazon’s privacy policies (https://www.mturk.com/mturk/privacynotice) and Amazon.com’s warning to workers page https://www.mturk.com/mturk/contact). 
                    </p>
                </div>

                <div>
                    <h4><u>Alternatives</u></h4>

                    <p>
                        There may be alternative(s) to participating in this study. These include not participating in this study.
                    </p>
                </div>

                <div>
                    <h4><u>Payments / Compensation</u></h4>

                    <p>
                        Payments for research participation are considered taxable income and participants may be required to pay taxes on this income. If participants are paid $600 or more in total within a calendar year for participation in one or more research studies, the University will report this as income to the IRS and participants may receive an Internal Revenue Service (IRS) Form 1099. This does not include any payments you receive to pay you back for expenses like parking fees.  
                    </p>
                </div>

                <div>
                    <h4><u>Cost</u></h4>
                    <p>
                        There are no costs related to participation.
                    </p>
                </div>

                <div>
                    <h4><u>Potential Conflict of Interest</u></h4>

                    <p>
                        Jonathan May, the primary investigator of this study, has a financial interest in Amazon, the company being used to facilitate your efforts via the MTurk platform. Dr. May is a paid consultant for a business unit of Amazon not related to the MTurk service, and he conducts this consultant duty independently outside of his duties working for USC. The nature of this conflict and the management of the conflict of interest have been reviewed by the USC Conflict of Interest Review Committee (CIRC).
                    </p>
                </div>

                <div>
                    <h4><u>Voluntary Participation</u></h4>

                    <p>
                    It is your choice whether to participate. If you choose to participate, you may change your mind and leave the study at any time. If you decide not to participate, or choose to end your participation in this study, you will not be penalized or lose any benefits that you are otherwise entitled to.
                    </p>

                    <p>
                    If withdrawal must be gradual for safety reasons, the study investigator will tell you. The study site may still, after your withdrawal, need to report any safety event that you may have experienced due to your participation to all entities involved in the study. Your personal information, including any identifiable information, that has already been collected up to the time of your withdrawal will be kept and used to guarantee the integrity of the study, to determine the safety effects, and to satisfy any legal or regulatory requirements.

                    </p>
                </div>

                <div>
                    <h4>
                        <u>Withdrawal from Study Participation</u>
                    </h4>
                </div>

                <div>
                    <h4>
                        <u>Participant Termination</u>
                    </h4>

                    <p>
                        You may be removed from this study without your consent for any of the following reasons: you do not follow the study investigator's instructions, at the discretion of the study investigator or the sponsor, or the sponsor closes the study. If this happens, the study investigator will discuss other options with you. 
                    </p>
                </div>

                <div>
                    <h4>
                        <u>Contact Information</u>
                    </h4>

                    <p>
                        If you have questions, concerns, complaints, or think the research has hurt you, talk to the study investigator at darma@usc.edu.
                    </p>

                    <p>
                        This research has been reviewed by the USC Institutional Review Board (IRB). The IRB is a research review board that reviews and monitors research studies to protect the rights and welfare of research participants. Contact the IRB if you have questions about your rights as a research participant or you have complaints about the research. You may contact the IRB at (323) 442-0114 or by email at irb@usc.edu.  
                    </p>
                    
                </div>                
            </div>
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