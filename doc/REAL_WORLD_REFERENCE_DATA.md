# Real-world reference data for explaining Retail-Mesh

These public facts were checked against the listed sources on November 3, 2026. They are reference observations, not a claim about current pricing or actual customer transactions. The machine-readable companion is `data/public_reference_facts.json`.

| Reference | Public fact | Mapping and limitation |
|---|---|---|
| Toyota Canada 2026 Corolla launch announcement | Corolla LE launch MSRP: CAD 25,700 | VehicleModel/catalogue context. Do not label MSRP as an actual SalePrice. |
| Jim Pattison Auto Group outlet listing | Jim Pattison Toyota Victoria, 3050 Douglas Street, Victoria, BC V8T 4N4 | Outlet context. The public trading name/address does not establish the provider's legal registration key. |
| Toyota Extra Care Protection supplementary coverage | Vehicle rental assistance advertised at CAD 50/day for up to 5 days, with up to 5 additional days for required parts on back-order | Service/replacement-rental and policy context. Covered-component, overnight-stay and repair-duration conditions apply. This is customer assistance, not evidence of a dealer incentive. |

Sources:

- https://media.toyota.ca/en/releases/2025/what-s-new--the-2026-toyota-corolla.html
- https://www.jpautogroup.com/toyota/
- https://www.toyota.ca/en/owners/warranty-and-coverage/supplementary/
- Additional vehicle specification source: https://vpic.nhtsa.dot.gov/api/

## Explain the difference between public facts and a demo journey

A customer purchases a Corolla, later has it serviced, and uses a different vehicle as a replacement rental. This illustrates Sale, Service, Rental, local CustomerAccount records and verified identity evidence. Unless backed by authorized business records, the customer, transaction dates, VIN associations, prices and activity links must be labelled illustrative.

The existing database continues to use synthetic data, with explicit synthetic registrations. These public references are intentionally not forced into mandatory legal/source business keys using invented registration numbers.

The latest presentation's Cedar Logistics / Northstar / Maple Motors / Harbour Service / Island Rentals story and CAD 150 provider award are a separate fictional acceptance scenario. Do not present its incentive rule as a Toyota policy. Fleet history, automatic qualification and its complete evidence checks are specified in Application-Plan.md for subsequent implementation.
