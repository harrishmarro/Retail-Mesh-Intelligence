-- Event beneficiary comes from the evaluated activity, never from a contributor.
-- Components are returned individually; incompatible units are never summed.
SELECT 'Event' AS Scope,p.LegalName AS Beneficiary,r.OfficialRuleCode,
 a.AwardStatus,c.RewardType,c.BenefitValue,c.UnitCode,c.Currency
FROM EventAward a JOIN VehicleActivity v ON v.Id=a.VehicleActivityId
JOIN Outlet o ON o.Id=v.IssuingOutletId JOIN Provider p ON p.Id=o.ProviderId
JOIN IncentiveRule r ON r.Id=a.IncentiveRuleId JOIN EventAwardComponent c ON c.EventAwardId=a.Id
UNION ALL
SELECT 'Period',p.LegalName,r.OfficialRuleCode,a.AwardStatus,c.RewardType,c.BenefitValue,c.UnitCode,c.Currency
FROM PeriodAward a JOIN Provider p ON p.Id=a.ProviderId
JOIN IncentiveRule r ON r.Id=a.IncentiveRuleId JOIN PeriodAwardComponent c ON c.PeriodAwardId=a.Id;
