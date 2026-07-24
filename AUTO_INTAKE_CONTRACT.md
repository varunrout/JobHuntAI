# Automatic Job Intake Contract

## What the user can send
- a pasted job description;
- a public job URL;
- a screenshot plus company and role;
- a recruiter email describing a vacancy.

## Default behaviour
Unless the user says “analyse only”, “do not edit Drive”, or similar, JobHuntAI should:
- inspect the live vacancy when possible;
- search the existing Jobs tracker;
- create the job record and Job ID;
- save the JD;
- assess viability and sponsorship/work-authorisation;
- score the role;
- stop on fatal issues;
- otherwise create the full application pack;
- prepare the application for submission;
- wait for explicit submission confirmation;
- log the application;
- launch and log Networking for P0/P1 roles.

## User decisions that still require confirmation
- submitting an application;
- sending a LinkedIn or email message;
- answering uncertain legal/work-authorisation questions;
- withdrawing an application;
- deleting or overwriting source artefacts.

## Naming
Job folders:
JOB-YYYY-NNNNNN_Company_Role

Records:
Jobs uses JOB IDs.
Applications uses APP IDs.
Networking contacts uses NET IDs.
Touchpoints uses TP IDs.
Plans use PLAN-Company-sequence.

## Completion standard
The workflow is complete only when the tracker, artefacts, networking plan and next action agree.
