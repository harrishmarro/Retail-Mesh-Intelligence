-- Avoid fanout double-counting by aggregating at measurement grain.
SELECT p.LegalName, d.OfficialMetricCode, m.PeriodStart, m.PeriodEnd,
 m.MeasuredValue, d.UnitCode, COUNT(DISTINCT c.VehicleActivityId) AS ContributingActivities
FROM PerformanceMeasurement m
JOIN Provider p ON p.Id=m.ProviderId
JOIN MetricDefinitionVersion d ON d.Id=m.MetricDefinitionVersionId
LEFT JOIN MeasurementContribution c ON c.PerformanceMeasurementId=m.Id
GROUP BY m.Id,p.LegalName,d.OfficialMetricCode,m.PeriodStart,m.PeriodEnd,m.MeasuredValue,d.UnitCode;
