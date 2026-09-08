## If there were no smartphones but LLMs exist/everything else exists except apps and you are an HR who has to track attendance of 1000 people everyday in 100 locations, what would you do?

If smartphones and apps did not exist, but we still had access to LLMs and other basic technology, I would avoid trying to recreate a smartphone-based attendance system. I would design something simple that works reliably across 100 locations.

For 1,000 employees, I would use a centralized attendance system where each location has one fixed device, such as a basic computer, tablet, kiosk, or even a shared terminal. Employees could mark attendance using an employee ID, QR/barcode card, RFID card, fingerprint device, or a simple numeric code. The exact hardware would depend on what is available at the locations.

When an employee checks in or checks out, the local device records the employee ID, location, timestamp, and event type. If internet connectivity is available, the data is immediately sent to the central HR system. If a location loses connectivity, the device should store the records locally and synchronize them once the connection comes back. This is important because I would not want network failures to become attendance failures.

The central system would maintain the complete attendance database for all 100 locations. HR could see daily attendance, late arrivals, absences, overtime, and location-wise reports from one place.

I would use the LLM mainly for reducing HR's manual work rather than for the actual attendance capture. For example, the LLM could analyze attendance data and generate a daily summary such as: which locations have unusual absenteeism, employees with repeated late arrivals, missing check-outs, or possible attendance anomalies. It could also allow HR to ask questions in natural language, such as "Who was absent more than three times this month?" or "Which locations had the highest absenteeism this week?"

For cases where physical attendance cannot be captured automatically, I would also keep a backup process. Each location could have a supervisor maintain a simple attendance register or enter attendance through the central terminal. The system could then use the employee ID and timestamp to digitize those records later.

The overall workflow would be:

Employee → Local attendance device → Local storage → Central HR system → Attendance database → HR dashboard/reports → LLM-based analysis

The main principle I would follow is to keep attendance collection deterministic and simple, and use the LLM only where it adds value, such as reporting, anomaly detection, and answering HR queries. That would make the system practical even without smartphones or mobile applications.
