-- A healthy database returns zero rows. Useful after SQL imports.
SELECT 'Wrong subtype' AS Problem,a.Id AS RecordId FROM VehicleActivity a
WHERE (a.ActivityKind='Sale' AND NOT EXISTS(SELECT 1 FROM Sale s WHERE s.Id=a.SaleId AND s.VehicleActivityId=a.Id))
OR (a.ActivityKind='Rental' AND NOT EXISTS(SELECT 1 FROM Rental r WHERE r.Id=a.RentalId AND r.VehicleActivityId=a.Id))
OR (a.ActivityKind='Service' AND NOT EXISTS(SELECT 1 FROM Service s WHERE s.Id=a.ServiceId AND s.VehicleActivityId=a.Id))
UNION ALL SELECT 'Event award without benefit',a.Id FROM EventAward a
WHERE NOT EXISTS(SELECT 1 FROM EventAwardComponent c WHERE c.EventAwardId=a.Id)
UNION ALL SELECT 'Period award without benefit',a.Id FROM PeriodAward a
WHERE NOT EXISTS(SELECT 1 FROM PeriodAwardComponent c WHERE c.PeriodAwardId=a.Id);
