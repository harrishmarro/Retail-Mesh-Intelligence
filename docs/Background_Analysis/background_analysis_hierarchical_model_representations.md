# Background Analysis: Hierarchical Model Representations

## 1. Overview

Existing automotive data models represent different parts of the
vehicle-retail domain. The hierarchy below groups them by their **main
modeling focus**.

``` text
                 Automotive Data Representations
                            |
          +-----------------+------------------+
          |                 |                  |
          v                 v                  v
   Vehicle-Centric    Commerce-Centric   Ecosystem-Centric
          |                 |                  |
       +--+--+              |             +----+----+
       |     |              |             |         |
       v     v              v             v         v
      VSO  Schema.org   GoodRelations  Catena-X   Other
           Automotive
```

## 2. Vehicle-Centric Representations

### VSO --- Vehicle Sales Ontology

**Main focus:** Describing vehicles and their automotive
characteristics.

``` text
Vehicle
  |
  +-- Model
  +-- Type
  +-- Features
  +-- Specifications
```

**Useful for our project:** Provides automotive-specific concepts for
representing vehicles.

**Limitation:** Vehicle description is the main focus; provider
transactions, performance, and incentives are not the central modeling
structure.

### Schema.org Automotive

**Main focus:** Representing vehicles and vehicle-related product
information on the Web.

``` text
Product
  |
  v
Vehicle
  |
  v
Car
  |
  +-- Mileage
  +-- Engine
  +-- Fuel Type
  +-- Transmission
  +-- VIN
```

**Useful for our project:** Provides reusable vehicle, product,
organization, and offer concepts.

**Limitation:** It does not make cross-provider transaction history and
incentive reasoning the central structure.

## 3. Commerce-Centric Representations

### GoodRelations

**Main focus:** Representing commercial relationships and offers.

``` text
Business Entity
      |
      | offers
      v
   Offering
      |
      v
 Product / Service
```

**Useful for our project:** Helps represent who offers a vehicle or
service and under what commercial conditions.

**Limitation:** An offer is different from a completed transaction and
does not by itself provide our provider-performance and incentive model.

## 4. Ecosystem-Centric Representations

### Catena-X

**Main focus:** Data interoperability and information exchange across
automotive organizations.

``` text
Organization
     |
     v
Digital Twin
     |
     v
Semantic Data / Aspect
```

**Useful for our project:** Demonstrates how independent automotive
organizations can share semantically consistent information.

**Limitation:** Its broader ecosystem and supply-chain interoperability
focus differs from our specific retail transaction and incentive
reasoning problem.

## 5. Where Our Model Fits

Our proposed **Retail-Mesh** model is primarily **event-centered**.

``` text
                    CUSTOMER
                       |
                       v
PROVIDER ----> TRANSACTION <---- VEHICLE
                  |
          +-------+-------+
          |       |       |
         Sale   Rental  Service
                  |
                  v
          Performance Metric
                  |
                  v
            Incentive Rule
                  |
                  v
            Incentive Award
```

### Main difference

Existing models mainly help answer:

-   **What is the vehicle?** --- VSO / Schema.org
-   **Who offers it?** --- GoodRelations / Schema.org
-   **How can organizations exchange semantic data?** --- Catena-X

Our model focuses on:

> **What happened, which provider performed it, how did the provider
> perform, and what incentive resulted?**

Therefore, Retail-Mesh builds on useful existing vehicle and commerce
concepts while adding an **event, performance, and incentive layer for
cross-provider analysis**.

## 6. Summary

  -----------------------------------------------------------------------
  Model                   Main Focus              Relevance to
                                                  Retail-Mesh
  ----------------------- ----------------------- -----------------------
  VSO                     Vehicle description     Vehicle concepts

  Schema.org Automotive   Web/product/vehicle     Vehicle and offer
                          description             concepts

  GoodRelations           Commercial offers       Provider and offer
                                                  concepts

  Catena-X                Automotive              Cross-organization
                          interoperability        semantics

  **Retail-Mesh**         **Transactions +        **Cross-provider retail
                          performance +           intelligence**
                          incentives**            
  -----------------------------------------------------------------------

### Key Takeaway

**Existing models provide important building blocks, while Retail-Mesh
connects those building blocks around transactions, provider
performance, and incentive decisions.**
