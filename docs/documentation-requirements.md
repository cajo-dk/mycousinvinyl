# Documentation Requirements

## Objective

I want you to analyze the code. Use that analysis together with your knowledge of the application and any .md files in docs to create three new markdown documents:

- Application Architecture, Development and Design Guide
- Installation Guide
- User's Guide

## Contents

This section describes the outline of each of the three documents. You must generate the content.

### Application Architecture, Development and Design Guide

#### Purpose

This guide must enable developers and specialists to work with- and extend the application.

#### Contents

1. Reference Architecture
   - Describe design patterns in use
   - Explain the rationale behind the architectural design decisions and blueprint
2. Data Model
   - Explain the data structures (include Mermaid UML diagram)
   - Explain how to modify and extend th data model
3. Security Model
   - Authentication via MS Azure Entra
   - RBAC roles used in the application
   - Security implemenation
   - Describe the CORS implementation
4. Service Description
   - Describe each service
   - Explain the relationship between the different services. Include a Mermaid UML diagram for reference.
   - Explain the flow of the major processes and back them with Mermaid Sequence Diagrams
5. Discogs Integration
   - Explain how authentication is implemented
   - Explain alignment with the Discogs data model as well as any major differences
   - Describe Discogs API methods used
6. UX
   - Provide general UX Guidelines for the application
   - Describe the layout
   - List foreground and background colors in use
   - Describe the choice of MDI icons and provide a list of icons in use
7. Testing
   - Describe how to do unit testing in the context of this application
   - Describe how to do integration testing in the context of this application

### Installation Guide

#### Purpose

This guide must enable DevOps specialists to install and configure the application.

#### Contents

1. Installation
   - Choice of host
   - Explain docker-compose.yml
   - Explain .env
   - Connecting to discogs
   - Ports
   - Deploy, Build, Run, and monitor
2. Daily Operation
   - Postgresql Backup and Restore
   - Liveness Probes

### User's Guide

#### Purpose

This guide must enable the end-user get started using the application

#### Contents

1. Walk-Through

   - Artists
   - Albums
   - Pressings
   - Collection Items
   - Statistice
   - Profile

2. Creating the first item in your collection

   - Step by step guide

## Constraints

- Any existing markdown documents may be used when creating these three new documents, but the new documents must be able to stand alone - so you must carry over anything you deem usable, but there can be no reference to the old documents.
- If an existing markdown document's file name is prefixed by "old-", they can be referenced, but specifics should always be fetched from the source code. Example: If old documentation lists a background color of #e9e9e9, but the background color actually used in the source is #707070, you must list #707070 as the background color.
