"""Static catalogue text for the synthetic dataset. All wording is original to this project;
company names are invented. Dates are offsets (days) from the seed's anchor day.
"""

# programme code -> (course-code prefix, [(number, title, kind)])  — six courses each
COURSES: dict[str, tuple[str, list[tuple[int, str, str]]]] = {
    "CS": (
        "CSE",
        [
            (305, "Database Management Systems", "Theory"),
            (316, "Operating Systems", "Theory"),
            (326, "Computer Networks", "Theory"),
            (331, "Design and Analysis of Algorithms", "Theory"),
            (343, "Software Engineering", "Theory"),
            (357, "Full Stack Development Lab", "Practical"),
        ],
    ),
    "EC": (
        "ECE",
        [
            (301, "Signals and Systems", "Theory"),
            (312, "Digital Signal Processing", "Theory"),
            (324, "Analog Communication", "Theory"),
            (335, "Microcontrollers and Interfacing", "Theory"),
            (348, "Electromagnetic Waves", "Theory"),
            (359, "Embedded Systems Lab", "Practical"),
        ],
    ),
    "ME": (
        "MEC",
        [
            (302, "Applied Thermodynamics", "Theory"),
            (314, "Fluid Mechanics", "Theory"),
            (325, "Strength of Materials", "Theory"),
            (336, "Manufacturing Processes", "Theory"),
            (347, "Machine Design", "Theory"),
            (358, "CAD and Drafting Lab", "Practical"),
        ],
    ),
    "BB": (
        "MGT",
        [
            (303, "Principles of Management", "Theory"),
            (315, "Financial Accounting", "Theory"),
            (327, "Marketing Management", "Theory"),
            (332, "Business Statistics", "Theory"),
            (344, "Organisational Behaviour", "Theory"),
            (356, "Business Analytics Lab", "Practical"),
        ],
    ),
    "BS": (
        "DSC",
        [
            (304, "Probability and Statistical Inference", "Theory"),
            (318, "Linear Algebra for Data Science", "Theory"),
            (329, "Machine Learning Foundations", "Theory"),
            (333, "Data Engineering", "Theory"),
            (345, "Ethics of Data and AI", "Theory"),
            (355, "Data Visualisation Lab", "Practical"),
        ],
    ),
}
COMMON_COURSE = ("GEN", 231, "Professional Communication", "Theory")

ANNOUNCEMENTS = [
    (
        "ribbon",
        "Re-appear registration",
        "Re-appear exam registration closes this Friday.",
        "reappear-registration",
    ),
    (
        "ribbon",
        "Library hours",
        "The central library stays open until midnight during exam weeks.",
        "library-search",
    ),
    (
        "ribbon",
        "Portal maintenance",
        "The portal will be briefly unavailable on Sunday, 02:00-03:00.",
        None,
    ),
    (
        "banner",
        "Term-end examinations",
        "Date sheets and seating plans are now published. Check yours before the first paper.",
        "exam-date-sheet",
    ),
    (
        "banner",
        "Hostel leave goes digital",
        "Apply for hostel leave online and track approval status in real time.",
        "hostel-leave",
    ),
    (
        "banner",
        "Placement season is open",
        "Eligible drives appear on your dashboard. Register before the deadline.",
        "placement-drives",
    ),
    (
        "banner",
        "Talk to the portal",
        "Tap the mic button and ask about attendance, fees or your requests.",
        None,
    ),
]

NEWS = [
    (
        -1,
        "Robotics team reaches national finals",
        "Our student robotics team qualified for the national finals after a three-round "
        "regional contest.",
    ),
    (
        -3,
        "New 24x7 reading room opens",
        "A quiet reading room with 120 seats is now open round the clock in the library annexe.",
    ),
    (
        -5,
        "Inter-hostel football league kicks off",
        "Twelve hostel teams will play over four weekends; fixtures are on the sports "
        "notice board.",
    ),
    (
        -8,
        "Workshop on research writing",
        "The research cell is running a two-day workshop on structuring and citing "
        "research papers.",
    ),
    (
        -11,
        "Campus goes solar on two more blocks",
        "Rooftop panels on two academic blocks now cover most of their daytime power use.",
    ),
    (
        -14,
        "Alumni mentoring programme",
        "Final-year students can now sign up for monthly sessions with alumni mentors.",
    ),
    (
        -18,
        "Blood donation drive collects 400 units",
        "Thanks to everyone who donated at last week's camp, run with the medical centre.",
    ),
    (
        -22,
        "Coding marathon results announced",
        "Winners of the 24-hour coding marathon have been announced on the clubs page.",
    ),
]

EVENTS = [
    (2, "18:00", "Open mic night", "Amphitheatre"),
    (4, "10:00", "Career fair: product and design roles", "Convention Hall"),
    (6, "15:00", "Guest lecture: building reliable software", "Auditorium 2"),
    (9, "09:00", "Annual sports meet: opening ceremony", "Main Ground"),
    (13, "17:30", "Photography club exhibition", "Arts Gallery"),
    (17, "11:00", "Hackathon briefing", "Innovation Lab"),
]

MESSAGE_TEMPLATES = [
    (
        "Extra class this week",
        "There will be an extra class for {course} on {day} at {time} in {room}. "
        "Attendance will be marked.",
    ),
    (
        "Assignment reminder",
        "Reminder: {assignment} for {course} is due on {date}. "
        "Late submissions will not be accepted.",
    ),
    (
        "Quiz syllabus",
        "The upcoming quiz in {course} covers units 3 and 4. "
        "Revise the solved examples from class.",
    ),
    (
        "Lab record submission",
        "Please bring your completed lab record for {course} to the next practical session.",
    ),
    (
        "Project groups",
        "Project groups for {course} are posted. Meet your group and send me your topic by {date}.",
    ),
    (
        "Class rescheduled",
        "Tomorrow's {course} class is moved to {time} in {room} because of a seminar.",
    ),
]

ASSIGNMENT_KINDS = ["Assignment", "Quiz", "Case Study", "Lab Report", "Term Paper"]

# Fictional companies. (company, role, package LPA, programmes, min CGPA, register-by offset)
DRIVES = [
    ("Quantiva Systems", "Graduate Software Engineer", 9.5, ["CS", "BS"], 7.0, 4),
    ("Brightlane Software", "Associate Developer", 7.2, ["CS", "EC", "BS"], 6.5, 6),
    ("Corvane Technologies", "Embedded Engineer Trainee", 6.8, ["EC"], 6.5, 5),
    ("Helioforge Engineering", "Graduate Engineer Trainee", 6.0, ["ME"], 6.0, 8),
    ("Lumora Finserv", "Business Analyst", 7.5, ["BB", "BS"], 7.0, 3),
    ("Zephyra Networks", "Network Engineer", 6.5, ["CS", "EC"], 6.0, 10),
    ("Mintleaf Retail", "Management Trainee", 5.8, ["BB"], 6.0, 12),
    ("Tessellate Labs", "Data Analyst", 8.0, ["BS", "CS"], 7.5, 7),
]

# Ticket wording per sub-category: (title, description)
TICKET_TEXT: dict[str, list[tuple[str, str]]] = {
    "Electrical": [
        ("Tube light not working", "The tube light in my room stopped working two days ago."),
        (
            "Power socket sparking",
            "The power socket near the study table sparks when anything is plugged in.",
        ),
    ],
    "Plumbing": [
        ("Tap leaking in washroom", "The washroom tap keeps leaking even when fully closed."),
        ("Washbasin drain blocked", "Water does not drain from the washbasin on our floor."),
    ],
    "Carpentry": [
        ("Cupboard door broken", "The cupboard door hinge is broken and the door does not close.")
    ],
    "Housekeeping": [
        (
            "Corridor not cleaned",
            "The corridor outside our rooms has not been cleaned for three days.",
        )
    ],
    "Furniture": [("Study chair damaged", "The study chair in my room has a cracked seat.")],
    "Water Cooler": [
        ("Water cooler not cooling", "The water cooler on our floor dispenses warm water.")
    ],
    "Pest Control": [
        ("Pest control needed", "There are cockroaches in the room; please arrange pest control.")
    ],
    "Wi-Fi": [
        (
            "Wi-Fi keeps disconnecting",
            "Wi-Fi disconnects every few minutes in my room, mostly in the evening.",
        ),
        ("No Wi-Fi signal", "My laptop cannot find the campus Wi-Fi network in my room."),
    ],
    "LAN Port": [("LAN port not working", "The LAN port in my room shows no connection.")],
    "UMS Login": [
        (
            "Cannot log in to UMS app",
            "The UMS mobile app says my session is invalid every time I log in.",
        )
    ],
    "University Email": [
        ("Email storage full", "My university email says storage is full but I have few emails.")
    ],
    "Software Installation": [
        (
            "Need licensed software",
            "I need the licensed simulation software installed for my lab course.",
        )
    ],
    "Marks Discrepancy": [
        (
            "CA marks not updated",
            "My continuous assessment marks for one course are not updated on UMS.",
        )
    ],
    "Attendance Discrepancy": [
        ("Attendance marked absent", "I attended the lecture but was marked absent.")
    ],
    "Timetable Clash": [
        ("Timetable clash", "Two of my classes are scheduled at the same time on Wednesday.")
    ],
    "Course Registration": [
        ("Elective not visible", "The elective I registered for is not showing in my courses.")
    ],
    "Duty Leave": [
        ("Duty leave not approved", "My duty leave for the sports meet has not been approved yet.")
    ],
    "Result Discrepancy": [
        ("Result shows wrong grade", "My result shows a grade different from the marks I was told.")
    ],
    "Admit Card": [("Admit card not generated", "My admit card is not available for download.")],
    "Seating Plan": [
        ("Seat not allotted", "No seat is shown for one of my papers in the seating plan.")
    ],
    "Re-appear Form": [
        ("Re-appear form error", "The re-appear form shows an error when I submit it.")
    ],
    "Payment Not Updated": [
        ("Fee payment not reflected", "I paid my fee online but the portal still shows it as due.")
    ],
    "Refund": [
        ("Refund of excess fee", "I paid my hostel fee twice by mistake and need a refund.")
    ],
    "Fee Receipt": [
        ("Fee receipt missing", "The receipt for my last payment is not available to download.")
    ],
    "Scholarship": [
        ("Scholarship not applied", "My scholarship has not been applied to this term's fee.")
    ],
    "Fine Waiver": [("Library fine waiver", "I was charged a fine for a book I returned on time.")],
    "Book Not Available": [
        ("Reference book unavailable", "The reference book for my course has no copies available.")
    ],
    "Account Issue": [
        ("Library account blocked", "My library account is blocked and I cannot issue books.")
    ],
    "Bus Pass": [
        ("Bus pass not issued", "I paid the transport fee but have not received my bus pass.")
    ],
    "Route or Timing": [
        (
            "Bus leaves early",
            "The evening bus on my route leaves ten minutes before the listed time.",
        )
    ],
    "Driver Conduct": [
        ("Rash driving", "The driver on my route drives very fast on the highway stretch.")
    ],
    "General Query": [("Lost ID card", "I lost my ID card and need to know the re-issue process.")],
}

CLOSING_REMARKS = [
    "Issue checked and fixed by the maintenance team.",
    "Resolved after on-site inspection. Please raise a new request if it happens again.",
    "Updated in the system. The change is now visible on the portal.",
    "Replaced the faulty part and tested it with the student present.",
    "Clarified with the student by phone; no further action needed.",
]

LEAVE_REASONS = [
    "Going home for a family function",
    "Medical appointment in my home town",
    "Attending a sibling's wedding",
    "Festival holidays with family",
    "Personal work at home",
]
