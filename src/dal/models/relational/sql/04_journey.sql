-- Source-specific accounts are connected only by an explicit verified identity assertion.
SELECT a.OfficialActivityReference, a.ActivityKind, p.LegalName AS Provider,
 v.VIN, ca.ExistingCustomerReference, a.StartedAt,
 serviceActivity.OfficialActivityReference AS ReplacementForService,
 rental.ReplacementPurpose
FROM VehicleActivity a
JOIN Outlet o ON o.Id=a.IssuingOutletId
JOIN Provider p ON p.Id=o.ProviderId
JOIN CustomerAccount ca ON ca.Id=a.CustomerAccountId
JOIN Vehicle v ON v.Id=a.VehicleId
LEFT JOIN Rental rental ON rental.VehicleActivityId=a.Id
LEFT JOIN Service service ON service.Id=rental.ReplacementForServiceId
LEFT JOIN VehicleActivity serviceActivity ON serviceActivity.Id=service.VehicleActivityId
WHERE ca.Id=1 OR EXISTS (
 SELECT 1 FROM CustomerIdentityLink l
 WHERE l.VerificationStatus='Verified' AND l.RevokedAt IS NULL
 AND ((l.AccountAId=1 AND l.AccountBId=ca.Id) OR (l.AccountBId=1 AND l.AccountAId=ca.Id)))
ORDER BY a.StartedAt,a.Id;
