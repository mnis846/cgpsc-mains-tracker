"""Seed syllabus for the Atlas — exam-shaped trees, not an encyclopedia.

Stable slugs. New topics can be appended; never rename a slug or progress breaks.
Bump ATLAS_SEED_VERSION when you add nodes so existing DBs pick them up.
"""

ATLAS_SEED_VERSION = 1

# (slug, title) — kind is always "topic" under a unit.
# Slugs are the identity. Titles can be edited later in a migration.

_ANCIENT = [
    ("sources", "Sources of Ancient Indian History"),
    ("prehistoric", "Prehistoric Cultures (Paleolithic to Chalcolithic)"),
    ("indus", "Indus Valley Civilization"),
    ("indus-sites", "Harappan Sites, Crafts & Decline"),
    ("early-vedic", "Early Vedic Age"),
    ("later-vedic", "Later Vedic Age"),
    ("mahajanapadas", "Mahajanapadas & Rise of Magadha"),
    ("jainism", "Jainism — Doctrine, Councils, Spread"),
    ("buddhism", "Buddhism — Doctrine, Councils, Spread"),
    ("maurya-polity", "Mauryan Empire — Polity & Ashoka"),
    ("maurya-econ", "Mauryan Economy, Society & Art"),
    ("post-maurya-north", "Post-Mauryan North (Shunga, Indo-Greek, Shaka, Kushana)"),
    ("satavahana", "Satavahanas & Deccan"),
    ("sangam", "Sangam Age"),
    ("gupta-polity", "Gupta Empire — Polity & Expansion"),
    ("gupta-culture", "Gupta Age — Economy, Society, Science, Culture"),
    ("harsha", "Harshavardhana & Post-Gupta North"),
    ("south-dynasties", "Pallavas, Chalukyas, Rashtrakutas"),
    ("ancient-society", "Ancient Society, Varna, Women, Education"),
    ("ancient-economy", "Ancient Economy, Guilds, Trade Routes"),
    ("ancient-science", "Ancient Science, Literature & Philosophy"),
]

_MEDIEVAL = [
    ("early-medieval", "Early Medieval North — Rajputs & Tripartite Struggle"),
    ("cholas", "Cholas — Administration, Navy, Culture"),
    ("sultanate-found", "Delhi Sultanate — Foundation (Slave dynasty)"),
    ("khilji-tughlaq", "Khilji & Tughlaq Experiments"),
    ("later-sultanate", "Sayyid, Lodi & Decline of the Sultanate"),
    ("sultanate-admin", "Sultanate Administration, Iqta, Economy"),
    ("sultanate-culture", "Sultanate Society, Architecture, Language"),
    ("vijayanagara", "Vijayanagara Empire"),
    ("bahmani", "Bahmani & Deccan Sultanates"),
    ("bhakti", "Bhakti Movement"),
    ("sufi", "Sufi Movement"),
    ("sher-shah", "Sher Shah Suri"),
    ("mughal-found", "Mughals — Babur, Humayun, Akbar"),
    ("mughal-later", "Jahangir, Shah Jahan, Aurangzeb"),
    ("mughal-admin", "Mansabdari, Jagirdari & Mughal Administration"),
    ("mughal-econ", "Mughal Economy, Trade, Agrarian System"),
    ("mughal-culture", "Mughal Art, Architecture, Painting, Literature"),
    ("maratha", "Marathas — Shivaji, Administration, Expansion"),
    ("18th-century", "18th Century States (Sikhs, Bengal, Awadh, Hyderabad, Mysore)"),
    ("europeans-arrive", "Arrival of Europeans & Early Company"),
]

_MODERN = [
    ("carnatic", "Carnatic Wars & Anglo-French Rivalry"),
    ("plassey-buxar", "Plassey, Buxar & Dual Government"),
    ("expansion", "British Expansion (Wellesley to Dalhousie)"),
    ("1857", "Revolt of 1857"),
    ("crown-rule", "Crown Rule & Important Viceroys"),
    ("drain", "Drain of Wealth & Deindustrialization"),
    ("land-revenue", "Land Revenue — Permanent, Ryotwari, Mahalwari"),
    ("peasant", "Peasant Movements"),
    ("tribal", "Tribal Uprisings"),
    ("reform-hindu", "Socio-Religious Reform — Hindu Streams"),
    ("reform-muslim", "Socio-Religious Reform — Muslim, Sikh, Parsi"),
    ("education-press", "Education Policy, Press & Social Legislation"),
    ("inc-moderates", "INC Formation & Moderate Phase"),
    ("swadeshi", "Swadeshi, Extremists & Surat Split"),
    ("revolutionaries", "Revolutionary Movement (India & Abroad)"),
    ("home-rule", "Home Rule Leagues"),
    ("gandhi-early", "Gandhi's Early Satyagrahas (Champaran, Kheda, Ahmedabad)"),
    ("ncm", "Non-Cooperation & Khilafat"),
    ("swarajists", "Swarajists, Simon Commission, Nehru Report"),
    ("cdm", "Civil Disobedience & Dandi March"),
    ("rtc-poona", "Round Table, Communal Award, Poona Pact"),
    ("quit-india", "Quit India Movement"),
    ("ina-subhas", "Subhas Chandra Bose & INA"),
    ("partition", "Towards Independence & Partition"),
    ("constitutional", "Constitutional Development (1773–1935)"),
    ("labour", "Labour Movement"),
    ("women-freedom", "Women in the Freedom Struggle"),
    ("left", "Socialist & Left Currents"),
    ("princes", "Princely States & Integration Backdrop"),
    ("cp-freedom", "Freedom Struggle in Central Provinces / Chhattisgarh"),
    ("post-1947-legacy", "Legacy: Constitution, Planning, Integration (overview)"),
]

_ART = [
    ("architecture-hindu", "Temple Architecture — Nagara, Dravida, Vesara"),
    ("buddhist-jain-art", "Stupa, Cave, Buddhist & Jain Art"),
    ("indo-islamic", "Indo-Islamic Architecture"),
    ("sculpture", "Indian Sculpture Traditions"),
    ("paintings", "Paintings — Ajanta, Mughal, Rajput, Pahari, Company"),
    ("dance", "Classical Dance Forms"),
    ("music", "Hindustani & Carnatic Music"),
    ("literature", "Literature — Sanskrit, Tamil, Persian, Vernacular"),
    ("crafts", "Crafts, Textiles & GI traditions (exam-facing)"),
    ("festivals", "Festivals, Fairs & Living Traditions"),
    ("unesco", "UNESCO & Important Heritage Sites"),
    ("cg-art", "Art, Dance & Festivals of Chhattisgarh"),
]

_CG_HISTORY = [
    ("south-kosala", "Ancient South Kosala / Dakshina Kosala"),
    ("kalchuri", "Kalchuri of Ratanpur & Raipur"),
    ("medieval-cg", "Medieval Chhattisgarh — Dynasties & Culture"),
    ("maratha-british-cg", "Maratha & British Period in CG"),
    ("veer-narayan", "Veer Narayan Singh & 1857 in CG"),
    ("bhumkal", "Tribal Revolts (Bhumkal and others)"),
    ("freedom-cg", "20th Century Freedom Movement in CG"),
    ("personalities-cg", "Important Personalities of CG History"),
    ("statehood", "State Formation (2000) — Political Background"),
    ("heritage-sites-cg", "Historical Sites & Heritage of CG"),
]

_POLITY = [
    ("making", "Making of the Constitution"),
    ("preamble", "Preamble, Union & Territory"),
    ("citizenship", "Citizenship"),
    ("fr", "Fundamental Rights"),
    ("dpsp", "DPSP & Fundamental Duties"),
    ("amendment", "Amendment Procedure & Basic Structure"),
    ("president-gov", "President, Vice-President, Governor"),
    ("parliament", "Parliament & State Legislature"),
    ("pm-com", "PM, CoM, Chief Minister, State CoM"),
    ("judiciary", "Supreme Court, High Courts, Judicial Review"),
    ("federalism", "Federalism, Centre-State Relations"),
    ("local", "Panchayats & Municipalities"),
    ("constitutional-bodies", "Constitutional Bodies (EC, CAG, UPSC, FC)"),
    ("statutory-bodies", "Statutory & Regulatory Bodies (exam set)"),
    ("emergency", "Emergency Provisions"),
    ("services", "All-India Services & Public Administration Basics"),
    ("transparency", "RTI, Lokpal, Accountability"),
    ("rights-issues", "Rights Issues — Women, Child, SC/ST, Minorities"),
    ("cg-admin", "Chhattisgarh Administration & Local Bodies"),
    ("schemes-gov", "Important Governance Schemes (rolling CA)"),
]

_GEOGRAPHY = [
    ("earth", "Earth, Landforms & Interior (basics)"),
    ("climate-world", "World Climate & Ocean Basics"),
    ("physiography", "Physiography of India"),
    ("monsoon", "Indian Monsoon & Climate"),
    ("rivers", "Drainage — Himalayan & Peninsular"),
    ("soils", "Soils of India"),
    ("natural-veg", "Natural Vegetation & Wildlife"),
    ("resources", "Minerals & Energy Resources"),
    ("agriculture", "Indian Agriculture & Crops"),
    ("industry", "Industries & Industrial Regions"),
    ("transport", "Transport, Ports & Communication"),
    ("population", "Population, Settlements, Migration"),
    ("maps", "Map Work — India (must-do)"),
    ("environment-basics", "Environment, Ecology & Biodiversity Basics"),
    ("disasters", "Natural Hazards & Disaster Basics"),
    ("cg-physio", "Chhattisgarh Physiography, Rivers, Climate"),
]

_ECONOMY = [
    ("basic-concepts", "Basic Economic Concepts (GDP, inflation, fiscal)"),
    ("planning", "Planning to NITI — Indian Planning History"),
    ("agri-econ", "Agriculture Economy, MSP, Food Security"),
    ("industry-econ", "Industry, MSME, Labour"),
    ("services-econ", "Services, Infra, Digital Economy"),
    ("money-banking", "Money, Banking, RBI, Monetary Policy"),
    ("budget", "Budget, Fiscal Policy, Taxation (GST basics)"),
    ("external", "External Sector, Trade, WTO (basics)"),
    ("poverty", "Poverty, Inequality, Inclusion"),
    ("human-dev", "HDI, Education, Health Economics"),
    ("reforms", "1991 Reforms & Liberalisation"),
    ("current-survey", "Latest Economic Survey / Budget highlights"),
    ("cg-economy", "Chhattisgarh Economy — Agri, Mines, Industry"),
    ("cg-budget", "CG Budget, Resources & Development Schemes"),
]

_SCIENCE = [
    ("physics-daily", "Physics in Daily Life (exam set)"),
    ("chemistry-daily", "Chemistry in Daily Life"),
    ("bio-human", "Human Body, Diseases, Nutrition"),
    ("bio-plant", "Plant Biology & Agriculture Science Bits"),
    ("space", "Space, ISRO, Defence Tech (overview)"),
    ("it-telecom", "IT, Computers, Telecom Basics"),
    ("biotech", "Biotech, Vaccines, GM crops"),
    ("energy-tech", "Energy Tech — Nuclear, Solar, New Energy"),
    ("environment-issues", "Pollution, Climate Change, Conventions"),
    ("conservation", "Conservation, Protected Areas, Species"),
    ("cg-environment", "CG Forests, Wildlife, Environmental Issues"),
    ("applied-science", "Applied Science in Governance / Daily Admin"),
]

_SOCIETY = [
    ("indian-society", "Features of Indian Society"),
    ("diversity", "Diversity, Pluralism, Communalism, Regionalism"),
    ("caste", "Caste, Tribe, Social Stratification"),
    ("women-society", "Women, Gender & Social Change"),
    ("urbanisation", "Urbanisation & Migration (social)"),
    ("globalisation-social", "Globalisation & Indian Society"),
    ("philosophy-schools", "Indian Philosophical Schools (overview)"),
    ("ethics-thinkers", "Moral Thinkers — Indian & Western (mains-facing)"),
    ("cg-tribes", "Tribes of Chhattisgarh — Society & Issues"),
    ("cg-social", "Social Structure, Festivals, Issues of CG"),
]

_WELFARE = [
    ("constitution-welfare", "Constitutional Basis of Welfare"),
    ("poverty-schemes", "Poverty Alleviation Schemes"),
    ("health-edu-schemes", "Health & Education Schemes"),
    ("women-child-schemes", "Women & Child Welfare"),
    ("sc-st-obc", "SC / ST / OBC / Minority Welfare"),
    ("labour-welfare", "Labour Welfare & Social Security"),
    ("disability-elderly", "Disability, Elderly, Social Defence"),
    ("ngo-shg", "NGOs, SHGs, Civil Society"),
    ("sports-orgs", "Organisations, Sports, Awards (Paper-7 set)"),
    ("hrd-edu", "Education Policy & HRD (NEP basics)"),
    ("cg-welfare", "Chhattisgarh Welfare Schemes & Social Sector"),
]


def _topics(prefix, pairs):
    return [
        {"slug": f"{prefix}.{slug}", "title": title, "kind": "topic"}
        for slug, title in pairs
    ]


def _unit(slug, title, pairs):
    return {
        "slug": slug,
        "title": title,
        "kind": "unit",
        "children": _topics(slug, pairs),
    }


def _region(slug, title, paper, units, accent="amber"):
    return {
        "slug": slug,
        "title": title,
        "kind": "region",
        "paper": paper,
        "accent": accent,
        "children": units,
    }


ATLAS_TREE = [
    _region(
        "hist",
        "Indian History",
        "Paper-3 (GS-I)",
        [
            _unit("hist.ancient", "Ancient India", _ANCIENT),
            _unit("hist.medieval", "Medieval India", _MEDIEVAL),
            _unit("hist.modern", "Modern India", _MODERN),
        ],
        accent="amber",
    ),
    _region(
        "art",
        "Art & Culture",
        "Paper-3 (GS-I)",
        [_unit("art.india", "Indian Art & Culture", _ART)],
        accent="violet",
    ),
    _region(
        "cghist",
        "Chhattisgarh History",
        "Paper-3 (GS-I)",
        [_unit("cghist.core", "CG History & Heritage", _CG_HISTORY)],
        accent="coral",
    ),
    _region(
        "polity",
        "Polity & Governance",
        "Paper-3 (GS-I)",
        [_unit("polity.core", "Constitution & Administration", _POLITY)],
        accent="sky",
    ),
    _region(
        "geo",
        "Geography",
        "Paper-5 (GS-III)",
        [_unit("geo.core", "India & World Geography", _GEOGRAPHY)],
        accent="teal",
    ),
    _region(
        "eco",
        "Economy",
        "Paper-5 (GS-III)",
        [_unit("eco.core", "Indian & CG Economy", _ECONOMY)],
        accent="coral",
    ),
    _region(
        "sci",
        "Science & Environment",
        "Paper-4 (GS-II)",
        [_unit("sci.core", "GS Science & Environment", _SCIENCE)],
        accent="accent",
    ),
    _region(
        "society",
        "Society & Philosophy",
        "Paper-6 (GS-IV)",
        [_unit("society.core", "Society, Ethics, CG Social", _SOCIETY)],
        accent="violet",
    ),
    _region(
        "welfare",
        "Welfare & HRD",
        "Paper-7 (GS-V)",
        [_unit("welfare.core", "Welfare, Organisations, Education", _WELFARE)],
        accent="success",
    ),
]


def iter_nodes(tree=None, parent_slug=None, paper=None, accent=None, depth=0):
    """Yield flat node dicts in depth-first order with parent + inherited paper."""
    if tree is None:
        tree = ATLAS_TREE
    for index, raw in enumerate(tree):
        node_paper = raw.get("paper") or paper
        node_accent = raw.get("accent") or accent
        yield {
            "slug": raw["slug"],
            "parent_slug": parent_slug,
            "title": raw["title"],
            "kind": raw["kind"],
            "paper": node_paper or "",
            "accent": node_accent or "accent",
            "sort_order": index,
            "depth": depth,
        }
        children = raw.get("children") or []
        if children:
            yield from iter_nodes(
                children,
                parent_slug=raw["slug"],
                paper=node_paper,
                accent=node_accent,
                depth=depth + 1,
            )


def node_count():
    return sum(1 for _ in iter_nodes())
