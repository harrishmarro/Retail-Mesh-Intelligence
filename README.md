# Retail-Mesh-Intelligence
A Webfront tool to manage and maintain the Retail and Dealer Data 

## Architecture Overview

The platform connects the **Parent Company, Dealers, Retailers, Service Providers, and Customers** through a centralized **Vehicle Retail Platform**.

* **Parent Company:** Manages policies, programs, incentives, and analytics.
* **Vehicle Retail Platform:** Handles vehicle sales, rentals, services, and customer interactions.
* **Incentive & Benefits Engine:** Processes business rules to provide rewards, benefits, and provider performance scores.
* **Knowledge Graph + AI:** Uses connected platform data to power chatbot assistance, recommendations, insights, anomaly detection, and intelligent knowledge retrieval.

Overall, the system creates a unified ecosystem for **vehicle commerce, services, incentives, analytics, and AI-powered decision support**.


                         ┌──────────────────────────┐
                         │      PARENT COMPANY      │
                         │ Policies / Programs /    │
                         │ Incentives / Analytics   │
                         └────────────┬─────────────┘
                                      │
                    ┌─────────────────┼─────────────────┐
                    │                 │                 │
                    ▼                 ▼                 ▼
              DEALERS            RETAILERS          SERVICE PROVIDERS
                    │                 │                 │
                    └─────────────────┼─────────────────┘
                                      │
                                      ▼
                         ┌──────────────────────────┐
                         │ VEHICLE RETAIL PLATFORM  │
                         └────────────┬─────────────┘
                                      │
              ┌───────────────────────┼──────────────────────┐
              │                       │                      │
              ▼                       ▼                      ▼
        SALES & RENTALS          SERVICES             CUSTOMER
              │                       │                      │
              └───────────────────────┼──────────────────────┘
                                      │
                                      ▼
                         ┌──────────────────────────┐
                         │ INCENTIVE / BENEFITS    │
                         │        ENGINE            │
                         └────────────┬─────────────┘
                                      │
                         ┌────────────┴────────────┐
                         ▼                         ▼
                  Rewards / Benefits          Provider Score
                         │
                         ▼
              ┌─────────────────────────┐
              │ KNOWLEDGE GRAPH + AI    │
              ├─────────────────────────┤
              │ Chatbot                 │
              │ Recommendations         │
              │ Insights                │
              │ Anomaly Detection       │
              │ Knowledge Retrieval     │
              └─────────────────────────┘
